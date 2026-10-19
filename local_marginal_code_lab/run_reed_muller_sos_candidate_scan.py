"""Scan a fixed exact family of valid integer-weight cuts against the seven-cut witness.

This is a separation experiment only.  It does not claim the optimum after a new
cut, and it does not import an LP solver or promote a floating-point candidate.
"""
from __future__ import annotations

import hashlib
import itertools
import json
from fractions import Fraction
from pathlib import Path

from reed_muller_full_level8 import allowed, build_model, canonicalize, pts

HERE = Path(__file__).resolve().parent
FULL = HERE / "REED_MULLER_LEVEL_D_FULL_RESULTS.json"
WITNESS = HERE / "REED_MULLER_SOS_SEVEN_CUT_RESULTS.json"
OUT = HERE / "REED_MULLER_SOS_CANDIDATE_SCAN_RESULTS.json"


def _moment_vectors(model: dict, full: dict) -> list[list[Fraction]]:
    index: dict[tuple[int, int], int] = {}
    for variable, orbit in enumerate(full["variable_orbits"]):
        scope = int(orbit["scope"])
        support = allowed(scope)
        for atom in orbit["atoms"]:
            index[(scope, support[atom])] = variable

    def variable_for(mask: int, atom: int) -> int:
        canonical, mapping, _ = canonicalize(mask)
        positions = {point: i for i, point in enumerate(pts(canonical))}
        canonical_atom = 0
        for i, point in enumerate(pts(mask)):
            if atom >> i & 1:
                canonical_atom |= 1 << positions[mapping[point]]
        return index[(canonical, canonical_atom)]

    n = int(model["variable_orbit_count"])
    vectors = [[Fraction(0)] * n for _ in range(5)]
    for k in range(1, 6):
        for combination in itertools.combinations(range(1, 32), k):
            mask = sum(1 << point for point in combination)
            vectors[k - 1][variable_for(mask, (1 << k) - 1)] += 1
    return vectors


def _multiply(left: tuple[int, ...], right: tuple[int, ...]) -> tuple[int, ...]:
    result = [0] * (len(left) + len(right) - 1)
    for i, a in enumerate(left):
        for j, b in enumerate(right):
            result[i + j] += a * b
    return tuple(result)


def _value(polynomial: tuple[int, ...], t: int) -> int:
    return sum(coefficient * t**power for power, coefficient in enumerate(polynomial))


def candidate_family() -> list[dict[str, object]]:
    base: list[tuple[str, tuple[int, ...]]] = []
    for root in range(32):
        base.append((f"square_{root}", (root * root, -2 * root, 1)))
    for root in range(31):
        base.append((f"adjacent_{root}_{root + 1}",
                     (root * (root + 1), -(2 * root + 1), 1)))
    base.append(("boundary_0_31", (0, 31, -1)))

    candidates: list[dict[str, object]] = []
    for name, polynomial in base:
        candidates.append({"name": name, "polynomial": list(polynomial),
                           "factors": [name]})
    for (left_name, left), (right_name, right) in itertools.combinations_with_replacement(base, 2):
        polynomial = _multiply(left, right)
        if len(polynomial) - 1 > 5:
            continue
        candidates.append({"name": f"{left_name}*{right_name}",
                           "polynomial": list(polynomial),
                           "factors": [left_name, right_name]})
    return candidates


def _expectation(polynomial: tuple[int, ...], moments: list[Fraction]) -> Fraction:
    values = [_value(polynomial, t) for t in range(32)]
    differences = values[:]
    binomial_coefficients: list[int] = []
    while differences:
        binomial_coefficients.append(differences[0])
        differences = [differences[i + 1] - differences[i]
                       for i in range(len(differences) - 1)]
    return sum(Fraction(binomial_coefficients[index]) * moments[index]
               for index in range(len(polynomial)))


def scan() -> dict[str, object]:
    full = json.loads(FULL.read_text(encoding="utf-8"))
    witness = json.loads(WITNESS.read_text(encoding="utf-8"))
    model = build_model()
    masses = [Fraction(value) for value in witness["primal_orbit_masses"]]
    vectors = _moment_vectors(model, full)
    moments = [Fraction(1)] + [sum(a * b for a, b in zip(vector, masses))
                               for vector in vectors]
    evaluated: list[dict[str, object]] = []
    for candidate in candidate_family():
        polynomial = tuple(int(value) for value in candidate["polynomial"])
        if not all(_value(polynomial, t) >= 0 for t in range(32)):
            raise ValueError(f"candidate is not nonnegative on the integer domain: {candidate['name']}")
        evaluated.append({**candidate, "degree": len(polynomial) - 1,
                          "expectation": str(_expectation(polynomial, moments))})
    evaluated.sort(key=lambda row: (Fraction(row["expectation"]), str(row["name"])))
    negative = [row for row in evaluated if Fraction(row["expectation"]) < 0]
    selected = negative[0]
    expected_name = "adjacent_6_7*adjacent_30_31"
    if selected["name"] != expected_name:
        raise ValueError(f"unexpected strongest candidate: {selected['name']}")
    return {
        "schema": "reed_muller_sos_candidate_scan_results_v1",
        "status": "SEPARATION_ONLY",
        "family": "RM(2,5)",
        "pin": 0,
        "domain": [0, 31],
        "degree_bound": 5,
        "candidate_construction": "squares, adjacent integer-root products, boundary product, and all pairwise products of degree at most five",
        "candidate_count": len(evaluated),
        "negative_candidate_count": len(negative),
        "moments_binomial_basis": [str(value) for value in moments],
        "selected_candidate": selected,
        "top_negative_candidates": negative[:20],
        "source_sha256": {
            FULL.name: hashlib.sha256(FULL.read_bytes()).hexdigest(),
            WITNESS.name: hashlib.sha256(WITNESS.read_bytes()).hexdigest(),
        },
        "scope": "Exact separation of the saved seven-cut witness; no post-cut optimum is certified.",
    }


def main() -> None:
    result = scan()
    OUT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print("REED_MULLER_SOS_CANDIDATE_SCAN_PASS")
    print(json.dumps({key: result[key] for key in (
        "status", "candidate_count", "negative_candidate_count", "selected_candidate")},
        sort_keys=True))


if __name__ == "__main__":
    main()
