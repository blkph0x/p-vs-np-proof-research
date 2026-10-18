"""Generate the exact full FWHT-Zeta operation-count artifact."""
from __future__ import annotations

import json
from hashlib import sha256
from pathlib import Path

from fwht_cost import exact_cost
from review_fwht_cost import review


HERE = Path(__file__).resolve().parent


def source_hashes():
    names = ("fwht_cost.py", "review_fwht_cost.py", "run_fwht_cost.py",
             "FWHT_COST_REPORT.md", "../test_fwht_cost_audit.py")
    return {name: sha256((HERE / name).read_bytes()).hexdigest() for name in names}


def main():
    rows = [exact_cost(dimension) for dimension in range(0, 21)]
    payload = {
        "schema": "fwht_zeta_cost_v1",
        "interpretation": "A full length-2^n FWHT plus subset zeta pass; conditional barrier only.",
        "rows": rows,
        "source_hashes": source_hashes(),
    }
    path = HERE / "FWHT_COST_RESULTS.json"
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n",
                    encoding="utf-8")
    check = review()
    payload["review"] = check
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n",
                    encoding="utf-8")
    (HERE / "FWHT_COST_REVIEW.json").write_text(
        json.dumps(check, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"status": "PASS", "rows": len(rows), **check}, indent=2))


if __name__ == "__main__":
    main()
