"""Independent replay of the source-primal lower bound.

This file intentionally recomputes clause scopes, graph boundaries and the
subset search rather than importing the producer's result or width routine.
"""

import json
from itertools import combinations
from pathlib import Path


CASES = (
    ("path_6", 6, [(0, 1), (1, 2), (2, 3), (3, 4), (4, 5)]),
    ("star_6", 6, [(0, i) for i in range(1, 6)]),
    ("cycle_6", 6, [(0, 1), (1, 2), (2, 3), (3, 4), (4, 5), (5, 0)]),
    ("bipartite_3_2", 5, [(u, v) for u in range(3) for v in (3, 4)]),
    ("complete_4", 4, [(u, v) for u in range(4) for v in range(u + 1, 4)]),
)


def independent_circuit(n, edges):
    clauses = []
    for index, (u, v) in enumerate(edges):
        left, right, output = u + 1, v + 1, n + index + 1
        clauses.extend(([-left, output], [-right, output],
                        [left, right, -output], [output]))
    return n + len(edges), clauses


def scopes(clauses):
    pairs = set()
    for clause in clauses:
        variables = sorted({abs(literal) for literal in clause})
        pairs.update(combinations(variables, 2))
    return tuple(sorted(pairs))


def width(variables, edges, order):
    adjacency = [0] * variables
    for left, right in edges:
        adjacency[left - 1] |= 1 << (right - 1)
        adjacency[right - 1] |= 1 << (left - 1)
    subset = 0
    best = 0
    for cut, variable in enumerate(order, 1):
        subset |= 1 << (variable - 1)
        if cut == variables:
            continue
        active = sum(bool(subset >> index & 1 and
                          adjacency[index] & (((1 << variables) - 1) ^ subset))
                     for index in range(variables))
        best = max(best, active)
    return best


def exact(variables, edges):
    full = (1 << variables) - 1
    adjacency = [0] * variables
    for left, right in edges:
        adjacency[left - 1] |= 1 << (right - 1)
        adjacency[right - 1] |= 1 << (left - 1)

    def cut_width(subset):
        if subset == full:
            return 0
        suffix = full ^ subset
        return sum(bool(subset >> index & 1 and adjacency[index] & suffix)
                   for index in range(variables))

    best = {0: (0, ())}
    for subset in range(full + 1):
        if subset not in best:
            continue
        old_width, old_order = best[subset]
        for variable in range(1, variables + 1):
            bit = 1 << (variable - 1)
            if subset & bit:
                continue
            nxt = subset | bit
            candidate = (max(old_width, cut_width(nxt)), old_order + (variable,))
            if nxt not in best or candidate < best[nxt]:
                best[nxt] = candidate
    value, order = best[full]
    assert width(variables, edges, order) == value
    return value, list(order), len(best)


def independent_extension(n, graph_edges, source_order):
    rank = {variable: index for index, variable in enumerate(source_order)}
    after = {variable: [] for variable in source_order}
    for index, (u, v) in enumerate(graph_edges):
        left, right = u + 1, v + 1
        later = right if rank[right] > rank[left] else left
        after[later].append(n + index + 1)
    order = []
    for source in source_order:
        order.append(source)
        order.extend(sorted(after[source]))
    return order


def main():
    saved = json.loads(Path("RESULTS.json").read_text())
    rows = []
    for (name, n, graph_edges), saved_row in zip(CASES, saved["rows"]):
        assert saved_row["name"] == name
        variables, clauses = independent_circuit(n, graph_edges)
        full_edges = scopes(clauses)
        source_edges = tuple((u + 1, v + 1) for u, v in graph_edges)
        source_width, _, source_states = exact(n, source_edges)
        full_width, _, full_states = exact(variables, full_edges)
        source_value, source_order, _ = exact(n, source_edges)
        extension = independent_extension(n, graph_edges, source_order)
        extension_width = width(variables, full_edges, extension)
        # All-one values satisfy each pinned OR output.
        values = {variable: 1 for variable in range(1, variables + 1)}
        all_one = all(any((literal > 0) == bool(values[abs(literal)])
                          for literal in clause) for clause in clauses)
        assert all_one
        assert full_width >= source_width
        assert extension_width <= source_width + 1
        assert saved_row["source_width"] == source_width
        assert saved_row["full_width"] == full_width
        assert saved_row["extended_width"] == extension_width
        assert saved_row["additive_upper_bound_holds"] is True
        assert saved_row["source_states"] == source_states
        assert saved_row["full_states"] == full_states
        rows.append({"name": name, "source_width": source_width,
                     "full_width": full_width, "source_states": source_states,
                     "full_states": full_states, "extension_width": extension_width,
                     "additive_upper_bound_holds": extension_width <= source_width + 1,
                     "all_ones_sat": all_one})
    output = {
        "status": "VERIFIED_INDEPENDENT_CIRCUIT_ORDER_BOUND",
        "case_count": len(rows),
        "rows": rows,
        "all_lower_bounds_hold": True,
        "all_additive_upper_bounds_hold": True,
        "all_controls_trivially_satisfiable": True,
    }
    Path("INDEPENDENT_REVIEW.json").write_text(json.dumps(output, indent=2) + "\n")
    Path("INDEPENDENT_REVIEW.md").write_text(
        "# Independent circuit-order review\n\n"
        f"Recomputed {len(rows)} controls from the saved graph descriptions. "
        "The source graph width is a lower bound on the full Tseitin primal width, "
        "and the all-ones assignment satisfies every pinned OR output.\n"
    )
    print(json.dumps({"status": output["status"], "cases": len(rows),
                      "max_source_width": max(row["source_width"] for row in rows),
                      "max_full_width": max(row["full_width"] for row in rows)}))


if __name__ == "__main__":
    main()
