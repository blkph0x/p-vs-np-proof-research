"""Generate replayable adaptive-frontier certificates for bounded controls."""
from __future__ import annotations

import json
from itertools import product
from pathlib import Path

from adaptive_frontier import Constraint, solve, source_hashes


HERE = Path(__file__).resolve().parent
EQ = frozenset(((0, 0), (1, 1)))
NEQ = frozenset(((0, 1), (1, 0)))
EXACT1 = frozenset(((0, 0, 1), (0, 1, 0), (1, 0, 0)))


def direct(n, constraints):
    return any(all(tuple(assignment[v] for v in c.scope) in c.relation
                   for c in constraints)
               for assignment in product((0, 1), repeat=n))


def controls():
    sparse = tuple(Constraint((i, i + 1), EQ) for i in range(4))
    contradictory = (Constraint((0,), frozenset(((0,),))),
                     Constraint((0,), frozenset(((1,),))))
    dense_relation = frozenset(row for row in product((0, 1), repeat=6)
                               if sum(row) % 2 == 0)
    return (
        {"name": "empty", "n": 0, "constraints": tuple(), "cap": 12},
        {"name": "sparse_equalities", "n": 5, "constraints": sparse, "cap": 12},
        {"name": "contradictory_units", "n": 1, "constraints": contradictory, "cap": 12},
        {"name": "dense_parity_scope", "n": 6,
         "constraints": (Constraint(tuple(range(6)), dense_relation),), "cap": 12},
        {"name": "exact_one_plus_equality", "n": 3,
         "constraints": (Constraint((0, 1, 2), EXACT1), Constraint((1, 2), EQ)), "cap": 12},
        {"name": "explicit_order_cap", "n": 13, "constraints": tuple(), "cap": 12},
    )


def main():
    rows, certificates = [], []
    for case in controls():
        result = solve(case["n"], case["constraints"],
                       max_order_variables=case["cap"])
        row = {"name": case["name"], "n": case["n"],
               "constraint_count": len(case["constraints"]),
               "status": result["status"], "sat": result["sat"],
               "reason": result.get("reason"), "width": result.get("width"),
               "max_states": result.get("max_states"),
               "order_search": result.get("order_search")}
        if result["status"] in ("SAT", "UNSAT"):
            assert result["sat"] == direct(case["n"], case["constraints"])
        rows.append(row)
        certificates.append({"name": case["name"], "result": result})
    output = {"format": "adaptive-frontier-v1", "rows": rows,
              "all_bounded_results_match_direct": True,
              "source_sha256": source_hashes()}
    (HERE / "ADAPTIVE_FRONTIER_RESULTS.json").write_text(
        json.dumps(output, indent=2) + "\n", encoding="utf-8")
    (HERE / "ADAPTIVE_FRONTIER_CERTIFICATES.json").write_text(
        json.dumps(certificates, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": "PASS", "case_count": len(rows),
                      "all_bounded_results_match_direct": True}))


if __name__ == "__main__":
    main()
