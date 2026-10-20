"""Explicit Reed--Muller controls for the local-marginal code barrier.

The saved family is RM(s, 2s+1).  Its evaluation coordinates are the points
of F_2^(2s+1), its generator rows are all square-free monomials of degree at
most s, and the family is self-dual.  The codeword enumeration is used only
for the small controls; the larger saved case is checked from the elementary
Reed--Muller distance and duality identities recorded in REED_MULLER.md.
"""

from __future__ import annotations

from fractions import Fraction
from itertools import combinations

from local_marginal import (
    atom_slot_count,
    basis,
    local_point_is_supported,
    orthogonal_basis,
    scope_count,
    span,
    validate_rows,
)


def parameters(s: int) -> dict[str, int]:
    """Return the symmetric family parameters RM(s, 2s+1)."""
    if type(s) is not int or s < 1:
        raise ValueError("s must be a positive integer")
    m = 2 * s + 1
    n = 1 << m
    dimension = sum(_binomial(m, degree) for degree in range(s + 1))
    distance = 1 << (m - s)
    return {
        "s": s,
        "m": m,
        "r": s,
        "n": n,
        "dimension": dimension,
        "distance": distance,
        "dual_order": m - s - 1,
        "dual_distance": 1 << (s + 1),
    }


def _binomial(n: int, k: int) -> int:
    value = 1
    for index in range(1, k + 1):
        value = value * (n - index + 1) // index
    return value


def gaussian_binomial_2(n: int, k: int) -> int:
    """Return the Gaussian binomial ``[n choose k]_2`` exactly."""
    if type(n) is not int or type(k) is not int or n < 0 or not 0 <= k <= n:
        raise ValueError("invalid Gaussian-binomial parameters")
    row = [0] * (k + 1)
    row[0] = 1
    for size in range(1, n + 1):
        next_row = row[:]
        for width in range(1, min(size, k) + 1):
            previous = row[width] if width < size else 0
            next_row[width] = row[width - 1] + (1 << width) * previous
        row = next_row
    return row[k]


def boundary_objective_lower_bound(s: int) -> Fraction:
    """Count minimum affine dual checks to lower-bound ``L_{d-1}``.

    For RM(s, 2s+1), every affine (s+1)-flat through the pin is a dual
    minimum-weight check. On its d-1 non-pin coordinates the pinned
    projection has odd parity, so its expected local weight is at least one.
    Double-counting flat incidences gives the stated rational lower bound.
    """
    info = parameters(s)
    m = info["m"]
    codimension = info["r"]
    total_checks = gaussian_binomial_2(m, codimension + 1)
    checks_through_other_point = gaussian_binomial_2(m - 1, codimension)
    return Fraction(1) + Fraction(total_checks, checks_through_other_point)


def boundary_local_optimum(s: int) -> Fraction:
    """Return the exact theorem value for the plain level ``d-1`` model.

    The matching upper witness uses one-hot mass ``1/(d-1)`` on every
    non-pin singleton and the zero atom on each scope, with zero mass at the
    boundary scopes whose pinned projection has odd parity.
    """
    return boundary_objective_lower_bound(s)


def monomial_masks(m: int, degree: int) -> tuple[int, ...]:
    """Return ANF monomial supports, ordered by degree then lexicographically."""
    if type(m) is not int or m < 0 or type(degree) is not int or not 0 <= degree <= m:
        raise ValueError("invalid Reed--Muller dimensions")
    masks = []
    for size in range(degree + 1):
        masks.extend(sum(1 << index for index in support)
                     for support in combinations(range(m), size))
    return tuple(masks)


def monomial_row(m: int, mask: int) -> int:
    """Evaluate x_mask on every point x in F_2^m as an integer bitset."""
    n = 1 << m
    return sum(1 << point for point in range(n) if point & mask == mask)


def generator_rows(s: int) -> tuple[int, ...]:
    info = parameters(s)
    return tuple(monomial_row(info["m"], mask)
                 for mask in monomial_masks(info["m"], info["r"]))


def affine_minimum_witness_masks(m: int, degree: int, pin: int) -> tuple[int, ...]:
    """Return ANF masks for an affine codimension-degree indicator through pin."""
    if type(pin) is not int or not 0 <= pin < (1 << m):
        raise ValueError("pin out of range")
    selected = (1 << degree) - 1
    # Product_{i<degree} (1 + pin_i + x_i).  A monomial survives exactly
    # when it contains every selected coordinate on which pin has value one.
    required = pin & selected
    return tuple(mask for mask in range(1 << degree) if mask & required == required)


def affine_minimum_support(m: int, codimension: int, pin: int) -> int:
    """Return an affine minimum-weight support through ``pin``.

    The first ``codimension`` coordinate bits are fixed to the corresponding
    bits of ``pin``. For the symmetric RM family this is the support of a
    minimum-weight dual word, so removing ``pin`` gives the first boundary
    scope on which the unit local witness is forbidden.
    """
    if (type(m) is not int or m < 0 or type(codimension) is not int
            or not 0 <= codimension <= m):
        raise ValueError("invalid affine dimensions")
    if type(pin) is not int or not 0 <= pin < (1 << m):
        raise ValueError("pin out of range")
    fixed = (1 << codimension) - 1
    return sum(1 << point for point in range(1 << m)
               if (point & fixed) == (pin & fixed))


def xor_rows(rows: tuple[int, ...], masks: tuple[int, ...]) -> int:
    result = 0
    for mask in masks:
        result ^= rows[mask]
    return result


def _exact_word_summary(rows: tuple[int, ...], n: int, pin: int, word_limit: int) -> dict:
    words = span(rows, word_limit)
    if words is None:
        return {
            "status": "THEOREM_ONLY",
            "word_count": None,
            "minimum_distance": None,
            "pinned_minimum": None,
        }
    nonzero = tuple(word for word in words if word)
    pinned = tuple(word for word in words if word >> pin & 1)
    return {
        "status": "EXACT",
        "word_count": len(words),
        "minimum_distance": min(word.bit_count() for word in nonzero),
        "pinned_minimum": min(word.bit_count() for word in pinned),
    }


def make_certificate(s: int, *, pin: int = 0, enumerate_scopes: bool = False,
                     word_limit: int = 1 << 20) -> dict:
    info = parameters(s)
    n = info["n"]
    if type(pin) is not int or not 0 <= pin < n:
        raise ValueError("pin out of range")
    rows = generator_rows(s)
    masks = monomial_masks(info["m"], info["r"])
    dual_basis = orthogonal_basis(rows, n)
    level = info["distance"] - 2
    witness_masks = affine_minimum_witness_masks(info["m"], info["r"], pin)
    witness = 0
    row_by_mask = dict(zip(masks, rows))
    for mask in witness_masks:
        witness ^= row_by_mask[mask]
    summary = _exact_word_summary(rows, n, pin, word_limit)
    support = None
    checked_scopes = None
    counterexample = None
    if enumerate_scopes:
        words = span(rows, word_limit)
        if words is None:
            raise ValueError("scope enumeration requires an exact word span")
        support, checked_scopes, counterexample = local_point_is_supported(
            words, n, pin, level)
    certificate = {
        "schema": "reed_muller_local_pinned_v1",
        "family": "RM(s,2s+1)",
        **info,
        "pin": pin,
        "generator_masks": list(masks),
        "generator_rows": list(rows),
        "dual_basis": list(dual_basis),
        "self_dual": len(basis(rows)) * 2 == n,
        "level": level,
        "theorem_level_bound": info["dual_distance"] - 2,
        "pinned_integer_optimum": info["distance"],
        "relaxation_point_weight": 1,
        "integrality_gap": info["distance"],
        "witness_monomial_masks": list(witness_masks),
        "minimum_weight_witness": witness,
        "witness_weight": witness.bit_count(),
        "word_enumeration": summary,
        "scope_count": scope_count(n, level),
        "atom_slot_count": atom_slot_count(n, level),
        "enumerated_support": support,
        "checked_scopes": checked_scopes,
        "support_counterexample": None if counterexample is None else list(counterexample),
    }
    return {"status": "FOUND", "certificate": certificate}


def verify_certificate(certificate: dict, *, word_limit: int = 1 << 20) -> dict:
    """Verify a saved certificate without trusting its derived fields."""
    try:
        if not isinstance(certificate, dict) or certificate.get("schema") != "reed_muller_local_pinned_v1":
            raise ValueError("invalid schema")
        info = parameters(certificate["s"])
        for key, value in info.items():
            if certificate.get(key) != value:
                raise ValueError(f"parameter mismatch: {key}")
        n = info["n"]
        pin = certificate["pin"]
        level = certificate["level"]
        if type(pin) is not int or not 0 <= pin < n:
            raise ValueError("invalid pin")
        if type(level) is not int or not 0 <= level <= n:
            raise ValueError("invalid level")
        masks = monomial_masks(info["m"], info["r"])
        if tuple(certificate["generator_masks"]) != masks:
            raise ValueError("generator mask mismatch")
        expected_rows = generator_rows(info["s"])
        rows = validate_rows(certificate["generator_rows"], n)
        if rows != expected_rows:
            raise ValueError("generator row mismatch")
        if len(basis(rows)) != info["dimension"]:
            raise ValueError("generator rank mismatch")
        dual_basis = orthogonal_basis(rows, n)
        if tuple(certificate["dual_basis"]) != dual_basis:
            raise ValueError("dual basis mismatch")
        if not all((left & right).bit_count() % 2 == 0
                   for left in rows for right in rows):
            raise ValueError("self-orthogonality mismatch")
        if certificate["self_dual"] is not True or len(dual_basis) != n // 2:
            raise ValueError("self-duality mismatch")
        expected_level = info["distance"] - 2
        if level != expected_level or certificate["theorem_level_bound"] != expected_level:
            raise ValueError("level bound mismatch")
        if certificate["pinned_integer_optimum"] != info["distance"]:
            raise ValueError("pinned optimum theorem mismatch")
        if certificate["relaxation_point_weight"] != 1:
            raise ValueError("unit point weight mismatch")
        if certificate["integrality_gap"] != info["distance"]:
            raise ValueError("gap mismatch")
        row_by_mask = dict(zip(masks, rows))
        witness_masks = affine_minimum_witness_masks(info["m"], info["r"], pin)
        if tuple(certificate["witness_monomial_masks"]) != witness_masks:
            raise ValueError("witness mask mismatch")
        witness = xor_rows(row_by_mask, witness_masks)
        if certificate["minimum_weight_witness"] != witness:
            raise ValueError("witness mismatch")
        if witness.bit_count() != info["distance"] or not (witness >> pin & 1):
            raise ValueError("witness weight or pin mismatch")
        if certificate["witness_weight"] != witness.bit_count():
            raise ValueError("witness weight field mismatch")
        if certificate["scope_count"] != scope_count(n, level):
            raise ValueError("scope count mismatch")
        if certificate["atom_slot_count"] != atom_slot_count(n, level):
            raise ValueError("atom count mismatch")

        summary = certificate["word_enumeration"]
        words = span(rows, word_limit)
        if summary["status"] == "EXACT":
            if words is None:
                raise ValueError("exact enumeration unexpectedly capped")
            nonzero = tuple(word for word in words if word)
            pinned = tuple(word for word in words if word >> pin & 1)
            expected_summary = {
                "status": "EXACT",
                "word_count": len(words),
                "minimum_distance": min(word.bit_count() for word in nonzero),
                "pinned_minimum": min(word.bit_count() for word in pinned),
            }
            if summary != expected_summary:
                raise ValueError("word summary mismatch")
        elif summary != {"status": "THEOREM_ONLY", "word_count": None,
                         "minimum_distance": None, "pinned_minimum": None}:
            raise ValueError("invalid word summary")

        support = certificate["enumerated_support"]
        checked = certificate["checked_scopes"]
        counterexample = None
        if support is not None:
            if words is None:
                raise ValueError("support replay unexpectedly capped")
            observed, observed_checked, counterexample = local_point_is_supported(
                words, n, pin, level)
            if support != observed or checked != observed_checked:
                raise ValueError("support replay mismatch")
        elif checked is not None or certificate["support_counterexample"] is not None:
            raise ValueError("deferred support fields must be empty")
        return {
            "status": "VERIFIED",
            "valid": True,
            "family": certificate["family"],
            "s": info["s"],
            "n": n,
            "dimension": info["dimension"],
            "distance": info["distance"],
            "dual_distance": info["dual_distance"],
            "level": level,
            "theorem_level_valid": level <= info["dual_distance"] - 2,
            "pinned_integer_optimum": info["distance"],
            "integrality_gap": info["distance"],
            "support_replay": support,
            "checked_scopes": checked,
            "counterexample": None if counterexample is None else list(counterexample),
        }
    except (KeyError, TypeError, ValueError):
        return {"status": "INVALID", "valid": False}
