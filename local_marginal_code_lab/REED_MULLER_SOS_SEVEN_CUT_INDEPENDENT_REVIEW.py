"""Pure-stdlib independent replay of the seven-cut RM(2,5) certificate."""
from __future__ import annotations

import itertools
import json
from fractions import Fraction
from pathlib import Path

HERE = Path(__file__).resolve().parent
SOURCE_PATH = HERE / "REED_MULLER_LEVEL_D_FULL_RESULTS.json"
CERTIFICATE_PATH = HERE / "REED_MULLER_SOS_SEVEN_CUT_RESULTS.json"
REVIEW_JSON = HERE / "REED_MULLER_SOS_SEVEN_CUT_INDEPENDENT_REVIEW.json"
REVIEW_MD = HERE / "REED_MULLER_SOS_SEVEN_CUT_INDEPENDENT_REVIEW.md"
_MOMENT_CACHE: dict[int, tuple[tuple[Fraction, ...], ...]] = {}


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


def _moment_vectors(source: dict) -> tuple[tuple[Fraction, ...], ...]:
    key = int(source["variable_orbit_count"])
    if key in _MOMENT_CACHE:
        return _MOMENT_CACHE[key]
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
    vectors = [[Fraction(0)] * n for _ in range(5)]
    for k in range(1, 6):
        for combination in itertools.combinations(range(1, 32), k):
            mask = sum(1 << point for point in combination)
            vectors[k - 1][variable_for(mask, (1 << k) - 1)] += 1
    result = tuple(tuple(vector) for vector in vectors)
    _MOMENT_CACHE[key] = result
    return result


def _q_vectors(source: dict) -> tuple[list[Fraction], ...]:
    first, second, third, fourth, fifth = _moment_vectors(source)
    q1 = [first[i] * (1 - Fraction(62, 5)) + 2 * second[i]
          for i in range(len(first))]
    q2 = [-12 * first[i] + 2 * second[i] for i in range(len(first))]
    q3 = [-8004 * first[i] + 2064 * second[i] - 324 * third[i]
          + 24 * fourth[i] for i in range(len(first))]
    q4 = [5220 * first[i] - 6960 * second[i] + 5220 * third[i]
          - 120 * fifth[i] for i in range(len(first))]
    q5 = [180 * first[i] - 244 * second[i] + 192 * third[i] - 24 * fourth[i]
          for i in range(len(first))]
    q6 = [-353148 * first[i] + 43528 * second[i] + 7212 * third[i]
          - 720 * fourth[i] - 120 * fifth[i] for i in range(len(first))]
    q7 = [-402 * first[i] + 82 * second[i] - 6 * third[i]
          for i in range(len(first))]
    return q1, q2, q3, q4, q5, q6, q7


def replay(source: dict, certificate: dict) -> dict[str, object]:
    if source.get("schema") != "reed_muller_level_d_full_results_v1":
        raise ValueError("full quotient schema mismatch")
    if certificate.get("schema") != "reed_muller_sos_seven_cut_results_v1":
        raise ValueError("seven-cut schema mismatch")
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
    if primal_objective != Fraction("35873801083/5129253893"):
        raise ValueError("primal objective mismatch")

    q1, q2, q3, q4, q5, q6, q7 = _q_vectors(source)
    cuts = {str(cut.get("name")): cut for cut in certificate.get("cuts", [])}
    names = {"square_31", "integer_adjacent_6_7",
             "integer_adjacent_product_6_23", "integer_boundary_product_3_4",
             "integer_boundary_product_3_4_core", "integer_adjacent_boundary_square_6_7",
             "integer_adjacent_boundary_product_6_7"}
    if set(cuts) != names:
        raise ValueError("seven-cut definitions missing")
    expected_polynomials = {
        "square_31": "(5*t-31)^2",
        "integer_adjacent_6_7": "(t-6)*(t-7)",
        "integer_adjacent_product_6_23": "(t-6)*(t-7)*(t-23)*(t-24)",
        "integer_boundary_product_3_4": "t*(31-t)*(t-3)*(t-4)*(t+28)",
        "integer_boundary_product_3_4_core": "t*(31-t)*(t-3)*(t-4)",
        "integer_adjacent_boundary_square_6_7": "(t-6)*(t-7)*(31-t)*(t+32)^2",
        "integer_adjacent_boundary_product_6_7": "(t-6)*(t-7)*(31-t)",
    }
    for name, polynomial in expected_polynomials.items():
        if cuts[name].get("polynomial") != polynomial:
            raise ValueError(f"{name} polynomial mismatch")
    constants = {name: Fraction(cuts[name]["q_constant"]) for name in names}
    values = {
        "square_31": sum(a * v for a, v in zip(q1, masses)) + constants["square_31"],
        "integer_adjacent_6_7": sum(a * v for a, v in zip(q2, masses)) + constants["integer_adjacent_6_7"],
        "integer_adjacent_product_6_23": sum(a * v for a, v in zip(q3, masses)) + constants["integer_adjacent_product_6_23"],
        "integer_boundary_product_3_4": sum(a * v for a, v in zip(q4, masses)) + constants["integer_boundary_product_3_4"],
        "integer_boundary_product_3_4_core": sum(a * v for a, v in zip(q5, masses)) + constants["integer_boundary_product_3_4_core"],
        "integer_adjacent_boundary_square_6_7": sum(a * v for a, v in zip(q6, masses)) + constants["integer_adjacent_boundary_square_6_7"],
        "integer_adjacent_boundary_product_6_7": sum(a * v for a, v in zip(q7, masses)) + constants["integer_adjacent_boundary_product_6_7"],
    }
    expected = {"square_31": Fraction("375250442768/128231347325"),
                "integer_adjacent_6_7": Fraction("11745880920/5129253893"),
                "integer_adjacent_product_6_23": Fraction(0),
                "integer_boundary_product_3_4": Fraction("542783746995840/5129253893"),
                "integer_boundary_product_3_4_core": Fraction("10399973492160/5129253893"),
                "integer_adjacent_boundary_square_6_7": Fraction("221990411583360/5129253893"),
                "integer_adjacent_boundary_product_6_7": Fraction(0)}
    if values != expected:
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
    if (basis.get("basis_column_count") != 2125
            or len(basis.get("basis_column_indices", [])) != 2125
            or len(set(basis.get("basis_column_indices", []))) != 2125
            or basis.get("basis_row_count") != 2123
            or len(basis.get("basis_row_indices", [])) != 2123):
        raise ValueError("seven-cut basis metadata mismatch")
    multipliers = {name: Fraction(cuts[name]["dual_multiplier"]) for name in names}
    expected_multipliers = {
        "square_31": Fraction(0),
        "integer_adjacent_6_7": Fraction(0),
        "integer_adjacent_product_6_23": Fraction("1843191/20517015572"),
        "integer_boundary_product_3_4": Fraction(0),
        "integer_boundary_product_3_4_core": Fraction(0),
        "integer_adjacent_boundary_square_6_7": Fraction(0),
        "integer_adjacent_boundary_product_6_7": Fraction("181738963/30775523358"),
    }
    if multipliers != expected_multipliers:
        raise ValueError("seven-cut multiplier mismatch")

    reduced = []
    for column, entries in enumerate(_columns(matrix, n)):
        reduced.append(objective[column]
                       - sum(Fraction(coefficient) * dual[row] for row, coefficient in entries)
                       - q1[column] * multipliers["square_31"]
                       - q2[column] * multipliers["integer_adjacent_6_7"]
                       - q3[column] * multipliers["integer_adjacent_product_6_23"]
                       - q4[column] * multipliers["integer_boundary_product_3_4"]
                       - q5[column] * multipliers["integer_boundary_product_3_4_core"]
                       - q6[column] * multipliers["integer_adjacent_boundary_square_6_7"]
                       - q7[column] * multipliers["integer_adjacent_boundary_product_6_7"])
    if any(value < 0 for value in reduced):
        raise ValueError("negative reduced cost")
    minimum = min(reduced)
    if minimum != Fraction(certificate["dual_reduced_cost_minimum"]):
        raise ValueError("reduced-cost minimum mismatch")
    if sum(value == 0 for value in reduced) != int(certificate["dual_zero_reduced_cost_count"]):
        raise ValueError("zero reduced-cost count mismatch")
    dual_objective = (sum(Fraction(value) * dual[row] for row, value in enumerate(rhs))
                      - sum(constants[name] * multipliers[name] for name in names))
    if dual_objective != Fraction(certificate["dual_objective"]):
        raise ValueError("dual objective mismatch")
    lower = Fraction(certificate["certified_lower_bound"])
    upper = Fraction(certificate["certified_upper_bound"])
    gap = Fraction(certificate["unresolved_optimum_gap"])
    if lower != Fraction("35873801083/5129253893") or upper != lower or dual_objective != lower or gap != 0:
        raise ValueError("invalid seven-cut exact optimum")
    return {"valid": True, "source_matrix": SOURCE_PATH.name,
            "variable_orbits": n, "row_orbits": row_count,
            "primal_upper_bound": str(upper), "dual_lower_bound": str(lower),
            "dual_objective": str(dual_objective), "unresolved_gap": str(gap),
            "reduced_cost_minimum": str(minimum),
            "zero_reduced_cost_count": sum(value == 0 for value in reduced),
            "status": "EXACT_OPTIMUM",
            "scope": "Independent arithmetic replay of the seven-cut quotient certificate."}


def main() -> None:
    result = replay(json.loads(SOURCE_PATH.read_text(encoding="utf-8")),
                    json.loads(CERTIFICATE_PATH.read_text(encoding="utf-8")))
    REVIEW_JSON.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    REVIEW_MD.write_text(
        "# Independent seven-cut integer-cut RM(2,5) review\n\n"
        "The pure-standard-library replay accepted the saved primal and dual certificates.\n\n"
        f"- dual lower bound: `{result['dual_lower_bound']}`\n"
        f"- primal upper bound: `{result['primal_upper_bound']}`\n"
        f"- unresolved gap: `{result['unresolved_gap']}`\n"
        f"- zero reduced costs: `{result['zero_reduced_cost_count']}`\n\n"
        "The cut is valid on the integer weight domain. This replay does not "
        "claim a bounded-degree SOS representation for it. The result is finite "
        "and representation-specific; it does not resolve P versus NP.\n",
        encoding="utf-8")
    print("REED_MULLER_SOS_SEVEN_CUT_INDEPENDENT_PASS")
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
