"""Build compact frontier/CDCL comparison records."""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(ROOT / "variable_boundary_sat_lab"))
sys.path.insert(0, str(ROOT / "proof_complexity_scaling_lab"))

from boundary_dp import solve  # noqa: E402
from families import all_assignment_clauses, controls, pigeonhole  # noqa: E402


def digest(path: Path) -> str:
    text = path.read_text(encoding="utf-8")
    return hashlib.sha256(text.replace("\r\n", "\n").replace("\r", "\n").encode()).hexdigest()


def compact_frontier(result: dict) -> dict:
    """Keep all layer counts while avoiding a second large state certificate."""
    return {
        "status": result["status"],
        "reason": result.get("reason"),
        "sat": result.get("sat"),
        "order": result["order"],
        "boundaries": result["boundaries"],
        "boundary_widths": [len(boundary) for boundary in result["boundaries"]],
        "layer_state_counts": [len(layer) for layer in result.get("states", [])],
        "layer_transition_counts": [len(layer) for layer in result.get("transitions", [])],
        "stats": result["stats"],
    }


def frontier_cases():
    rows = []
    for nvars in range(1, 8):
        rows.append({
            "name": f"all_assignments_n{nvars}",
            "family": "all_assignments",
            "parameter": nvars,
            "nvars": nvars,
            "clauses": all_assignment_clauses(nvars),
        })
    for holes in range(1, 8):
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


def main() -> None:
    scaling_path = ROOT / "proof_complexity_scaling_lab" / "SCALING_RESULTS.json"
    scaling = json.loads(scaling_path.read_text(encoding="utf-8"))
    scaling_by_name = {row["name"]: row for row in scaling["rows"]}
    rows = []
    for case in frontier_cases():
        result = solve(case["nvars"], [list(c) for c in case["clauses"]],
                       list(range(case["nvars"])))
        assert result["status"] == "EXACT"
        saved_scaling = scaling_by_name[case["name"]]
        rows.append({
            "name": case["name"],
            "family": case["family"],
            "parameter": case["parameter"],
            "pigeons": case.get("pigeons"),
            "holes": case.get("holes"),
            "nvars": case["nvars"],
            "clause_count": len(case["clauses"]),
            "input_literals": sum(len(clause) for clause in case["clauses"]),
            "frontier": compact_frontier(result),
            "cdcl": {
                "status": saved_scaling["status"],
                "proof_events": saved_scaling["proof_events"],
                "elapsed_seconds": saved_scaling["elapsed_seconds"],
                "stats": saved_scaling["stats"],
            },
        })

    output = {
        "format": "proof-complexity-frontier-comparison-v1",
        "rows": rows,
        "all_frontier_cases_exact": True,
        "source_sha256": {
            "proof_complexity_scaling_lab/SCALING_RESULTS.json": digest(scaling_path),
            "variable_boundary_sat_lab/boundary_dp.py": digest(ROOT / "variable_boundary_sat_lab" / "boundary_dp.py"),
            "proof_complexity_frontier_lab/run_frontier.py": digest(HERE / "run_frontier.py"),
            "proof_complexity_frontier_lab/review_frontier.py": digest(HERE / "review_frontier.py"),
            "proof_complexity_frontier_lab/THEOREM.md": digest(HERE / "THEOREM.md"),
        },
    }
    (HERE / "FRONTIER_RESULTS.json").write_text(json.dumps(output, indent=2) + "\n", encoding="utf-8")
    write_report(rows)
    print(json.dumps({"status": "PASS", "case_count": len(rows), "all_frontier_cases_exact": True}))


def write_report(rows: list[dict]) -> None:
    lines = [
        "# Proof width, CDCL traces, and frontier-state growth",
        "",
        "Every row below is reconstructed by `review_frontier.py`. CDCL fields",
        "come from the separately replayed proof-producing scaling certificates.",
        "",
        "## All-assignment family",
        "",
        "| n | input literals | frontier width | retained states | CDCL conflicts | resolution steps |",
        "| ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for row in rows:
        if row["family"] != "all_assignments":
            continue
        lines.append(
            f"| {row['parameter']} | {row['input_literals']} | "
            f"{row['frontier']['stats']['max_width']} | {row['frontier']['stats']['states']} | "
            f"{row['cdcl']['stats']['conflicts']} | {row['cdcl']['stats']['resolution_steps']} |"
        )
    lines += [
        "",
        "## Pigeonhole family",
        "",
        "| holes | input literals | frontier width | retained states | CDCL conflicts | resolution steps |",
        "| ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for row in rows:
        if row["family"] != "pigeonhole":
            continue
        lines.append(
            f"| {row['parameter']} | {row['input_literals']} | "
            f"{row['frontier']['stats']['max_width']} | {row['frontier']['stats']['states']} | "
            f"{row['cdcl']['stats']['conflicts']} | {row['cdcl']['stats']['resolution_steps']} |"
        )
    lines += [
        "",
        "The all-assignment input is already exponential in `n`; its exact count",
        "identities are controls, not input-length lower bounds. The pigeonhole",
        "inputs are polynomial in the hole parameter and have a direct injection",
        "contradiction. The table still measures one supplied variable order and",
        "one deterministic resolution-based CDCL implementation. It is evidence",
        "for adversarial scaling, not a lower bound for every SAT algorithm.",
        "",
    ]
    (HERE / "FRONTIER_REPORT.md").write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    main()
