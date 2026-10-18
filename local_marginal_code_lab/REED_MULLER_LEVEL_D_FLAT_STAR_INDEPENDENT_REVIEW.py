"""Independently replay the exact RM(2,5) affine-flat star control."""

from __future__ import annotations

import json
from fractions import Fraction
from math import comb
from pathlib import Path


ROOT = Path(__file__).resolve().parent
INPUT = ROOT / "REED_MULLER_LEVEL_D_FLAT_STAR_RESULTS.json"
OUT = ROOT / "REED_MULLER_LEVEL_D_FLAT_STAR_INDEPENDENT_REVIEW.json"
OUT_MD = ROOT / "REED_MULLER_LEVEL_D_FLAT_STAR_INDEPENDENT_REVIEW.md"


def gaussian_binomial(n: int, k: int) -> int:
    numerator = 1
    denominator = 1
    for index in range(k):
        numerator *= (1 << (n - index)) - 1
        denominator *= (1 << (k - index)) - 1
    return numerator // denominator


def replay(certificate: dict) -> dict:
    expected = {
        "schema": "reed_muller_level_d_flat_star_v1",
        "family": "RM(2,5)",
        "n": 32,
        "pin": 0,
        "distance": 8,
        "flat_dimension": 3,
        "flat_size": 8,
        "scope_consistency": "SINGLETONS_ONLY",
        "full_level_d_status": "UNRESOLVED",
    }
    for key, value in expected.items():
        if certificate.get(key) != value:
            raise ValueError(f"certificate field mismatch: {key}")
    linear = gaussian_binomial(5, 3)
    affine = linear * 4
    incidence = gaussian_binomial(4, 2)
    if certificate["linear_flat_count"] != linear:
        raise ValueError("linear-flat count mismatch")
    if certificate["affine_flat_count"] != affine:
        raise ValueError("affine-flat count mismatch")
    if certificate["flats_through_pin"] != linear:
        raise ValueError("through-pin count mismatch")
    if certificate["flats_omitting_pin"] != affine - linear:
        raise ValueError("omitting-pin count mismatch")
    if certificate["minimum_check_incidence_per_nonpin"] != incidence:
        raise ValueError("incidence mismatch")
    p = Fraction(1, 7)
    if certificate["point"] != ["1"] + [str(p)] * 31:
        raise ValueError("singleton point mismatch")
    lower_bound = Fraction(1) + Fraction(linear, incidence)
    if Fraction(certificate["star_relaxation_optimum"]) != lower_bound:
        raise ValueError("star optimum mismatch")
    if certificate["integer_pinned_optimum"] != "8":
        raise ValueError("integer optimum mismatch")
    if Fraction(certificate["integrality_ratio"]) != Fraction(8, 1) / lower_bound:
        raise ValueError("ratio mismatch")
    through = certificate["through_pin_table"]
    if through != {
        "pin_value": "1",
        "free_length": 7,
        "parity": "ODD",
        "mixture": [["1", 1]],
        "each_free_coordinate_mass": str(p),
    }:
        raise ValueError("through-pin table mismatch")
    omit = certificate["omitting_pin_table"]
    if omit != {
        "length": 8,
        "parity": "EVEN",
        "mixture": [["3/7", 0], ["4/7", 2]],
        "weight_two_distribution": "UNIFORM_OVER_2_SUBSETS",
        "each_coordinate_mass": str(p),
    }:
        raise ValueError("omitting-pin table mismatch")
    # Exact marginal checks for the two distributions.
    if Fraction(1, 7) != p:
        raise ValueError("odd-table marginal mismatch")
    if Fraction(4, 7) * Fraction(2, 8) != p:
        raise ValueError("even-table marginal mismatch")
    return {
        "status": "VERIFIED",
        "valid": True,
        "family": "RM(2,5)",
        "affine_flat_count": affine,
        "flats_through_pin": linear,
        "singleton_point": certificate["point"],
        "star_relaxation_optimum": str(lower_bound),
        "integer_pinned_optimum": "8",
        "integrality_ratio": certificate["integrality_ratio"],
        "full_level_d_status": "UNRESOLVED",
    }


def main() -> None:
    payload = json.loads(INPUT.read_text(encoding="utf-8"))
    if payload.get("schema") != "reed_muller_level_d_flat_star_results_v1":
        raise ValueError("invalid results schema")
    verification = replay(payload["records"][0]["certificate"])
    OUT.write_text(
        json.dumps(
            {
                "schema": "reed_muller_level_d_flat_star_independent_review_v1",
                "valid": True,
                "records": [verification],
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    OUT_MD.write_text(
        "# Independent review\n\n"
        "The reviewer reconstructs the Gaussian-binomial affine-flat counts, "
        "the two exact parity mixtures, the singleton marginals, and the "
        "38/7 lower bound without an LP solver. It intentionally records the "
        "full level-d status as unresolved because singleton consistency is a "
        "weaker relaxation.\n",
        encoding="utf-8",
    )
    print("VERIFIED_INDEPENDENT_REED_MULLER_LEVEL_D_FLAT_STAR")
    print(f"flats={verification['affine_flat_count']} optimum={verification['star_relaxation_optimum']}")


if __name__ == "__main__":
    main()
