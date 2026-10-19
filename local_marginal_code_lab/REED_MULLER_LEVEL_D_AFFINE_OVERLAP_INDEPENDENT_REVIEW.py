"""Independent pure-stdlib replay of the affine-overlap RM(2,5) certificate."""

from __future__ import annotations

import json
from collections import Counter
from fractions import Fraction
from itertools import combinations
from pathlib import Path

HERE = Path(__file__).resolve().parent
N = 32
PIN = 0


def _rank(values):
    pivots = []
    for value in values:
        value = int(value)
        for pivot in pivots:
            value = min(value, value ^ pivot)
        if value:
            pivots.append(value)
            pivots.sort(reverse=True)
    return len(pivots)


def _subspace(basis):
    points = {0}
    for vector in basis:
        points |= {point ^ vector for point in tuple(points)}
    return frozenset(points)


def _affine_sets(dimension):
    linear = {_subspace(candidate) for candidate in combinations(range(1, N), dimension)
              if _rank(candidate) == dimension}
    result = set()
    for subspace in linear:
        remaining = set(range(N))
        while remaining:
            offset = min(remaining)
            coset = tuple(sorted(offset ^ point for point in subspace))
            result.add(coset)
            remaining.difference_update(coset)
    return tuple(sorted(result))


def _allowed(scope):
    size = len(scope)
    if size == 8:
        if PIN in scope:
            pin_index = scope.index(PIN)
            return tuple(atom for atom in range(256)
                         if atom >> pin_index & 1 and atom.bit_count() % 2 == 0)
        return tuple(atom for atom in range(256) if atom.bit_count() % 2 == 0)
    if PIN in scope:
        pin_index = scope.index(PIN)
        return tuple(atom for atom in range(1 << size) if atom >> pin_index & 1)
    return tuple(range(1 << size))


def _group():
    maps = []
    for first, second in combinations(range(5), 2):
        maps.append(tuple(
            (point & ~(1 << first | 1 << second))
            | (((point >> first) & 1) << second)
            | (((point >> second) & 1) << first)
            for point in range(N)))
    for source in range(5):
        for target in range(5):
            if source != target:
                maps.append(tuple(point ^ (((point >> source) & 1) << target)
                                  for point in range(N)))
    return tuple(maps)


def _move_assignment(scope, atom, mapping):
    image = tuple(sorted(mapping[point] for point in scope))
    positions = {point: index for index, point in enumerate(image)}
    mapped_atom = 0
    for index, point in enumerate(scope):
        if atom >> index & 1:
            mapped_atom |= 1 << positions[mapping[point]]
    return image, mapped_atom


def _orbit_partition(items, move, group):
    index = {item: number for number, item in enumerate(items)}
    orbit_of = [-1] * len(items)
    orbits = []
    for seed in range(len(items)):
        if orbit_of[seed] >= 0:
            continue
        orbit_id = len(orbits)
        pending = [seed]
        orbit_of[seed] = orbit_id
        members = []
        while pending:
            number = pending.pop()
            members.append(number)
            for mapping in group:
                image = index[move(items[number], mapping)]
                if orbit_of[image] < 0:
                    orbit_of[image] = orbit_id
                    pending.append(image)
        orbits.append(tuple(members))
    return orbit_of, tuple(orbits)


def _rebuild():
    scopes = {8: _affine_sets(3), 4: _affine_sets(2), 2: _affine_sets(1),
              1: tuple((point,) for point in range(N))}
    allowed = {scope: _allowed(scope) for family in scopes.values() for scope in family}
    variables = {}
    variable_keys = []
    variable_index = {}
    for size in (8, 4, 2, 1):
        for scope in scopes[size]:
            ids = []
            for atom in allowed[scope]:
                variable_index[(scope, atom)] = len(variable_keys)
                ids.append(len(variable_keys))
                variable_keys.append((scope, atom))
            variables[scope] = tuple(ids)
    group = _group()
    var_orbit_of, var_orbits = _orbit_partition(
        variable_keys, lambda item, mapping: _move_assignment(*item, mapping), group)
    rows = []
    for size in (8, 4, 2, 1):
        rows.extend(("normalization", scope) for scope in scopes[size])
    for parent_size, child_size in ((8, 4), (8, 2), (8, 1), (4, 2), (4, 1), (2, 1)):
        for parent in scopes[parent_size]:
            for child in scopes[child_size]:
                if set(child).issubset(parent):
                    rows.extend(("consistency", parent, child, atom) for atom in allowed[child])
    row_index = {row: number for number, row in enumerate(rows)}

    def move_row(row, mapping):
        if row[0] == "normalization":
            return (row[0], tuple(sorted(mapping[point] for point in row[1])))
        _, parent, child, atom = row
        image_parent = tuple(sorted(mapping[point] for point in parent))
        image_child, image_atom = _move_assignment(child, atom, mapping)
        return row[0], image_parent, image_child, image_atom

    row_orbit_of, row_orbits = _orbit_partition(rows, move_row, group)
    atom_indices = {scope: {atom: index for index, atom in enumerate(values)}
                    for scope, values in allowed.items()}
    matrix = []
    rhs = []
    representatives = []
    for orbit in row_orbits:
        row = rows[orbit[0]]
        representatives.append(row)
        coefficients = Counter()
        if row[0] == "normalization":
            for variable in variables[row[1]]:
                coefficients[var_orbit_of[variable]] += 1
            rhs.append(Fraction(1))
        else:
            _, parent, child, child_atom = row
            positions = {point: index for index, point in enumerate(parent)}
            for parent_atom, variable in zip(allowed[parent], variables[parent]):
                projected = sum(((parent_atom >> positions[point]) & 1) << index
                                for index, point in enumerate(child))
                if projected == child_atom:
                    coefficients[var_orbit_of[variable]] += 1
            child_variable = variables[child][atom_indices[child][child_atom]]
            coefficients[var_orbit_of[child_variable]] -= 1
            rhs.append(Fraction(0))
        matrix.append(dict(coefficients))
    objective = [Fraction(0)] * len(var_orbits)
    for scope in scopes[1]:
        if scope[0] != PIN:
            objective[var_orbit_of[variables[scope][1]]] += 1
    flat_rows = [sum(1 << point for point in scope) for scope in scopes[8]]
    pivots = []
    for value in flat_rows:
        for pivot in pivots:
            value = min(value, value ^ pivot)
        if value:
            pivots.append(value)
            pivots.sort(reverse=True)
    return scopes, allowed, variable_keys, var_orbits, representatives, row_orbits, matrix, rhs, objective, len(pivots)


def _row_json(row):
    if row[0] == "normalization":
        return {"kind": "normalization", "scope": list(row[1])}
    return {"kind": "consistency", "parent": list(row[1]), "child": list(row[2]),
            "child_atom": row[3]}


def replay(certificate, model=None):
    if certificate.get("schema") != "reed_muller_level_d_affine_overlap_results_v1":
        raise ValueError("schema mismatch")
    if certificate.get("family") != "RM(2,5)" or certificate.get("pin") != 0:
        raise ValueError("family or pin mismatch")
    if certificate.get("selected_scope_sizes") != [8, 4, 2, 1]:
        raise ValueError("scope selection mismatch")
    scopes, allowed, variable_keys, var_orbits, row_reps, row_orbits, matrix, rhs, objective, flat_rank = model or _rebuild()
    if certificate.get("scope_counts") != {str(size): len(scopes[size]) for size in (8, 4, 2, 1)}:
        raise ValueError("scope count mismatch")
    if certificate.get("variable_orbit_count") != len(var_orbits) or certificate.get("row_orbit_count") != len(row_orbits):
        raise ValueError("orbit count mismatch")
    if certificate.get("affine_flat_span_rank") != flat_rank or flat_rank != 16:
        raise ValueError("affine-flat span rank mismatch")
    expected_vars = [
        {"representative_scope": list(variable_keys[orbit[0]][0]),
         "representative_atom": variable_keys[orbit[0]][1], "orbit_size": len(orbit)}
        for orbit in var_orbits
    ]
    saved_vars = [{key: row[key] for key in ("representative_scope", "representative_atom", "orbit_size")}
                  for row in certificate.get("variable_orbits", [])]
    if saved_vars != expected_vars:
        raise ValueError("variable orbit representatives mismatch")
    expected_rows = [{"representative": _row_json(row), "orbit_size": len(orbit)}
                     for row, orbit in zip(row_reps, row_orbits)]
    if certificate.get("row_orbits") != expected_rows:
        raise ValueError("row orbit representatives mismatch")
    expected_matrix = [{str(index): coefficient for index, coefficient in sorted(row.items())}
                       for row in matrix]
    if certificate.get("quotient_matrix") != expected_matrix:
        raise ValueError("quotient matrix mismatch")
    parse = lambda values: [Fraction(value) for value in values]
    saved_rhs, saved_objective = parse(certificate["rhs"]), parse(certificate["objective"])
    if saved_rhs != rhs or saved_objective != objective:
        raise ValueError("linear-program data mismatch")
    primal, dual = parse(certificate["primal_orbit_masses"]), parse(certificate["dual_row_values"])
    if len(primal) != len(var_orbits) or len(dual) != len(row_orbits):
        raise ValueError("solution vector length mismatch")
    if any(value < 0 for value in primal):
        raise ValueError("negative primal mass")
    for row, target in zip(matrix, rhs):
        if sum(Fraction(coefficient) * primal[index] for index, coefficient in row.items()) != target:
            raise ValueError("primal equation mismatch")
    reduced = [saved_objective[index] - sum(Fraction(row.get(index, 0)) * dual[row_index]
                                            for row_index, row in enumerate(matrix))
               for index in range(len(var_orbits))]
    if any(value < 0 for value in reduced):
        raise ValueError("negative reduced cost")
    primal_value = sum(coefficient * value for coefficient, value in zip(saved_objective, primal))
    dual_value = sum(value * target for value, target in zip(dual, rhs))
    if primal_value != Fraction(31, 5) or dual_value != primal_value:
        raise ValueError("objective mismatch")
    if certificate.get("selected_model_optimum") != "31/5":
        raise ValueError("selected optimum claim mismatch")
    if certificate.get("integer_pinned_optimum") != "8":
        raise ValueError("integer optimum claim mismatch")
    if certificate.get("selected_model_integrality_ratio") != "40/31":
        raise ValueError("ratio claim mismatch")
    if certificate.get("full_level_8_lower_bound") != "31/5":
        raise ValueError("full-level lower bound mismatch")
    if certificate.get("full_level_8_status") != "UNRESOLVED":
        raise ValueError("full-level status must remain unresolved")
    return {"valid": True, "scope_counts": {str(size): len(scopes[size]) for size in (8, 4, 2, 1)},
            "variable_orbits": len(var_orbits), "row_orbits": len(row_orbits),
            "selected_model_optimum": "31/5", "dual_reduced_cost_minimum": str(min(reduced)),
            "full_level_8_lower_bound": "31/5", "full_level_8_status": "UNRESOLVED"}


def main():
    source = HERE / "REED_MULLER_LEVEL_D_AFFINE_OVERLAP_RESULTS.json"
    payload = json.loads(source.read_text(encoding="utf-8"))
    verification = replay(payload)
    (HERE / "REED_MULLER_LEVEL_D_AFFINE_OVERLAP_INDEPENDENT_REVIEW.json").write_text(
        json.dumps({"schema": "reed_muller_level_d_affine_overlap_independent_review_v1",
                    "verification": verification}, indent=2, sort_keys=True) + "\n",
        encoding="utf-8")
    (HERE / "REED_MULLER_LEVEL_D_AFFINE_OVERLAP_INDEPENDENT_REVIEW.md").write_text(
        "# Independent affine-overlap replay\n\n"
        "The pure-standard-library replay rebuilds the finite-geometry scope sets, "
        "GL(5,2) orbit quotient, affine-flat span rank, exact rational primal witness, and dual reduced-cost "
        "certificate. It verifies the selected-model optimum `31/5`. The selected-"
        "model record does not itself certify arbitrary scopes; the later full"
        " level-eight replay closes that separate finite model.\n",
        encoding="utf-8")
    print("REED_MULLER_AFFINE_OVERLAP_INDEPENDENT_PASS")
    print(json.dumps(verification, sort_keys=True))


if __name__ == "__main__":
    main()
