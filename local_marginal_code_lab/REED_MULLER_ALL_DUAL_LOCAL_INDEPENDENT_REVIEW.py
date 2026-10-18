"""Independent replay for the combined RM all-dual/local certificates."""

from __future__ import annotations

import json
from fractions import Fraction
from itertools import combinations
from math import comb
from pathlib import Path


ROOT = Path(__file__).resolve().parent
INPUT = ROOT / "REED_MULLER_ALL_DUAL_LOCAL_RESULTS.json"
OUT_JSON = ROOT / "REED_MULLER_ALL_DUAL_LOCAL_INDEPENDENT_REVIEW.json"
OUT_MD = ROOT / "REED_MULLER_ALL_DUAL_LOCAL_INDEPENDENT_REVIEW.md"


def family_parameters(s: int) -> dict[str, int]:
    m = 2 * s + 1
    return {
        "s": s,
        "m": m,
        "r": s,
        "n": 1 << m,
        "dimension": sum(comb(m, degree) for degree in range(s + 1)),
        "distance": 1 << (m - s),
        "dual_order": m - s - 1,
        "dual_distance": 1 << (s + 1),
    }


def gaussian_binomial(n: int, k: int) -> int:
    numerator = 1
    denominator = 1
    for index in range(k):
        numerator *= (1 << (n - index)) - 1
        denominator *= (1 << (k - index)) - 1
    return numerator // denominator


def mixture(length: int, mean: Fraction, parity: int):
    allowed = list(range(parity, length + 1, 2))
    below = max(weight for weight in allowed if weight <= mean)
    above = min(weight for weight in allowed if weight >= mean)
    if below == above:
        return ((Fraction(1), below),)
    upper = (mean - below) / (above - below)
    return ((1 - upper, below), (upper, above))


def mixture_cases(n: int, distance: int):
    p = Fraction(1, distance - 1)
    cases = []
    for weight in range(distance, n + 1):
        for contains_pin in (0, 1):
            free = weight - contains_pin
            values = mixture(free, p * free, contains_pin)
            cases.append({
                "weight": weight,
                "contains_pin": bool(contains_pin),
                "free_length": free,
                "mixture": [[str(probability), cardinality] for probability, cardinality in values],
            })
    return cases


def monomial_row(m: int, mask: int) -> int:
    return sum(1 << point for point in range(1 << m) if point & mask == mask)


def rows_for(s: int) -> list[int]:
    m = 2 * s + 1
    return [
        monomial_row(m, mask)
        for degree in range(s + 1)
        for mask in range(1 << m)
        if mask.bit_count() == degree
    ]


def codewords(rows: list[int], limit: int = 1 << 20):
    words = [0]
    for row in rows:
        if len(words) * 2 > limit:
            return None
        words += [word ^ row for word in tuple(words)]
    return sorted(words)


def support_replay_s1(pin: int, level: int) -> bool:
    words = codewords(rows_for(1))
    pinned = [word for word in words if word >> pin & 1]
    n = 8
    for size in range(level + 1):
        for scope in combinations(range(n), size):
            projected = {tuple((word >> coordinate) & 1 for coordinate in scope) for word in pinned}
            assignments = set(__import__("itertools").product((0, 1), repeat=size))
            if pin in scope or size < level:
                expected = {
                    assignment for assignment in assignments
                    if pin not in scope or assignment[scope.index(pin)] == 1
                }
                if projected != expected:
                    return False
            else:
                # At the boundary, a minimum dual word may impose odd parity.
                # Every one-hot assignment is valid in either the full or odd
                # projection and is therefore enough for the sparse witness.
                if not {
                    assignment for assignment in assignments
                    if sum(assignment) == 1
                }.issubset(projected):
                    return False
    return True


def replay_certificate(certificate: dict) -> dict:
    s = certificate["s"]
    if s not in (1, 2, 3):
        raise ValueError("unexpected family member")
    info = family_parameters(s)
    for key, value in info.items():
        if certificate.get(key) != value:
            raise ValueError(f"parameter mismatch: {key}")
    n = info["n"]
    d = info["dual_distance"]
    level = d - 1
    if certificate["pin"] != 0 or certificate["level"] != level:
        raise ValueError("pin or level mismatch")
    expected_point = ["1"] + [str(Fraction(1, d - 1))] * (n - 1)
    if certificate["point"] != expected_point:
        raise ValueError("point mismatch")
    fractional = Fraction(1) + Fraction(n - 1, d - 1)
    if Fraction(certificate["fractional_feasible_weight"]) != fractional:
        raise ValueError("fractional weight mismatch")
    if Fraction(certificate["combined_relaxation_optimum"]) != fractional:
        raise ValueError("combined optimum mismatch")
    if Fraction(certificate["integrality_ratio"]) != Fraction(d, 1) / fractional:
        raise ValueError("integrality ratio mismatch")
    through_pin = gaussian_binomial(info["m"], info["r"])
    incidence = gaussian_binomial(info["m"] - 1, info["r"])
    if certificate["minimum_check_count_through_pin"] != through_pin:
        raise ValueError("check count mismatch")
    if certificate["minimum_check_other_coordinate_incidence"] != incidence:
        raise ValueError("incidence mismatch")
    if Fraction(certificate["minimum_check_ratio"]) != Fraction(n - 1, d - 1):
        raise ValueError("check ratio mismatch")
    if certificate["all_dual_mixture_cases"] != mixture_cases(n, d):
        raise ValueError("mixture replay mismatch")
    if certificate["all_nonzero_dual_checks_feasible"] is not True:
        raise ValueError("all-dual feasibility mismatch")
    sparse = certificate["local_sparse_marginal"]
    expected_sparse = {
        "pin_value": "1",
        "one_hot_coordinate_mass": str(Fraction(1, d - 1)),
        "all_zero_mass": "1-|free_scope|/(d-1)",
        "marginal_consistency": "one_hot_or_zero",
        "supported_by_pinned_code_projection": True,
    }
    if sparse != expected_sparse:
        raise ValueError("sparse marginal mismatch")
    expected_support = {
        "level": level,
        "scope_plus_pin_max": level + 1,
        "strictly_below_dual_distance": False,
        "boundary_scope_size": d - 1,
        "pin_omitted_below_boundary": "FULL_CUBE",
        "pin_omitted_boundary": "FULL_CUBE_OR_ODD_PARITY",
        "pin_included_scope_support": "PIN_ONE_TIMES_FULL_FREE_CUBE",
        "one_hot_boundary_assignments_supported": True,
    }
    if certificate["projection_support"] != expected_support:
        raise ValueError("projection support mismatch")
    expected_scope_count = sum(comb(n, size) for size in range(level + 1))
    expected_atom_count = sum(
        comb(n - 1, size) * (size + (0 if size == d - 1 else 1))
        + (comb(n - 1, size - 1) * size if size else 0)
        for size in range(level + 1)
    )
    if certificate["scope_count"] != expected_scope_count:
        raise ValueError("scope count mismatch")
    if certificate["local_witness_atom_count"] != expected_atom_count:
        raise ValueError("witness atom count mismatch")
    replay = certificate["word_replay"]
    words = codewords(rows_for(s))
    if words is None:
        if replay != {"status": "THEOREM_ONLY", "word_count": None}:
            raise ValueError("theorem-only replay mismatch")
    else:
        pinned = [word for word in words if word & 1]
        expected_replay = {
            "status": "EXACT",
            "word_count": len(words),
            "minimum_distance": min(word.bit_count() for word in words if word),
            "pinned_minimum": min(word.bit_count() for word in pinned),
        }
        if replay != expected_replay:
            raise ValueError("word replay mismatch")
    if s == 1 and not support_replay_s1(certificate["pin"], level):
        raise ValueError("exact RM(1,3) projection replay failed")
    return {
        "s": s,
        "n": n,
        "level": level,
        "fractional_optimum": str(fractional),
        "integrality_ratio": str(Fraction(d, 1) / fractional),
        "word_replay": replay["status"],
        "exact_scope_replay": s == 1,
    }


def main() -> None:
    payload = json.loads(INPUT.read_text(encoding="utf-8"))
    if payload.get("schema") != "reed_muller_all_dual_local_results_v2":
        raise ValueError("invalid results schema")
    reviews = [replay_certificate(record["certificate"]) for record in payload["records"]]
    result = {
        "schema": "reed_muller_all_dual_local_independent_review_v2",
        "valid": True,
        "records": reviews,
    }
    OUT_JSON.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    OUT_MD.write_text(
        "# Independent review\n\n"
        "The reviewer reconstructs the RM parameters, Gaussian incidences, "
        "all-dual parity mixtures, projection-support theorem fields, and the "
        "exact RM(1,3) scope replay without importing the producer.\n",
        encoding="utf-8",
    )
    print("VERIFIED_INDEPENDENT_REED_MULLER_ALL_DUAL_LOCAL")
    for review in reviews:
        print(
            f"s={review['s']} n={review['n']} level={review['level']} "
            f"fractional={review['fractional_optimum']} ratio={review['integrality_ratio']}"
        )


if __name__ == "__main__":
    main()
