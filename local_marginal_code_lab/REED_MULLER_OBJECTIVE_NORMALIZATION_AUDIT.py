"""Audit the pinned-coordinate objective convention in the RM(2,5) records."""

from __future__ import annotations

import itertools
import json
from fractions import Fraction
from pathlib import Path


HERE = Path(__file__).resolve().parent


def _rows():
    masks = []
    for degree in range(3):
        for support in itertools.combinations(range(5), degree):
            masks.append(sum(1 << index for index in support))
    return tuple(
        sum(1 << point for point in range(32) if point & mask == mask)
        for mask in masks
    )


def _pinned_words():
    words = [0]
    for row in _rows():
        words += [word ^ row for word in tuple(words)]
    return tuple(word for word in words if word & 1)


def _fractional_value(path: Path) -> Fraction:
    payload = json.loads(path.read_text(encoding="utf-8"))
    return sum(
        Fraction(coefficient) * Fraction(value)
        for coefficient, value in zip(
            payload["objective"], payload["primal_orbit_masses"]
        )
    )


def main() -> None:
    words = _pinned_words()
    total_optimum = min(word.bit_count() for word in words)
    nonpin_optimum = min((word & ~1).bit_count() for word in words)
    full = HERE / "REED_MULLER_LEVEL_D_FULL_RESULTS.json"
    affine = HERE / "REED_MULLER_LEVEL_D_AFFINE_OVERLAP_RESULTS.json"
    nonpin_full = _fractional_value(full)
    nonpin_affine = _fractional_value(affine)
    if (total_optimum, nonpin_optimum) != (8, 7):
        raise ValueError("unexpected pinned RM(2,5) benchmark")
    if nonpin_full != Fraction(31, 5) or nonpin_affine != Fraction(31, 5):
        raise ValueError("unexpected reduced objective value")
    result = {
        "schema": "reed_muller_objective_normalization_audit_v1",
        "family": "RM(2,5)",
        "pin": 0,
        "objective_convention_in_certificates": "nonpin_weight",
        "nonpin_fractional_optimum": "31/5",
        "total_fractional_optimum": "36/5",
        "nonpin_integer_optimum": "7",
        "total_integer_optimum": "8",
        "nonpin_ratio": "35/31",
        "total_ratio": "10/9",
        "full_certificate_reduced_value": str(nonpin_full),
        "affine_certificate_reduced_value": str(nonpin_affine),
        "pinned_word_count": len(words),
        "status": "VERIFIED_OBJECTIVE_NORMALIZATION",
    }
    (HERE / "REED_MULLER_OBJECTIVE_NORMALIZATION_AUDIT.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    (HERE / "REED_MULLER_OBJECTIVE_NORMALIZATION_AUDIT.md").write_text(
        "# RM(2,5) objective normalization audit\n\n"
        "The quotient producer and independent replay build the objective over "
        "the 31 non-pinned singleton coordinates. Their saved value `31/5` is "
        "therefore a non-pin weight, not the total Hamming weight. Independent "
        "enumeration of the pinned RM(2,5) code gives total minimum weight `8` "
        "and non-pin minimum weight `7`. Adding the fixed pin contribution gives "
        "the equivalent total objective `36/5`, with ratio `10/9`; using the "
        "reduced objective gives ratio `35/31`. The old `40/31` comparison mixed "
        "these two conventions and is retired.\n\n"
        "This is a normalization correction to the finite certificate record. "
        "It does not change the saved rational masses or quotient equations, and "
        "it does not imply anything about arbitrary SAT algorithms or P versus NP.\n",
        encoding="utf-8",
    )
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
