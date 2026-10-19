"""Exact symmetry quotient for an affine-overlap RM(2,5) local model.

The selected scopes are every affine 3-flat (8 points), every affine 2-flat
(4 points), every affine line (2 points), and every singleton in F_2^5.  A
table on each scope is supported on the pinned RM(2,5) projection, and tables
are required to agree on every selected containment edge.  The model is a
finite submodel of the full level-8 projection relaxation: every full-level
feasible point projects to it.

The quotient is exact because GL(5,2) fixes the pinned point and preserves
RM(2,5).  Averaging any feasible point over this group gives an invariant
feasible point with the same objective.  This module builds the orbit model
with only the Python standard library; the saved certificate supplies exact
rational primal and dual values.
"""

from __future__ import annotations

from collections import Counter
from fractions import Fraction
from itertools import combinations

N = 32
PIN = 0


def rank(vectors: tuple[int, ...]) -> int:
    basis: list[int] = []
    for value in vectors:
        value = int(value)
        for pivot in basis:
            value = min(value, value ^ pivot)
        if value:
            basis.append(value)
            basis.sort(reverse=True)
    return len(basis)


def span_mask(vectors: tuple[int, ...]) -> int:
    values = [0]
    for vector in vectors:
        values += [value ^ vector for value in tuple(values)]
    return sum(1 << value for value in values)


def affine_scopes(dimension: int) -> tuple[tuple[int, ...], ...]:
    linear: set[int] = set()
    for candidate in combinations(range(1, N), dimension):
        if rank(candidate) == dimension:
            linear.add(span_mask(candidate))
    scopes: set[tuple[int, ...]] = set()
    for subspace in linear:
        points = [point for point in range(N) if subspace >> point & 1]
        seen: set[int] = set()
        for offset in range(N):
            if offset in seen:
                continue
            coset = tuple(sorted(offset ^ point for point in points))
            scopes.add(coset)
            seen.update(coset)
    return tuple(sorted(scopes))


def scope_atoms(scope: tuple[int, ...]) -> tuple[int, ...]:
    size = len(scope)
    if size == 8:
        if PIN in scope:
            pin_index = scope.index(PIN)
            return tuple(
                atom for atom in range(1 << size)
                if atom >> pin_index & 1 and atom.bit_count() % 2 == 0
            )
        return tuple(atom for atom in range(1 << size) if atom.bit_count() % 2 == 0)
    if PIN in scope:
        pin_index = scope.index(PIN)
        return tuple(atom for atom in range(1 << size) if atom >> pin_index & 1)
    return tuple(range(1 << size))


def generators() -> tuple[tuple[int, ...], ...]:
    result = []
    for first, second in combinations(range(5), 2):
        result.append(tuple(
            (point & ~(1 << first | 1 << second))
            | (((point >> first) & 1) << second)
            | (((point >> second) & 1) << first)
            for point in range(N)
        ))
    for source in range(5):
        for target in range(5):
            if source == target:
                continue
            result.append(tuple(
                point ^ (((point >> source) & 1) << target)
                for point in range(N)
            ))
    return tuple(result)


def map_atom(scope: tuple[int, ...], atom: int, generator: tuple[int, ...]):
    mapped_scope = tuple(sorted(generator[point] for point in scope))
    positions = {point: index for index, point in enumerate(mapped_scope)}
    mapped_atom = 0
    for index, point in enumerate(scope):
        if atom >> index & 1:
            mapped_atom |= 1 << positions[generator[point]]
    return mapped_scope, mapped_atom


def _orbits(items, move, group):
    item_index = {item: index for index, item in enumerate(items)}
    orbit_of = [-1] * len(items)
    orbits: list[tuple[int, ...]] = []
    for seed in range(len(items)):
        if orbit_of[seed] >= 0:
            continue
        orbit_id = len(orbits)
        pending = [seed]
        orbit_of[seed] = orbit_id
        members = []
        while pending:
            index = pending.pop()
            members.append(index)
            for generator in group:
                image = item_index[move(items[index], generator)]
                if orbit_of[image] < 0:
                    orbit_of[image] = orbit_id
                    pending.append(image)
        orbits.append(tuple(members))
    return orbit_of, tuple(orbits)


def build_quotient() -> dict:
    scopes = {
        8: affine_scopes(3),
        4: affine_scopes(2),
        2: affine_scopes(1),
        1: tuple((point,) for point in range(N)),
    }
    atoms = {scope: scope_atoms(scope) for values in scopes.values() for scope in values}
    variable_keys = []
    variables: dict[tuple[int, ...], tuple[int, ...]] = {}
    variable_index = {}
    for size in (8, 4, 2, 1):
        for scope in scopes[size]:
            indices = []
            for atom in atoms[scope]:
                index = len(variable_keys)
                indices.append(index)
                variable_keys.append((scope, atom))
                variable_index[(scope, atom)] = index
            variables[scope] = tuple(indices)
    group = generators()

    def move_variable(item, generator):
        scope, atom = item
        return map_atom(scope, atom, generator)

    variable_orbit_of, variable_orbits = _orbits(variable_keys, move_variable, group)

    rows = []
    for size in (8, 4, 2, 1):
        rows.extend(("normalization", scope) for scope in scopes[size])
    for parent_size, child_size in ((8, 4), (8, 2), (8, 1), (4, 2), (4, 1), (2, 1)):
        for parent in scopes[parent_size]:
            parent_points = set(parent)
            for child in scopes[child_size]:
                if not set(child).issubset(parent_points):
                    continue
                rows.extend(("consistency", parent, child, atom) for atom in atoms[child])
    row_index = {row: index for index, row in enumerate(rows)}

    def move_row(row, generator):
        if row[0] == "normalization":
            return (row[0], tuple(sorted(generator[point] for point in row[1])))
        _, parent, child, atom = row
        mapped_parent = tuple(sorted(generator[point] for point in parent))
        mapped_child, mapped_atom = map_atom(child, atom, generator)
        return (row[0], mapped_parent, mapped_child, mapped_atom)

    row_orbit_of, row_orbits = _orbits(rows, move_row, group)
    matrix: list[dict[int, int]] = []
    rhs: list[Fraction] = []
    row_representatives = []
    child_atom_index = {scope: {atom: i for i, atom in enumerate(values)} for scope, values in atoms.items()}
    for orbit in row_orbits:
        row = rows[orbit[0]]
        row_representatives.append(row)
        coefficients: Counter[int] = Counter()
        if row[0] == "normalization":
            for variable in variables[row[1]]:
                coefficients[variable_orbit_of[variable]] += 1
            rhs.append(Fraction(1))
        else:
            _, parent, child, child_atom = row
            positions = {point: index for index, point in enumerate(parent)}
            for parent_atom, variable in zip(atoms[parent], variables[parent]):
                projected = sum(
                    ((parent_atom >> positions[point]) & 1) << index
                    for index, point in enumerate(child)
                )
                if projected == child_atom:
                    coefficients[variable_orbit_of[variable]] += 1
            child_variable = variables[child][child_atom_index[child][child_atom]]
            coefficients[variable_orbit_of[child_variable]] -= 1
            rhs.append(Fraction(0))
        matrix.append(dict(coefficients))

    objective = [Fraction(0)] * len(variable_orbits)
    for scope in scopes[1]:
        if scope[0] != PIN:
            objective[variable_orbit_of[variables[scope][1]]] += 1
    return {
        "scopes": scopes,
        "atoms": atoms,
        "variables": variables,
        "variable_keys": variable_keys,
        "variable_orbit_of": variable_orbit_of,
        "variable_orbits": variable_orbits,
        "rows": rows,
        "row_orbit_of": row_orbit_of,
        "row_orbits": row_orbits,
        "row_representatives": row_representatives,
        "matrix": matrix,
        "rhs": rhs,
        "objective": objective,
        "affine_flat_span_rank": rank(tuple(sum(1 << point for point in scope) for scope in scopes[8])),
    }


def dot_row(row: dict[int, int], vector: list[Fraction]) -> Fraction:
    return sum(Fraction(coefficient) * vector[index] for index, coefficient in row.items())


def exact_certificate_values() -> tuple[list[Fraction], list[Fraction]]:
    primal = [Fraction(0)] * 28
    for index, value in {
        0: Fraction(4, 35), 1: Fraction(1, 35), 5: Fraction(1, 5),
        6: Fraction(1, 35), 11: Fraction(16, 35), 12: Fraction(6, 35),
        14: Fraction(1, 35), 15: Fraction(13, 35), 16: Fraction(4, 35),
        17: Fraction(1, 35), 20: Fraction(4, 5), 21: Fraction(1, 5),
        22: Fraction(22, 35), 23: Fraction(6, 35), 24: Fraction(1, 35),
        25: Fraction(1), 26: Fraction(4, 5), 27: Fraction(1, 5),
    }.items():
        primal[index] = value
    dual = [Fraction(0)] * 53
    for index, value in {
        5: Fraction(-124, 5), 7: Fraction(31), 9: Fraction(-248, 5),
        10: Fraction(-248, 5), 12: Fraction(-124, 5), 13: Fraction(-62),
        16: Fraction(-124, 5), 17: Fraction(124, 5), 18: Fraction(62),
        19: Fraction(-124, 5), 20: Fraction(-248, 5), 27: Fraction(-124, 5),
        31: Fraction(31), 38: Fraction(-248, 5), 42: Fraction(-124, 5),
    }.items():
        dual[index] = value
    return primal, dual


def verify_quotient(model: dict, primal: list[Fraction], dual: list[Fraction]) -> dict:
    if len(primal) != len(model["variable_orbits"]):
        raise ValueError("primal orbit length mismatch")
    if len(dual) != len(model["row_orbits"]):
        raise ValueError("dual orbit length mismatch")
    if any(value < 0 for value in primal):
        raise ValueError("negative primal mass")
    for row, expected in zip(model["matrix"], model["rhs"]):
        if dot_row(row, primal) != expected:
            raise ValueError("primal consistency failure")
    reduced = [
        model["objective"][index]
        - sum(Fraction(row.get(index, 0)) * dual[row_index] for row_index, row in enumerate(model["matrix"]))
        for index in range(len(model["variable_orbits"]))
    ]
    if any(value < 0 for value in reduced):
        raise ValueError("dual reduced-cost failure")
    primal_value = sum(coefficient * value for coefficient, value in zip(model["objective"], primal))
    dual_value = sum(value * rhs for value, rhs in zip(dual, model["rhs"]))
    if primal_value != Fraction(31, 5) or dual_value != primal_value:
        raise ValueError("objective mismatch")
    return {
        "valid": True,
        "variable_orbits": len(model["variable_orbits"]),
        "row_orbits": len(model["row_orbits"]),
        "selected_model_optimum": str(primal_value),
        "dual_reduced_cost_minimum": str(min(reduced)),
        "full_level_8_status": "UNRESOLVED",
    }
