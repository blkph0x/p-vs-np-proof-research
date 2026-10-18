"""Generate the all-n PHP width certificate and its compact summary."""
from __future__ import annotations

import json
from pathlib import Path

from php_width_proof import (HERE, build_php_width_proof, certificate_digest,
                             expected_resolution_steps, source_hashes)
from review_php_width_proof import review_certificate


def main():
    rows = []
    certificate = None
    for holes in range(1, 6):
        current = build_php_width_proof(holes)
        row = {
            "holes": holes,
            "pigeons": holes + 1,
            "variables": current["nvars"],
            "stage_counts": current["stage_counts"],
            "resolution_steps": current["resolution_steps"],
            "expected_resolution_steps": expected_resolution_steps(holes),
            "max_width": current["max_width"],
            "final_clause": current["events"][current["final_event"]]["clause"],
            "event_count": len(current["events"]),
            "certificate_status": current["status"],
        }
        rows.append(row)
        if holes == 5:
            certificate = current
    certificate_path = HERE / "PHP_WIDTH_CERTIFICATE_N5.json"
    certificate_path.write_text(json.dumps(certificate, indent=2, sort_keys=True) + "\n",
                                encoding="utf-8")
    review = review_certificate(certificate_path)
    results = {
        "schema": "php_width_results_v1",
        "family": "standard PHP(n+1,n)",
        "theorem": "minimum resolution refutation width is n for n >= 2 (PHP(2,1) has width 2)",
        "rows": rows,
        "certificate": certificate_path.name,
        "certificate_sha256": review["certificate_sha256"],
        "independent_replay": review,
        "source_hashes": source_hashes(),
        "status": "PASS",
    }
    (HERE / "PHP_WIDTH_RESULTS.json").write_text(
        json.dumps(results, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    (HERE / "PHP_WIDTH_REVIEW.json").write_text(
        json.dumps({"status": "PASS", "certificate": review,
                    "source_hashes": source_hashes()},
                   indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps(results, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
