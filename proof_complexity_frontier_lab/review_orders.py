"""Independent replay of the exact small-order discovery artifact."""
from __future__ import annotations

import hashlib
import json
from itertools import combinations
from pathlib import Path

HERE = Path(__file__).resolve().parent


def pigeonhole(pigeons, holes):
    variable = lambda pigeon, hole: pigeon * holes + hole + 1
    clauses = [tuple(variable(pigeon, hole) for hole in range(holes))
               for pigeon in range(pigeons)]
    clauses += [(-variable(pigeon, left), -variable(pigeon, right))
                for pigeon in range(pigeons)
                for left, right in combinations(range(holes), 2)]
    clauses += [(-variable(left, hole), -variable(right, hole))
                for hole in range(holes)
                for left, right in combinations(range(pigeons), 2)]
    return pigeons * holes, tuple(clauses)


def adjacency(nvars, clauses):
    output = [0] * nvars
    for clause in clauses:
        variables = sorted({abs(literal) - 1 for literal in clause})
        for left_index, left in enumerate(variables):
            for right in variables[left_index + 1:]:
                output[left] |= 1 << right
                output[right] |= 1 << left
    return output


def boundary(mask, adjacency):
    result = 0
    remaining = mask
    while remaining:
        bit = remaining & -remaining
        variable = bit.bit_length() - 1
        remaining ^= bit
        if adjacency[variable] & ~mask:
            result |= bit
    return result.bit_count()


def optimal(nvars, clauses):
    graph = adjacency(nvars, clauses)
    limit = 1 << nvars
    values = [nvars + 1] * limit
    values[0] = 0
    chosen = [0] * limit
    boundary_values = [0] * limit
    for mask in range(1, limit):
        boundary_values[mask] = boundary(mask, graph)
        remaining = mask
        while remaining:
            bit = remaining & -remaining
            remaining ^= bit
            candidate = max(values[mask ^ bit], boundary_values[mask])
            if candidate < values[mask]:
                values[mask] = candidate
                chosen[mask] = bit
    mask = limit - 1
    reverse_order = []
    while mask:
        bit = chosen[mask]
        assert bit
        reverse_order.append(bit.bit_length() - 1)
        mask ^= bit
    order = reverse_order[::-1]
    prefix = 0
    prefix_widths = []
    for variable in order:
        prefix |= 1 << variable
        prefix_widths.append(boundary_values[prefix])
    return values[-1], order, prefix_widths


def widths_for_order(nvars, clauses, order):
    graph = adjacency(nvars, clauses)
    prefix = 0
    widths = []
    for variable in order:
        prefix |= 1 << variable
        widths.append(boundary(prefix, graph))
    return widths


def digest(path):
    text = path.read_text(encoding="utf-8")
    return hashlib.sha256(text.replace("\r\n", "\n").replace("\r", "\n").encode()).hexdigest()


def main():
    artifact = json.loads((HERE / "ORDER_RESULTS.json").read_text(encoding="utf-8"))
    for saved in artifact["rows"]:
        nvars, clauses = pigeonhole(saved["pigeons"], saved["holes"])
        width, order, prefix_widths = optimal(nvars, clauses)
        assert nvars == saved["nvars"]
        assert width == saved["optimal_width"]
        assert order == saved["optimal_order"]
        assert prefix_widths == saved["optimal_prefix_widths"]
        assert max(prefix_widths, default=0) == width
        assert sorted(order) == list(range(nvars))
        row_widths = widths_for_order(nvars, clauses, list(range(nvars)))
        assert row_widths == saved["row_major_prefix_widths"]
        assert max(row_widths, default=0) == saved["row_major_width"]
    expected_hashes = {
        "proof_complexity_frontier_lab/order_dp.py": digest(HERE / "order_dp.py"),
        "proof_complexity_frontier_lab/run_orders.py": digest(HERE / "run_orders.py"),
        "proof_complexity_frontier_lab/review_orders.py": digest(HERE / "review_orders.py"),
        "proof_complexity_frontier_lab/THEOREM.md": digest(HERE / "THEOREM.md"),
    }
    assert artifact["source_sha256"] == expected_hashes
    assert artifact["all_orders_exact"]
    output = {"status": "PASS", "case_count": len(artifact["rows"]),
              "recurrence_matches": True, "orders_are_permutations": True,
              "source_hashes_match": True}
    (HERE / "ORDER_REVIEW.json").write_text(json.dumps(output, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(output))


if __name__ == "__main__":
    main()
