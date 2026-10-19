"""Pure-stdlib independent replay of the SOS-strengthened RM(2,5) optimum.

This checker consumes the saved full quotient matrix instead of importing the
model builder used by the producer.  The cut vector is reconstructed from the
two canonical nonpin supports: a nonpin singleton is ``scope=2, atom=1`` and a
pair of distinct nonpin points is ``scope=6, atom=3``.  Those are the only
supports needed for ``t`` and ``t^2``.
"""
from __future__ import annotations

import copy
import json
from fractions import Fraction
from pathlib import Path


HERE = Path(__file__).resolve().parent
SOURCE_PATH = HERE / "REED_MULLER_LEVEL_D_FULL_RESULTS.json"
CERTIFICATE_PATH = HERE / "REED_MULLER_SOS_STRENGTHENED_RESULTS.json"
REVIEW_JSON = HERE / "REED_MULLER_SOS_STRENGTHENED_INDEPENDENT_REVIEW.json"
REVIEW_MD = HERE / "REED_MULLER_SOS_STRENGTHENED_INDEPENDENT_REVIEW.md"


def _fraction(value: object) -> Fraction:
    return value if isinstance(value, Fraction) else Fraction(str(value))


def _columns(matrix: list[dict[str, int]], count: int) -> list[list[tuple[int, int]]]:
    columns = [[] for _ in range(count)]
    for row, coefficients in enumerate(matrix):
        for column, coefficient in coefficients.items():
            columns[int(column)].append((row, int(coefficient)))
    return columns


def _cut_vector(source: dict) -> list[Fraction]:
    variables = source["variable_orbits"]
    singleton = [i for i, value in enumerate(variables)
                 if int(value["scope"]) == 2 and value["atoms"] == [1]]
    pair = [i for i, value in enumerate(variables)
            if int(value["scope"]) == 6 and value["atoms"] == [3]]
    if len(singleton) != 1 or len(pair) != 1:
        raise ValueError("canonical nonpin supports are not unique")
    q = [Fraction(0)] * int(source["variable_orbit_count"])
    # There are 31 nonpin points and C(31,2) unordered nonpin pairs.
    q[singleton[0]] = Fraction(31) - Fraction(62, 5) * 31
    q[pair[0]] = Fraction(2 * 31 * 30 // 2)
    return q


def replay(source: dict, certificate: dict) -> dict[str, object]:
    if source.get("schema") != "reed_muller_level_d_full_results_v1":
        raise ValueError("full quotient schema mismatch")
    if certificate.get("schema") != "reed_muller_sos_strengthened_results_v1":
        raise ValueError("strengthened schema mismatch")
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
    if primal_objective != Fraction("7037/1095"):
        raise ValueError("primal upper bound mismatch")

    q = _cut_vector(source)
    cut = certificate["cut"]
    if cut.get("polynomial") != "(5*t-31)^2" or cut.get("q_linear") != "-62/5":
        raise ValueError("cut polynomial metadata mismatch")
    constant = Fraction(cut["q_constant"])
    cut_value = sum(coefficient * value for coefficient, value in zip(q, masses)) + constant
    if cut_value != 0 or certificate.get("primal_cut_value") != "0":
        raise ValueError("primal cut equality failure")

    dual = [Fraction(0)] * row_count
    for row, value in certificate["dual_row_values"].items():
        index = int(row)
        if not 0 <= index < row_count:
            raise ValueError("dual row out of range")
        dual[index] = Fraction(value)
    if sum(value != 0 for value in dual) != int(certificate["dual_nonzero_rows"]):
        raise ValueError("dual sparsity mismatch")
    basis = certificate.get("dual_basis", {})
    basis_indices = basis.get("basis_column_indices", [])
    if (basis.get("basis_column_count") != 1890
            or len(basis_indices) != 1890
            or len(set(basis_indices)) != 1890):
        raise ValueError("exact dual basis metadata mismatch")
    multiplier = Fraction(cut["dual_multiplier"])
    columns = _columns(matrix, n)
    reduced = [objective[column]
               - sum(Fraction(coefficient) * dual[row]
                     for row, coefficient in entries)
               - q[column] * multiplier
               for column, entries in enumerate(columns)]
    if any(value < 0 for value in reduced):
        raise ValueError("negative reduced cost")
    minimum = min(reduced)
    if minimum != Fraction(certificate["dual_reduced_cost_minimum"]):
        raise ValueError("reduced-cost minimum mismatch")
    dual_objective = (sum(Fraction(value) * dual[row] for row, value in enumerate(rhs))
                      - constant * multiplier)
    if dual_objective != Fraction(certificate["dual_objective"]):
        raise ValueError("dual objective mismatch")

    lower = Fraction(certificate["certified_lower_bound"])
    upper = Fraction(certificate["certified_upper_bound"])
    gap = Fraction(certificate["unresolved_optimum_gap"])
    if lower != Fraction("7037/1095") or upper != Fraction("7037/1095"):
        raise ValueError("exact optimum endpoints changed")
    if dual_objective != lower or upper != primal_objective or gap != 0:
        raise ValueError("invalid exact primal/dual equality")
    return {
        "valid": True,
        "source_matrix": "REED_MULLER_LEVEL_D_FULL_RESULTS.json",
        "variable_orbits": n,
        "row_orbits": row_count,
        "primal_upper_bound": str(upper),
        "dual_lower_bound": str(lower),
        "dual_objective": str(dual_objective),
        "unresolved_gap": str(gap),
        "reduced_cost_minimum": str(minimum),
        "status": "EXACT_OPTIMUM",
        "scope": "Independent arithmetic replay of the saved quotient; source construction is checked by the full-level reviewer.",
    }


def main() -> None:
    source = json.loads(SOURCE_PATH.read_text(encoding="utf-8"))
    certificate = json.loads(CERTIFICATE_PATH.read_text(encoding="utf-8"))
    result = replay(source, certificate)
    REVIEW_JSON.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    REVIEW_MD.write_text(
        "# Independent SOS-strengthened RM(2,5) review\n\n"
        "The pure-stdlib replay accepted the saved primal and dual certificates. "
        "It proves the finite exact optimum\n\n"
        f"- dual lower bound: `{result['dual_lower_bound']}`\n"
        f"- primal upper bound: `{result['primal_upper_bound']}`\n"
        f"- unresolved gap: `{result['unresolved_gap']}`\n\n"
        "The result is finite and representation-specific; it is not a SAT or P-versus-NP result.\n",
        encoding="utf-8",
    )
    print("REED_MULLER_SOS_STRENGTHENED_INDEPENDENT_PASS")
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
