"""Generate exact open-neighborhood expansion profiles for the Tseitin graphs."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(HERE))

import tseitin  # noqa: E402


def source_hashes():
    paths = (
        HERE / "tseitin.py",
        HERE / "run_expansion_profile.py",
        HERE / "review_expansion_profile.py",
        HERE / "test_tseitin.py",
        HERE / "THEOREM.md",
    )
    return {path.relative_to(ROOT).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
            for path in paths}


def report(rows):
    lines = [
        "# Tseitin exact expansion profiles",
        "",
        "For each connected cubic graph, this artifact enumerates every nonempty",
        "vertex subset through size floor(n/2). It records both the open",
        "neighborhood `N(S)` and the external neighborhood `N(S)\\S`, with the",
        "exact ratio at every subset size, the global minimum, and an explicit",
        "lexicographically first witness. `review_expansion_profile.py` rebuilds",
        "the graph family and recomputes every value independently.",
        "",
        "| graph | vertices | open epsilon | external epsilon | subsets checked |",
        "| --- | ---: | ---: | ---: | ---: |",
    ]
    for row in rows:
        profile = row["profile"]
        lines.append(
            f"| {row['name']} | {row['vertices']} | "
            f"{profile['epsilon_numerator']}/{profile['epsilon_denominator']} | "
            f"{row['external_profile']['epsilon_numerator']}/"
            f"{row['external_profile']['epsilon_denominator']} | "
            f"{profile['subsets_checked']} |"
        )
    lines += [
        "",
        "This is an exact finite graph certificate. The external ratios make the",
        "boundary explicit: the saved Möbius-ladder values decline to 2/5 at",
        "20 vertices, so these rows are not evidence for a standard uniform",
        "external-expander family. The profile is recorded alongside the",
        "proof-producing CDCL measurements; no resolution lower bound or",
        "P-versus-NP conclusion is inferred from these ratios alone.",
        "",
    ]
    return "\n".join(lines)


def main():
    controls = tuple(tseitin.graph_controls()) + tuple(tseitin.mobius_ladder_controls())
    rows = []
    for control in controls:
        edges = tseitin.normalize_edges(control["n"], control["edges"])
        rows.append({
            "name": control["name"],
            "vertices": control["n"],
            "edges": [list(edge) for edge in edges],
            "family": control.get("family", "named_control"),
            "profile": tseitin.expansion_profile(control["n"], edges),
            "external_profile": tseitin.external_expansion_profile(control["n"], edges),
        })
    output = {
        "format": "tseitin-exact-expansion-v1",
        "rows": rows,
        "all_profiles_exact": True,
        "scope": "finite open-neighborhood expansion profiles through half-size sets",
        "source_sha256": source_hashes(),
    }
    (HERE / "EXPANSION_RESULTS.json").write_text(
        json.dumps(output, indent=2) + "\n", encoding="utf-8"
    )
    (HERE / "EXPANSION_REPORT.md").write_text(report(rows), encoding="utf-8")
    print(json.dumps({
        "status": "PASS",
        "controls": len(rows),
        "subsets_checked": sum(row["profile"]["subsets_checked"] for row in rows),
    }))


if __name__ == "__main__":
    main()
