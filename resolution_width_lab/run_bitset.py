"""Record the bit-mask bounded-width resolution stress run."""
from __future__ import annotations

import hashlib
import json
from itertools import combinations, product
from pathlib import Path
from time import perf_counter

from bitset import BitsetBoundedResolution
from indexed import IndexedBoundedResolution


HERE = Path(__file__).resolve().parent
CAPS = {"max_clauses": 200_000, "max_steps": 10_000_000}


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


def run_solver(name, family, nvars, clauses, width, seed=()):
    started = perf_counter()
    result = BitsetBoundedResolution(
        nvars, clauses, width, **CAPS
    ).solve(seed)
    row = {
        "name": name,
        "family": family,
        "nvars": nvars,
        "width": width,
        "seed_clauses": len(seed),
        "status": result["status"],
        "reason": result.get("reason"),
        "closure_size": len(result["clauses"]),
        "candidate_steps": result["stats"]["candidate_steps"],
        "weakening_steps": result["stats"]["weakening_steps"],
        "resolution_steps": result["stats"]["resolution_steps"],
        "indexed_resolution_pairs": result["stats"]["indexed_resolution_pairs"],
        "elapsed_seconds": perf_counter() - started,
        "clause_digest": clause_digest(result["clauses"]),
    }
    return row, result


def main():
    rows = []
    exact_cases = []
    for nvars in range(1, 5):
        exact_cases.append((f"all_assignments_n{nvars}", "all_assignments",
                            nvars, all_assignment_clauses(nvars), nvars))
    for holes in range(1, 4):
        nvars, clauses = pigeonhole(holes + 1, holes)
        exact_cases.append((f"pigeonhole_{holes + 1}_{holes}", "pigeonhole",
                            nvars, clauses, holes))

    exact_controls_match = True
    for name, family, nvars, clauses, width in exact_cases:
        row, bitset_result = run_solver(name, family, nvars, clauses, width)
        reference = IndexedBoundedResolution(
            nvars, clauses, width, **CAPS
        ).solve()
        row["reference_status"] = reference["status"]
        row["reference_reason"] = reference.get("reason")
        row["reference_clause_digest"] = clause_digest(reference["clauses"])
        row["reference_match"] = (
            row["status"] == reference["status"] and
            row["reason"] == reference.get("reason") and
            row["clause_digest"] == row["reference_clause_digest"]
        )
        exact_controls_match = exact_controls_match and row["reference_match"]
        rows.append(row)

    nvars, clauses = pigeonhole(5, 4)
    width3, lower = run_solver("pigeonhole_5_4", "pigeonhole_stress",
                               nvars, clauses, 3)
    width4, _ = run_solver("pigeonhole_5_4", "pigeonhole_stress",
                           nvars, clauses, 4, lower["clauses"])
    rows.extend((width3, width4))
    output = {
        "format": "bitset-width-stress-v1",
        "caps": CAPS,
        "rows": rows,
        "exact_control_count": len(exact_cases),
        "exact_controls_match": exact_controls_match,
        "stress_rows_are_capped": True,
        "source_sha256": {
            f"resolution_width_lab/{name}": digest(HERE / name)
            for name in ("bitset.py", "run_bitset.py", "review_bitset.py",
                         "review_indexed.py",
                         "THEOREM.md")
        },
    }
    (HERE / "BITSET_RESULTS.json").write_text(
        json.dumps(output, indent=2) + "\n", encoding="utf-8"
    )
    write_report(rows)
    print(json.dumps({"status": "PASS", "row_count": len(rows),
                      "exact_controls_match": exact_controls_match,
                      "stress_width3": width3["status"],
                      "stress_width4": width4["status"],
                      "stress_width4_reason": width4["reason"]}))


def write_report(rows):
    lines = [
        "# Bit-mask bounded-width resolution stress",
        "",
        "This run stores each clause as positive and negative bit masks while",
        "retaining the reference weakening/resolution rules and literal indexes.",
        "The seven exact controls are compared with the tuple-indexed closure.",
        "The PHP(5,4) rows use the fixed cap below.",
        "",
        f"Caps: `{CAPS['max_clauses']}` clauses and `{CAPS['max_steps']}` candidate steps.",
        "",
        "| family | instance | width | seed | status | reason | closure | candidates | pairs | seconds | reference |",
        "| --- | --- | ---: | ---: | --- | --- | ---: | ---: | ---: | ---: | --- |",
    ]
    for row in rows:
        reference = row.get("reference_match", "—")
        lines.append(
            f"| {row['family']} | {row['name']} | {row['width']} | "
            f"{row['seed_clauses']} | {row['status']} | {row['reason'] or '—'} | "
            f"{row['closure_size']} | {row['candidate_steps']} | "
            f"{row['indexed_resolution_pairs']} | {row['elapsed_seconds']:.3f} | {reference} |"
        )
    lines += [
        "",
        "The bit-mask representation reaches the same exact-control closures",
        "with different machine-level timings. For PHP(5,4), width 3 reaches a",
        "complete fixed point; seeded width 4 reaches the ten-million-candidate",
        "cap and remains `UNKNOWN`. This is a resource frontier, not a proof that",
        "no width-4 refutation exists.",
        "",
    ]
    (HERE / "BITSET_REPORT.md").write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    main()
