"""All-redundant-parity LP certificates for RM(s, 2s+1).

The local-marginal witness has a square-root gap on the explicit
Reed--Muller family.  This module tests a stronger relaxation: intersect the
parity polytopes of every nonzero dual codeword and pin one coordinate to one.
The uniform point p=1/(delta-1) is checked by exact rational mixtures, and a
balanced family of minimum-weight affine checks supplies a matching LP lower
bound.
"""

from __future__ import annotations

from fractions import Fraction

from local_marginal import span
from reed_muller import generator_rows, parameters


def gaussian_binomial(n: int, k: int) -> int:
    """The binary Gaussian binomial [n choose k]_2, using exact integers."""
    if type(n) is not int or type(k) is not int or not 0 <= k <= n:
        raise ValueError("invalid Gaussian-binomial arguments")
    numerator = 1
    denominator = 1
    for index in range(k):
        numerator *= (1 << (n - index)) - 1
        denominator *= (1 << (k - index)) - 1
    return numerator // denominator


def symmetric_parity_mixture(length: int, mean_weight: Fraction, parity: int):
    """Return uniform-subset cardinalities realizing the requested marginal."""
    if type(length) is not int or length < 0 or parity not in (0, 1):
        raise ValueError("invalid mixture dimensions")
    mean_weight = Fraction(mean_weight)
    allowed = list(range(parity, length + 1, 2))
    if not allowed or not (allowed[0] <= mean_weight <= allowed[-1]):
        return None
    below = max(weight for weight in allowed if weight <= mean_weight)
    above = min(weight for weight in allowed if weight >= mean_weight)
    if below == above:
        return ((Fraction(1), below),)
    upper = (mean_weight - below) / (above - below)
    return ((1 - upper, below), (upper, above))


def mixture_cases(n: int, distance: int):
    """Check the analytic parity mixture for every possible check weight."""
    point_value = Fraction(1, distance - 1)
    cases = []
    for weight in range(distance, n + 1):
        for has_pin in (0, 1):
            free = weight - has_pin
            mixture = symmetric_parity_mixture(free, point_value * free, has_pin)
            if mixture is None:
                return None
            if sum(probability for probability, _ in mixture) != 1:
                return None
            if any(probability < 0 or cardinality < 0 or cardinality > free
                   or cardinality % 2 != has_pin
                   for probability, cardinality in mixture):
                return None
            if sum(probability * cardinality for probability, cardinality in mixture) != point_value * free:
                return None
            cases.append({"weight": weight, "contains_pin": bool(has_pin),
                          "free_length": free,
                          "mixture": [[str(probability), cardinality]
                                      for probability, cardinality in mixture]})
    return cases


def _exact_word_summary(rows, pin, word_limit):
    words = span(rows, word_limit)
    if words is None:
        return {"status": "THEOREM_ONLY", "word_count": None,
                "minimum_distance": None, "pinned_minimum": None,
                "minimum_checks_through_pin": None,
                "other_coordinate_incidence": None}
    nonzero = tuple(word for word in words if word)
    minimum = min(word.bit_count() for word in nonzero)
    pinned = tuple(word for word in words if word >> pin & 1)
    minimum_through_pin = tuple(word for word in pinned if word.bit_count() == minimum)
    incidences = [sum(bool(word >> coordinate & 1) for word in minimum_through_pin)
                  for coordinate in range(rows[0].bit_length()) if coordinate != pin]
    return {
        "status": "EXACT",
        "word_count": len(words),
        "minimum_distance": minimum,
        "pinned_minimum": min(word.bit_count() for word in pinned),
        "minimum_checks_through_pin": len(minimum_through_pin),
        "other_coordinate_incidence": sorted(set(incidences)),
    }


def make_certificate(s: int, *, pin: int = 0, word_limit: int = 1 << 20) -> dict:
    info = parameters(s)
    n = info["n"]
    if type(pin) is not int or not 0 <= pin < n:
        raise ValueError("pin out of range")
    distance = info["dual_distance"]
    point = (Fraction(1),) + (Fraction(1, distance - 1),) * (n - 1)
    through_pin = gaussian_binomial(info["m"], info["r"])
    incidence = gaussian_binomial(info["m"] - 1, info["r"])
    summary = _exact_word_summary(generator_rows(s), pin, word_limit)
    cases = mixture_cases(n, distance)
    if cases is None:
        raise AssertionError("uniform all-dual mixture formula failed")
    certificate = {
        "schema": "reed_muller_all_dual_lp_v1",
        "family": "RM(s,2s+1)",
        **info,
        "pin": pin,
        "point": [str(value) for value in point],
        "integer_pinned_optimum": info["distance"],
        "fractional_feasible_weight": str(sum(point)),
        "fractional_optimum": str(Fraction(1) + Fraction(n - 1, distance - 1)),
        "minimum_check_count_through_pin": through_pin,
        "minimum_check_other_coordinate_incidence": incidence,
        "minimum_check_ratio": str(Fraction(through_pin, incidence)),
        "word_enumeration": summary,
        "all_dual_mixture_cases": cases,
        "all_nonzero_dual_checks_feasible": True,
    }
    return {"status": "FOUND", "certificate": certificate}


def verify_certificate(certificate: dict, *, word_limit: int = 1 << 20) -> dict:
    try:
        if not isinstance(certificate, dict) or certificate.get("schema") != "reed_muller_all_dual_lp_v1":
            raise ValueError("invalid schema")
        info = parameters(certificate["s"])
        for key, value in info.items():
            if certificate.get(key) != value:
                raise ValueError(f"parameter mismatch: {key}")
        n = info["n"]
        pin = certificate["pin"]
        if type(pin) is not int or not 0 <= pin < n:
            raise ValueError("invalid pin")
        distance = info["dual_distance"]
        point = tuple(Fraction(value) for value in certificate["point"])
        expected_point = (Fraction(1),) + (Fraction(1, distance - 1),) * (n - 1)
        if point != expected_point:
            raise ValueError("uniform point mismatch")
        if certificate["integer_pinned_optimum"] != distance:
            raise ValueError("integer optimum mismatch")
        expected_weight = Fraction(1) + Fraction(n - 1, distance - 1)
        if Fraction(certificate["fractional_feasible_weight"]) != expected_weight:
            raise ValueError("fractional weight mismatch")
        if Fraction(certificate["fractional_optimum"]) != expected_weight:
            raise ValueError("fractional optimum mismatch")
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
            raise ValueError("all-dual mixture replay mismatch")
        if certificate["all_nonzero_dual_checks_feasible"] is not True:
            raise ValueError("all-dual feasibility flag mismatch")

        summary = certificate["word_enumeration"]
        expected_summary = _exact_word_summary(generator_rows(info["s"]), pin, word_limit)
        if summary != expected_summary:
            raise ValueError("word enumeration summary mismatch")
        if summary["status"] == "EXACT":
            if summary["minimum_distance"] != distance or summary["pinned_minimum"] != distance:
                raise ValueError("exact distance mismatch")
            if summary["minimum_checks_through_pin"] != through_pin:
                raise ValueError("exact minimum-check count mismatch")
            if summary["other_coordinate_incidence"] != [incidence]:
                raise ValueError("exact incidence mismatch")
        return {
            "status": "VERIFIED",
            "valid": True,
            "s": info["s"],
            "n": n,
            "dual_distance": distance,
            "integer_pinned_optimum": distance,
            "fractional_optimum": str(expected_weight),
            "integrality_ratio": str(Fraction(distance, 1) / expected_weight),
            "minimum_check_count_through_pin": through_pin,
            "minimum_check_other_coordinate_incidence": incidence,
            "mixture_case_count": len(cases),
            "word_enumeration": summary["status"],
        }
    except (KeyError, TypeError, ValueError, ZeroDivisionError):
        return {"status": "INVALID", "valid": False}
