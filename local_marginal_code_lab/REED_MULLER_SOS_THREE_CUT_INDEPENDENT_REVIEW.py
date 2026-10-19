"""Pure-stdlib independent replay of the three-cut RM(2,5) certificate."""
from __future__ import annotations

import itertools
import json
import math
from fractions import Fraction
from pathlib import Path

HERE = Path(__file__).resolve().parent
SOURCE_PATH = HERE / "REED_MULLER_LEVEL_D_FULL_RESULTS.json"
CERTIFICATE_PATH = HERE / "REED_MULLER_SOS_THREE_CUT_RESULTS.json"
REVIEW_JSON = HERE / "REED_MULLER_SOS_THREE_CUT_INDEPENDENT_REVIEW.json"
REVIEW_MD = HERE / "REED_MULLER_SOS_THREE_CUT_INDEPENDENT_REVIEW.md"


def _points(mask: int) -> tuple[int, ...]:
    return tuple(point for point in range(32) if mask >> point & 1)


def _rank(vectors: tuple[int, ...]) -> int:
    basis: list[int] = []
    for value in vectors:
        for pivot in basis:
            value = min(value, value ^ pivot)
        if value:
            basis.append(value)
            basis.sort(reverse=True)
    return len(basis)


def _canonicalize(mask: int) -> tuple[int, dict[int, int]]:
    points = _points(mask)
    nonzero = tuple(point for point in points if point)
    rank = _rank(nonzero)
    if rank == 0:
        return mask, {0: 0}
    best: int | None = None
    best_mapping: dict[int, int] | None = None
    for basis in itertools.combinations(nonzero, rank):
        if _rank(basis) != rank:
            continue
        for ordered in itertools.permutations(basis):
            coordinates: dict[int, int] = {0: 0}
            for index, vector in enumerate(ordered):
                for value, image in list(coordinates.items()):
                    coordinates[value ^ vector] = image | (1 << index)
            image = sum(1 << coordinates[point] for point in points)
            if best is None or image < best:
                best = image
                best_mapping = {point: coordinates[point] for point in points}
    if best is None or best_mapping is None:
        raise ValueError("failed to canonicalize scope")
    return best, best_mapping


def _columns(matrix: list[dict[str, int]], count: int) -> list[list[tuple[int, int]]]:
    columns = [[] for _ in range(count)]
    for row, coefficients in enumerate(matrix):
        for column, coefficient in coefficients.items():
            columns[int(column)].append((row, int(coefficient)))
    return columns


def _moment_vectors(source: dict) -> list[list[Fraction]]:
    index: dict[tuple[int, int], int] = {}
    for variable, orbit in enumerate(source["variable_orbits"]):
        scope = int(orbit["scope"])
        support = [int(value) for value in source["allowed_projection_representatives"][str(scope)]]
        for atom in orbit["atoms"]:
            index[(scope, support[int(atom)])] = variable

    def variable_for(mask: int, atom: int) -> int:
        canonical, mapping = _canonicalize(mask)
        positions = {point: i for i, point in enumerate(_points(canonical))}
        canonical_atom = 0
        for i, point in enumerate(_points(mask)):
            if atom >> i & 1:
                canonical_atom |= 1 << positions[mapping[point]]
        return index[(canonical, canonical_atom)]

    n = int(source["variable_orbit_count"])
    vectors = [[Fraction(0)] * n for _ in range(4)]
    for k in range(1, 5):
        for combination in itertools.combinations(range(1, 32), k):
            mask = sum(1 << point for point in combination)
            vectors[k - 1][variable_for(mask, (1 << k) - 1)] += 1
    return vectors


def _q_vectors(source: dict) -> tuple[list[Fraction], list[Fraction], list[Fraction]]:
    first, second, third, fourth = _moment_vectors(source)
    q1 = [first[i] * (1 - Fraction(62, 5)) + 2 * second[i]
          for i in range(len(first))]
    q2 = [-12 * first[i] + 2 * second[i] for i in range(len(first))]
    differences = [-8004, 2064, -324, 24]
    q3 = [differences[0] * first[i] + differences[1] * second[i]
          + differences[2] * third[i] + differences[3] * fourth[i]
          for i in range(len(first))]
    return q1, q2, q3


def replay(source: dict, certificate: dict) -> dict[str, object]:
    if source.get("schema") != "reed_muller_level_d_full_results_v1":
        raise ValueError("full quotient schema mismatch")
    if certificate.get("schema") != "reed_muller_sos_three_cut_results_v1":
        raise ValueError("three-cut schema mismatch")
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
    if primal_objective != Fraction("5231/801"):
        raise ValueError("primal objective mismatch")

    q1, q2, q3 = _q_vectors(source)
    cuts = {str(cut.get("name")): cut for cut in certificate.get("cuts", [])}
    names = {"square_31", "integer_adjacent_6_7", "integer_adjacent_product_6_23"}
    if set(cuts) != names:
        raise ValueError("three-cut definitions missing")
    if cuts["square_31"].get("polynomial") != "(5*t-31)^2":
        raise ValueError("square polynomial mismatch")
    if cuts["integer_adjacent_6_7"].get("polynomial") != "(t-6)*(t-7)":
        raise ValueError("second polynomial mismatch")
    if cuts["integer_adjacent_product_6_23"].get("polynomial") != "(t-6)*(t-7)*(t-23)*(t-24)":
        raise ValueError("third polynomial mismatch")
    constants = {name: Fraction(cuts[name]["q_constant"]) for name in names}
    values = {
        "square_31": sum(a * v for a, v in zip(q1, masses)) + constants["square_31"],
        "integer_adjacent_6_7": sum(a * v for a, v in zip(q2, masses)) + constants["integer_adjacent_6_7"],
        "integer_adjacent_product_6_23": sum(a * v for a, v in zip(q3, masses)) + constants["integer_adjacent_product_6_23"],
    }
    expected = {"square_31": Fraction("17392/6675"),
                "integer_adjacent_6_7": Fraction("200/89"),
                "integer_adjacent_product_6_23": Fraction(0)}
    if values != expected:
        raise ValueError("primal cut values mismatch")
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
    if basis.get("basis_column_count") != 1183 or len(indices) != 1183 or len(set(indices)) != 1183:
        raise ValueError("three-cut basis metadata mismatch")
    multipliers = {name: Fraction(cuts[name]["dual_multiplier"]) for name in names}
    if multipliers["square_31"] != 0 or multipliers["integer_adjacent_6_7"] != 0:
        raise ValueError("unexpected earlier-cut multipliers")
    if multipliers["integer_adjacent_product_6_23"] != Fraction(7, 9612):
        raise ValueError("third multiplier mismatch")
    reduced = []
    for column, entries in enumerate(_columns(matrix, n)):
        reduced.append(objective[column]
                       - sum(Fraction(coefficient) * dual[row] for row, coefficient in entries)
                       - q3[column] * multipliers["integer_adjacent_product_6_23"])
    if any(value < 0 for value in reduced):
        raise ValueError("negative reduced cost")
    minimum = min(reduced)
    if minimum != Fraction(certificate["dual_reduced_cost_minimum"]):
        raise ValueError("reduced-cost minimum mismatch")
    dual_objective = (sum(Fraction(value) * dual[row] for row, value in enumerate(rhs))
                      - constants["integer_adjacent_product_6_23"]
                      * multipliers["integer_adjacent_product_6_23"])
    if dual_objective != Fraction(certificate["dual_objective"]):
        raise ValueError("dual objective mismatch")
    lower = Fraction(certificate["certified_lower_bound"])
    upper = Fraction(certificate["certified_upper_bound"])
    gap = Fraction(certificate["unresolved_optimum_gap"])
    if lower != Fraction("5231/801") or upper != lower or dual_objective != lower or gap != 0:
        raise ValueError("invalid exact optimum")
    return {"valid": True, "source_matrix": SOURCE_PATH.name, "variable_orbits": n,
            "row_orbits": row_count, "primal_upper_bound": str(upper),
            "dual_lower_bound": str(lower), "dual_objective": str(dual_objective),
            "unresolved_gap": str(gap), "reduced_cost_minimum": str(minimum),
            "status": "EXACT_OPTIMUM",
            "scope": "Independent stdlib replay of the three-cut quotient certificate."}


def main() -> None:
    result = replay(json.loads(SOURCE_PATH.read_text(encoding="utf-8")),
                    json.loads(CERTIFICATE_PATH.read_text(encoding="utf-8")))
    REVIEW_JSON.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    REVIEW_MD.write_text(
        "# Independent three-cut SOS RM(2,5) review\n\n"
        "The pure-stdlib replay accepted the saved primal and dual certificates.\n\n"
        f"- dual lower bound: `{result['dual_lower_bound']}`\n"
        f"- primal upper bound: `{result['primal_upper_bound']}`\n"
        f"- unresolved gap: `{result['unresolved_gap']}`\n\n"
        "The result is finite and representation-specific; it does not resolve P versus NP.\n",
        encoding="utf-8")
    print("REED_MULLER_SOS_THREE_CUT_INDEPENDENT_PASS")
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
