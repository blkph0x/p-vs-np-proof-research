"""Generate the deterministic Reed--Muller local-marginal certificate set."""

import json
from pathlib import Path

from reed_muller import make_certificate, verify_certificate


def main():
    cases = []
    for s in (1, 2, 3):
        made = make_certificate(s, pin=0, enumerate_scopes=(s == 1))
        if made["status"] != "FOUND":
            raise RuntimeError(made)
        checked = verify_certificate(made["certificate"])
        if not checked["valid"]:
            raise RuntimeError(checked)
        cases.append({"name": f"RM({s},{2 * s + 1})_level_{checked['level']}",
                      "certificate": made["certificate"],
                      "verification": checked})
    output = {
        "format": "reed-muller-local-pinned-v1",
        "family": "RM(s,2s+1)",
        "cases": cases,
        "all_valid": all(case["verification"]["valid"] for case in cases),
        "theorem": {
            "length": "2^(2s+1)",
            "dimension": "2^(2s)",
            "minimum_distance": "2^(s+1)",
            "dual_distance": "2^(s+1)",
            "local_level": "2^(s+1)-2",
            "pinned_integer_optimum": "2^(s+1)",
        },
        "scope": "exact local projection-marginal relaxation; no claim about a named hierarchy",
        "source_urls": [
            "https://doi.org/10.1109/TIT.1954.1057465",
            "https://ocw.mit.edu/courses/6-895-essential-coding-theory-fall-2004/resources/lect05slx4/",
        ],
    }
    Path("REED_MULLER_RESULTS.json").write_text(json.dumps(output, indent=2) + "\n")
    print(json.dumps({
        "status": "REED_MULLER_LOCAL_MARGINAL_PASS",
        "cases": len(cases),
        "parameters": [(case["certificate"]["s"], case["certificate"]["n"],
                        case["certificate"]["distance"]) for case in cases],
        "all_valid": output["all_valid"],
    }))


if __name__ == "__main__":
    main()
