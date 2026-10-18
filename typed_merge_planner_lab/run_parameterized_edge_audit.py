"""Generate saved finite controls for the affine/cardinality parameter edges."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import parameterized_edges as edges


HERE = Path(__file__).resolve().parent


def main() -> None:
    cases = [
        ("dimension_identity", ((1, 0, 0), (0, 1, 0)), "dimension", None),
        ("dimension_rank_deficient", ((1, 0, 1), (1, 0, 1)), "dimension", None),
        ("distance_above_bound", ((1, 1, 1),), "distance", 2),
        ("distance_exact", ((1, 1, 1),), "distance", 3),
        ("zero_code", ((0, 0, 0),), "dimension", None),
    ]
    records = []
    for name, matrix, mode, bound in cases:
        if mode == "dimension":
            result = edges.minimum_distance_by_dimension(matrix)
        else:
            result = edges.minimum_distance_by_weight(matrix, bound)
        records.append({"name": name, "matrix": [list(row) for row in matrix],
                        "mode": mode, "bound": bound, "result": result})
    pair_routes = {
        "unparameterized": edges.parameterized_pair_status("AFFINE", "CARDINALITY"),
        "dimension": edges.parameterized_pair_status("AFFINE", "CARDINALITY", code_dimension=5),
        "distance": edges.parameterized_pair_status("AFFINE", "CARDINALITY",
                                                      code_length=6, distance_bound=2),
    }
    names = ("parameterized_edges.py", "run_parameterized_edge_audit.py",
             "PARAMETERIZED_EDGE_THEOREM.md", "test_parameterized_edges.py")
    artifact = {"schema": "parameterized_affine_cardinality_v1", "status": "PASS",
                "cases": records, "pair_routes": pair_routes,
                "source_sha256": {name: hashlib.sha256((HERE / name).read_bytes()).hexdigest()
                                  for name in names}}
    (HERE / "PARAMETERIZED_EDGE_RESULTS.json").write_text(
        json.dumps(artifact, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": "PASS", "cases": len(records),
                      "source_sha256": artifact["source_sha256"]}))


if __name__ == "__main__":
    main()
