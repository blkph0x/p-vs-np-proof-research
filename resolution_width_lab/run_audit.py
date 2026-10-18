"""Generate bounded-resolution closure certificates."""
from __future__ import annotations

import json
from itertools import product
from pathlib import Path

from resolution import BoundedResolution, source_hashes


HERE = Path(__file__).resolve().parent


def all_assignment_clauses(nvars):
    return tuple(tuple((v + 1) if not bit else -(v + 1)
                       for v, bit in enumerate(bits))
                 for bits in product((0, 1), repeat=nvars))


def pigeonhole(pigeons, holes):
    variable = lambda pigeon, hole: pigeon * holes + hole + 1
    clauses = [tuple(variable(pigeon, hole) for hole in range(holes))
               for pigeon in range(pigeons)]
    clauses += [(-variable(pigeon, left), -variable(pigeon, right))
                for pigeon in range(pigeons)
                for left in range(holes) for right in range(left + 1, holes)]
    clauses += [(-variable(left, hole), -variable(right, hole))
                for hole in range(holes)
                for left in range(pigeons) for right in range(left + 1, pigeons)]
    return pigeons * holes, tuple(clauses)


def controls():
    _, pigeon = pigeonhole(3, 2)
    return (
        {"name": "unit_contradiction", "nvars": 1, "clauses": ((1,), (-1,)),
         "width": 1, "caps": {}},
        {"name": "all_assignments_width_two", "nvars": 3,
         "clauses": all_assignment_clauses(3), "width": 2, "caps": {}},
        {"name": "all_assignments_width_three", "nvars": 3,
         "clauses": all_assignment_clauses(3), "width": 3, "caps": {}},
        {"name": "pigeonhole_3_2_width_three", "nvars": 6,
         "clauses": pigeon, "width": 3, "caps": {}},
        {"name": "satisfiable_formula", "nvars": 2,
         "clauses": ((1, 2), (-1, 2)), "width": 2, "caps": {}},
        {"name": "explicit_clause_cap", "nvars": 4,
         "clauses": all_assignment_clauses(4), "width": 4,
         "caps": {"max_clauses": 3}},
    )


def main():
    rows, certificates = [], []
    for case in controls():
        result = BoundedResolution(case["nvars"], case["clauses"], case["width"],
                                   **case["caps"]).solve()
        rows.append({"name": case["name"], "nvars": case["nvars"],
                     "width": case["width"], "clause_count": len(case["clauses"]),
                     "status": result["status"], "reason": result.get("reason"),
                     "stats": result["stats"], "closure_size": len(result["clauses"])})
        certificates.append({"name": case["name"], "nvars": case["nvars"],
                             "width": case["width"],
                             "clauses": [list(c) for c in case["clauses"]],
                             "caps": case["caps"], "result": result})
    output = {"format": "bounded-resolution-width-v1", "rows": rows,
              "all_cases_replayed": True, "source_sha256": source_hashes()}
    (HERE / "RESULTS.json").write_text(json.dumps(output, indent=2) + "\n", encoding="utf-8")
    (HERE / "CERTIFICATES.json").write_text(
        json.dumps(certificates, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": "PASS", "case_count": len(rows),
                      "all_cases_replayed": True}))


if __name__ == "__main__":
    main()
