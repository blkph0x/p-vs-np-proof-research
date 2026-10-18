"""Record an indexed bounded-width closure stress result."""
from __future__ import annotations

import hashlib
import json
from itertools import combinations, product
from pathlib import Path
from time import perf_counter

from indexed import IndexedBoundedResolution


HERE = Path(__file__).resolve().parent
CAPS = {"max_clauses": 100_000, "max_steps": 1_000_000}


def digest(path):
    text = path.read_text(encoding="utf-8")
    return hashlib.sha256(text.replace("\r\n", "\n").replace("\r", "\n").encode()).hexdigest()


def clause_digest(clauses):
    payload = json.dumps(sorted(clauses), separators=(",", ":"))
    return hashlib.sha256(payload.encode()).hexdigest()


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


def solve_row(name, family, nvars, clauses, width, seed=()):
    started = perf_counter()
    result = IndexedBoundedResolution(
        nvars, clauses, width, **CAPS
    ).solve(seed)
    elapsed = perf_counter() - started
    stats = result["stats"]
    return {
        "name": name,
        "family": family,
        "nvars": nvars,
        "width": width,
        "seed_clauses": len(seed),
        "status": result["status"],
        "reason": result.get("reason"),
        "closure_size": len(result["clauses"]),
        "candidate_steps": stats["candidate_steps"],
        "weakening_steps": stats["weakening_steps"],
        "resolution_steps": stats["resolution_steps"],
        "indexed_resolution_pairs": stats["indexed_resolution_pairs"],
        "elapsed_seconds": elapsed,
        "clause_digest": clause_digest(result["clauses"]),
    }, result


def exact_ladder(name, family, nvars, clauses, max_width):
    rows, seed = [], ()
    for width in range(max_width + 1):
        row, result = solve_row(name, family, nvars, clauses, width, seed)
        rows.append(row)
        if result["status"] == "UNSAT" or result.get("reason") in {"CLAUSE_CAP", "STEP_CAP"}:
            break
        seed = tuple(tuple(clause) for clause in result["clauses"])
    return rows


def main():
    rows = []
    for nvars in range(1, 5):
        clauses = all_assignment_clauses(nvars)
        rows.extend(exact_ladder(
            f"all_assignments_n{nvars}", "all_assignments",
            nvars, clauses, nvars,
        ))
    for holes in range(1, 4):
        nvars, clauses = pigeonhole(holes + 1, holes)
        rows.extend(exact_ladder(
            f"pigeonhole_{holes + 1}_{holes}", "pigeonhole",
            nvars, clauses, holes,
        ))

    # The next pigeonhole instance is intentionally recorded under a fixed
    # cap. Width 3 is an exact saturated negative; width 4 is a capped
    # UNKNOWN, so neither row is promoted to a mathematical width theorem.
    nvars, clauses = pigeonhole(5, 4)
    width3, lower = solve_row("pigeonhole_5_4", "pigeonhole_stress",
                              nvars, clauses, 3)
    width4, _ = solve_row("pigeonhole_5_4", "pigeonhole_stress",
                          nvars, clauses, 4, lower["clauses"])
    rows.extend((width3, width4))

    output = {
        "format": "indexed-width-stress-v1",
        "caps": CAPS,
        "rows": rows,
        "exact_control_count": 7,
        "stress_rows_are_capped": True,
        "source_sha256": {
            f"resolution_width_lab/{name}": digest(HERE / name)
            for name in ("indexed.py", "run_indexed.py", "review_indexed.py",
                         "THEOREM.md")
        },
    }
    (HERE / "INDEXED_RESULTS.json").write_text(
        json.dumps(output, indent=2) + "\n", encoding="utf-8"
    )
    write_report(rows)
    print(json.dumps({"status": "PASS", "row_count": len(rows),
                      "stress_width3": width3["status"],
                      "stress_width4": width4["status"],
                      "stress_width4_reason": width4["reason"]}))


def write_report(rows):
    lines = [
        "# Indexed bounded-width resolution stress",
        "",
        "The indexed closure uses the same weakening and binary-resolution",
        "rules as the reference closure, but indexes clauses by literal before",
        "testing a resolution pair. The exact controls are cross-checked against",
        "the reference implementation; the 5-into-4 stress rows use the fixed",
        "resource cap shown below.",
        "",
        f"Caps: `{CAPS['max_clauses']}` clauses and `{CAPS['max_steps']}` candidate steps.",
        "",
        "| family | instance | width | seed | status | reason | closure | candidates | indexed pairs | seconds |",
        "| --- | --- | ---: | ---: | --- | --- | ---: | ---: | ---: | ---: |",
    ]
    for row in rows:
        lines.append(
            f"| {row['family']} | {row['name']} | {row['width']} | "
            f"{row['seed_clauses']} | {row['status']} | {row['reason'] or '—'} | "
            f"{row['closure_size']} | {row['candidate_steps']} | "
            f"{row['indexed_resolution_pairs']} | {row['elapsed_seconds']:.3f} |"
        )
    lines += [
        "",
        "For `pigeonhole_5_4`, width 3 reaches a complete bounded closure without",
        "the empty clause. Width 4 is deliberately reported as `UNKNOWN` after",
        "the step cap, even though the indexed implementation has already reused",
        "the complete width-3 seed. This is an implementation frontier, not a",
        "proof that the formula has no width-4 refutation.",
        "",
    ]
    (HERE / "INDEXED_REPORT.md").write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    main()
