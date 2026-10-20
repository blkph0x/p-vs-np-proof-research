"""Independent exact finite checks for the all-dimension RM(2,m) L8 proof.

No optimizer and no production witness generator are imported. The lower
bound explicitly depends on the previously saved selected-model certificate
and its independent reconstruction. This script never rewrites those files.
"""

from __future__ import annotations

import hashlib
import json
import platform
import sys
import time
from collections import Counter
from datetime import datetime, timezone
from fractions import Fraction
from itertools import combinations
from pathlib import Path

HERE = Path(__file__).resolve().parent
RESULT_NAME = "RM2_LEVEL8_FAMILY_REVIEW.json"
SOURCE_NAMES = (
    "review_rm2_level8_family.py",
    "test_rm2_level8_family.py",
    "REED_MULLER_QUADRATIC_LEVEL8_THEOREM.md",
)
DEPENDENCY_NAMES = (
    "REED_MULLER_LEVEL_D_AFFINE_OVERLAP_RESULTS.json",
    "REED_MULLER_LEVEL_D_AFFINE_OVERLAP_INDEPENDENT_REVIEW.py",
    "REED_MULLER_AFFINE_OVERLAP_DUAL_NOTE.md",
)
EXPECTED_RANK_COUNTS = {4: 12870, 5: 31005, 6: 6769, 7: 219, 8: 1}
EXPECTED_REDUCED_COSTS = {
    2: Fraction(434, 5), 3: Fraction(682, 5), 4: Fraction(124, 5),
    7: Fraction(496, 5), 8: Fraction(1736, 5), 9: Fraction(248),
}


def _points(points):
    if not isinstance(points, (tuple, list)) or len(points) > 8:
        raise ValueError("scope must be an explicit sequence of at most eight points")
    if any(type(point) is not int or point <= 0 for point in points):
        raise ValueError("points must be distinct positive exact integers")
    if len(set(points)) != len(points):
        raise ValueError("duplicate point")
    return tuple(points)


def line_triples(points):
    """Return local-index triples, without any ambient-dimension assumption."""
    points = _points(points)
    return tuple((a, b, c) for a, b, c in combinations(range(len(points)), 3)
                 if points[a] ^ points[b] ^ points[c] == 0)


def scope_masses(points):
    """Proposed exact atom probabilities, represented as numerators over 35."""
    points = _points(points)
    k = len(points)
    triples = line_triples(points)
    degrees = [0] * k
    for triple in triples:
        for index in triple:
            degrees[index] += 1
    masses = [0] * (1 << k)
    masses[0] = 35 - 7 * k + k * (k - 1) // 2 - len(triples)
    for index in range(k):
        masses[1 << index] = 8 - k + degrees[index]
    point_set = set(points)
    for a, b in combinations(range(k), 2):
        masses[(1 << a) | (1 << b)] = int(points[a] ^ points[b] not in point_set)
    for a, b, c in triples:
        masses[(1 << a) | (1 << b) | (1 << c)] = 1
    return masses


def _row_basis(rows):
    """Independent high-pivot Gaussian elimination on evaluation vectors."""
    pivots = {}
    for row in rows:
        while row:
            pivot = row.bit_length() - 1
            if pivot in pivots:
                row ^= pivots[pivot]
            else:
                pivots[pivot] = row
                break
    return tuple(pivots[pivot] for pivot in sorted(pivots, reverse=True))


def projection_basis(points):
    """Span all degree<=2 evaluations on [0]+points, with no flat theorem.

    Reduce the coordinate linear evaluations first. Their pairwise products
    span all quadratic evaluations, since products distribute over GF(2).
    This avoids allocating a quadratic number of ambient-coordinate pairs.
    """
    points = _points(points)
    dimension = max(points, default=0).bit_length()
    linear = _row_basis(
        sum(((point >> coordinate) & 1) << (index + 1)
            for index, point in enumerate(points))
        for coordinate in range(dimension)
    )
    rows = [(1 << (len(points) + 1)) - 1, *linear]
    rows.extend(first & second for first, second in combinations(linear, 2))
    return _row_basis(rows)


def in_span(word, basis):
    for row in basis:
        if word & (1 << (row.bit_length() - 1)):
            word ^= row
    return word == 0


def check_scope(points, masses):
    """Check complete moments and pinned projection support independently.

    A generic superset zeta transform of supplied atom masses checks all
    2^k moments, not just the producer's atom formulas. Positive support is
    checked against quadratic evaluations, independently of zero-sum lines.
    Raises ValueError on any malformed or false proposed table.
    """
    points = _points(points)
    k = len(points)
    if not isinstance(masses, (list, tuple)) or len(masses) != 1 << k:
        raise ValueError("wrong table shape")
    if any(type(value) is not int or value < 0 for value in masses):
        raise ValueError("masses must be nonnegative exact integer numerators")
    if sum(masses) != 35:
        raise ValueError("normalization")
    basis = projection_basis(points)
    positive_atoms = 0
    for atom, mass in enumerate(masses):
        if mass:
            positive_atoms += 1
            if not in_span(1 | (atom << 1), basis):
                raise ValueError("positive atom is outside the pinned quadratic projection")
    moments = list(masses)
    for bit in range(k):
        for mask in range(1 << k):
            if not (mask >> bit) & 1:
                moments[mask] += moments[mask | (1 << bit)]
    expected = [0] * (1 << k)
    expected[0] = 35
    for index in range(k):
        expected[1 << index] = 7
    for a, b in combinations(range(k), 2):
        expected[(1 << a) | (1 << b)] = 1
    for a, b, c in combinations(range(k), 3):
        if points[a] ^ points[b] ^ points[c] == 0:
            expected[(1 << a) | (1 << b) | (1 << c)] = 1
    if moments != expected:
        raise ValueError("common-moment assignment")
    return {
        "positive_atoms": positive_atoms,
        "moment_comparisons": 1 << k,
        "zeta_additions": k * (1 << (k - 1)) if k else 0,
        "projection_rank": len(basis),
    }


def rref_configurations(k=8):
    """All rowspaces of GF(2)^k, as rank and ordered column coordinates.

    Rows have increasing pivot positions. A nonpivot entry in row i is
    free exactly when its column is to the right of that row's pivot.
    """
    if type(k) is not int or not 0 <= k <= 8:
        raise ValueError("enumeration width must be an integer from zero to eight")
    for rank in range(k + 1):
        for pivots in combinations(range(k), rank):
            pivot_set = set(pivots)
            free = [(i, column) for i, pivot in enumerate(pivots)
                    for column in range(pivot + 1, k) if column not in pivot_set]
            base = [0] * k
            for i, pivot in enumerate(pivots):
                base[pivot] = 1 << i
            for choice in range(1 << len(free)):
                points = base.copy()
                for bit, (i, column) in enumerate(free):
                    if (choice >> bit) & 1:
                        points[column] |= 1 << i
                yield rank, tuple(points)


def enumerate_configurations(k=8):
    started = time.perf_counter()
    raw_ranks, simple_ranks, triples_histogram = Counter(), Counter(), Counter()
    projection_ranks = Counter()
    positive_atoms = moment_comparisons = zeta_additions = 0
    digest = hashlib.sha256()
    max_lines = 0
    for rank, points in rref_configurations(k):
        raw_ranks[rank] += 1
        if 0 in points or len(set(points)) != k:
            continue
        simple_ranks[rank] += 1
        triples = line_triples(points)
        triples_histogram[len(triples)] += 1
        max_lines = max(max_lines, len(triples))
        if len(triples) > 7:
            raise AssertionError("eight-point triple bound failed")
        masses = scope_masses(points)
        checked = check_scope(points, masses)
        positive_atoms += checked["positive_atoms"]
        moment_comparisons += checked["moment_comparisons"]
        zeta_additions += checked["zeta_additions"]
        projection_ranks[checked["projection_rank"]] += 1
        digest.update(bytes([rank, *points, *masses]))
    if k == 8:
        if sum(raw_ranks.values()) != 417199 or dict(simple_ranks) != EXPECTED_RANK_COUNTS:
            raise AssertionError("RREF classification count")
        if positive_atoms != 1496936 or max_lines != 7:
            raise AssertionError("independent support/triple counts")
    return {
        "width": k,
        "all_rref_rowspaces": sum(raw_ranks.values()),
        "all_rref_rank_counts": dict(sorted(raw_ranks.items())),
        "simple_configurations": sum(simple_ranks.values()),
        "simple_rank_counts": dict(sorted(simple_ranks.items())),
        "zero_sum_triple_histogram": dict(sorted(triples_histogram.items())),
        "maximum_zero_sum_triples": max_lines,
        "quadratic_projection_rank_histogram": dict(sorted(projection_ranks.items())),
        "positive_atoms_checked": positive_atoms,
        "all_moment_comparisons": moment_comparisons,
        "generic_zeta_additions": zeta_additions,
        "ordered_case_sha256": digest.hexdigest(),
        "elapsed_seconds": time.perf_counter() - started,
    }


def replay_lower_bound():
    # Deliberately import the independent reconstruction, not its main()
    # (main rewrites historical artifacts) or an LP solver.
    from REED_MULLER_LEVEL_D_AFFINE_OVERLAP_INDEPENDENT_REVIEW import _rebuild, replay

    started = time.perf_counter()
    certificate = json.loads(
        (HERE / "REED_MULLER_LEVEL_D_AFFINE_OVERLAP_RESULTS.json").read_text(encoding="utf-8")
    )
    model = _rebuild()
    replayed = replay(certificate, model)
    if replayed.get("valid") is not True:
        raise AssertionError("selected model certificate rejected")
    _, _, _, _, _, _, matrix, rhs, objective, _ = model
    dual = [Fraction(value) for value in certificate["dual_row_values"]]
    costs = [
        objective[column] - sum(Fraction(row.get(column, 0)) * dual[index]
                                for index, row in enumerate(matrix))
        for column in range(len(objective))
    ]
    nonzero = {index: value for index, value in enumerate(costs) if value}
    value = sum(multiplier * target for multiplier, target in zip(dual, rhs))
    if nonzero != EXPECTED_REDUCED_COSTS or value != Fraction(31, 5):
        raise AssertionError("exact compact lower identity")
    return {
        "valid": True,
        "method": "independent orbit/matrix rebuild plus exact rational primal/dual replay",
        "variable_orbits": len(objective),
        "row_orbits": len(matrix),
        "scope_counts": replayed["scope_counts"],
        "dual_value": str(value),
        "nonzero_reduced_costs": {str(index): str(cost) for index, cost in nonzero.items()},
        "historical_certificate_full_L8_status": replayed["full_level_8_status"],
        "historical_status_explanation": (
            "The earlier selected-scope artifact is preserved. The new all-dimension "
            "proof combines its lower bound with a separately proved full-L8 upper bound."
        ),
        "elapsed_seconds": time.perf_counter() - started,
    }


def level_nine_control():
    points = list(range(16, 25))
    if any(a ^ b ^ c == 0 for a, b, c in combinations(points, 3)):
        raise AssertionError("chosen nine-point affine cap")
    values = [t * (t - 2) * (t - 3) // 2 for t in range(10)]
    if min(values) < 0:
        raise AssertionError("integer-valid polynomial")
    lhs = Fraction(1, 5) - 8 * Fraction(1, 35)
    if lhs != -Fraction(1, 35):
        raise AssertionError("level-nine witness obstruction")
    return {
        "ambient_dimension": 5,
        "nonpin_points": points,
        "zero_sum_triples": 0,
        "integer_polynomial_values_t_0_through_9": values,
        "normalized_inequality": "p - 8*q + 28*r >= 0",
        "witness_p_q_r": ["1/5", "1/35", "0"],
        "witness_left_side": str(lhs),
        "claim": "Rejects this witness at full L9; does not determine the L9 optimum.",
    }


def normalized_sha256(content):
    """Hash text bytes with CRLF normalized to LF for Git checkout portability."""
    if not isinstance(content, bytes):
        raise ValueError("hash input must be bytes")
    return hashlib.sha256(content.replace(b"\r\n", b"\n")).hexdigest()


def _hashes(names):
    return {name: normalized_sha256((HERE / name).read_bytes()) for name in names}


def main():
    started = time.perf_counter()
    names = SOURCE_NAMES + DEPENDENCY_NAMES
    before = _hashes(names)
    classification = enumerate_configurations()
    lower = replay_lower_bound()
    nine = level_nine_control()
    after = _hashes(names)
    if before != after:
        changed = [name for name in names if before[name] != after[name]]
        raise AssertionError(f"source/dependency changed during the run: {changed}")
    payload = {
        "format": "rm2-level8-family-independent-check-v1",
        "status": "PASS",
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "environment": {
            "python": sys.version,
            "implementation": platform.python_implementation(),
            "platform": platform.platform(),
            "machine": platform.machine(),
            "executable": sys.executable,
        },
        "scope": {
            "code": "RM(2,m)",
            "dimension": "all integers m >= 4",
            "pin": "coordinate zero equals one",
            "ordinary_level": "all total coordinate scopes of size <=8",
            "upper_witness_additional_scope": "pin plus any <=8 nonpin coordinates",
            "reduced_optimum": "(2**m - 1)/5",
            "total_optimum": "(2**m + 4)/5",
            "integer_pinned_optimum": "2**(m-2)",
            "novelty": "UNKNOWN",
            "logical_basis": (
                "Written all-size support/Mobius/triple proof plus transported finite "
                "exact lower identity; finite checks alone are not the all-size proof."
            ),
        },
        "classification": classification,
        "finite_lower_certificate_replay": lower,
        "next_level_negative_control": nine,
        "example_objectives": [
            {"m": m, "reduced": str(Fraction((1 << m) - 1, 5)),
             "total": str(Fraction((1 << m) + 4, 5)), "integer": 1 << (m - 2)}
            for m in range(4, 13)
        ],
        "source_sha256": {name: after[name] for name in SOURCE_NAMES},
        "dependency_sha256": {name: after[name] for name in DEPENDENCY_NAMES},
        "hash_convention": "SHA256 of file bytes after CRLF-to-LF normalization",
        "source_unchanged_during_run": True,
        "elapsed_seconds": time.perf_counter() - started,
    }
    (HERE / RESULT_NAME).write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n",
                                    encoding="utf-8", newline="\n")
    print(json.dumps({
        "status": payload["status"],
        "simple_configurations": classification["simple_configurations"],
        "positive_atoms_checked": classification["positive_atoms_checked"],
        "all_moment_comparisons": classification["all_moment_comparisons"],
        "dual_value": lower["dual_value"],
        "elapsed_seconds": payload["elapsed_seconds"],
        "result": str(HERE / RESULT_NAME),
    }, sort_keys=True))


if __name__ == "__main__":
    main()
