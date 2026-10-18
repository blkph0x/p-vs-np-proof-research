from itertools import combinations
import json
from hashlib import sha256
from pathlib import Path

from mixed_bridge_width import transformed_primal
from mixed_horn_affine_reduction import transformed_sat
from mixed_order_discovery import discover, order_width
from mixed_relation_dp import Constraint, solve


HERE = Path(__file__).resolve().parent
H = frozenset(((0, 0, 0), (1, 1, 0), (0, 0, 1)))
A = frozenset(((0, 1, 0, 0), (0, 0, 1, 0),
               (1, 0, 0, 1), (1, 1, 1, 1)))


def constraints(clauses, variables):
    result = []
    for i, (x, y, w) in enumerate(clauses):
        z0, z1 = variables + 2 * i, variables + 2 * i + 1
        result.extend((Constraint((x, z0, z1), H), Constraint((y, w, z0, z1), A)))
    return tuple(result)


def main():
    triples = tuple(combinations(range(4), 3))
    rows, certificates = [], []
    for mask in range(1 << len(triples)):
        clauses = tuple(triples[i] for i in range(len(triples)) if mask >> i & 1)
        adj = transformed_primal(clauses, 4)
        result = discover(adj)
        order = tuple(result["order"])
        solver = solve(len(adj), constraints(clauses, 4), order)
        direct = transformed_sat(clauses, 4)
        assert result["width"] == order_width(adj, order)
        assert solver["sat"] == direct
        rows.append({"mask": mask, "clause_count": len(clauses),
                     "variables": len(adj), "width": result["width"],
                     "order": list(order), "search_subsets": result["subsets"],
                     "search_transitions": result["transitions"],
                     "sat": direct, "frontier_states": solver["max_states"]})
        certificates.append({"mask": mask, "adjacency": list(adj),
                             "order": list(order), "width": result["width"]})
    names = ("mixed_order_discovery.py", "run_mixed_order_discovery.py",
             "MIXED_ORDER_DISCOVERY_THEOREM.md", "MIXED_ORDER_DISCOVERY_REVIEW.py",
             "test_mixed_order_discovery.py")
    output = {"format": "mixed-order-discovery-v1", "formula_count": len(rows),
              "rows": rows, "all_orders_optimal": True,
              "source_sha256": {name: sha256((HERE / name).read_bytes()).hexdigest()
                                for name in names}}
    (HERE / "MIXED_ORDER_DISCOVERY_RESULTS.json").write_text(
        json.dumps(output, indent=2) + "\n", encoding="utf-8")
    (HERE / "MIXED_ORDER_DISCOVERY_CERTIFICATES.json").write_text(
        json.dumps(certificates, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": "PASS", "formula_count": len(rows),
                      "all_orders_optimal": True}))


if __name__ == "__main__":
    main()
