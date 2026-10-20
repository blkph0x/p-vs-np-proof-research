"""Independent bounded checks of the rank-moment RM(2,m) level-nine witness.

This module imports neither the nine-scope producer nor its LP checker.
It constructs moments by binary rank and inverts them, then separately
checks all moments, exact quadratic projection support, and selected complete
marginal families.  It is finite evidence, not the all-dimension proof.
Running this file prints JSON and does not rewrite any result artifact.
"""
from __future__ import annotations

from collections import Counter
from functools import lru_cache
import hashlib
from itertools import combinations
import json
from pathlib import Path
import random
import time


DENOMINATOR = 155
RANK_NUMERATORS = (155, 35, 7, 1)


def checked_scope(scope) -> tuple[int, ...]:
    if type(scope) not in (list, tuple) or len(scope) > 9:
        raise ValueError("scope must list at most nine nonpin points")
    if any(type(point) is not int or point <= 0 for point in scope):
        raise ValueError("nonpin points must be positive exact integers")
    if len(set(scope)) != len(scope):
        raise ValueError("scope points must be distinct")
    return tuple(scope)


def binary_rank(vectors) -> int:
    pivots = {}
    for vector in vectors:
        while vector:
            pivot = vector.bit_length() - 1
            if pivot not in pivots:
                pivots[pivot] = vector
                break
            vector ^= pivots[pivot]
    return len(pivots)


def moment_numerators(scope) -> list[int]:
    scope = checked_scope(scope)
    result = []
    for subset in range(1 << len(scope)):
        dimension = binary_rank(point for i, point in enumerate(scope) if subset >> i & 1)
        result.append(RANK_NUMERATORS[dimension] if dimension < 4 else 0)
    return result


def mobius_table(scope) -> list[int]:
    """Return atom masses as exact numerators over the common denominator155."""
    scope = checked_scope(scope)
    masses = moment_numerators(scope)
    for i in range(len(scope)):
        for subset in range(1 << len(scope)):
            if not (subset >> i & 1):
                masses[subset] -= masses[subset | (1 << i)]
    return masses


def _span_coordinates(scope) -> tuple[tuple[int, ...], int]:
    """Give coordinates in a basis of the supplied span, without 2^m storage."""
    pivots = {}
    coordinates = []
    dimension = 0
    for point in scope:
        value, coordinate = point, 0
        while value:
            pivot = value.bit_length() - 1
            if pivot in pivots:
                vector, mask = pivots[pivot]
                value ^= vector
                coordinate ^= mask
            else:
                new_coordinate = 1 << dimension
                pivots[pivot] = (value, coordinate ^ new_coordinate)
                coordinate = new_coordinate
                dimension += 1
                break
        coordinates.append(coordinate)
    return tuple(coordinates), dimension


def quadratic_projection_support(scope) -> set[int]:
    """Independently enumerate the pinned quadratic evaluation span.

    Restriction to the span of the coordinates loses no quadratic function:
    every quadratic on that span extends through a linear projection from the
    ambient space.  Its dimension is at most nine, even for wide coordinates.
    No minimum-dual-weight or affine-flat classification is used here.
    """
    scope = checked_scope(scope)
    points, dimension = _span_coordinates(scope)
    rows = []
    for first in range(dimension):
        rows.append(sum(((point >> first) & 1) << i for i, point in enumerate(points)))
    for first, second in combinations(range(dimension), 2):
        rows.append(sum((((point >> first) & 1) & ((point >> second) & 1)) << i
                        for i, point in enumerate(points)))
    span = {0}
    for row in rows:
        span.update(tuple(word ^ row for word in span))
    pin_one_offset = (1 << len(scope)) - 1
    return {word ^ pin_one_offset for word in span}


def verify_table(scope, masses) -> dict:
    """Check proposed atom numerators using direct sums, not Möbius inversion."""
    scope = checked_scope(scope)
    if type(masses) not in (list, tuple) or len(masses) != 1 << len(scope):
        raise ValueError("wrong atom-array shape")
    if any(type(value) is not int or value < 0 for value in masses):
        raise ValueError("atom numerators must be nonnegative exact integers")
    if sum(masses) != DENOMINATOR:
        raise ValueError("table is not normalized")
    positive = [(word, value) for word, value in enumerate(masses) if value]
    for subset in range(1 << len(scope)):
        dimension = binary_rank(point for i, point in enumerate(scope) if subset >> i & 1)
        expected = RANK_NUMERATORS[dimension] if dimension < 4 else 0
        actual = sum(value for word, value in positive if word & subset == subset)
        if actual != expected:
            raise ValueError("direct moment mismatch")
    support = quadratic_projection_support(scope)
    if any(word not in support for word, _ in positive):
        raise ValueError("positive atom lies outside the pinned quadratic projection")
    return {
        "atoms": len(masses), "positive_atoms": len(positive),
        "moments_checked": 1 << len(scope), "quadratic_support_size": len(support),
    }


def project_table(scope, masses, subset_mask: int) -> list[int]:
    scope = checked_scope(scope)
    if type(subset_mask) is not int or not 0 <= subset_mask < 1 << len(scope):
        raise ValueError("invalid retained-coordinate mask")
    if len(masses) != 1 << len(scope):
        raise ValueError("wrong atom-array shape")
    kept = [i for i in range(len(scope)) if subset_mask >> i & 1]
    result = [0] * (1 << len(kept))
    for word, value in enumerate(masses):
        if value:
            projected = sum(((word >> old) & 1) << new for new, old in enumerate(kept))
            result[projected] += value
    return result


def verify_all_marginals(scope, masses) -> int:
    """Compare every proper-subscope marginal to its own rank/Möbius table."""
    scope = checked_scope(scope)
    count = 0
    for subset in range((1 << len(scope)) - 1):
        retained = tuple(point for i, point in enumerate(scope) if subset >> i & 1)
        if project_table(scope, masses, subset) != mobius_table(retained):
            raise ValueError("proper-subscope marginal mismatch")
        count += 1
    return count


def empty_atom_counts(scope) -> dict:
    """Count actual closed rank-three flats and zero-sum quadruples."""
    scope = checked_scope(scope)
    if len(scope) != 9:
        raise ValueError("the displayed empty-atom identity is for nine points")
    flats = set()
    for triple in combinations(scope, 3):
        # Span is enumerated directly, independently of binary_rank.
        span = {0}
        for point in triple:
            span.update(tuple(value ^ point for value in span))
        if len(span) == 8:
            flats.add(tuple(point for point in scope if point in span))
    sizes = Counter(map(len, flats))
    quadruples = sum(a ^ b ^ c ^ d == 0 for a, b, c, d in combinations(scope, 4))
    formula = 8 + quadruples - sizes[5] - 5 * sizes[6] - 15 * sizes[7]
    return {
        "zero_sum_quadruples": quadruples,
        "closed_rank3_flats_by_size": dict(sorted(sizes.items())),
        "empty_numerator_formula": formula,
    }


@lru_cache(maxsize=1)
def three_subspaces_five() -> tuple[frozenset[int], ...]:
    """Enumerate the155 actual3-subspaces of F2^5 from independent triples."""
    spaces = set()
    for a, b, c in combinations(range(1, 32), 3):
        span = frozenset((0, a, b, c, a ^ b, a ^ c, b ^ c, a ^ b ^ c))
        if len(span) == 8:
            spaces.add(span)
    return tuple(sorted(spaces, key=lambda values: tuple(sorted(values))))


def actual_five_space_table(scope) -> list[int]:
    """Count uniform3-subspace intersections, using the actual coordinate points."""
    scope = checked_scope(scope)
    if any(point >= 32 for point in scope):
        raise ValueError("this direct control uses actual five-bit coordinates")
    counts = [0] * (1 << len(scope))
    for subspace in three_subspaces_five():
        word = sum(int(point in subspace) << i for i, point in enumerate(scope))
        counts[word] += 1
    return counts


def named_scopes() -> dict[str, tuple[int, ...]]:
    return {
        "empty": (),
        "full_fano": tuple(range(1, 8)),
        "six_fano_plus_three_independent": (1, 2, 3, 4, 5, 6, 8, 16, 32),
        "seven_fano_plus_two_independent": (1, 2, 3, 4, 5, 6, 7, 8, 16),
        "eight_cap_plus_external": tuple(range(16, 25)),
        "nine_independent": tuple(1 << i for i in range(9)),
        "two_independent_lines_plus_three": (1, 2, 3, 4, 8, 12, 16, 32, 64),
        "five_fano_plus_four_independent": (1, 2, 3, 4, 5, 8, 16, 32, 64),
    }


def run_review(seed: int = 202610209) -> dict:
    """Bounded reproducible coverage; no claim to enumerate all nine-point types."""
    rng = random.Random(seed)
    scopes = list(named_scopes().items())
    for dimension, count in ((6, 48), (7, 32), (8, 16)):
        basis = [1 << i for i in range(dimension)]
        remaining = [value for value in range(1, 1 << dimension) if value not in basis]
        for i in range(count):
            points = basis + rng.sample(remaining, 9 - dimension)
            rng.shuffle(points)
            scopes.append((f"seeded_rank{dimension}_{i}", tuple(points)))
    for i in range(64):
        scopes.append((f"five_space_{i}", tuple(rng.sample(range(1, 32), rng.randrange(10)))))
    totals = Counter()
    named = {}
    for name, scope in scopes:
        masses = mobius_table(scope)
        checked = verify_table(scope, masses)
        totals.update({key: checked[key] for key in ("positive_atoms", "moments_checked")})
        totals["scope_cases"] += 1
        if len(scope) == 9:
            counts = empty_atom_counts(scope)
            if counts["empty_numerator_formula"] != masses[0]:
                raise ValueError("empty-atom incidence identity failed")
            totals["empty_identities"] += 1
            if binary_rank(scope) >= 6:
                if counts["closed_rank3_flats_by_size"].get(7, 0):
                    raise ValueError("high-rank scope contains a seven-point rank3 flat")
                if checked["quadratic_support_size"] != 512:
                    raise ValueError("high-rank pinned projection is not full")
                totals["high_rank_nine_scopes"] += 1
        if all(point < 32 for point in scope):
            if masses != actual_five_space_table(scope):
                raise ValueError("table differs from the actual155-flat distribution")
            totals["actual_five_space_controls"] += 1
        if name in named_scopes():
            totals["proper_marginal_tables"] += verify_all_marginals(scope, masses)
            named[name] = {"rank": binary_rank(scope), "empty_numerator": masses[0], **checked}
            if len(scope) == 9:
                named[name].update(empty_atom_counts(scope))
    return {
        "status": "PASS", "seed": seed, "denominator": DENOMINATOR,
        "coverage": "eight named scopes,96 seeded rank6..8 scopes,64 five-bit scopes",
        "all_nine_point_types_enumerated": False,
        "counts": dict(totals), "named_controls": named,
    }


def main():
    started = time.perf_counter()
    result = run_review()
    result["wall_seconds"] = round(time.perf_counter() - started, 6)
    base = Path(__file__).resolve().parent
    names = ("review_rm2_level9_family.py", "test_rm2_level9_family.py",
             "REED_MULLER_QUADRATIC_LEVEL9_THEOREM.md")
    result["source_sha256_lf"] = {
        name: hashlib.sha256((base / name).read_bytes().replace(b"\r\n", b"\n")).hexdigest()
        for name in names if (base / name).is_file()
    }
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
