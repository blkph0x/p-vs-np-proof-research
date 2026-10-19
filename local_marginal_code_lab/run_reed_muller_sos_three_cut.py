"""Replay the exact RM(2,5) optimum after three valid integer-weight cuts."""
from __future__ import annotations

import itertools
import json
import math
from fractions import Fraction
from pathlib import Path

from reed_muller_full_level8 import allowed, build_model, canonicalize, pts

HERE = Path(__file__).resolve().parent
FULL = HERE / "REED_MULLER_LEVEL_D_FULL_RESULTS.json"
OUT = HERE / "REED_MULLER_SOS_THREE_CUT_RESULTS.json"


def _moment_vectors(model: dict, full: dict) -> list[list[Fraction]]:
    """Return quotient vectors for E[binom(t,k)], k=1,...,4."""
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
    vectors = [[Fraction(0)] * n for _ in range(4)]
    for k in range(1, 5):
        for combination in itertools.combinations(range(1, 32), k):
            mask = sum(1 << point for point in combination)
            vectors[k - 1][variable_for(mask, (1 << k) - 1)] += 1
    return vectors


def _q_vectors(model: dict, full: dict) -> tuple[list[Fraction], list[Fraction], list[Fraction]]:
    moments = _moment_vectors(model, full)
    first, second, third, fourth = moments
    q1 = [first[i] * (1 - Fraction(62, 5)) + 2 * second[i]
          for i in range(len(first))]
    q2 = [-12 * first[i] + 2 * second[i] for i in range(len(first))]
    # Delta^k f(0) for f(t)=(t-6)(t-7)(t-23)(t-24).
    differences = [-8004, 2064, -324, 24]
    q3 = [differences[0] * first[i] + differences[1] * second[i]
          + differences[2] * third[i] + differences[3] * fourth[i]
          for i in range(len(first))]
    return q1, q2, q3


def _columns(matrix: list[dict[str, int]], count: int) -> list[list[tuple[int, int]]]:
    columns = [[] for _ in range(count)]
    for row, coefficients in enumerate(matrix):
        for column, coefficient in coefficients.items():
            columns[int(column)].append((row, int(coefficient)))
    return columns


def replay() -> dict[str, str | int | bool]:
    full = json.loads(FULL.read_text(encoding="utf-8"))
    certificate = json.loads(OUT.read_text(encoding="utf-8"))
    if certificate.get("schema") != "reed_muller_sos_three_cut_results_v1":
        raise ValueError("three-cut certificate schema mismatch")
    if certificate.get("family") != "RM(2,5)" or certificate.get("pin") != 0:
        raise ValueError("three-cut family or pin mismatch")
    if certificate.get("status") != "EXACT_OPTIMUM":
        raise ValueError("three-cut result must be labelled exact")

    model = build_model()
    if model["variable_orbit_count"] != 2174 or model["row_orbit_count"] != 27926:
        raise ValueError("unexpected rebuilt model dimensions")
    masses = [Fraction(value) for value in certificate["primal_orbit_masses"]]
    if len(masses) != model["variable_orbit_count"] or any(value < 0 for value in masses):
        raise ValueError("invalid three-cut primal mass vector")
    for row, target in zip(model["matrix"], model["rhs"]):
        observed = sum(Fraction(coefficient) * masses[int(index)]
                       for index, coefficient in row.items())
        if observed != target:
            raise ValueError("three-cut primal quotient equality failure")

    objective = [Fraction(value) for value in model["objective"]]
    primal_objective = sum(coefficient * value for coefficient, value in zip(objective, masses))
    if primal_objective != Fraction("5231/801"):
        raise ValueError("unexpected three-cut primal objective")
    if primal_objective != Fraction(certificate["primal_objective"]):
        raise ValueError("saved three-cut primal objective mismatch")

    q1, q2, q3 = _q_vectors(model, full)
    cuts = {str(cut.get("name")): cut for cut in certificate.get("cuts", [])}
    expected = {"square_31", "integer_adjacent_6_7", "integer_adjacent_product_6_23"}
    if set(cuts) != expected:
        raise ValueError("three-cut definitions missing")
    if cuts["square_31"].get("polynomial") != "(5*t-31)^2":
        raise ValueError("square cut polynomial mismatch")
    if cuts["integer_adjacent_6_7"].get("polynomial") != "(t-6)*(t-7)":
        raise ValueError("second cut polynomial mismatch")
    if cuts["integer_adjacent_product_6_23"].get("polynomial") != "(t-6)*(t-7)*(t-23)*(t-24)":
        raise ValueError("third cut polynomial mismatch")
    constants = {name: Fraction(cuts[name]["q_constant"]) for name in expected}
    cut_values = {
        "square_31": sum(a * v for a, v in zip(q1, masses)) + constants["square_31"],
        "integer_adjacent_6_7": sum(a * v for a, v in zip(q2, masses)) + constants["integer_adjacent_6_7"],
        "integer_adjacent_product_6_23": sum(a * v for a, v in zip(q3, masses)) + constants["integer_adjacent_product_6_23"],
    }
    expected_values = {
        "square_31": Fraction("17392/6675"),
        "integer_adjacent_6_7": Fraction("200/89"),
        "integer_adjacent_product_6_23": Fraction(0),
    }
    if cut_values != expected_values:
        raise ValueError("three-cut primal values mismatch")
    for name, value in cut_values.items():
        if value != Fraction(certificate["primal_cut_values"][name]):
            raise ValueError("saved three-cut value mismatch")

    dual = [Fraction(0)] * model["row_orbit_count"]
    for row, value in certificate["dual_row_values"].items():
        row_index = int(row)
        if not 0 <= row_index < len(dual):
            raise ValueError("three-cut dual row out of range")
        dual[row_index] = Fraction(value)
    if sum(value != 0 for value in dual) != int(certificate["dual_nonzero_rows"]):
        raise ValueError("three-cut dual sparsity mismatch")
    basis = certificate.get("dual_basis", {})
    indices = basis.get("basis_column_indices", [])
    if (basis.get("basis_column_count") != 1183
            or len(indices) != 1183 or len(set(indices)) != 1183):
        raise ValueError("three-cut basis metadata mismatch")
    multipliers = {name: Fraction(cuts[name]["dual_multiplier"]) for name in expected}
    if multipliers["square_31"] != 0 or multipliers["integer_adjacent_6_7"] != 0:
        raise ValueError("unexpected earlier-cut multiplier")
    if multipliers["integer_adjacent_product_6_23"] != Fraction(7, 9612):
        raise ValueError("unexpected third-cut multiplier")

    columns = _columns(model["matrix"], model["variable_orbit_count"])
    reduced_costs = [objective[column]
                     - sum(Fraction(coefficient) * dual[row]
                           for row, coefficient in entries)
                     - q1[column] * multipliers["square_31"]
                     - q2[column] * multipliers["integer_adjacent_6_7"]
                     - q3[column] * multipliers["integer_adjacent_product_6_23"]
                     for column, entries in enumerate(columns)]
    if any(value < 0 for value in reduced_costs):
        raise ValueError("three-cut dual reduced-cost violation")
    reduced_minimum = min(reduced_costs)
    if reduced_minimum != Fraction(certificate["dual_reduced_cost_minimum"]):
        raise ValueError("saved three-cut reduced-cost minimum mismatch")
    dual_objective = (sum(Fraction(rhs) * value for rhs, value in zip(model["rhs"], dual))
                      - constants["integer_adjacent_product_6_23"]
                      * multipliers["integer_adjacent_product_6_23"])
    if dual_objective != Fraction(certificate["dual_objective"]):
        raise ValueError("three-cut dual objective mismatch")
    lower = Fraction(certificate["certified_lower_bound"])
    upper = Fraction(certificate["certified_upper_bound"])
    gap = Fraction(certificate["unresolved_optimum_gap"])
    if lower != Fraction("5231/801") or upper != lower or dual_objective != lower or gap != 0:
        raise ValueError("invalid three-cut exact optimum")
    return {
        "valid": True,
        "variable_orbits": model["variable_orbit_count"],
        "row_orbits": model["row_orbit_count"],
        "primal_upper_bound": str(upper),
        "dual_lower_bound": str(lower),
        "unresolved_gap": str(gap),
        "dual_reduced_cost_minimum": str(reduced_minimum),
        "status": "EXACT_OPTIMUM",
    }


def main() -> None:
    result = replay()
    print("REED_MULLER_SOS_THREE_CUT_PASS")
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
