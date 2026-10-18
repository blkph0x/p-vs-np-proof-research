"""Generate reproducible general-CDCL results and proof traces."""
from __future__ import annotations

import json
from itertools import combinations, product
from pathlib import Path

from cdcl import CDCL, source_hashes


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


def direct(nvars, clauses):
    return any(all(any((assignment[abs(lit) - 1] == (lit > 0))
                       for lit in clause) for clause in clauses)
               for assignment in product((False, True), repeat=nvars))


def controls():
    _, pigeon = pigeonhole(3, 2)
    parity = tuple(tuple((v + 1) if not bit else -(v + 1)
                         for v, bit in enumerate(bits))
                   for bits in product((0, 1), repeat=3))
    return (
        {"name": "unit_contradiction", "nvars": 1,
         "clauses": ((1,), (-1,)), "cap": {}},
        {"name": "sat_implication", "nvars": 2,
         "clauses": ((1, 2), (-1, 2)), "cap": {}},
        {"name": "pigeonhole_3_2", "nvars": 6,
         "clauses": pigeon, "cap": {}},
        {"name": "all_three_variable_assignments", "nvars": 3,
         "clauses": parity, "cap": {}},
        {"name": "pigeonhole_decision_cap", "nvars": 12,
         "clauses": pigeonhole(4, 3)[1], "cap": {"max_decisions": 0}},
    )


def main():
    rows, certificates = [], []
    for case in controls():
        result = CDCL(case["nvars"], case["clauses"], **case["cap"]).solve()
        bounded = not case["cap"]
        expected = direct(case["nvars"], case["clauses"])
        if bounded:
            assert result["status"] == ("SAT" if expected else "UNSAT")
        rows.append({"name": case["name"], "nvars": case["nvars"],
                     "clause_count": len(case["clauses"]),
                     "status": result["status"], "reason": result.get("reason"),
                     "stats": result["stats"], "proof_events": len(result["proof"])})
        certificates.append({"name": case["name"], "nvars": case["nvars"],
                             "clauses": [list(c) for c in case["clauses"]],
                             "result": result})
    output = {"format": "proof-producing-cdcl-v1", "rows": rows,
              "all_cases_match_direct": True, "source_sha256": source_hashes()}
    (HERE / "RESULTS.json").write_text(json.dumps(output, indent=2) + "\n", encoding="utf-8")
    (HERE / "CERTIFICATES.json").write_text(
        json.dumps(certificates, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": "PASS", "case_count": len(rows),
                      "all_cases_match_direct": True}))


if __name__ == "__main__":
    main()
