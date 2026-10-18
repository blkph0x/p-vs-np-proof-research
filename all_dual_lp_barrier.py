"""Exact all-redundant-parity LP counterexample, using rational arithmetic.

No floating-point solver is required. The conclusion concerns intersections
of single-parity-check polytopes, even after every dual codeword is included.
It is not a lower bound for general linear programming or SAT algorithms.
"""

from collections import Counter
from fractions import Fraction


def binary_span(rows):
    span = {0}
    for row in rows:
        span |= {word ^ row for word in tuple(span)}
    return tuple(sorted(span))


def symmetric_parity_mixture(length, mean_weight, parity):
    """Express a symmetric vector via uniform subsets of allowed parity.

    An entry (probability,k) means: choose uniformly a k-element subset of
    `length` coordinates. Its coordinate marginal is k/length. A mixture
    whose expected k is mean_weight has every marginal mean_weight/length.
    Returning None means this symmetric construction is impossible.
    """
    mean_weight = Fraction(mean_weight)
    allowed = list(range(parity, length + 1, 2))
    if not allowed or not (allowed[0] <= mean_weight <= allowed[-1]):
        return None
    below = max(k for k in allowed if k <= mean_weight)
    above = min(k for k in allowed if k >= mean_weight)
    if below == above:
        return ((Fraction(1), below),)
    upper_probability = (mean_weight - below) / (above - below)
    return ((1 - upper_probability, below), (upper_probability, above))


def golay_all_dual_certificate():
    """Construct a [24,12,8] certificate; its code facts are verified below.

    The generator g=1+x+x^5+x^6+x^7+x^9+x^11 gives twelve shifted length-23
    rows; append their parity bit. The resulting row space is self-dual.
    The verifier checks that fact and enumerates its full 4,096-word span.

    Pin x_0=1 and set x_i=1/7 for i>0. Its weight is 30/7, hence <=5, while
    every nonzero codeword has weight >=8. Every dual check has weight >=8.
    Its local marginal vector has an explicit even-parity convex mixture:
    if the check includes the pin, the remaining coordinates need odd parity;
    otherwise they need even parity. symmetric_parity_mixture supplies the
    rational mixture of uniform subsets in both cases.
    """
    generator_polynomial = sum(1 << i for i in (0, 1, 5, 6, 7, 9, 11))
    rows = tuple((generator_polynomial << i) | (1 << 23) for i in range(12))
    return {
        "n": 24,
        "parity_check_rows": rows,
        "point": (Fraction(1),) + (Fraction(1, 7),) * 23,
        "pinned_one_coordinate": 0,
        "decision_upper_bound": 5,
        "claimed_distance": 8,
    }


def verify_golay_certificate(certificate):
    """Independently verify the exact code and every dual-check mixture.

    The certificate format intentionally restricts the point to one pinned
    coordinate and one common value on the others. This verifier therefore
    checks an explicit witness family, not arbitrary fractional vectors.
    """
    try:
        n = certificate["n"]
        rows = tuple(certificate["parity_check_rows"])
        point = tuple(Fraction(value) for value in certificate["point"])
        pin = certificate["pinned_one_coordinate"]
        bound = certificate["decision_upper_bound"]
        if n != 24 or len(point) != n or not 0 <= pin < n:
            return {"verified": False, "reason": "malformed dimensions"}
        if any(not isinstance(row, int) or row < 0 or row >> n for row in rows):
            return {"verified": False, "reason": "malformed row"}
        if point[pin] != 1 or any(not 0 <= value <= 1 for value in point):
            return {"verified": False, "reason": "invalid fractional point or pin"}
        free_values = {value for i, value in enumerate(point) if i != pin}
        if len(free_values) != 1:
            return {"verified": False, "reason": "point is outside the symmetric certificate format"}
        common = next(iter(free_values))
        dual = binary_span(rows)
        # An orthogonal space of dimension n/2 is its own orthogonal complement.
        if len(dual) != 1 << (n // 2):
            return {"verified": False, "reason": "row-space dimension is not n/2"}
        if any((a & b).bit_count() % 2 for a in rows for b in rows):
            return {"verified": False, "reason": "row space is not self-orthogonal"}
        distance = min(word.bit_count() for word in dual if word)
        pinned_distance = min(word.bit_count() for word in dual if word >> pin & 1)
        if certificate["claimed_distance"] != distance:
            return {"verified": False, "reason": "wrong distance claim"}
        if not sum(point) <= bound < pinned_distance:
            return {"verified": False, "reason": "no integer-threshold separation"}
        templates = {}
        for check in dual:
            if not check:
                continue
            has_pin = (check >> pin) & 1
            free_length = check.bit_count() - has_pin
            required_parity = has_pin
            mixture = symmetric_parity_mixture(free_length, common * free_length,
                                                required_parity)
            if mixture is None:
                return {"verified": False, "reason": "a redundant check excludes the point",
                        "violated_check": check}
            if sum(probability for probability, _ in mixture) != 1:
                return {"verified": False, "reason": "bad mixture normalization"}
            if any(probability < 0 or k < 0 or k > free_length or k % 2 != required_parity
                   for probability, k in mixture):
                return {"verified": False, "reason": "bad local mixture support"}
            expected_weight = sum(probability * k for probability, k in mixture)
            if expected_weight != common * free_length:
                return {"verified": False, "reason": "bad local marginal"}
            templates[(check.bit_count(), has_pin)] = mixture
        # Sum x_pin <= sum(other check bits) over minimum-weight checks that
        # contain the pin. Equal incidence counts yield an exact LP bound.
        bound_checks = [check for check in dual
                        if check.bit_count() == distance and check >> pin & 1]
        incidences = [sum(bool(check >> i & 1) for check in bound_checks)
                      for i in range(n) if i != pin]
        if not incidences or len(set(incidences)) != 1 or not incidences[0]:
            return {"verified": False, "reason": "missing uniform-incidence LP bound"}
        multiplicity = incidences[0]
        lp_lower_bound = 1 + Fraction(len(bound_checks), multiplicity)
        if lp_lower_bound != sum(point):
            return {"verified": False, "reason": "LP upper and lower certificates disagree"}
        return {
            "verified": True,
            "dual_checks_verified": len(dual) - 1,
            "codewords_verified": len(dual),
            "weight_distribution": dict(sorted(Counter(word.bit_count() for word in dual).items())),
            "distance": distance,
            "pinned_integer_optimum": pinned_distance,
            "fractional_feasible_weight": sum(point),
            "fractional_optimum": lp_lower_bound,
            "dual_bound_check_count": len(bound_checks),
            "dual_bound_coordinate_multiplicity": multiplicity,
            "decision_upper_bound": bound,
            "local_mixture_templates": templates,
        }
    except (KeyError, TypeError, ValueError, ZeroDivisionError):
        return {"verified": False, "reason": "malformed certificate"}


if __name__ == "__main__":
    result = verify_golay_certificate(golay_all_dual_certificate())
    for key, value in result.items():
        print(f"{key}: {value}")
