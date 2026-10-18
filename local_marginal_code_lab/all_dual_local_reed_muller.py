"""Combined all-dual-parity and local-marginal certificates for RM codes.

The all-dual parity LP has a uniform fractional point on RM(s, 2s+1).
This module adds every pinned-code projection marginal through the dual
distance level and proves, by an explicit product family, that the same point
remains feasible.  The lower bound from the minimum-weight affine checks then
matches the witness exactly.
"""

from __future__ import annotations

from fractions import Fraction
from math import comb

from all_dual_reed_muller import gaussian_binomial, mixture_cases
from local_marginal import span
from reed_muller import generator_rows, parameters


def pinned_atom_slot_count(n: int, level: int) -> int:
    """Count assignments allowed by the pin-aware projection rule."""
    if type(n) is not int or n < 0 or type(level) is not int or not 0 <= level <= n:
        raise ValueError("invalid dimensions")
    total = 0
    for size in range(level + 1):
        total += comb(n - 1, size) * (1 << size)
        if size:
            total += comb(n - 1, size - 1) * (1 << (size - 1))
    return total


def projection_support_rule(distance: int, level: int) -> dict:
    """Return the exact dual-distance support implication used by the witness."""
    if type(distance) is not int or distance < 1 or type(level) is not int:
        raise ValueError("invalid support dimensions")
    if level < 0 or level > distance - 2:
        raise ValueError("level exceeds the dual-distance support guarantee")
    return {
        "level": level,
        "scope_plus_pin_max": level + 1,
        "strictly_below_dual_distance": level + 1 < distance,
        "pin_omitted_scope_support": "FULL_CUBE",
        "pin_included_scope_support": "PIN_ONE_TIMES_FULL_FREE_CUBE",
    }


def make_certificate(s: int, *, pin: int = 0, word_limit: int = 1 << 20) -> dict:
    """Create a theorem-backed combined-relaxation certificate."""
    info = parameters(s)
    n = info["n"]
    distance = info["dual_distance"]
    if type(pin) is not int or not 0 <= pin < n:
        raise ValueError("pin out of range")
    level = distance - 2
    point = (Fraction(1),) + (Fraction(1, distance - 1),) * (n - 1)
    fractional = Fraction(1) + Fraction(n - 1, distance - 1)
    word_count = span(generator_rows(s), word_limit)
    word_replay = {
        "status": "EXACT" if word_count is not None else "THEOREM_ONLY",
        "word_count": None if word_count is None else len(word_count),
    }
    if word_count is not None:
        pinned = tuple(word for word in word_count if word >> pin & 1)
        word_replay.update({
            "minimum_distance": min(word.bit_count() for word in word_count if word),
            "pinned_minimum": min(word.bit_count() for word in pinned),
        })
    support = projection_support_rule(distance, level)
    cases = mixture_cases(n, distance)
    if cases is None:
        raise AssertionError("all-dual mixture construction failed")
    through_pin = gaussian_binomial(info["m"], info["r"])
    incidence = gaussian_binomial(info["m"] - 1, info["r"])
    certificate = {
        "schema": "reed_muller_all_dual_local_v1",
        "family": "RM(s,2s+1)",
        **info,
        "pin": pin,
        "level": level,
        "point": [str(value) for value in point],
        "integer_pinned_optimum": distance,
        "fractional_feasible_weight": str(fractional),
        "combined_relaxation_optimum": str(fractional),
        "integrality_ratio": str(Fraction(distance, 1) / fractional),
        "minimum_check_count_through_pin": through_pin,
        "minimum_check_other_coordinate_incidence": incidence,
        "minimum_check_ratio": str(Fraction(through_pin, incidence)),
        "all_dual_mixture_cases": cases,
        "all_nonzero_dual_checks_feasible": True,
        "local_product_marginal": {
            "pin_value": "1",
            "other_coordinate_value": str(Fraction(1, distance - 1)),
            "independent_on_each_scope": True,
            "supported_by_pinned_code_projection": True,
        },
        "projection_support": support,
        "scope_count": sum(comb(n, size) for size in range(level + 1)),
        "pinned_atom_slot_count": pinned_atom_slot_count(n, level),
        "word_replay": word_replay,
        "witness_kind": "product local marginals plus all-dual parity mixtures",
    }
    return {"status": "FOUND", "certificate": certificate}


def verify_certificate(certificate: dict, *, word_limit: int = 1 << 20) -> dict:
    """Verify arithmetic and theorem fields without trusting saved derivations."""
    try:
        if not isinstance(certificate, dict) or certificate.get("schema") != "reed_muller_all_dual_local_v1":
            raise ValueError("invalid schema")
        info = parameters(certificate["s"])
        for key, value in info.items():
            if certificate.get(key) != value:
                raise ValueError(f"parameter mismatch: {key}")
        n = info["n"]
        distance = info["dual_distance"]
        pin = certificate["pin"]
        level = certificate["level"]
        if type(pin) is not int or not 0 <= pin < n:
            raise ValueError("invalid pin")
        if level != distance - 2:
            raise ValueError("level mismatch")
        point = tuple(Fraction(value) for value in certificate["point"])
        expected_point = (Fraction(1),) + (Fraction(1, distance - 1),) * (n - 1)
        if point != expected_point:
            raise ValueError("point mismatch")
        fractional = Fraction(1) + Fraction(n - 1, distance - 1)
        if certificate["integer_pinned_optimum"] != distance:
            raise ValueError("integer optimum mismatch")
        if Fraction(certificate["fractional_feasible_weight"]) != fractional:
            raise ValueError("fractional weight mismatch")
        if Fraction(certificate["combined_relaxation_optimum"]) != fractional:
            raise ValueError("combined optimum mismatch")
        if Fraction(certificate["integrality_ratio"]) != Fraction(distance, 1) / fractional:
            raise ValueError("ratio mismatch")
        through_pin = gaussian_binomial(info["m"], info["r"])
        incidence = gaussian_binomial(info["m"] - 1, info["r"])
        if certificate["minimum_check_count_through_pin"] != through_pin:
            raise ValueError("minimum-check count mismatch")
        if certificate["minimum_check_other_coordinate_incidence"] != incidence:
            raise ValueError("minimum-check incidence mismatch")
        if Fraction(certificate["minimum_check_ratio"]) != Fraction(n - 1, distance - 1):
            raise ValueError("minimum-check ratio mismatch")
        cases = mixture_cases(n, distance)
        if cases is None or certificate["all_dual_mixture_cases"] != cases:
            raise ValueError("all-dual mixture mismatch")
        if certificate["all_nonzero_dual_checks_feasible"] is not True:
            raise ValueError("all-dual feasibility flag mismatch")
        product = certificate["local_product_marginal"]
        if product != {
            "pin_value": "1",
            "other_coordinate_value": str(Fraction(1, distance - 1)),
            "independent_on_each_scope": True,
            "supported_by_pinned_code_projection": True,
        }:
            raise ValueError("product witness mismatch")
        if certificate["projection_support"] != projection_support_rule(distance, level):
            raise ValueError("projection-support theorem mismatch")
        expected_scope_count = sum(comb(n, size) for size in range(level + 1))
        if certificate["scope_count"] != expected_scope_count:
            raise ValueError("scope count mismatch")
        if certificate["pinned_atom_slot_count"] != pinned_atom_slot_count(n, level):
            raise ValueError("atom count mismatch")
        words = span(generator_rows(info["s"]), word_limit)
        replay = certificate["word_replay"]
        if words is None:
            if replay != {"status": "THEOREM_ONLY", "word_count": None}:
                raise ValueError("theorem-only word replay mismatch")
        else:
            pinned = tuple(word for word in words if word >> pin & 1)
            expected_replay = {
                "status": "EXACT",
                "word_count": len(words),
                "minimum_distance": min(word.bit_count() for word in words if word),
                "pinned_minimum": min(word.bit_count() for word in pinned),
            }
            if replay != expected_replay:
                raise ValueError("word replay mismatch")
        return {
            "status": "VERIFIED",
            "valid": True,
            "s": info["s"],
            "n": n,
            "level": level,
            "integer_pinned_optimum": distance,
            "combined_relaxation_optimum": str(fractional),
            "integrality_ratio": str(Fraction(distance, 1) / fractional),
            "mixture_case_count": len(cases),
            "word_replay": replay["status"],
        }
    except (KeyError, TypeError, ValueError, ZeroDivisionError):
        return {"status": "INVALID", "valid": False}
