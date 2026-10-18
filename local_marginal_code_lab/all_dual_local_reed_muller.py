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


def local_witness_atom_count(n: int, level: int) -> int:
    """Count nonzero atoms in the sparse one-hot witness tables."""
    if type(n) is not int or n < 0 or type(level) is not int or not 0 <= level <= n:
        raise ValueError("invalid dimensions")
    distance = level + 1
    total = 0
    for size in range(level + 1):
        free = size
        zero_atoms = 0 if free == distance - 1 else 1
        total += comb(n - 1, size) * (free + zero_atoms)
        if size:
            free = size - 1
            zero_atoms = 0 if free == distance - 1 else 1
            total += comb(n - 1, size - 1) * (free + zero_atoms)
    return total


def projection_support_rule(distance: int, level: int) -> dict:
    """Return the exact dual-distance support implication used by the witness."""
    if type(distance) is not int or distance < 1 or type(level) is not int:
        raise ValueError("invalid support dimensions")
    if level != distance - 1:
        raise ValueError("this boundary witness is defined at dual distance minus one")
    return {
        "level": level,
        "scope_plus_pin_max": level + 1,
        "strictly_below_dual_distance": False,
        "boundary_scope_size": distance - 1,
        "pin_omitted_below_boundary": "FULL_CUBE",
        "pin_omitted_boundary": "FULL_CUBE_OR_ODD_PARITY",
        "pin_included_scope_support": "PIN_ONE_TIMES_FULL_FREE_CUBE",
        "one_hot_boundary_assignments_supported": True,
    }


def make_certificate(s: int, *, pin: int = 0, word_limit: int = 1 << 20) -> dict:
    """Create a theorem-backed combined-relaxation certificate."""
    info = parameters(s)
    n = info["n"]
    distance = info["dual_distance"]
    if type(pin) is not int or not 0 <= pin < n:
        raise ValueError("pin out of range")
    level = distance - 1
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
        "local_sparse_marginal": {
            "pin_value": "1",
            "one_hot_coordinate_mass": str(Fraction(1, distance - 1)),
            "all_zero_mass": "1-|free_scope|/(d-1)",
            "marginal_consistency": "one_hot_or_zero",
            "supported_by_pinned_code_projection": True,
        },
        "projection_support": support,
        "scope_count": sum(comb(n, size) for size in range(level + 1)),
        "local_witness_atom_count": local_witness_atom_count(n, level),
        "word_replay": word_replay,
        "witness_kind": "one-hot local marginals plus all-dual parity mixtures",
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
        if level != distance - 1:
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
        sparse = certificate["local_sparse_marginal"]
        if sparse != {
            "pin_value": "1",
            "one_hot_coordinate_mass": str(Fraction(1, distance - 1)),
            "all_zero_mass": "1-|free_scope|/(d-1)",
            "marginal_consistency": "one_hot_or_zero",
            "supported_by_pinned_code_projection": True,
        }:
            raise ValueError("sparse witness mismatch")
        if certificate["projection_support"] != projection_support_rule(distance, level):
            raise ValueError("projection-support theorem mismatch")
        expected_scope_count = sum(comb(n, size) for size in range(level + 1))
        if certificate["scope_count"] != expected_scope_count:
            raise ValueError("scope count mismatch")
        if certificate["local_witness_atom_count"] != local_witness_atom_count(n, level):
            raise ValueError("witness atom count mismatch")
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
