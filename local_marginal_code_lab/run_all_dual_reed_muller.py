"""Generate and verify all-dual-parity RM certificates."""

import json
from fractions import Fraction
from pathlib import Path

from all_dual_reed_muller import make_certificate, verify_certificate


def main():
    cases = []
    for s in (1, 2, 3):
        made = make_certificate(s)
        if made["status"] != "FOUND":
            raise RuntimeError(made)
        verification = verify_certificate(made["certificate"])
        if not verification["valid"]:
            raise RuntimeError(verification)
        cases.append({"name": f"RM({s},{2 * s + 1})_all_dual",
                      "certificate": made["certificate"],
                      "verification": verification})
    output = {
        "format": "reed-muller-all-dual-lp-v1",
        "family": "RM(s,2s+1)",
        "cases": cases,
        "all_valid": all(case["verification"]["valid"] for case in cases),
        "interpretation": (
            "Every nonzero dual check is supplied for free in the relaxation; "
            "the uniform rational point remains feasible, while balanced "
            "minimum-weight affine checks prove its exact fractional optimum."
        ),
        "source_report": "REED_MULLER_ALL_DUAL_REPORT.md",
    }
    Path("REED_MULLER_ALL_DUAL_RESULTS.json").write_text(
        json.dumps(output, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "status": "REED_MULLER_ALL_DUAL_PASS",
        "cases": len(cases),
        "fractional_optima": [case["verification"]["fractional_optimum"]
                              for case in cases],
        "integrality_ratios": [str(case["verification"]["integrality_ratio"])
                               for case in cases],
    }))


if __name__ == "__main__":
    main()
