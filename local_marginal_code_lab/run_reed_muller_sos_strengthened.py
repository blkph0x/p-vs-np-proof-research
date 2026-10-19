"""Replay the exact bracket for the SOS-strengthened RM(2,5) model.

The base model is rebuilt with exact integer arithmetic.  The saved primal and
dual values are then checked as rational certificates for the added inequality
``E[(5t-31)^2] >= 0``.  The two certificates intentionally leave a nonzero
interval; this runner must never turn a bracket into an exact optimum claim.
"""
from __future__ import annotations

import json
from fractions import Fraction
from pathlib import Path

from reed_muller_full_level8 import allowed, build_model, canonicalize, pts


HERE = Path(__file__).resolve().parent
FULL = HERE / "REED_MULLER_LEVEL_D_FULL_RESULTS.json"
OUT = HERE / "REED_MULLER_SOS_STRENGTHENED_RESULTS.json"


def _q_vector(model: dict, full: dict) -> list[Fraction]:
    """Build the linear part of the Boolean-square cut on quotient columns."""
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
    first_moment = [Fraction(0)] * n
    second_moment = [Fraction(0)] * n
    for point in range(1, 32):
        column = variable_for(1 << point, 1)
        first_moment[column] += 1
        second_moment[column] += 1
    for left in range(1, 32):
        for right in range(left + 1, 32):
            column = variable_for((1 << left) | (1 << right), 3)
            second_moment[column] += 2
    return [second_moment[i] - Fraction(62, 5) * first_moment[i]
            for i in range(n)]


def _columns(matrix: list[dict[str, int]], count: int) -> list[list[tuple[int, int]]]:
    columns = [[] for _ in range(count)]
    for row, coefficients in enumerate(matrix):
        for column, coefficient in coefficients.items():
            columns[int(column)].append((row, int(coefficient)))
    return columns


def replay() -> dict[str, str | int | bool]:
    full = json.loads(FULL.read_text(encoding="utf-8"))
    certificate = json.loads(OUT.read_text(encoding="utf-8"))
    if certificate.get("schema") != "reed_muller_sos_strengthened_results_v1":
        raise ValueError("strengthened certificate schema mismatch")
    if certificate.get("family") != "RM(2,5)" or certificate.get("pin") != 0:
        raise ValueError("strengthened family or pin mismatch")
    if certificate.get("status") != "BRACKETED_NOT_EXACT":
        raise ValueError("the strengthened result must remain bracketed")

    model = build_model()
    if model["variable_orbit_count"] != 2174 or model["row_orbit_count"] != 27926:
        raise ValueError("unexpected rebuilt model dimensions")
    if int(certificate["variable_orbit_count"]) != model["variable_orbit_count"]:
        raise ValueError("variable count mismatch")
    if int(certificate["row_orbit_count"]) != model["row_orbit_count"]:
        raise ValueError("row count mismatch")

    masses = [Fraction(value) for value in certificate["primal_orbit_masses"]]
    if len(masses) != model["variable_orbit_count"] or any(value < 0 for value in masses):
        raise ValueError("invalid primal mass vector")
    for row, target in zip(model["matrix"], model["rhs"]):
        observed = sum(Fraction(coefficient) * masses[int(index)]
                       for index, coefficient in row.items())
        if observed != target:
            raise ValueError("primal quotient equality failure")

    objective_coefficients = [Fraction(value) for value in model["objective"]]
    primal_objective = sum(coefficient * value
                           for coefficient, value in zip(objective_coefficients, masses))
    if primal_objective != Fraction(certificate["primal_objective"]):
        raise ValueError("saved primal objective mismatch")
    if primal_objective != Fraction(7037, 1095):
        raise ValueError("unexpected primal upper bound")

    q = _q_vector(model, full)
    cut = certificate["cut"]
    if cut.get("polynomial") != "(5*t-31)^2" or cut.get("q_linear") != "-62/5":
        raise ValueError("cut definition mismatch")
    constant = Fraction(cut["q_constant"])
    cut_value = sum(q[i] * masses[i] for i in range(len(masses))) + constant
    if cut_value != Fraction(certificate["primal_cut_value"]) or cut_value != 0:
        raise ValueError("primal does not lie on the strengthened cut")

    columns = _columns(model["matrix"], model["variable_orbit_count"])
    dual = [Fraction(0)] * model["row_orbit_count"]
    for row, value in certificate["dual_row_values"].items():
        row_index = int(row)
        if not 0 <= row_index < len(dual):
            raise ValueError("dual row index out of range")
        dual[row_index] = Fraction(value)
    if sum(value != 0 for value in dual) != int(certificate["dual_nonzero_rows"]):
        raise ValueError("dual sparsity count mismatch")
    multiplier = Fraction(cut["dual_multiplier"])
    reduced_costs = [objective_coefficients[column]
                     - sum(Fraction(coefficient) * dual[row]
                           for row, coefficient in entries)
                     - q[column] * multiplier
                     for column, entries in enumerate(columns)]
    if any(value < 0 for value in reduced_costs):
        raise ValueError("dual reduced-cost violation")
    reduced_minimum = min(reduced_costs)
    if reduced_minimum != Fraction(certificate["dual_reduced_cost_minimum"]):
        raise ValueError("saved reduced-cost minimum mismatch")

    dual_objective = (sum(Fraction(rhs) * value
                          for rhs, value in zip(model["rhs"], dual))
                      - constant * multiplier)
    if dual_objective != Fraction(certificate["dual_objective"]):
        raise ValueError("saved dual objective mismatch")
    lower = Fraction(certificate["certified_lower_bound"])
    upper = Fraction(certificate["certified_upper_bound"])
    gap = Fraction(certificate["unresolved_optimum_gap"])
    if lower != Fraction(64263, 10000) or upper != Fraction(7037, 1095):
        raise ValueError("unexpected certified bracket")
    if dual_objective < lower or upper != primal_objective or gap != upper - lower or not lower < upper:
        raise ValueError("invalid certified bracket")
    return {
        "valid": True,
        "variable_orbits": model["variable_orbit_count"],
        "row_orbits": model["row_orbit_count"],
        "primal_upper_bound": str(upper),
        "dual_lower_bound": str(lower),
        "unresolved_gap": str(gap),
        "status": "BRACKETED_NOT_EXACT",
    }


def main() -> None:
    result = replay()
    print("REED_MULLER_SOS_STRENGTHENED_PASS")
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
