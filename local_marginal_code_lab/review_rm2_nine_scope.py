"""Independent source binding for the selected RM(2,5) nine-scope LP.

Imports neither the nine-scope producer nor its LP exporter/solver. The base
geometry comes from the existing independent reconstruction. New projection
atoms are obtained by evaluating all 2^15 pinned quadratic polynomials, not
by reading a producer support list or using the dual-flat classification.

An optimum certified here is an optimum of the named finite selected model.
It supplies a lower bound for full L9; full-L9 feasibility needs a separate
construction. The intermediate one-cut model is checked separately.
"""
from __future__ import annotations

import argparse
from collections import Counter
from functools import lru_cache
import json
from pathlib import Path

from exact_lp_verify import model_digest, verify_solution


SCOPE = tuple(range(16, 25))
NINE_NAME = "rm25_affine_plus_nine_scope"
CUT_NAME = "rm25_affine_overlap_nine_point_cut"


def _require(condition, message):
    if not condition:
        raise ValueError(message)


def _json(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"))


def _points(points, *, maximum=9):
    _require(type(points) in (list, tuple) and len(points) <= maximum,
             "scope must be a bounded explicit point sequence")
    _require(all(type(point) is int and 0 <= point < 32 for point in points),
             "points must be exact integers in GF(2)^5")
    _require(len(set(points)) == len(points), "repeated point")
    return tuple(points)


def affine_closure(points):
    """Compute the affine span from translations, preserving original points."""
    points = _points(points)
    if not points:
        return ()
    origin = min(points)
    direction = {0}
    for point in points:
        difference = point ^ origin
        direction.update(value ^ difference for value in tuple(direction))
    return tuple(sorted(origin ^ value for value in direction))


@lru_cache(maxsize=64)
def _pinned_atoms(scope):
    # Pinning evaluation at zero to one fixes exactly the constant coefficient.
    # Enumerate every setting of the other five linear and ten quadratic bits.
    evaluations = []
    for coordinate in range(5):
        evaluations.append(sum(((point >> coordinate) & 1) << index
                               for index, point in enumerate(scope)))
    for first in range(5):
        for second in range(first + 1, 5):
            evaluations.append(sum((((point >> first) & (point >> second)) & 1) << index
                                   for index, point in enumerate(scope)))
    seen = set()
    all_ones = (1 << len(scope)) - 1
    for coefficients in range(1 << len(evaluations)):
        atom = all_ones
        pending = coefficients
        while pending:
            bit = pending & -pending
            atom ^= evaluations[bit.bit_length() - 1]
            pending ^= bit
        seen.add(atom)
    return tuple(sorted(seen))


def pinned_projection_atoms(points):
    """All exact restrictions of pinned RM(2,5), by polynomial evaluation."""
    return _pinned_atoms(_points(points))


@lru_cache(maxsize=1)
def _base():
    from REED_MULLER_LEVEL_D_AFFINE_OVERLAP_INDEPENDENT_REVIEW import _rebuild

    scopes, allowed, keys, orbits, _, row_orbits, matrix, rhs, objective, rank = _rebuild()
    _require({size: len(values) for size, values in scopes.items()} ==
             {8: 620, 4: 1240, 2: 496, 1: 32}, "base scope coverage")
    _require(len(orbits) == 28 and len(row_orbits) == 53 and rank == 16,
             "base quotient dimensions/rank")
    var_for = {}
    for orbit_id, orbit in enumerate(orbits):
        for original_id in orbit:
            key = keys[original_id]
            _require(key not in var_for, "duplicate base orbit ownership")
            var_for[key] = orbit_id
    _require(len(var_for) == len(keys), "missing base orbit ownership")
    # Private cached data are never returned to a caller.
    return allowed, var_for, matrix, rhs, objective


def _model(name, rows, rhs, objective):
    return {
        "schema": "exact-equality-lp-v1", "name": name,
        "variable_ids": [f"x{i:06d}" for i in range(len(objective))],
        "row_ids": [f"r{i:06d}" for i in range(len(rows))],
        "rows": [{str(column): str(value) for column, value in row.items() if value}
                 for row in rows],
        "rhs": [str(value) for value in rhs],
        "objective": [str(value) for value in objective],
        "objective_offset": "1",
    }


def _moment(points, allowed, var_for):
    points = _points(points)
    _require(bool(points), "empty moment uses normalization instead")
    closure = affine_closure(points)
    _require(len(closure) <= 8 and closure in allowed, "moment is not selected-flat readable")
    selected = sum(1 << closure.index(point) for point in points)
    coefficients = Counter()
    for atom in allowed[closure]:
        if atom & selected == selected:
            coefficients[var_for[(closure, atom)]] += 1
    return dict(coefficients), closure


def base_moment(points):
    """Return a fresh orbit coefficient map derived from original scope atoms."""
    allowed, var_for, _, _, _ = _base()
    coefficients, closure = _moment(points, allowed, var_for)
    return {"coefficients": coefficients, "closure": closure}


@lru_cache(maxsize=1)
def _nine_json():
    allowed, var_for, matrix, rhs, objective = _base()
    atoms = pinned_projection_atoms(SCOPE)
    rows = [dict(row) for row in matrix]
    targets = list(rhs)
    costs = list(objective)
    first_new = len(costs)
    costs.extend([0] * len(atoms))
    normalization_row = len(rows)
    rows.append({first_new + index: 1 for index in range(len(atoms))})
    targets.append(1)
    metadata = []
    for mask in range(1, 1 << len(SCOPE)):
        points = tuple(point for index, point in enumerate(SCOPE) if mask >> index & 1)
        if len(affine_closure(points)) > 8:
            continue
        moment, closure = _moment(points, allowed, var_for)
        row = Counter({first_new + index: 1 for index, atom in enumerate(atoms)
                       if atom & mask == mask})
        for column, coefficient in moment.items():
            row[column] -= coefficient
        metadata.append({"mask": mask, "points": list(points), "closure": list(closure),
                         "row_index": len(rows)})
        rows.append({column: coefficient for column, coefficient in row.items() if coefficient})
        targets.append(0)
    model = _model(NINE_NAME, rows, targets, costs)
    model_digest(model)  # Independent strict schema validation.
    return _json({
        "model": model, "scope": list(SCOPE), "allowed_atoms": list(atoms),
        "base_variables": first_new, "base_rows": len(matrix),
        "normalization_row": normalization_row, "moment_rows": metadata,
    })


def rebuild_details():
    """Return fresh data, so caller mutation cannot poison the reconstruction."""
    return json.loads(_nine_json())


def rebuild_model():
    return rebuild_details()["model"]


@lru_cache(maxsize=1)
def _cut_json():
    allowed, var_for, matrix, rhs, objective = _base()
    cut = Counter()
    for multiplier, points in ((1, (1,)), (-8, (1, 2)), (28, (1, 2, 4))):
        moment, _ = _moment(points, allowed, var_for)
        for column, value in moment.items():
            cut[column] += multiplier * value
    # The slack sign matters: Gx-s=0, so its dual reduced cost is +lambda.
    cut[len(objective)] = -1
    model = _model(CUT_NAME, [dict(row) for row in matrix] + [dict(cut)],
                   list(rhs) + [0], list(objective) + [0])
    model_digest(model)
    return _json(model)


def rebuild_nine_point_cut_model():
    return json.loads(_cut_json())


def _replay(model, certificate, expected, scope):
    try:
        model_digest(model)
        _require(_json(model) == expected(),
                 "model differs from independently rebuilt " + scope)
        result = verify_solution(model, certificate)
        if result["valid"]:
            result["scope"] = scope
            result["source_binding"] = (
                "independent affine geometry/orbit reconstruction and original point/atom moments")
            result["full_L9_upper_bound"] = "NOT_ESTABLISHED_BY_THIS_CERTIFICATE"
        return result
    except (TypeError, ValueError, KeyError, OverflowError) as exc:
        return {"valid": False, "status": "INVALID", "errors": [str(exc)]}


def replay_nine_scope(model, certificate):
    return _replay(model, certificate, lambda: _json(rebuild_model()),
                   "RM(2,5) selected affine scopes plus one nine-coordinate scope")


def replay_nine_point_cut(model, certificate):
    return _replay(model, certificate, _cut_json,
                   "RM(2,5) selected affine scopes plus the necessary nine-point moment cut")


replay = replay_nine_scope


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", type=Path)
    parser.add_argument("--cut", action="store_true", help="check the weaker intermediate cut LP")
    args = parser.parse_args()
    model = json.loads((args.directory / "model.json").read_text(encoding="utf-8"))
    candidate = json.loads((args.directory / "candidate.json").read_text(encoding="utf-8"))
    result = (replay_nine_point_cut if args.cut else replay_nine_scope)(model, candidate)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
