"""Generate the incremental bounded-width closure comparison."""
from __future__ import annotations

import hashlib
import json
from itertools import combinations, product
from pathlib import Path

from incremental import run_ladder

HERE = Path(__file__).resolve().parent
CAPS = {"max_clauses": 100_000, "max_steps": 500_000}


def digest(path):
    text = path.read_text(encoding="utf-8")
    return hashlib.sha256(text.replace("\r\n", "\n").replace("\r", "\n").encode()).hexdigest()


def all_assignment_clauses(nvars):
    return tuple(tuple((variable + 1) if not bit else -(variable + 1)
                       for variable, bit in enumerate(bits))
                 for bits in product((0, 1), repeat=nvars))


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


def cases():
    rows = []
    for nvars in range(1, 5):
        rows.append({"name": f"all_assignments_n{nvars}",
                     "family": "all_assignments", "parameter": nvars,
                     "nvars": nvars, "clauses": all_assignment_clauses(nvars)})
    for holes in range(1, 4):
        nvars, clauses = pigeonhole(holes + 1, holes)
        rows.append({"name": f"pigeonhole_{holes + 1}_{holes}",
                     "family": "pigeonhole", "parameter": holes,
                     "pigeons": holes + 1, "holes": holes,
                     "nvars": nvars, "clauses": clauses})
    return rows


def main():
    rows = []
    for case in cases():
        ladder = run_ladder(case["nvars"], case["clauses"], **CAPS)
        rows.append({"name": case["name"], "family": case["family"],
                     "parameter": case["parameter"], "pigeons": case.get("pigeons"),
                     "holes": case.get("holes"), "nvars": case["nvars"],
                     "clauses": [list(c) for c in case["clauses"]],
                     "clause_count": len(case["clauses"]), "caps": CAPS,
                     "ladder": ladder})
    output = {
        "format": "incremental-width-ladder-v1",
        "rows": rows,
        "all_closures_match": all(
            observation["baseline"]["clause_digest"] ==
            observation["incremental"]["clause_digest"]
            for row in rows for observation in row["ladder"]
        ),
        "source_sha256": {
            "resolution_width_lab/resolution.py": digest(HERE / "resolution.py"),
            "resolution_width_lab/incremental.py": digest(HERE / "incremental.py"),
            "resolution_width_lab/run_incremental.py": digest(HERE / "run_incremental.py"),
            "resolution_width_lab/review_incremental.py": digest(HERE / "review_incremental.py"),
            "resolution_width_lab/THEOREM.md": digest(HERE / "THEOREM.md"),
        },
    }
    (HERE / "INCREMENTAL_RESULTS.json").write_text(
        json.dumps(output, indent=2) + "\n", encoding="utf-8"
    )
    write_report(rows)
    print(json.dumps({"status": "PASS", "case_count": len(rows),
                      "all_closures_match": output["all_closures_match"]}))


def write_report(rows):
    lines = [
        "# Incremental bounded-width resolution ladder",
        "",
        "Each row compares a fresh closure at every width with a ladder that",
        "seeds width `w` from the complete width `w-1` closure.",
        "",
        "| family | parameter | width | seed clauses | fresh candidates | incremental candidates | status |",
        "| --- | ---: | ---: | ---: | ---: | ---: | --- |",
    ]
    for row in rows:
        for observation in row["ladder"]:
            fresh = observation["baseline"]
            inc = observation["incremental"]
            lines.append(
                f"| {row['family']} | {row['parameter']} | {observation['width']} | "
                f"{inc['seed_clauses']} | {fresh['candidate_steps']} | "
                f"{inc['candidate_steps']} | {fresh['status']} |"
            )
    lines += [
        "",
        "The independent reviewer checks equality of the complete closure at",
        "each width and verifies that a seed is used only after a non-capped lower",
        "width. Candidate counts measure inference attempts in this deterministic",
        "implementation; they are not a machine-independent runtime bound.",
        "",
    ]
    (HERE / "INCREMENTAL_REPORT.md").write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    main()
