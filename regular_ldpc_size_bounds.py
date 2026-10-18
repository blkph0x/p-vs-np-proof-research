"""Exact size accounting for the degree-three LDPC reductions.

The formulas mirror the size variables in Theorems 16 and 18 of
Jia et al., arXiv:2606.23161v3.  This module is an accounting checker: it
does not claim to prove the source paper's parity bijections.
"""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent


def first_phase(n, auxiliary, threshold):
    """Return the replication and threshold parameters of Phase I.

    ``auxiliary`` is the number M of check-splitting variables.  The source
    uses ``m=2*max(1,M)``, ``lambda=m+4``, and ``hat_w=lambda*w+2*M``.
    """
    if not isinstance(n, int) or not isinstance(auxiliary, int) or not isinstance(threshold, int):
        raise ValueError("parameters must be integers")
    if n < 1 or auxiliary < 0 or not 0 <= threshold <= n:
        raise ValueError("invalid first-phase parameters")
    m = 2 * max(1, auxiliary)
    lam = m + 4
    variables = lam * n + 2 * auxiliary
    target = lam * threshold + 2 * auxiliary
    return {
        "n": n,
        "auxiliary": auxiliary,
        "threshold": threshold,
        "replication": m,
        "lambda": lam,
        "phase_one_variables": variables,
        "phase_one_threshold": target,
    }


def suffix_phase(phase_one_variables, degree_two_checks):
    """Return exact copy and suffix sizes for Phase II.

    The smallest admissible multiple of three is
    ``c = 3*ceil((N+1)/q)``.  Thus ``h=c*q >= 3*N+3``.  With ``t=h/3``
    stages, the suffix variable count is the exact sum
    ``sum_{j=0}^{t-1}(h-3*j-2) = h*(h-1)/6``.
    """
    if not isinstance(phase_one_variables, int) or not isinstance(degree_two_checks, int):
        raise ValueError("parameters must be integers")
    if phase_one_variables < 1 or degree_two_checks < 1:
        raise ValueError("positive graph sizes are required")
    q = degree_two_checks
    c = 3 * ((phase_one_variables + q) // q)
    # The expression above is ceil((N+1)/q) written without floating point.
    if c * q < 3 * phase_one_variables + 3:
        raise AssertionError("copy multiplier did not meet the source bound")
    h = c * q
    t = h // 3
    direct_sum = sum(h - 3 * j - 2 for j in range(t))
    suffix_variables = h * (h - 1) // 6
    if direct_sum != suffix_variables:
        raise AssertionError((h, direct_sum, suffix_variables))
    copied_variables = c * phase_one_variables
    final_variables = copied_variables + suffix_variables
    return {
        "phase_one_variables": phase_one_variables,
        "degree_two_checks": q,
        "copy_multiplier": c,
        "completed_degree_two_checks": h,
        "stages": t,
        "copied_variables": copied_variables,
        "suffix_variables": suffix_variables,
        "final_variables": final_variables,
    }


def run_audit(max_n=32):
    """Check the exact inequalities over a finite but broad integer grid."""
    if not isinstance(max_n, int) or max_n < 1:
        raise ValueError("max_n must be a positive integer")
    first_rows = 0
    suffix_rows = 0
    max_suffix = 0
    for n in range(1, max_n + 1):
        # A 3-left-regular input has 3*n incidences, so M<=3*n is a safe
        # accounting envelope for check-splitting auxiliaries.
        for auxiliary in range(0, 3 * n + 1):
            for threshold in range(n + 1):
                row = first_phase(n, auxiliary, threshold)
                assert row["lambda"] > 2 * auxiliary
                assert row["phase_one_threshold"] <= row["phase_one_variables"]
                first_rows += 1
            # q is at most the number of checks, and 3*n is a conservative
            # envelope for the non-isolated checks in the transformed graph.
            for q in range(1, 3 * n + 1):
                row = suffix_phase(first_phase(n, auxiliary, n)["phase_one_variables"], q)
                assert row["completed_degree_two_checks"] >= 3 * row["phase_one_variables"] + 3
                assert row["completed_degree_two_checks"] // 3 > row["phase_one_variables"]
                max_suffix = max(max_suffix, row["suffix_variables"])
                suffix_rows += 1
    return {
        "all_checks_passed": True,
        "max_n": max_n,
        "first_phase_rows": first_rows,
        "suffix_phase_rows": suffix_rows,
        "max_suffix_variables": max_suffix,
        "scope": "integer size-accounting audit; parity bijections remain separately scoped",
    }


def main():
    payload = run_audit()
    (ROOT / "REGULAR_LDPC_SIZE_BOUND_AUDIT.json").write_text(
        json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(payload, indent=2))


if __name__ == "__main__":
    main()
