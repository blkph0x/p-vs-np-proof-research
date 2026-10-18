"""Run the finite common-polymorphism audit for H and A."""
from __future__ import annotations

import json
from pathlib import Path
import sys

import polymorphism as p


ROOT = Path(__file__).resolve().parent


def main():
    common = {}
    projection_exact = {}
    for arity in range(1, 5):
        ops = p.common_operations(arity)
        projections = [p.projection_table(arity, i) for i in range(arity)]
        common[str(arity)] = ops
        projection_exact[str(arity)] = sorted(ops) == sorted(projections)
    matrix = p.named_preservation_matrix()
    symbolic = {}
    for arity in range(1, 13):
        candidates = p.affine_common_candidates(arity)
        symbolic[str(arity)] = {
            "count": len(candidates),
            "supports": [support for _, support, _ in candidates],
            "all_singletons": all(support.bit_count() == 1 and constant == 0
                                   for constant, support, _ in candidates),
        }
    result = {
        "status": "finite polymorphism audit; no P=NP result",
        "relations": {"H": [list(x) for x in p.H], "A": [list(x) for x in p.A]},
        "common_operations_by_arity": common,
        "common_counts": {k: len(v) for k, v in common.items()},
        "common_are_projections": projection_exact,
        "named_matrix": matrix,
        "all_arity_symbolic_candidates": symbolic,
    }
    (ROOT / "POLYMORPHISM_RESULTS.json").write_text(json.dumps(result, indent=2) + "\n",
                                                        encoding="utf-8")
    review = {
        "common_counts_expected": result["common_counts"] == {"1": 1, "2": 2,
                                                                "3": 3, "4": 4},
        "all_common_are_projections": all(projection_exact.values()),
        "named_matrix_replayed": all(
            row["preserves_H"] == p.preserves(p.H, row["arity"], row["table"]) and
            row["preserves_A"] == p.preserves(p.A, row["arity"], row["table"])
            for row in matrix.values()),
        "all_arity_symbolic_singletons": all(
            row["count"] == int(arity) and row["all_singletons"]
            for arity, row in symbolic.items()),
    }
    review["all_checks_passed"] = all(review.values())
    (ROOT / "POLYMORPHISM_REVIEW.json").write_text(json.dumps(review, indent=2) + "\n",
                                                    encoding="utf-8")
    print(json.dumps({"review": review, "matrix": matrix}, indent=2))
    return 0 if review["all_checks_passed"] else 1


if __name__ == "__main__":
    sys.exit(main())
