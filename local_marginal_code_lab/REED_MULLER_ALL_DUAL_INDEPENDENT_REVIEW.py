"""Independent replay of the all-dual RM parity-polytope certificates."""

import json
from fractions import Fraction
from itertools import combinations
from math import comb
from pathlib import Path


def parameters(s):
    m = 2 * s + 1
    return {"s": s, "m": m, "r": s, "n": 1 << m,
            "dimension": sum(comb(m, degree) for degree in range(s + 1)),
            "distance": 1 << (s + 1), "dual_order": s,
            "dual_distance": 1 << (s + 1)}


def monomial_masks(m, degree):
    masks = []
    for size in range(degree + 1):
        masks.extend(sum(1 << index for index in support)
                     for support in combinations(range(m), size))
    return tuple(masks)


def row(m, mask):
    return sum(1 << point for point in range(1 << m)
               if point & mask == mask)


def generator_rows(s):
    info = parameters(s)
    return tuple(row(info["m"], mask)
                 for mask in monomial_masks(info["m"], info["r"]))


def rank(rows):
    pivots = {}
    for value in rows:
        while value:
            bit = value.bit_length() - 1
            if bit in pivots:
                value ^= pivots[bit]
            else:
                pivots[bit] = value
                break
    return len(pivots)


def span(rows, limit=1 << 20):
    if len(rows) >= 21:
        return None
    words = [0]
    for value in rows:
        words += [word ^ value for word in tuple(words)]
    return tuple(sorted(words)) if len(words) <= limit else None


def gaussian_binomial(n, k):
    numerator = 1
    denominator = 1
    for index in range(k):
        numerator *= (1 << (n - index)) - 1
        denominator *= (1 << (k - index)) - 1
    return numerator // denominator


def mixture(length, mean_weight, parity):
    mean_weight = Fraction(mean_weight)
    allowed = list(range(parity, length + 1, 2))
    if not allowed or not (allowed[0] <= mean_weight <= allowed[-1]):
        return None
    below = max(weight for weight in allowed if weight <= mean_weight)
    above = min(weight for weight in allowed if weight >= mean_weight)
    if below == above:
        pairs = ((Fraction(1), below),)
    else:
        upper = (mean_weight - below) / (above - below)
        pairs = ((1 - upper, below), (upper, above))
    return [[str(probability), cardinality]
            for probability, cardinality in pairs]


def expected_mixtures(n, distance):
    point_value = Fraction(1, distance - 1)
    result = []
    for weight in range(distance, n + 1):
        for has_pin in (0, 1):
            free = weight - has_pin
            result.append({"weight": weight, "contains_pin": bool(has_pin),
                           "free_length": free,
                           "mixture": mixture(free, point_value * free, has_pin)})
    return result


def expected_summary(rows, pin):
    words = span(rows)
    if words is None:
        return {"status": "THEOREM_ONLY", "word_count": None,
                "minimum_distance": None, "pinned_minimum": None,
                "minimum_checks_through_pin": None,
                "other_coordinate_incidence": None}
    nonzero = [word for word in words if word]
    distance = min(word.bit_count() for word in nonzero)
    minimum_pin = [word for word in words
                   if word >> pin & 1 and word.bit_count() == distance]
    incidences = [sum(bool(word >> coordinate & 1) for word in minimum_pin)
                  for coordinate in range(rows[0].bit_length()) if coordinate != pin]
    return {"status": "EXACT", "word_count": len(words),
            "minimum_distance": distance,
            "pinned_minimum": min(word.bit_count() for word in words if word >> pin & 1),
            "minimum_checks_through_pin": len(minimum_pin),
            "other_coordinate_incidence": sorted(set(incidences))}


def verify_case(saved):
    certificate = saved["certificate"]
    s = certificate["s"]
    info = parameters(s)
    for key, value in info.items():
        assert certificate[key] == value, (key, certificate[key], value)
    assert certificate["family"] == "RM(s,2s+1)"
    n = info["n"]
    pin = certificate["pin"]
    assert 0 <= pin < n
    rows = generator_rows(s)
    assert rank(rows) == n // 2 == info["dimension"]
    assert all((left & right).bit_count() % 2 == 0
               for left in rows for right in rows)
    distance = info["distance"]
    expected_point = (Fraction(1),) + (Fraction(1, distance - 1),) * (n - 1)
    assert tuple(Fraction(value) for value in certificate["point"]) == expected_point
    expected_weight = Fraction(1) + Fraction(n - 1, distance - 1)
    assert Fraction(certificate["fractional_feasible_weight"]) == expected_weight
    assert Fraction(certificate["fractional_optimum"]) == expected_weight
    assert certificate["integer_pinned_optimum"] == distance
    assert certificate["minimum_check_count_through_pin"] == gaussian_binomial(info["m"], info["r"])
    assert certificate["minimum_check_other_coordinate_incidence"] == gaussian_binomial(info["m"] - 1, info["r"])
    assert Fraction(certificate["minimum_check_ratio"]) == Fraction(n - 1, distance - 1)
    assert certificate["all_dual_mixture_cases"] == expected_mixtures(n, distance)
    assert certificate["all_nonzero_dual_checks_feasible"] is True
    assert certificate["word_enumeration"] == expected_summary(rows, pin)
    if certificate["word_enumeration"]["status"] == "EXACT":
        summary = certificate["word_enumeration"]
        assert summary["minimum_distance"] == distance
        assert summary["pinned_minimum"] == distance
        assert summary["minimum_checks_through_pin"] == certificate["minimum_check_count_through_pin"]
        assert summary["other_coordinate_incidence"] == [certificate["minimum_check_other_coordinate_incidence"]]
    assert saved["verification"]["valid"] is True
    return {
        "name": saved["name"], "s": s, "n": n,
        "distance": distance, "dual_distance": distance,
        "fractional_optimum": str(expected_weight),
        "integrality_ratio": str(Fraction(distance, 1) / expected_weight),
        "mixture_case_count": len(certificate["all_dual_mixture_cases"]),
        "word_enumeration": certificate["word_enumeration"]["status"],
    }


def main():
    saved = json.loads(Path("REED_MULLER_ALL_DUAL_RESULTS.json").read_text(encoding="utf-8"))
    rows = [verify_case(case) for case in saved["cases"]]
    assert saved["all_valid"] is True
    output = {
        "status": "VERIFIED_INDEPENDENT_REED_MULLER_ALL_DUAL",
        "case_count": len(rows), "rows": rows,
        "all_dual_checks_supplied_analytically": True,
        "exact_word_replays": [row["name"] for row in rows if row["word_enumeration"] == "EXACT"],
    }
    Path("REED_MULLER_ALL_DUAL_INDEPENDENT_REVIEW.json").write_text(
        json.dumps(output, indent=2) + "\n", encoding="utf-8")
    Path("REED_MULLER_ALL_DUAL_INDEPENDENT_REVIEW.md").write_text(
        "# Independent all-dual Reed--Muller review\n\n"
        "Reconstructed the RM evaluation rows, rank and self-orthogonality, "
        "Gaussian-binomial incidence counts, exact rational all-dual mixture "
        "cases, and exact RM(1,3)/RM(2,5) word spans. RM(3,7) retains a "
        "theorem-backed word summary rather than expanding its 64-dimensional span.\n",
        encoding="utf-8")
    print(json.dumps({"status": output["status"], "case_count": len(rows),
                      "ratios": [row["integrality_ratio"] for row in rows]}))


if __name__ == "__main__":
    main()
