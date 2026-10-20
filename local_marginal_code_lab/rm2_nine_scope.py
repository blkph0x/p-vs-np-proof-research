"""Source-built affine RM(2,5) quotient plus one exact nine-point table.

This finite LP is necessary for a GL(5,2)-invariant full level-nine solution;
it is not the full level-nine LP.  In addition to the original selected-flat
model, it contains a supported table on points 16,...,24.  Every nonempty
subset whose affine closure has at most eight points has its table moment
matched to the original selected-flat table on that closure.  The closure
may contain points outside the nine-point scope.

No saved solution, basis, objective value, or result artifact is read.
The 15 nonconstant quadratic monomials generate the exact pinned projection.
At most 512 projected atoms and 511 moment subsets are considered explicitly.
The existing base quotient construction is a separate finite enumeration.
"""
from __future__ import annotations

from collections import Counter
import importlib.util
from itertools import combinations
from pathlib import Path
import sys


SCOPE = tuple(range(16, 25))
NAME = "rm25_affine_plus_nine_scope"


def _exporter():
    path = Path(__file__).resolve().with_name("exact_lp_model.py")
    name = "_rm2_nine_scope_exact_lp_model"
    if name in sys.modules:
        module = sys.modules[name]
        if Path(module.__file__).resolve() != path:
            raise RuntimeError("exact LP exporter module path collision")
        return module
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load the exact LP exporter")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    try:
        spec.loader.exec_module(module)
    except BaseException:
        del sys.modules[name]
        raise
    return module


def _points(points):
    if type(points) not in (list, tuple):
        raise ValueError("points must be a list or tuple")
    if any(type(point) is not int or not 0 <= point < 32 for point in points):
        raise ValueError("points must be distinct five-bit integers")
    if len(set(points)) != len(points):
        raise ValueError("points must be distinct")
    return tuple(points)


def affine_closure(points) -> tuple[int, ...]:
    """Return the affine span of distinct explicitly supplied RM(2,5) points."""
    points = _points(points)
    if not points:
        return ()
    anchor = points[0]
    span = {0}
    for point in points[1:]:
        direction = point ^ anchor
        span.update(tuple(value ^ direction for value in span))
    return tuple(sorted(anchor ^ value for value in span))


def projected_atoms(scope) -> tuple[tuple[int, ...], tuple[int, ...]]:
    """Return exact pin-zero-equals-one support and its nonconstant generators.

    Local atom bit i is the value at scope[i].  The constant polynomial is
    fixed to one; every linear and quadratic coefficient is free over GF(2).
    This helper is bounded to at most nine five-bit coordinate points.
    """
    scope = _points(scope)
    if len(scope) > 9:
        raise ValueError("this finite projection helper supports at most nine points")
    generators = []
    for first in range(5):
        generators.append(sum(((point >> first) & 1) << i
                              for i, point in enumerate(scope)))
    for first, second in combinations(range(5), 2):
        generators.append(sum((((point >> first) & 1) & ((point >> second) & 1)) << i
                              for i, point in enumerate(scope)))
    span = {0}
    for generator in generators:
        span.update(tuple(value ^ generator for value in span))
    constant = (1 << len(scope)) - 1
    return tuple(sorted(constant ^ value for value in span)), tuple(generators)


def moment_form(source: dict, points) -> tuple[tuple[int, ...], dict[int, int]]:
    """Reconstruct a moment from the original atom-to-orbit map.

    A quotient variable is a common per-atom mass.  Consequently repeated
    atoms from one orbit contribute their multiplicity, not one total orbit
    mass.  No quotient variable index is assumed in advance.
    """
    points = _points(points)
    if not points:
        raise ValueError("empty moment is represented separately by normalization")
    closure = affine_closure(points)
    if len(closure) not in (1, 2, 4, 8):
        raise ValueError("moment needs an affine closure of dimension at most three")
    positions = {point: i for i, point in enumerate(closure)}
    required = sum(1 << positions[point] for point in points)
    coefficients = Counter()
    for original_variable in source["variables"][closure]:
        original_scope, atom = source["variable_keys"][original_variable]
        if original_scope != closure:
            raise ValueError("base variable scope mapping is inconsistent")
        if atom & required == required:
            coefficients[source["variable_orbit_of"][original_variable]] += 1
    return closure, dict(sorted(coefficients.items()))


def build_details() -> dict:
    """Build the canonical model and explanatory source-derived row metadata.

    Base rows and columns retain their original order.  New columns follow
    increasing supported local atom masks.  Appended rows consist of table
    normalization followed by eligible subset masks 1,...,511 in that order.
    Neither the metadata nor this producer substitutes for independent model
    reconstruction and primal/dual verification.
    """
    exporter = _exporter()
    source = exporter._load_sibling("reed_muller_affine_overlap.py").build_quotient()
    base_variables = len(source["objective"])
    base_rows = len(source["matrix"])
    atoms, generators = projected_atoms(SCOPE)
    matrix = [dict(row) for row in source["matrix"]]
    rhs = list(source["rhs"])
    objective = list(source["objective"]) + [0] * len(atoms)
    normalization_row = len(matrix)
    matrix.append({base_variables + i: 1 for i in range(len(atoms))})
    rhs.append(1)
    moment_rows = []
    for subset_mask in range(1, 1 << len(SCOPE)):
        points = tuple(point for i, point in enumerate(SCOPE) if subset_mask >> i & 1)
        closure = affine_closure(points)
        if len(closure) > 8:
            continue
        closure, form = moment_form(source, points)
        row = {column: -coefficient for column, coefficient in form.items()}
        for i, atom in enumerate(atoms):
            if atom & subset_mask == subset_mask:
                row[base_variables + i] = 1
        row_index = len(matrix)
        matrix.append(row)
        rhs.append(0)
        moment_rows.append({
            "row_index": row_index,
            "subset_mask": subset_mask,
            "points": list(points),
            "affine_closure": list(closure),
            "base_moment": {str(column): coefficient for column, coefficient in form.items()},
        })
    moments = {}
    for name, points in (("p", (1,)), ("q", (1, 2)), ("r", (1, 2, 4))):
        closure, form = moment_form(source, points)
        moments[name] = {
            "points": list(points), "affine_closure": list(closure),
            "coefficients": {str(column): value for column, value in form.items()},
        }
    model = exporter._from_matrix(NAME, matrix, rhs, objective)
    return {
        "model": model,
        "scope": list(SCOPE),
        "allowed_atoms": list(atoms),
        "projection_generator_rows": list(generators),
        "base_variable_count": base_variables,
        "base_row_count": base_rows,
        "normalization_row": normalization_row,
        "moment_rows": moment_rows,
        "representative_moments": moments,
    }


def build_model() -> dict:
    """Return only the canonical exact-equality-lp-v1 model."""
    return build_details()["model"]
