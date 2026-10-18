"""Build a finite bridge between resolution width, frontier state, and CDCL data."""
from __future__ import annotations

import hashlib
import json
import sys
from itertools import combinations, product
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(ROOT / "resolution_width_lab"))

from resolution import BoundedResolution  # noqa: E402


CAPS = {"max_clauses": 100_000, "max_steps": 500_000}


def digest(path: Path) -> str:
    text = path.read_text(encoding="utf-8")
    normalized = text.replace("\r\n", "\n").replace("\r", "\n")
    return hashlib.sha256(normalized.encode()).hexdigest()


def all_assignment_clauses(nvars: int) -> tuple[tuple[int, ...], ...]:
    return tuple(
        tuple((variable + 1) if not bit else -(variable + 1)
              for variable, bit in enumerate(bits))
        for bits in product((0, 1), repeat=nvars)
    )


def pigeonhole(pigeons: int, holes: int) -> tuple[int, tuple[tuple[int, ...], ...]]:
    variable = lambda pigeon, hole: pigeon * holes + hole + 1
    clauses = [
        tuple(variable(pigeon, hole) for hole in range(holes))
        for pigeon in range(pigeons)
    ]
    clauses += [
        (-variable(pigeon, left), -variable(pigeon, right))
        for pigeon in range(pigeons)
        for left, right in combinations(range(holes), 2)
    ]
    clauses += [
        (-variable(left, hole), -variable(right, hole))
        for hole in range(holes)
        for left, right in combinations(range(pigeons), 2)
    ]
    return pigeons * holes, tuple(clauses)


def cases() -> list[dict]:
    rows = []
    for nvars in range(1, 5):
        rows.append({
            "name": f"all_assignments_n{nvars}",
            "family": "all_assignments",
            "parameter": nvars,
            "nvars": nvars,
            "clauses": all_assignment_clauses(nvars),
        })
    for holes in range(1, 4):
        nvars, clauses = pigeonhole(holes + 1, holes)
        rows.append({
            "name": f"pigeonhole_{holes + 1}_{holes}",
            "family": "pigeonhole",
            "parameter": holes,
            "pigeons": holes + 1,
            "holes": holes,
            "nvars": nvars,
            "clauses": clauses,
        })
    return rows


def width_record(nvars: int, clauses: tuple[tuple[int, ...], ...]) -> dict:
    max_width = max((len(clause) for clause in clauses), default=0)
    sweep = []
    minimum = None
    final_stats = None
    for width in range(max_width + 1):
        result = BoundedResolution(nvars, clauses, width, **CAPS).solve()
        row = {
            "width": width,
            "status": result["status"],
            "reason": result.get("reason"),
            "closure_size": len(result["clauses"]),
            "candidate_steps": result["stats"]["candidate_steps"],
        }
        sweep.append(row)
        if result["status"] == "UNSAT":
            minimum = width
            final_stats = result["stats"]
            break
        if result.get("reason") in {"CLAUSE_CAP", "STEP_CAP"}:
            break
    return {
        "minimum_refutation_width": minimum,
        "sweep": sweep,
        "final_stats": final_stats,
    }


def main() -> None:
    scaling = json.loads(
        (ROOT / "proof_complexity_scaling_lab" / "SCALING_RESULTS.json")
        .read_text(encoding="utf-8")
    )
    scaling_by_name = {row["name"]: row for row in scaling["rows"]}
    frontier = json.loads((HERE / "FRONTIER_RESULTS.json").read_text(encoding="utf-8"))
    frontier_by_name = {row["name"]: row for row in frontier["rows"]}
    rows = []
    for case in cases():
        width = width_record(case["nvars"], case["clauses"])
        source_cdcl = scaling_by_name[case["name"]]
        source_frontier = frontier_by_name[case["name"]]
        rows.append({
            "name": case["name"],
            "family": case["family"],
            "parameter": case["parameter"],
            "pigeons": case.get("pigeons"),
            "holes": case.get("holes"),
            "nvars": case["nvars"],
            "clauses": [list(clause) for clause in case["clauses"]],
            "clause_count": len(case["clauses"]),
            "input_literals": sum(map(len, case["clauses"])),
            "caps": CAPS,
            "width": width,
            "frontier": source_frontier["frontier"]["stats"],
            "cdcl": {
                "status": source_cdcl["status"],
                "proof_events": source_cdcl["proof_events"],
                "elapsed_seconds": source_cdcl["elapsed_seconds"],
                "stats": source_cdcl["stats"],
            },
        })
    output = {
        "format": "proof-width-frontier-cdcl-bridge-v1",
        "rows": rows,
        "all_width_cases_exact": all(row["width"]["minimum_refutation_width"] is not None
                                       for row in rows),
        "source_sha256": {
            "resolution_width_lab/resolution.py": digest(ROOT / "resolution_width_lab" / "resolution.py"),
            "proof_complexity_scaling_lab/SCALING_RESULTS.json": digest(
                ROOT / "proof_complexity_scaling_lab" / "SCALING_RESULTS.json"
            ),
            "proof_complexity_frontier_lab/FRONTIER_RESULTS.json": digest(
                HERE / "FRONTIER_RESULTS.json"
            ),
            "proof_complexity_frontier_lab/run_width_bridge.py": digest(HERE / "run_width_bridge.py"),
            "proof_complexity_frontier_lab/review_width_bridge.py": digest(
                HERE / "review_width_bridge.py"
            ),
            "proof_complexity_frontier_lab/THEOREM.md": digest(HERE / "THEOREM.md"),
        },
    }
    (HERE / "WIDTH_RESULTS.json").write_text(json.dumps(output, indent=2) + "\n", encoding="utf-8")
    write_report(rows)
    print(json.dumps({"status": "PASS", "case_count": len(rows),
                      "all_width_cases_exact": output["all_width_cases_exact"]}))


def write_report(rows: list[dict]) -> None:
    lines = [
        "# Resolution width, frontier states, and CDCL traces",
        "",
        "The same seven finite CNFs are replayed in three representations:",
        "minimum refutation width from bounded weakening/resolution closure,",
        "supplied-order frontier state counts, and one proof-producing CDCL trace.",
        "",
        "| family | parameter | variables | clauses | min width | width closure | frontier width | frontier states | CDCL conflicts | CDCL resolution steps |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for row in rows:
        lines.append(
            f"| {row['family']} | {row['parameter']} | {row['nvars']} | "
            f"{row['clause_count']} | {row['width']['minimum_refutation_width']} | "
            f"{row['width']['final_stats']['known_clauses']} | "
            f"{row['frontier']['max_width']} | {row['frontier']['states']} | "
            f"{row['cdcl']['stats']['conflicts']} | {row['cdcl']['stats']['resolution_steps']} |"
        )
    lines += [
        "",
        "The width sweep is complete only for the displayed finite controls and",
        "uses an explicit 100,000-clause/500,000-candidate cap. Each saved sweep",
        "is recomputed by an independent reviewer. The frontier order is supplied",
        "row-major order, and the CDCL fields come from separately replayed",
        "first-UIP resolution certificates.",
        "",
        "These measurements do not imply that width controls every proof system,",
        "that CDCL is optimal, or that any value lower-bounds arbitrary SAT",
        "algorithms. They are a finite adversarial comparison, not a P-versus-NP",
        "resolution.",
        "",
    ]
    (HERE / "WIDTH_REPORT.md").write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    main()
