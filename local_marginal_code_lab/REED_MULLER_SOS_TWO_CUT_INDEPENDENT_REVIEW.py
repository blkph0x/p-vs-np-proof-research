"""Pure-stdlib independent replay of the two-cut RM(2,5) certificate."""
from __future__ import annotations

import json
from fractions import Fraction
from pathlib import Path

HERE = Path(__file__).resolve().parent
SOURCE_PATH = HERE / "REED_MULLER_LEVEL_D_FULL_RESULTS.json"
CERTIFICATE_PATH = HERE / "REED_MULLER_SOS_TWO_CUT_RESULTS.json"
REVIEW_JSON = HERE / "REED_MULLER_SOS_TWO_CUT_INDEPENDENT_REVIEW.json"
REVIEW_MD = HERE / "REED_MULLER_SOS_TWO_CUT_INDEPENDENT_REVIEW.md"


def _columns(matrix: list[dict[str, int]], count: int) -> list[list[tuple[int, int]]]:
    columns = [[] for _ in range(count)]
    for row, coefficients in enumerate(matrix):
        for column, coefficient in coefficients.items():
            columns[int(column)].append((row, int(coefficient)))
    return columns


def _q_vectors(source: dict) -> tuple[list[Fraction], list[Fraction]]:
    singleton = [i for i, value in enumerate(source["variable_orbits"])
                 if int(value["scope"]) == 2 and value["atoms"] == [1]]
    pair = [i for i, value in enumerate(source["variable_orbits"])
            if int(value["scope"]) == 6 and value["atoms"] == [3]]
    if len(singleton) != 1 or len(pair) != 1:
        raise ValueError("canonical nonpin supports are not unique")
    q1 = [Fraction(0)] * int(source["variable_orbit_count"])
    q2 = [Fraction(0)] * int(source["variable_orbit_count"])
    q1[singleton[0]] = Fraction(-1767, 5)
    q1[pair[0]] = Fraction(930)
    q2[singleton[0]] = Fraction(-372)
    q2[pair[0]] = Fraction(930)
    return q1, q2


def replay(source: dict, certificate: dict) -> dict[str, object]:
    if source.get("schema") != "reed_muller_level_d_full_results_v1":
        raise ValueError("full quotient schema mismatch")
    if certificate.get("schema") != "reed_muller_sos_two_cut_results_v1":
        raise ValueError("two-cut schema mismatch")
    if source.get("family") != "RM(2,5)" or source.get("pin") != 0:
        raise ValueError("source family or pin mismatch")
    if certificate.get("family") != "RM(2,5)" or certificate.get("pin") != 0:
        raise ValueError("certificate family or pin mismatch")
    if certificate.get("status") != "EXACT_OPTIMUM":
        raise ValueError("the certificate must be labelled exact")
    n = int(source["variable_orbit_count"])
    row_count = int(source["row_orbit_count"])
    if n != 2174 or row_count != 27926:
        raise ValueError("unexpected source dimensions")
    matrix = source["quotient_matrix"]
    rhs = source["rhs"]
    objective = [Fraction(value) for value in source["objective"]]
    masses = [Fraction(value) for value in certificate["primal_orbit_masses"]]
    if len(masses) != n or any(value < 0 for value in masses):
        raise ValueError("invalid primal masses")
    for row, target in zip(matrix, rhs):
        if sum(Fraction(coefficient) * masses[int(index)]
               for index, coefficient in row.items()) != target:
            raise ValueError("primal equality failure")
    primal_objective = sum(coefficient * value for coefficient, value in zip(objective, masses))
    if primal_objective != Fraction("367/57"):
        raise ValueError("primal upper bound mismatch")

    q1, q2 = _q_vectors(source)
    cuts = {str(cut.get("name")): cut for cut in certificate.get("cuts", [])}
    if set(cuts) != {"square_31", "integer_adjacent_6_7"}:
        raise ValueError("two-cut definitions missing")
    if cuts["square_31"].get("polynomial") != "(5*t-31)^2":
        raise ValueError("square cut metadata mismatch")
    if cuts["integer_adjacent_6_7"].get("polynomial") != "(t-6)*(t-7)":
        raise ValueError("integer cut metadata mismatch")
    constants = {name: Fraction(cuts[name]["q_constant"]) for name in cuts}
    values = {
        "square_31": sum(a * v for a, v in zip(q1, masses)) + constants["square_31"],
        "integer_adjacent_6_7": sum(a * v for a, v in zip(q2, masses)) + constants["integer_adjacent_6_7"],
    }
    if values["square_31"] != Fraction("144/475") or values["integer_adjacent_6_7"] != 0:
        raise ValueError("primal cut value mismatch")
    if {name: str(value) for name, value in values.items()} != certificate["primal_cut_values"]:
        raise ValueError("saved cut values mismatch")

    dual = [Fraction(0)] * row_count
    for row, value in certificate["dual_row_values"].items():
        index = int(row)
        if not 0 <= index < row_count:
            raise ValueError("dual row out of range")
        dual[index] = Fraction(value)
    if sum(value != 0 for value in dual) != int(certificate["dual_nonzero_rows"]):
        raise ValueError("dual sparsity mismatch")
    basis = certificate["dual_basis"]
    indices = basis.get("basis_column_indices", [])
    if basis.get("basis_column_count") != 337 or len(indices) != 337 or len(set(indices)) != 337:
        raise ValueError("two-cut basis metadata mismatch")
    z1 = Fraction(cuts["square_31"]["dual_multiplier"])
    z2 = Fraction(cuts["integer_adjacent_6_7"]["dual_multiplier"])
    if z1 != 0 or z2 != Fraction(7, 171):
        raise ValueError("two-cut multiplier mismatch")
    reduced = []
    for column, entries in enumerate(_columns(matrix, n)):
        reduced.append(objective[column]
                       - sum(Fraction(coefficient) * dual[row] for row, coefficient in entries)
                       - q1[column] * z1 - q2[column] * z2)
    if any(value < 0 for value in reduced):
        raise ValueError("negative reduced cost")
    minimum = min(reduced)
    if minimum != Fraction(certificate["dual_reduced_cost_minimum"]):
        raise ValueError("reduced-cost minimum mismatch")
    dual_objective = (sum(Fraction(value) * dual[row] for row, value in enumerate(rhs))
                      - constants["square_31"] * z1 - constants["integer_adjacent_6_7"] * z2)
    if dual_objective != Fraction(certificate["dual_objective"]):
        raise ValueError("dual objective mismatch")
    lower = Fraction(certificate["certified_lower_bound"])
    upper = Fraction(certificate["certified_upper_bound"])
    gap = Fraction(certificate["unresolved_optimum_gap"])
    if lower != Fraction("367/57") or upper != lower or dual_objective != lower or gap != 0:
        raise ValueError("invalid exact optimum")
    return {"valid": True, "source_matrix": SOURCE_PATH.name, "variable_orbits": n,
            "row_orbits": row_count, "primal_upper_bound": str(upper),
            "dual_lower_bound": str(lower), "dual_objective": str(dual_objective),
            "unresolved_gap": str(gap), "reduced_cost_minimum": str(minimum),
            "status": "EXACT_OPTIMUM",
            "scope": "Independent arithmetic replay of the saved two-cut quotient certificate."}


def main() -> None:
    result = replay(json.loads(SOURCE_PATH.read_text(encoding="utf-8")),
                    json.loads(CERTIFICATE_PATH.read_text(encoding="utf-8")))
    REVIEW_JSON.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    REVIEW_MD.write_text(
        "# Independent two-cut SOS RM(2,5) review\n\n"
        "The pure-stdlib replay accepted the saved primal and dual certificates.\n\n"
        f"- dual lower bound: `{result['dual_lower_bound']}`\n"
        f"- primal upper bound: `{result['primal_upper_bound']}`\n"
        f"- unresolved gap: `{result['unresolved_gap']}`\n\n"
        "The finite exact result is representation-specific and does not resolve P versus NP.\n",
        encoding="utf-8")
    print("REED_MULLER_SOS_TWO_CUT_INDEPENDENT_PASS")
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
