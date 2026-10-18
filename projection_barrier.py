"""Exact certificates for the bounded-coordinate projection-hull limitation.

The scope is intersections of coordinate projection convex hulls, not moment
hierarchies or consistency constraints among lifted joint distributions.
"""
from math import comb
from pathlib import Path
import json


def _rows(values, n):
    if type(n) is not int or n < 0:
        raise ValueError("n must be a nonnegative integer")
    result = tuple(values)
    if any(type(value) is not int or value < 0 or value.bit_length() > n for value in result):
        raise ValueError("rows must contain nonnegative n-bit integers")
    return result


def _basis(rows):
    pivots = {}
    for value in rows:
        while value:
            bit = value.bit_length() - 1
            if bit in pivots:
                value ^= pivots[bit]
            else:
                pivots[bit] = value
                break
    return tuple(pivots[bit] for bit in sorted(pivots, reverse=True))


def _orthogonal_basis(rows, n):
    reduced = list(rows)
    pivots = []
    rank = 0
    for bit in range(n):
        index = next((i for i in range(rank, len(reduced)) if reduced[i] >> bit & 1), None)
        if index is None:
            continue
        reduced[rank], reduced[index] = reduced[index], reduced[rank]
        for i in range(len(reduced)):
            if i != rank and reduced[i] >> bit & 1:
                reduced[i] ^= reduced[rank]
        pivots.append(bit)
        rank += 1
    return tuple((1 << free) | sum(1 << pivot for i, pivot in enumerate(pivots)
                                  if reduced[i] >> free & 1)
                 for free in range(n) if free not in pivots)


def _span(rows, limit):
    if type(limit) is not int or limit < 1:
        raise ValueError("word limit must be a positive integer")
    basis = _basis(rows)
    if 1 << len(basis) > limit:
        return None
    words = [0]
    for row in basis:
        words += [word ^ row for word in tuple(words)]
    return words


def _pin(pin, n):
    if pin is not None and (type(pin) is not int or not 0 <= pin < n):
        raise ValueError("pin must be None or an original coordinate index")


def _guarantees(n, delta, pin):
    # None dual distance denotes the zero dual code, whose primal is the cube.
    unconditioned = n if delta is None else delta - 1
    conditioned = None
    if pin is not None:
        conditioned = n - 1 if delta is None else (delta - 2 if delta >= 2 else None)
    return unconditioned, conditioned


def make_projection_certificate(generator, n, *, pin=None, max_dual_words=1 << 20):
    rows = _rows(generator, n)
    _pin(pin, n)
    dual = _orthogonal_basis(rows, n)
    words = _span(dual, max_dual_words)
    if words is None:
        return {"status": "UNKNOWN", "reason": "DUAL_WORD_LIMIT", "certificate": None}
    delta = min((word.bit_count() for word in words if word), default=None)
    unconditioned, conditioned = _guarantees(n, delta, pin)
    certificate = {"schema": "bounded_projection_dual_distance_v1", "n": n,
                   "dimension": len(_basis(rows)), "dual_basis": list(dual),
                   "dual_distance": delta, "pin": pin,
                   "unconditioned_cube_max_size": unconditioned,
                   "conditioned_other_cube_max_size": conditioned}
    return {"status": "FOUND", "certificate": certificate}


def verify_projection_certificate(generator, n, certificate, *, pin=None,
                                  max_dual_words=1 << 20):
    """Check the entire dual and apply the proved annihilator identity.

    Verification is deliberately exponential in dual dimension, under an
    explicit cap. UNKNOWN is not a certificate rejection or a distance claim.
    """
    try:
        rows = _rows(generator, n)
        _pin(pin, n)
        if not isinstance(certificate, dict) or certificate.get("schema") != "bounded_projection_dual_distance_v1":
            raise ValueError("invalid certificate schema")
        required = ("n", "pin", "dimension", "dual_basis", "dual_distance",
                    "unconditioned_cube_max_size", "conditioned_other_cube_max_size")
        if any(name not in certificate for name in required):
            raise ValueError("missing certificate field")
        if type(certificate.get("n")) is not int or certificate["n"] != n:
            raise ValueError("n mismatch")
        if certificate.get("pin") != pin or (certificate.get("pin") is not None and type(certificate["pin"]) is not int):
            raise ValueError("pin mismatch")
        dimension = len(_basis(rows))
        if type(certificate.get("dimension")) is not int or certificate["dimension"] != dimension:
            raise ValueError("dimension mismatch")
        dual = _rows(certificate["dual_basis"], n)
        if len(dual) != n - dimension or len(_basis(dual)) != len(dual):
            raise ValueError("dual basis has incorrect rank or is dependent")
        if any((row & check).bit_count() % 2 for row in rows for check in dual):
            raise ValueError("dual basis is not orthogonal to the generator")
        words = _span(dual, max_dual_words)
        if words is None:
            return {"valid": False, "status": "UNKNOWN", "errors": [], "reason": "DUAL_WORD_LIMIT"}
        delta = min((word.bit_count() for word in words if word), default=None)
        claimed = certificate["dual_distance"]
        if claimed != delta or (claimed is not None and type(claimed) is not int):
            raise ValueError("dual-distance claim is incorrect")
        limits = _guarantees(n, delta, pin)
        for name, expected in zip(("unconditioned_cube_max_size", "conditioned_other_cube_max_size"), limits):
            value = certificate[name]
            if value != expected or (value is not None and type(value) is not int):
                raise ValueError(f"incorrect projection guarantee: {name}")
        return {"valid": True, "status": "VERIFIED", "errors": [],
                "dimension": dimension, "dual_distance": delta,
                "dual_words_checked": len(words), "nonzero_dual_words_checked": len(words) - 1,
                "unconditioned_cube_max_size": limits[0],
                "conditioned_other_cube_max_size": limits[1],
                "pin_one_feasible": None if pin is None else any(row >> pin & 1 for row in rows),
                "unconditioned_coordinate_sets_covered": sum(comb(n, i) for i in range(limits[0] + 1)),
                "conditioned_coordinate_sets_covered": None if limits[1] is None else
                    sum(comb(n - 1, i) for i in range(limits[1] + 1))}
    except (ValueError, TypeError, KeyError) as exc:
        return {"valid": False, "status": "INVALID", "errors": [str(exc)]}


def projection_dimension(generator, n, coordinates, *, pin=None, pin_value=1):
    """Exact affine projection dimension, using GF(2) elimination only."""
    rows = _rows(generator, n)
    _pin(pin, n)
    coordinates = tuple(coordinates)
    if any(type(i) is not int or not 0 <= i < n for i in coordinates) or len(set(coordinates)) != len(coordinates):
        raise ValueError("coordinates must be distinct original indices")
    if pin in coordinates:
        raise ValueError("conditioned projections use coordinates other than the pin")
    if type(pin_value) is not int or pin_value not in (0, 1):
        raise ValueError("pin_value must be integer zero or one")
    base = _basis(rows)
    offset = 0
    if pin is not None:
        pivot = next((row for row in base if row >> pin & 1), None)
        if pivot is None:
            if pin_value:
                return {"feasible": False, "dimension": None, "is_full_cube": False,
                        "projected_offset": None, "projected_basis": []}
        else:
            offset = pivot if pin_value else 0
            base = tuple(row ^ pivot if row >> pin & 1 else row for row in base if row != pivot)

    def project(word):
        return sum(((word >> coordinate) & 1) << i for i, coordinate in enumerate(coordinates))

    projected = _basis(project(row) for row in base)
    return {"feasible": True, "dimension": len(projected),
            "is_full_cube": len(projected) == len(coordinates),
            "projected_offset": project(offset), "projected_basis": list(projected)}


def golay_projection_audit(pin=0):
    """Combine independently checked projection guarantees with the all-dual LP witness."""
    from fractions import Fraction
    from all_dual_lp_barrier import golay_all_dual_certificate, verify_golay_certificate

    lp_certificate = golay_all_dual_certificate()
    lp_certificate["pinned_one_coordinate"] = pin
    lp_certificate["point"] = tuple(Fraction(1) if i == pin else Fraction(1, 7) for i in range(24))
    generator = tuple(lp_certificate["parity_check_rows"])
    # The imported verifier explicitly proves this code is self-dual, so the
    # same rows really do generate the primal used by the projection checker.
    lp_check = verify_golay_certificate(lp_certificate)
    if not lp_check["verified"]:
        raise ArithmeticError(f"all-dual rational certificate failed: {lp_check}")
    made = make_projection_certificate(generator, 24, pin=pin)
    certificate = made["certificate"]
    checked = verify_projection_certificate(generator, 24, certificate, pin=pin)
    if not checked["valid"]:
        raise ArithmeticError(f"projection certificate failed: {checked}")
    dual_words = _span(certificate["dual_basis"], 4096)
    witness_check = next(word for word in dual_words if word.bit_count() == 8 and word >> pin & 1)
    support = [i for i in range(24) if witness_check >> i & 1]
    others = [i for i in support if i != pin]
    original_boundary = projection_dimension(generator, 24, support)
    conditioned_boundary = projection_dimension(generator, 24, others, pin=pin)
    if original_boundary["is_full_cube"] or conditioned_boundary["is_full_cube"]:
        raise ArithmeticError("minimum-dual-support boundary unexpectedly has full projection")
    exact_lp = lp_check["fractional_optimum"]
    return {"schema": "golay_bounded_projection_audit_v1", "n": 24,
            "generator_rows": list(generator), "pin": pin,
            "projection_certificate": certificate, "projection_verification": checked,
            "point_rationals": [[x.numerator, x.denominator] for x in lp_certificate["point"]],
            "all_dual_checks_verified": lp_check["dual_checks_verified"],
            "integer_pinned_optimum": lp_check["pinned_integer_optimum"],
            "fractional_feasible_weight": [30, 7],
            "combined_exact_lp_optimum": [exact_lp.numerator, exact_lp.denominator],
            "lp_lower_certificate": {"check_count": lp_check["dual_bound_check_count"],
                                     "other_coordinate_multiplicity": lp_check["dual_bound_coordinate_multiplicity"]},
            "combined_all_dual_and_bounded_projection_witness_valid": True,
            "projection_only_unit_vector_is_feasible": True,
            "boundary_control": {"dual_check": witness_check, "support": support,
                                 "unconditioned_projection": original_boundary,
                                 "conditioned_projection": conditioned_boundary},
            "scope": "Coordinate projection hulls only; no claim about Sherali-Adams, "
                     "Lasserre, lifted moment consistency, arbitrary global inequalities, or P versus NP."}


if __name__ == "__main__":
    result = golay_projection_audit()
    destination = Path(__file__).with_name("PROJECTION_RESULTS.json")
    destination.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"saved": str(destination),
                      "projection_verification": result["projection_verification"],
                      "integer_pinned_optimum": result["integer_pinned_optimum"],
                      "fractional_feasible_weight": result["fractional_feasible_weight"]}, indent=2))
