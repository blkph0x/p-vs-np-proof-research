"""Produce the exact affine-flat star-relaxation control for RM(2,5)."""

from __future__ import annotations

import json
from fractions import Fraction
from math import comb
from pathlib import Path


ROOT = Path(__file__).resolve().parent
OUT = ROOT / "REED_MULLER_LEVEL_D_FLAT_STAR_RESULTS.json"


def gaussian_binomial(n: int, k: int) -> int:
    numerator = 1
    denominator = 1
    for index in range(k):
        numerator *= (1 << (n - index)) - 1
        denominator *= (1 << (k - index)) - 1
    return numerator // denominator


def make_certificate() -> dict:
    linear_flats = gaussian_binomial(5, 3)
    affine_flats = linear_flats * (1 << (5 - 3))
    through_pin = linear_flats
    omitting_pin = affine_flats - through_pin
    incidence = gaussian_binomial(4, 2)
    p = Fraction(1, 7)
    fractional = Fraction(1) + Fraction(through_pin, incidence)
    return {
        "schema": "reed_muller_level_d_flat_star_v1",
        "family": "RM(2,5)",
        "n": 32,
        "pin": 0,
        "distance": 8,
        "flat_dimension": 3,
        "flat_size": 8,
        "linear_flat_count": linear_flats,
        "affine_flat_count": affine_flats,
        "flats_through_pin": through_pin,
        "flats_omitting_pin": omitting_pin,
        "minimum_check_incidence_per_nonpin": incidence,
        "point": ["1"] + [str(p)] * 31,
        "objective_convention": "total_weight",
        "star_relaxation_optimum": str(fractional),
        "star_relaxation_nonpin_optimum": str(fractional - 1),
        "integer_pinned_optimum": "8",
        "integer_pinned_nonpin_optimum": "7",
        "integrality_ratio": str(Fraction(8, 1) / fractional),
        "through_pin_table": {
            "pin_value": "1",
            "free_length": 7,
            "parity": "ODD",
            "mixture": [["1", 1]],
            "each_free_coordinate_mass": str(p),
        },
        "omitting_pin_table": {
            "length": 8,
            "parity": "EVEN",
            "mixture": [["3/7", 0], ["4/7", 2]],
            "weight_two_distribution": "UNIFORM_OVER_2_SUBSETS",
            "each_coordinate_mass": str(p),
        },
        "scope_consistency": "SINGLETONS_ONLY",
        "full_level_d_status": "UNRESOLVED",
    }


def main() -> None:
    certificate = make_certificate()
    OUT.write_text(
        json.dumps(
            {
                "schema": "reed_muller_level_d_flat_star_results_v1",
                "description": "Exact affine-flat star relaxation control for RM(2,5).",
                "records": [{"status": "FOUND", "certificate": certificate}],
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    print("PRODUCED_REED_MULLER_LEVEL_D_FLAT_STAR")
    print(f"flats={certificate['affine_flat_count']} optimum={certificate['star_relaxation_optimum']}")


if __name__ == "__main__":
    main()
