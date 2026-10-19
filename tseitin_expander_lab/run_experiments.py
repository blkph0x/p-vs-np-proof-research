"""Generate proof-producing odd-charge Tseitin scaling certificates."""
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
import tseitin  # noqa: E402


def source_hashes():
    paths = (
        HERE / "tseitin.py",
        HERE / "run_experiments.py",
        HERE / "INDEPENDENT_REVIEW.py",
        HERE / "test_tseitin.py",
        HERE / "THEOREM.md",
        ROOT / "proof_producing_cdcl_lab" / "cdcl.py",
    )
    return {path.relative_to(ROOT).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
            for path in paths}


def markdown_report(rows):
    lines = [
        "# Tseitin expander scaling report",
        "",
        "Each row is an odd-charge Tseitin contradiction on a connected cubic",
        "graph. The local parity constraints are encoded as 3-CNF, and the",
        "saved result is a complete first-UIP CDCL resolution trace replayed by",
        "`INDEPENDENT_REVIEW.py`.",
        "",
        "| graph | vertices | edge variables | clauses | decisions | conflicts | resolution steps | seconds |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for row in rows:
        stats = row["stats"]
        lines.append(
            f"| {row['name']} | {row['vertices']} | {row['edge_variables']} | "
            f"{row['clause_count']} | {stats['decisions']} | {stats['conflicts']} | "
            f"{stats['resolution_steps']} | {row['elapsed_seconds']:.6f} |"
        )
    lines += [
        "",
        "The odd-charge certificate is an exact XOR argument: every edge",
        "variable occurs at two vertices, so summing all vertex equations",
        "cancels every variable while leaving total charge one. This proves",
        "unsatisfiability of each encoded CNF independently of the CDCL trace.",
        "",
        "[Ben-Sasson and Wigderson](https://people.inf.ethz.ch/emo/SatSem05/Papers/BensassonWidgerson01.pdf)'s width-size tradeoff, together with graph",
        "expansion, supplies the literature boundary for asymptotic resolution",
        "lower bounds on Tseitin contradictions. These finite rows measure one",
        "solver and do not reprove that theorem, lower-bound every SAT algorithm,",
        "or resolve P versus NP.",
        "",
    ]
    return "\n".join(lines)


def main():
    rows, certificates = [], []
    for control in tseitin.graph_controls():
        n = control["n"]
        edges = tseitin.normalize_edges(n, control["edges"])
        charges = [1] + [0] * (n - 1)
        nvars, clauses = tseitin.tseitin_cnf(n, edges, charges)
        parity = tseitin.parity_certificate(n, edges, charges)
        assert parity["parity_proves_unsat"]
        started = time.perf_counter()
        result = CDCL(nvars, clauses, max_conflicts=200_000,
                      max_resolution_steps=2_000_000).solve()
        elapsed = time.perf_counter() - started
        assert result["status"] == "UNSAT", (control["name"], result)
        row = {
            "name": control["name"],
            "vertices": n,
            "edge_variables": nvars,
            "edge_count": len(edges),
            "clause_count": len(clauses),
            "charge": charges,
            "parity": parity,
            "status": result["status"],
            "proof_events": len(result["proof"]),
            "elapsed_seconds": elapsed,
            "stats": result["stats"],
        }
        rows.append(row)
        certificates.append({
            "name": control["name"],
            "vertices": n,
            "edges": [list(edge) for edge in edges],
            "charges": charges,
            "nvars": nvars,
            "clauses": [list(clause) for clause in clauses],
            "parity": parity,
            "result": result,
        })
    output = {
        "format": "tseitin-expander-cdcl-v1",
        "rows": rows,
        "all_cases_unsat": True,
        "source_sha256": source_hashes(),
        "scope": "finite odd-charge Tseitin controls; not an all-size resolution lower-bound proof",
    }
    (HERE / "RESULTS.json").write_text(json.dumps(output, indent=2) + "\n", encoding="utf-8")
    (HERE / "CERTIFICATES.json").write_text(json.dumps(certificates, indent=2) + "\n", encoding="utf-8")
    (HERE / "REPORT.md").write_text(markdown_report(rows), encoding="utf-8")
    print(json.dumps({"status": "PASS", "controls": len(rows),
                      "proof_events": sum(row["proof_events"] for row in rows)}))


if __name__ == "__main__":
    main()
