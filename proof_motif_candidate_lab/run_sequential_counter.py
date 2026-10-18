"""Generate the bounded prefix-counter certificate and adversarial controls."""
from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path

import sequential_counter as sc


ROOT = Path(__file__).resolve().parent


def _renamed_clauses(clauses, mapping):
    out = []
    for clause in clauses:
        out.append(tuple((1 if literal > 0 else -1) * (mapping[abs(literal) - 1] + 1)
                         for literal in clause))
    return tuple(out)


def main():
    positive_cert = sc.certificate(5, 2)
    positive_clauses = sc.expected_clauses(5, 2)
    positive_check = sc.verify_certificate(positive_clauses, positive_cert)

    missing = list(positive_clauses)
    missing.pop(len(missing) // 2)
    missing_check = sc.verify_certificate(missing, positive_cert)

    mutated = [list(clause) for clause in positive_clauses]
    mutated[0][0] = -mutated[0][0]
    mutated_check = sc.verify_certificate(mutated, positive_cert)

    wrong_threshold = sc.verify_certificate(positive_clauses, sc.certificate(5, 1))
    canonical_discovery = sc.discover_canonical(positive_clauses, max_inputs=5, max_threshold=4)

    # A role-permuted formula remains valid under the supplied role map, while
    # the canonical scanner deliberately does not pretend to discover it.
    role_map = {index: (31 - index) for index in range(20)}
    shuffled_inputs = tuple(role_map[index] for index in positive_cert["inputs"])
    shuffled_states = tuple(tuple(role_map[index] for index in row)
                            for row in positive_cert["states"])
    shuffled_cert = sc.certificate(5, 2, shuffled_inputs, shuffled_states)
    shuffled_clauses = _renamed_clauses(positive_clauses, role_map)
    shuffled_check = sc.verify_certificate(shuffled_clauses, shuffled_cert)
    shuffled_discovery = sc.discover_canonical(shuffled_clauses, max_inputs=5, max_threshold=4)
    isomorphic_discovery = sc.discover_isomorphic(shuffled_clauses, 5, 2)
    cap_discovery = sc.discover_isomorphic(shuffled_clauses, 5, 2, max_variables=8)

    scaling = []
    for n_inputs in range(1, 8):
        threshold = max(0, n_inputs // 2)
        cert = sc.certificate(n_inputs, threshold)
        clauses = sc.expected_clauses(n_inputs, threshold)
        check = sc.verify_certificate(clauses, cert, semantic_cap=20)
        scaling.append({"n_inputs": n_inputs, "threshold": threshold,
                        "variables": cert["variable_count"], "clauses": len(clauses),
                        "status": check["status"],
                        "semantic_status": check["semantic"].get("status")})

    source_names = ("sequential_counter.py", "run_sequential_counter.py",
                    "review_sequential_counter.py", "SEQUENTIAL_COUNTER_REPORT.md")
    source_hashes = {name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest()
                     for name in source_names if (ROOT / name).exists()}
    result = {
        "all_checks_passed": positive_check["status"] == "ACCEPT"
        and missing_check["status"] == "REJECT"
        and mutated_check["status"] == "REJECT"
        and wrong_threshold["status"] == "REJECT"
        and shuffled_check["status"] == "ACCEPT"
        and canonical_discovery["status"] == "FOUND"
        and shuffled_discovery["status"] == "NOT_FOUND"
        and isomorphic_discovery["status"] == "FOUND"
        and cap_discovery["status"] == "UNKNOWN_CAP",
        "scope": "exact prefix-threshold sequential counter with supplied role map",
        "positive": {"certificate": positive_cert, "clauses": [list(c) for c in positive_clauses],
                     "verification": positive_check},
        "controls": {
            "missing_clause": {"verification": missing_check},
            "literal_mutation": {"verification": mutated_check},
            "wrong_threshold": {"verification": wrong_threshold},
            "shuffled_roles": {"certificate": shuffled_cert,
                               "clauses": [list(c) for c in shuffled_clauses],
                               "verification": shuffled_check,
                               "canonical_discovery": shuffled_discovery,
                               "isomorphic_discovery": isomorphic_discovery,
                               "cap_discovery": cap_discovery},
        },
        "canonical_discovery": canonical_discovery,
        "scaling": scaling,
        "source_sha256": source_hashes,
    }
    (ROOT / "SEQUENTIAL_COUNTER_RESULTS.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps({"all_checks_passed": result["all_checks_passed"],
                      "positive": positive_check["status"],
                      "missing": missing_check["status"],
                      "mutation": mutated_check["status"],
                      "wrong_threshold": wrong_threshold["status"],
                      "shuffled": shuffled_check["status"],
                      "canonical_discovery": canonical_discovery["status"],
                      "shuffled_discovery": shuffled_discovery["status"],
                      "isomorphic_discovery": isomorphic_discovery["status"],
                      "cap_discovery": cap_discovery["status"]}, sort_keys=True))
    return 0 if result["all_checks_passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
