"""Independent replay of adaptive-frontier results and certificates."""
from __future__ import annotations

from hashlib import sha256
import json
from itertools import product
from pathlib import Path


HERE = Path(__file__).resolve().parent
EQ = {(0, 0), (1, 1)}
NEQ = {(0, 1), (1, 0)}
EXACT1 = {(0, 0, 1), (0, 1, 0), (1, 0, 0)}


def graph(n, constraints):
    adjacency = [0] * n
    for scope, _ in constraints:
        for i, left in enumerate(scope):
            for right in scope[i + 1:]:
                adjacency[left] |= 1 << right
                adjacency[right] |= 1 << left
    return tuple(adjacency)


def boundary(adj, subset):
    return sum(bool(subset >> v & 1 and adj[v] & ~subset)
               for v in range(len(adj)))


def discover(adj):
    n = len(adj)
    if n == 0:
        return {"width": 0, "order": [], "subsets": 1, "transitions": 0}
    size = 1 << n
    dp, choice = [n + 1] * size, [-1] * size
    dp[0] = 0
    values = [boundary(adj, s) for s in range(size)]
    transitions = 0
    for subset in range(1, size):
        rest, best, pick = subset, n + 1, -1
        while rest:
            bit = rest & -rest
            previous = subset ^ bit
            value = max(dp[previous], values[subset])
            transitions += 1
            if value < best:
                best, pick = value, bit.bit_length() - 1
            rest ^= bit
        dp[subset], choice[subset] = best, pick
    subset, reverse = size - 1, []
    while subset:
        vertex = choice[subset]
        reverse.append(vertex)
        subset ^= 1 << vertex
    return {"width": dp[-1], "order": list(reversed(reverse)),
            "subsets": size, "transitions": transitions}


def direct(n, constraints):
    return any(all(tuple(assignment[v] for v in scope) in relation
                   for scope, relation in constraints)
               for assignment in product((0, 1), repeat=n))


def frontier_certificate(n, constraints, order):
    """Recompute every frontier cut without importing the implementation."""
    positions = {vertex: i for i, vertex in enumerate(order)}
    last = [max((positions[v] for v in scope), default=-1)
            for scope, _ in constraints]
    boundaries = [tuple(v for v in order[:cut]
                       if any(v in scope and any(positions[u] >= cut for u in scope)
                              for scope, _ in constraints))
                  for cut in range(n + 1)]
    states = [()]
    cuts = [{"boundary": list(boundaries[0]), "states": [[]], "transitions": []}]
    for cut, variable in enumerate(order):
        old_boundary, new_boundary = boundaries[cut], boundaries[cut + 1]
        candidates = []
        for state_index, state in enumerate(states):
            assignment = dict(zip(old_boundary, state))
            for bit in (0, 1):
                assignment[variable] = bit
                accepted = True
                for (scope, relation), end in zip(constraints, last):
                    if end != cut:
                        continue
                    if tuple(assignment[v] for v in scope) not in relation:
                        accepted = False
                        break
                if accepted:
                    candidates.append((state_index, bit,
                                       tuple(assignment[v] for v in new_boundary)))
        unique = sorted({state for _, _, state in candidates})
        index = {state: i for i, state in enumerate(unique)}
        transitions = [{"from": state_index, "bit": bit, "to": index[state]}
                       for state_index, bit, state in candidates]
        states = unique
        cuts.append({"boundary": list(new_boundary),
                     "states": [list(state) for state in states],
                     "transitions": transitions})
    constraint_rows = [{"scope": list(scope),
                        "relation": [list(row) for row in sorted(relation)]}
                       for scope, relation in constraints]
    return {"n": n, "order": list(order), "constraints": constraint_rows,
            "cuts": cuts, "sat": bool(states and states == [()]),
            "max_width": max(map(len, boundaries), default=0),
            "max_states": max((len(cut["states"]) for cut in cuts), default=0)}


def rows():
    sparse = tuple(((i, i + 1), EQ) for i in range(4))
    contradictory = (((0,), {(0,)}), ((0,), {(1,)}))
    dense_relation = {row for row in product((0, 1), repeat=6)
                      if sum(row) % 2 == 0}
    return (
        ("empty", 0, tuple(), 12),
        ("sparse_equalities", 5, sparse, 12),
        ("contradictory_units", 1, contradictory, 12),
        ("dense_parity_scope", 6, ((tuple(range(6)), dense_relation),), 12),
        ("exact_one_plus_equality", 3,
         (((0, 1, 2), EXACT1), ((1, 2), EQ)), 12),
        ("explicit_order_cap", 13, tuple(), 12),
    )


def main():
    artifact = json.loads((HERE / "ADAPTIVE_FRONTIER_RESULTS.json").read_text(encoding="utf-8"))
    certificates = json.loads((HERE / "ADAPTIVE_FRONTIER_CERTIFICATES.json").read_text(encoding="utf-8"))
    expected_rows = []
    for (name, n, constraints, cap), saved in zip(rows(), certificates):
        expected_graph = graph(n, constraints)
        result = saved["result"]
        assert saved["name"] == name
        assert result["certificate"]["graph"] == {"n": n, "adjacency": list(expected_graph)}
        if n > cap:
            assert result["status"] == "UNKNOWN"
            assert result["reason"] == "ORDER_DISCOVERY_CAP"
            assert result["certificate"]["order"] is None
            width = max_states = order_search = None
            sat = None
        else:
            expected_order = discover(expected_graph)
            assert result["order_search"] == expected_order
            assert result["certificate"]["order"] == expected_order["order"]
            assert result["width"] == expected_order["width"]
            assert result["status"] in ("SAT", "UNSAT")
            assert result["sat"] == direct(n, constraints)
            assert result["certificate"]["frontier"] == frontier_certificate(
                n, constraints, tuple(expected_order["order"]))
            width, max_states, order_search = result["width"], result["max_states"], expected_order
            sat = result["sat"]
        expected_rows.append({"name": name, "n": n,
                              "constraint_count": len(constraints),
                              "status": result["status"], "sat": sat,
                              "reason": result.get("reason"), "width": width,
                              "max_states": max_states,
                              "order_search": order_search})
    assert artifact["rows"] == expected_rows
    assert artifact["all_bounded_results_match_direct"]
    for name, digest in artifact["source_sha256"].items():
        assert sha256((HERE / name).read_bytes()).hexdigest() == digest
    output = {"status": "PASS", "case_count": len(expected_rows),
              "certificates_match": True, "source_hashes_match": True}
    (HERE / "ADAPTIVE_FRONTIER_REVIEW.json").write_text(
        json.dumps(output, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(output))


if __name__ == "__main__":
    main()
