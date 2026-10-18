from itertools import combinations
import json
from pathlib import Path

from mixed_horn_affine_reduction import transformed_sat
from mixed_relation_dp import Constraint, solve, source_hashes, write_json


HERE = Path(__file__).resolve().parent
H = frozenset(((0, 0, 0), (1, 1, 0), (0, 0, 1)))
A = frozenset(((0, 1, 0, 0), (0, 0, 1, 0),
               (1, 0, 0, 1), (1, 1, 1, 1)))


def transformed_constraints(clauses, variables):
    constraints = []
    for i, (x, y, w) in enumerate(clauses):
        z0, z1 = variables + 2 * i, variables + 2 * i + 1
        constraints.append(Constraint((x, z0, z1), H))
        constraints.append(Constraint((y, w, z0, z1), A))
    return tuple(constraints)


def main():
    triples = tuple(combinations(range(4), 3))
    rows = []
    certificates = []
    for mask in range(1 << len(triples)):
        clauses = tuple(triples[i] for i in range(len(triples)) if mask >> i & 1)
        n = 4 + 2 * len(clauses)
        result = solve(n, transformed_constraints(clauses, 4), tuple(range(n)))
        direct = transformed_sat(clauses, 4)
        assert result["sat"] == direct
        rows.append({"mask": mask, "clause_count": len(clauses),
                     "sat": direct, "max_width": result["max_width"],
                     "max_states": result["max_states"]})
        certificates.append(result["certificate"])
    output = {"format": "mixed-relation-frontier-dp-v1", "variables": 4,
              "formula_count": len(rows), "rows": rows,
              "all_results_match_direct": True,
              "source_sha256": source_hashes()}
    write_json(HERE / "MIXED_RELATION_DP_RESULTS.json", output)
    write_json(HERE / "MIXED_RELATION_DP_CERTIFICATES.json", certificates)
    print(json.dumps({"status": "PASS", "formula_count": len(rows),
                      "all_results_match_direct": True}))


if __name__ == "__main__":
    main()
