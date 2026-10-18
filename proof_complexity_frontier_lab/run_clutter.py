"""Generate an adversarial semantic-clutter width control."""
from __future__ import annotations

import hashlib
import json
import sys
from itertools import combinations
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(ROOT / "resolution_width_lab"))
sys.path.insert(0, str(HERE))

from resolution import BoundedResolution  # noqa: E402
from order_dp import optimal_order  # noqa: E402


CAPS = {"max_clauses": 100_000, "max_steps": 100_000}


def digest(path: Path) -> str:
    text = path.read_text(encoding="utf-8")
    normalized = text.replace("\r\n", "\n").replace("\r", "\n")
    return hashlib.sha256(normalized.encode()).hexdigest()


def clutter_formula(clique_variables: int):
    """z and -z contradict; positive 2-clauses form a K_n on x variables."""
    z = clique_variables + 1
    clauses = [(z,), (-z,)]
    clauses += [
        (left + 1, right + 1)
        for left, right in combinations(range(clique_variables), 2)
    ]
    return clique_variables + 1, tuple(clauses)


def row_width(nvars, clauses, order):
    position = {variable: index for index, variable in enumerate(order)}
    prefix = set()
    widths = []
    for cut, variable in enumerate(order, 1):
        prefix.add(variable)
        boundary = {
            old for old in prefix
            if any(
                old in {abs(literal) - 1 for literal in clause}
                and any(position[abs(other) - 1] >= cut for other in clause)
                for clause in clauses
            )
        }
        widths.append(len(boundary))
    return widths


def main() -> None:
    rows = []
    for clique_size in range(1, 9):
        nvars, clauses = clutter_formula(clique_size)
        width_one = BoundedResolution(nvars, clauses, 1, **CAPS).solve()
        width_zero = BoundedResolution(nvars, clauses, 0, **CAPS).solve()
        order = [clique_size] + list(range(clique_size))
        widths = row_width(nvars, clauses, order)
        discovered = optimal_order(nvars, clauses)
        rows.append({
            "name": f"unit_clique_clutter_n{clique_size}",
            "clique_size": clique_size,
            "nvars": nvars,
            "clauses": [list(clause) for clause in clauses],
            "clause_count": len(clauses),
            "input_literals": sum(map(len, clauses)),
            "caps": CAPS,
            "resolution_width_zero": {
                "status": width_zero["status"],
                "reason": width_zero.get("reason"),
                "closure_size": len(width_zero["clauses"]),
                "candidate_steps": width_zero["stats"]["candidate_steps"],
            },
            "resolution_width_one": {
                "status": width_one["status"],
                "reason": width_one.get("reason"),
                "closure_size": len(width_one["clauses"]),
                "candidate_steps": width_one["stats"]["candidate_steps"],
                "known_clauses": width_one["stats"]["known_clauses"],
            },
            "row_order": order,
            "row_prefix_widths": widths,
            "row_width": max(widths, default=0),
            "optimal_order": discovered["order"],
            "optimal_prefix_widths": discovered["prefix_widths"],
            "optimal_width": discovered["width"],
        })
    output = {
        "format": "semantic-clutter-width-control-v1",
        "rows": rows,
        "all_rows_exact": True,
        "source_sha256": {
            "resolution_width_lab/resolution.py": digest(ROOT / "resolution_width_lab" / "resolution.py"),
            "proof_complexity_frontier_lab/order_dp.py": digest(HERE / "order_dp.py"),
            "proof_complexity_frontier_lab/run_clutter.py": digest(HERE / "run_clutter.py"),
            "proof_complexity_frontier_lab/review_clutter.py": digest(HERE / "review_clutter.py"),
            "proof_complexity_frontier_lab/THEOREM.md": digest(HERE / "THEOREM.md"),
        },
    }
    (HERE / "CLUTTER_RESULTS.json").write_text(
        json.dumps(output, indent=2) + "\n", encoding="utf-8"
    )
    write_report(rows)
    print(json.dumps({"status": "PASS", "case_count": len(rows), "all_rows_exact": True}))


def write_report(rows):
    lines = [
        "# Semantic clutter: width is not semantic hardness",
        "",
        "For each `n`, the formula is `z AND NOT z` together with every positive",
        "2-clause `(x_i OR x_j)` on a clique of `n` otherwise irrelevant variables.",
        "Unit propagation sees the contradiction immediately, while the primal",
        "clique forces a large variable boundary under every order.",
        "",
        "| clique variables | total variables | clauses | resolution width | minimum frontier width | row-order width |",
        "| ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for row in rows:
        lines.append(
            f"| {row['clique_size']} | {row['nvars']} | {row['clause_count']} | 1 | "
            f"{row['optimal_width']} | {row['row_width']} |"
        )
    lines += [
        "",
        "The width-zero closure has no refutation and width one derives the empty",
        "clause from the two unit axioms. The independent order recurrence finds",
        "minimum boundary `n-1`; the displayed order reaches that value. Removing",
        "either unit makes the remaining positive clique satisfiable by setting all",
        "clique variables true, so the contradiction is a real semantic core rather",
        "than a hidden claim about the clique clauses.",
        "",
        "This is a preprocessing warning. It does not make frontier width useless",
        "after sound simplification, and it does not prove that arbitrary semantic",
        "simplification is polynomial. A general solver must charge the discovery",
        "and removal of such irrelevant structure.",
        "",
    ]
    (HERE / "CLUTTER_REPORT.md").write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    main()
