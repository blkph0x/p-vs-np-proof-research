"""Generate proof-producing CDCL scaling certificates."""
from __future__ import annotations

import hashlib
import json
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(ROOT))

from proof_producing_cdcl_lab.cdcl import CDCL  # noqa: E402
from families import controls  # noqa: E402


def source_hashes() -> dict[str, str]:
    paths = (
        HERE / "families.py",
        HERE / "run_scaling.py",
        HERE / "review_scaling.py",
        HERE / "test_scaling.py",
        HERE / "THEOREM.md",
        ROOT / "proof_producing_cdcl_lab" / "cdcl.py",
    )
    return {path.relative_to(ROOT).as_posix():
            hashlib.sha256(path.read_bytes()).hexdigest() for path in paths}


def write_report(rows: list[dict]) -> None:
    all_rows = [row for row in rows if row["family"] == "all_assignments"]
    pigeon_rows = [row for row in rows if row["family"] == "pigeonhole"]
    lines = [
        "# Proof-complexity scaling report",
        "",
        "This report is generated from `SCALING_RESULTS.json`. Every row has a",
        "complete CDCL resolution trace that is replayed by `review_scaling.py`.",
        "",
        "## All-assignment family",
        "",
        "| n | clauses | decisions | conflicts | resolution steps | seconds |",
        "| ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    lines += [
        f"| {row['parameter']} | {row['clause_count']} | "
        f"{row['stats']['decisions']} | {row['stats']['conflicts']} | "
        f"{row['stats']['resolution_steps']} | {row['elapsed_seconds']:.6f} |"
        for row in all_rows
    ]
    lines += [
        "",
        "## Pigeonhole family",
        "",
        "| pigeons | holes | variables | clauses | decisions | conflicts | resolution steps | seconds |",
        "| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    lines += [
        f"| {row['pigeons']} | {row['holes']} | {row['nvars']} | "
        f"{row['clause_count']} | {row['stats']['decisions']} | "
        f"{row['stats']['conflicts']} | {row['stats']['resolution_steps']} | "
        f"{row['elapsed_seconds']:.6f} |"
        for row in pigeon_rows
    ]
    lines += [
        "",
        "The first family has exponential size in its parameter, so its",
        "exponential-in-`n` trace is not a super-polynomial-in-input-size",
        "lower bound. The pigeonhole family has polynomial-size CNFs in the",
        "hole parameter and is unsatisfiable by the injection counting proof.",
        "These measurements concern this resolution-based CDCL implementation",
        "and do not lower-bound every SAT algorithm or settle P versus NP.",
        "",
    ]
    (HERE / "SCALING_REPORT.md").write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    rows, certificates = [], []
    for case in controls():
        started = time.perf_counter()
        result = CDCL(case["nvars"], case["clauses"]).solve()
        elapsed = time.perf_counter() - started
        assert result["status"] == "UNSAT"
        proof = result["proof"]
        stats = result["stats"]
        row = {
            "name": case["name"],
            "family": case["family"],
            "parameter": case["parameter"],
            "nvars": case["nvars"],
            "clause_count": len(case["clauses"]),
            "input_literals": sum(len(clause) for clause in case["clauses"]),
            "status": result["status"],
            "proof_events": len(proof),
            "elapsed_seconds": elapsed,
            "stats": stats,
        }
        if case["family"] == "pigeonhole":
            row.update({"pigeons": case["pigeons"], "holes": case["holes"]})
        rows.append(row)
        certificates.append({
            "name": case["name"],
            "family": case["family"],
            "parameter": case["parameter"],
            "pigeons": case.get("pigeons"),
            "holes": case.get("holes"),
            "nvars": case["nvars"],
            "clauses": [list(clause) for clause in case["clauses"]],
            "elapsed_seconds": elapsed,
            "result": result,
        })

    output = {
        "format": "proof-producing-cdcl-scaling-v1",
        "rows": rows,
        "all_cases_unsat": True,
        "source_sha256": source_hashes(),
    }
    (HERE / "SCALING_RESULTS.json").write_text(
        json.dumps(output, indent=2) + "\n", encoding="utf-8"
    )
    (HERE / "SCALING_CERTIFICATES.json").write_text(
        json.dumps(certificates, indent=2) + "\n", encoding="utf-8"
    )
    write_report(rows)
    print(json.dumps({"status": "PASS", "case_count": len(rows)}))


if __name__ == "__main__":
    main()
