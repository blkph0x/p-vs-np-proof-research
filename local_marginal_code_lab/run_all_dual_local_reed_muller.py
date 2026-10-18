"""Generate combined all-dual/local Reed--Muller certificates."""

from __future__ import annotations

import json
from pathlib import Path

from all_dual_local_reed_muller import make_certificate, verify_certificate


ROOT = Path(__file__).resolve().parent
OUT = ROOT / "REED_MULLER_ALL_DUAL_LOCAL_RESULTS.json"


def main() -> None:
    records = []
    for s in (1, 2, 3):
        produced = make_certificate(s)
        if produced.get("status") != "FOUND":
            raise AssertionError(f"certificate generation failed for s={s}")
        certificate = produced["certificate"]
        verification = verify_certificate(certificate)
        if verification.get("valid") is not True:
            raise AssertionError(f"self-verification failed for s={s}: {verification}")
        records.append({"status": "FOUND", "certificate": certificate, "verification": verification})
    payload = {
        "schema": "reed_muller_all_dual_local_results_v1",
        "description": "All-dual parity plus level-(dual-distance-2) local marginal certificates",
        "records": records,
    }
    OUT.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print("REED_MULLER_ALL_DUAL_LOCAL_PASS")
    for record in records:
        certificate = record["certificate"]
        print(
            f"s={certificate['s']} n={certificate['n']} level={certificate['level']} "
            f"fractional={certificate['combined_relaxation_optimum']} "
            f"ratio={certificate['integrality_ratio']}"
        )


if __name__ == "__main__":
    main()
