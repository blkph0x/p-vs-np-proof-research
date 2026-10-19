"""Replay the exact optimum after two valid integer-weight SOS cuts."""
from __future__ import annotations

import json
from fractions import Fraction
from pathlib import Path

from reed_muller_full_level8 import allowed, build_model, canonicalize, pts
from run_reed_muller_sos_strengthened import _columns, _q_vector

HERE = Path(__file__).resolve().parent
FULL = HERE / "REED_MULLER_LEVEL_D_FULL_RESULTS.json"
OUT = HERE / "REED_MULLER_SOS_TWO_CUT_RESULTS.json"


def _second_q_vector(model: dict, full: dict) -> list[Fraction]:
    """Build E[t^2] - 13 E[t] for the integer nonpin weight t."""
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
    first = [Fraction(0)] * n
    second = [Fraction(0)] * n
    for point in range(1, 32):
        column = variable_for(1 << point, 1)
        first[column] += 1
        second[column] += 1
    for left in range(1, 32):
        for right in range(left + 1, 32):
            column = variable_for((1 << left) | (1 << right), 3)
            second[column] += 2
    return [second[i] - 13 * first[i] for i in range(n)]


def replay() -> dict[str, str | int | bool]:
    full = json.loads(FULL.read_text(encoding="utf-8"))
    certificate = json.loads(OUT.read_text(encoding="utf-8"))
    if certificate.get("schema") != "reed_muller_sos_two_cut_results_v1":
        raise ValueError("two-cut certificate schema mismatch")
    if certificate.get("family") != "RM(2,5)" or certificate.get("pin") != 0:
        raise ValueError("two-cut family or pin mismatch")
    if certificate.get("status") != "EXACT_OPTIMUM":
        raise ValueError("two-cut result must be labelled exact")

    model = build_model()
    if model["variable_orbit_count"] != 2174 or model["row_orbit_count"] != 27926:
        raise ValueError("unexpected rebuilt model dimensions")
    masses = [Fraction(value) for value in certificate["primal_orbit_masses"]]
    if len(masses) != model["variable_orbit_count"] or any(value < 0 for value in masses):
        raise ValueError("invalid two-cut primal mass vector")
    for row, target in zip(model["matrix"], model["rhs"]):
        observed = sum(Fraction(coefficient) * masses[int(index)]
                       for index, coefficient in row.items())
        if observed != target:
            raise ValueError("two-cut primal quotient equality failure")

    objective = [Fraction(value) for value in model["objective"]]
    primal_objective = sum(coefficient * value for coefficient, value in zip(objective, masses))
    if primal_objective != Fraction("367/57"):
        raise ValueError("unexpected two-cut primal objective")
    if primal_objective != Fraction(certificate["primal_objective"]):
        raise ValueError("saved two-cut primal objective mismatch")

    q1 = _q_vector(model, full)
    q2 = _second_q_vector(model, full)
    cuts = {str(cut.get("name")): cut for cut in certificate.get("cuts", [])}
    if set(cuts) != {"square_31", "integer_adjacent_6_7"}:
        raise ValueError("two-cut definitions missing")
    if cuts["square_31"].get("polynomial") != "(5*t-31)^2":
        raise ValueError("first cut polynomial mismatch")
    if cuts["integer_adjacent_6_7"].get("polynomial") != "(t-6)*(t-7)":
        raise ValueError("second cut polynomial mismatch")
    constants = {
        "square_31": Fraction(cuts["square_31"]["q_constant"]),
        "integer_adjacent_6_7": Fraction(cuts["integer_adjacent_6_7"]["q_constant"]),
    }
    cut_values = {
        "square_31": sum(a * v for a, v in zip(q1, masses)) + constants["square_31"],
        "integer_adjacent_6_7": sum(a * v for a, v in zip(q2, masses)) + constants["integer_adjacent_6_7"],
    }
    if cut_values["square_31"] != Fraction("144/475"):
        raise ValueError("first cut value mismatch")
    if cut_values["integer_adjacent_6_7"] != 0:
        raise ValueError("integer-weight cut is not tight")
    for name, value in cut_values.items():
        if value != Fraction(certificate["primal_cut_values"][name]):
            raise ValueError("saved cut value mismatch")

    columns = _columns(model["matrix"], model["variable_orbit_count"])
    dual = [Fraction(0)] * model["row_orbit_count"]
    for row, value in certificate["dual_row_values"].items():
        row_index = int(row)
        if not 0 <= row_index < len(dual):
            raise ValueError("two-cut dual row out of range")
        dual[row_index] = Fraction(value)
    if sum(value != 0 for value in dual) != int(certificate["dual_nonzero_rows"]):
        raise ValueError("two-cut dual sparsity mismatch")
    basis = certificate.get("dual_basis", {})
    indices = basis.get("basis_column_indices", [])
    if basis.get("basis_column_count") != 337 or len(indices) != 337 or len(set(indices)) != 337:
        raise ValueError("two-cut basis metadata mismatch")
    multipliers = {
        "square_31": Fraction(cuts["square_31"]["dual_multiplier"]),
        "integer_adjacent_6_7": Fraction(cuts["integer_adjacent_6_7"]["dual_multiplier"]),
    }
    if multipliers["square_31"] != 0 or multipliers["integer_adjacent_6_7"] != Fraction(7, 171):
        raise ValueError("unexpected two-cut multipliers")
    reduced_costs = [objective[column]
                     - sum(Fraction(coefficient) * dual[row]
                           for row, coefficient in entries)
                     - q1[column] * multipliers["square_31"]
                     - q2[column] * multipliers["integer_adjacent_6_7"]
                     for column, entries in enumerate(columns)]
    if any(value < 0 for value in reduced_costs):
        raise ValueError("two-cut dual reduced-cost violation")
    reduced_minimum = min(reduced_costs)
    if reduced_minimum != Fraction(certificate["dual_reduced_cost_minimum"]):
        raise ValueError("saved two-cut reduced-cost minimum mismatch")
    dual_objective = (sum(Fraction(rhs) * value for rhs, value in zip(model["rhs"], dual))
                      - constants["square_31"] * multipliers["square_31"]
                      - constants["integer_adjacent_6_7"] * multipliers["integer_adjacent_6_7"])
    if dual_objective != Fraction(certificate["dual_objective"]):
        raise ValueError("saved two-cut dual objective mismatch")
    lower = Fraction(certificate["certified_lower_bound"])
    upper = Fraction(certificate["certified_upper_bound"])
    gap = Fraction(certificate["unresolved_optimum_gap"])
    if lower != Fraction("367/57") or upper != lower or dual_objective != lower or gap != 0:
        raise ValueError("invalid two-cut exact optimum")
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
    print("REED_MULLER_SOS_TWO_CUT_PASS")
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
