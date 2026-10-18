"""Generate the checked finite fixtures for the strong-backdoor lab."""
from __future__ import annotations

import hashlib
import json
from itertools import product
from pathlib import Path

import backdoor_solver as solver


HERE = Path(__file__).resolve().parent


def exact_one(arity: int) -> frozenset[tuple[int, ...]]:
    return frozenset(row for row in product((0, 1), repeat=arity) if sum(row) == 1)


def exact_two(arity: int) -> frozenset[tuple[int, ...]]:
    return frozenset(row for row in product((0, 1), repeat=arity) if sum(row) == 2)


def brute_force(n: int, constraints: tuple[solver.Constraint, ...]) -> list[tuple[int, ...]]:
    return [bits for bits in product((0, 1), repeat=n)
            if all(tuple(bits[v] for v in c.scope) in c.relation for c in constraints)]


def encode(constraints):
    return [{"scope": list(c.scope), "relation": [list(row) for row in sorted(c.relation)]}
            for c in constraints]


def main() -> None:
    cases = [
        ("exact_one_affine_sat", 5,
         (solver.Constraint((0, 1, 2), exact_one(3)),
          solver.Constraint((2, 3, 4), exact_one(3))), (2,), "AFFINE"),
        ("exact_one_affine_unsat", 3,
         (solver.Constraint((0, 1, 2), exact_one(3)),
          solver.Constraint((0, 1, 2), exact_two(3))), (0, 1), "AFFINE"),
        ("unassigned_exact_one_unknown", 3,
         (solver.Constraint((0, 1, 2), exact_one(3)),), (), "AFFINE"),
        ("horn_implication_sat", 2,
         (solver.Constraint((0, 1), frozenset(((0, 0), (0, 1), (1, 1)))),
          solver.Constraint((1,), frozenset(((1,),)))), (), "HORN"),
    ]
    records = []
    for name, n, constraints, backdoor, target in cases:
        result = solver.solve_with_backdoor(n, constraints, backdoor, target)
        expected = bool(brute_force(n, constraints))
        expected_status = "UNKNOWN" if name == "unassigned_exact_one_unknown" else ("SAT" if expected else "UNSAT")
        if result["status"] != expected_status:
            raise AssertionError((name, result["status"], expected_status))
        records.append({"name": name, "n": n, "constraints": encode(constraints),
                        "backdoor": list(backdoor), "target": target,
                        "expected_status": expected_status, "result": result})
    names = ("backdoor_solver.py", "run_backdoor_audit.py", "BACKDOOR_THEOREM.md",
             "test_backdoor_solver.py")
    artifact = {"schema": "strong_schaefer_backdoor_v1", "status": "PASS",
                "cases": records,
                "source_sha256": {name: hashlib.sha256((HERE / name).read_bytes()).hexdigest()
                                  for name in names}}
    (HERE / "BACKDOOR_RESULTS.json").write_text(json.dumps(artifact, indent=2) + "\n",
                                                encoding="utf-8")
    print(json.dumps({"status": "PASS", "cases": len(records),
                      "source_sha256": artifact["source_sha256"]}))


if __name__ == "__main__":
    main()
