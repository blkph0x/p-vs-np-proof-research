"""Exact finite controls for the direct-terminal min-cut gadget obstruction.

No max-flow implementation or optimization package is used. Every auxiliary
assignment is explicitly enumerated. The main audit covers up to three input
terminals and two auxiliary vertices, at most three useful directed arcs,
and capacities in {1,2}; it does not enumerate all graphs of these dimensions.
"""

from fractions import Fraction
from functools import lru_cache
from hashlib import sha256
from itertools import combinations, product
import json
from math import comb
from pathlib import Path


def _natural(value, name):
    if type(value) is not int or value < 0:
        raise ValueError(name + " must be a nonnegative integer")
    return value


def terminal_cut_values(terminals, auxiliaries, arcs):
    """Return min_y cut(x,y) for each x, with source=0 and sink=1.

    Variable vertices are 0..terminals+auxiliaries-1; source and sink have
    the next two IDs. Arcs are (tail,head,nonnegative exact capacity).
    """
    _natural(terminals, "terminals")
    _natural(auxiliaries, "auxiliaries")
    variables = terminals + auxiliaries
    source, sink = variables, variables + 1
    validated = []
    for arc in arcs:
        if type(arc) not in (tuple, list) or len(arc) != 3:
            raise ValueError("arcs require tail, head, capacity")
        u, v, capacity = arc
        if (type(u) is not int or type(v) is not int or
                not 0 <= u <= sink or not 0 <= v <= sink):
            raise ValueError("arc endpoint outside graph")
        if type(capacity) not in (int, Fraction) or capacity < 0:
            raise ValueError("capacity must be nonnegative exact int/Fraction")
        validated.append((u, v, capacity))
    values = []
    for x in range(1 << terminals):
        best = None
        for y in range(1 << auxiliaries):
            assignment = x | (y << terminals) | (1 << sink)
            cost = sum(capacity for u, v, capacity in validated
                       if not (assignment >> u & 1) and (assignment >> v & 1))
            if best is None or cost < best:
                best = cost
        values.append(best)
    return values


def first_submodularity_violation(values):
    """Return a falsifying lattice pair, or None; use exact arithmetic."""
    length = len(values)
    if not length or length & (length - 1):
        raise ValueError("a Boolean truth table must have power-of-two length")
    for x in range(length):
        for y in range(length):
            left = values[x] + values[y]
            right = values[x & y] + values[x | y]
            if left < right:
                return {"x": x, "y": y, "meet": x & y, "join": x | y,
                        "left": left, "right": right, "slack": left - right}
    return None


def useful_arc_positions(variables):
    """Omit zero-contribution arcs and the source->sink constant arc."""
    source, sink = variables, variables + 1
    return ([(u, v) for u in range(variables) for v in range(variables) if u != v]
            + [(source, v) for v in range(variables)]
            + [(u, sink) for u in range(variables)])


def exhaustive_audit(max_terminals=3, max_auxiliaries=2, max_arcs=3):
    for name, value in [("max_terminals", max_terminals),
                        ("max_auxiliaries", max_auxiliaries), ("max_arcs", max_arcs)]:
        _natural(value, name)
    graphs = cuts = pair_checks = 0
    records = []
    for terminals in range(max_terminals + 1):
        for auxiliaries in range(max_auxiliaries + 1):
            variables = terminals + auxiliaries
            positions = useful_arc_positions(variables)
            count = 0
            for size in range(min(max_arcs, len(positions)) + 1):
                for selected in combinations(positions, size):
                    for capacities in product((1, 2), repeat=size):
                        arcs = [(u, v, weight) for (u, v), weight in zip(selected, capacities)]
                        values = terminal_cut_values(terminals, auxiliaries, arcs)
                        violation = first_submodularity_violation(values)
                        if violation is not None:
                            raise AssertionError((terminals, auxiliaries, arcs, values, violation))
                        count += 1
            expected = sum(comb(len(positions), size) * (2 ** size)
                           for size in range(min(max_arcs, len(positions)) + 1))
            assert count == expected
            records.append({"terminals": terminals, "auxiliaries": auxiliaries,
                            "useful_arc_positions": len(positions), "graphs": count})
            graphs += count
            cuts += count * (1 << variables)
            pair_checks += count * (1 << (2 * terminals))
    return {"status": "PASS", "family": "all simple directed graphs on the stated vertices with at most max_arcs useful arcs, capacities 1 or 2",
            "max_terminals": max_terminals, "max_auxiliaries": max_auxiliaries,
            "max_arcs": max_arcs, "graphs": graphs, "cuts_enumerated": cuts,
            "submodularity_pairs_checked": pair_checks, "cases": records}


def parity_controls():
    cases = []
    for desired_parity in (0, 1):
        for complemented_inputs in range(8):
            values = [int(((x ^ complemented_inputs).bit_count() & 1) != desired_parity)
                      for x in range(8)]
            violation = first_submodularity_violation(values)
            assert violation is not None and violation["slack"] == -2
            cases.append({"desired_parity": desired_parity,
                          "complemented_inputs": complemented_inputs,
                          "values": values, "violation": violation})
    return cases


def perfect_matching_count(vertices, edges, deleted=0):
    """Tiny exact matching counter, independent of the graph-cut evaluator."""
    adjacency = [0] * vertices
    for u, v in edges:
        adjacency[u] |= 1 << v
        adjacency[v] |= 1 << u

    @lru_cache(None)
    def count(mask):
        if not mask:
            return 1
        if mask.bit_count() & 1:
            return 0
        u_bit = mask & -mask
        u = u_bit.bit_length() - 1
        possible = adjacency[u] & mask & ~u_bit
        result = 0
        while possible:
            v_bit = possible & -possible
            result += count(mask ^ u_bit ^ v_bit)
            possible ^= v_bit
        return result

    return count(((1 << vertices) - 1) & ~deleted)


def alternative_encoding_controls():
    # Ports 0,1,2 are deleted when their Boolean value is one. Vertex3 is
    # internal. All matching edges have cost zero; counts need not be equal.
    k4 = list(combinations(range(4), 2))
    matching_counts = [perfect_matching_count(4, k4, deleted=x) for x in range(8)]
    assert matching_counts == [3, 0, 0, 1, 0, 1, 1, 0]
    # One-hot code a -> (a,1-a). A cut edge between a and 1-b restricts
    # to [a=b], which is not submodular in logical coordinates.
    full_values = terminal_cut_values(4, 0, [(0, 3, 1), (3, 0, 1)])
    assert first_submodularity_violation(full_values) is None
    restricted = []
    for x in range(4):
        a, b = x & 1, (x >> 1) & 1
        encoded = a | ((1 - a) << 1) | (b << 2) | ((1 - b) << 3)
        restricted.append(full_values[encoded])
    assert restricted == [1, 0, 0, 1]
    violation = first_submodularity_violation(restricted)
    assert violation is not None
    return {"matching_model": "K4, ports0..2 deleted if input1; all edge weights zero",
            "matching_counts": matching_counts,
            "matching_feasible_iff_even_parity": True,
            "one_hot_full_cut_is_submodular": True,
            "one_hot_restricted_values": restricted,
            "one_hot_restricted_violation": violation,
            "warning": "The restricted-domain example does not construct an unconstrained min-cut parity reduction or enforce one-hot validity."}


def run_audit():
    return {"scope": "direct-terminal nonnegative s-t cut gadgets with free auxiliary bits; no universal algorithmic conclusion",
            "exhaustive_cut_audit": exhaustive_audit(),
            "parity_complement_controls": parity_controls(),
            "alternative_encoding_controls": alternative_encoding_controls(),
            "source_sha256": sha256(Path(__file__).read_bytes()).hexdigest()}


if __name__ == "__main__":
    results = run_audit()
    destination = Path(__file__).with_name("RESULTS.json")
    destination.write_text(json.dumps(results, indent=2) + "\n", encoding="utf-8")
    audit = results["exhaustive_cut_audit"]
    print(json.dumps({key: audit[key] for key in
                      ("status", "graphs", "cuts_enumerated", "submodularity_pairs_checked")}))
