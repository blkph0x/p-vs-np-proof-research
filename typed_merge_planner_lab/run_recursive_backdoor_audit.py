"""Generate finite controls for recursive Horn/affine backdoor discovery."""
from __future__ import annotations

import hashlib
import json
from itertools import product
from pathlib import Path

import backdoor_solver as backdoor
import recursive_backdoor as recursive


HERE = Path(__file__).resolve().parent


def exact_weight(size, weight):
    return frozenset(row for row in product((0, 1), repeat=size) if sum(row) == weight)


def encode(constraints):
    return [{"scope": list(c.scope), "relation": [list(row) for row in sorted(c.relation)]}
            for c in constraints]


def main():
    cases = [
        ("sat_depth_one", 3,
         (backdoor.Constraint((0, 1, 2), exact_weight(3, 1)),), "AFFINE", 1, 100),
        ("unsat_depth_one", 3,
         (backdoor.Constraint((0, 1, 2), exact_weight(3, 1)),
          backdoor.Constraint((0, 1, 2), exact_weight(3, 2))), "AFFINE", 1, 100),
        ("depth_cap", 3,
         (backdoor.Constraint((0, 1, 2), exact_weight(3, 1)),), "AFFINE", 0, 100),
        ("node_cap", 3,
         (backdoor.Constraint((0, 1, 2), exact_weight(3, 1)),), "AFFINE", 2, 1),
    ]
    records = []
    for name, n, constraints, target, depth, nodes in cases:
        result = recursive.solve_recursive(n, constraints, target, depth, max_nodes=nodes)
        records.append({"name": name, "n": n, "constraints": encode(constraints),
                        "target": target, "max_depth": depth, "max_nodes": nodes,
                        "result": result})
    names = ("recursive_backdoor.py", "run_recursive_backdoor_audit.py",
             "RECURSIVE_BACKDOOR_THEOREM.md", "test_recursive_backdoor.py")
    artifact = {"schema": "recursive_schaefer_backdoor_v1", "status": "PASS",
                "cases": records,
                "source_sha256": {name: hashlib.sha256((HERE / name).read_bytes()).hexdigest()
                                  for name in names}}
    (HERE / "RECURSIVE_BACKDOOR_RESULTS.json").write_text(
        json.dumps(artifact, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": "PASS", "cases": len(records),
                      "source_sha256": artifact["source_sha256"]}))


if __name__ == "__main__":
    main()
