"""Exhaustive two-bridge Horn/affine factorization controls.

The target is the positive exact-one relation on three original Boolean
variables.  The two factors share two existential bridge bits.  All relation
families are enumerated directly from their closure definitions; no finite
catalogue is imported.
"""
from __future__ import annotations

from hashlib import sha256
import json
from itertools import product
from pathlib import Path


HERE = Path(__file__).resolve().parent
TARGET = frozenset(point for point in range(8) if point.bit_count() == 1)


def points(arity: int) -> range:
    return range(1 << arity)


def is_horn(mask: int, arity: int) -> bool:
    """Horn/AND closure for a relation encoded by a point bit mask."""
    active = [x for x in points(arity) if (mask >> x) & 1]
    return all(((mask >> (x & y)) & 1) for x in active for y in active)


def is_affine(mask: int, arity: int) -> bool:
    """Affine/minority closure, translated to an XOR-closed set."""
    active = [x for x in points(arity) if (mask >> x) & 1]
    if not active:
        return True
    base = active[0]
    translated = {x ^ base for x in active}
    return all((x ^ y) in translated for x in translated for y in translated)


def enumerate_relations(arity: int, kind: str) -> tuple[int, ...]:
    if kind not in {"HORN", "AFFINE"}:
        raise ValueError(kind)
    predicate = is_horn if kind == "HORN" else is_affine
    return tuple(mask for mask in range(1 << (1 << arity)) if predicate(mask, arity))


def exact_one_target() -> frozenset[int]:
    return TARGET


def project_pair(left: int, right: int, layout: str) -> frozenset[int]:
    """Project two shared bridge bits from a one/two-original split.

    ONE_LEFT uses L(x,z0,z1) and R(y,w,z0,z1).
    TWO_LEFT uses L(x,y,z0,z1) and R(w,z0,z1).
    Point encodings list original variables first and bridge bits last.
    """
    if layout == "ONE_LEFT":
        output = set()
        for x, y, w in product((0, 1), repeat=3):
            for z in range(4):
                z0, z1 = z & 1, (z >> 1) & 1
                lp = x | (z0 << 1) | (z1 << 2)
                rp = y | (w << 1) | (z0 << 2) | (z1 << 3)
                if ((left >> lp) & 1) and ((right >> rp) & 1):
                    output.add(x | (y << 1) | (w << 2))
                    break
        return frozenset(output)
    if layout == "TWO_LEFT":
        output = set()
        for x, y, w in product((0, 1), repeat=3):
            for z in range(4):
                z0, z1 = z & 1, (z >> 1) & 1
                lp = x | (y << 1) | (z0 << 2) | (z1 << 3)
                rp = w | (z0 << 1) | (z1 << 2)
                if ((left >> lp) & 1) and ((right >> rp) & 1):
                    output.add(x | (y << 1) | (w << 2))
                    break
        return frozenset(output)
    raise ValueError(layout)


def _source_hashes() -> dict[str, str]:
    names = (
        "two_bridge_factorization.py",
        "run_two_bridge_factorization.py",
        "TWO_BRIDGE_FACTOR_THEOREM.md",
        "TWO_BRIDGE_FACTOR_REVIEW.py",
        "test_two_bridge_factorization.py",
        "mixed_horn_affine_reduction.py",
        "test_mixed_horn_affine_reduction.py",
        "MIXED_REDUCTION_REVIEW.py",
    )
    return {name: sha256((HERE / name).read_bytes()).hexdigest() for name in names}


def record(left_kind: str, left_arity: int, right_kind: str, right_arity: int,
           layout: str) -> dict[str, object]:
    left = enumerate_relations(left_arity, left_kind)
    right = enumerate_relations(right_arity, right_kind)
    projections: set[frozenset[int]] = set()
    target_pairs = 0
    for l in left:
        for r in right:
            projected = project_pair(l, r, layout)
            projections.add(projected)
            target_pairs += projected == TARGET
    return {
        "left_kind": left_kind,
        "left_arity": left_arity,
        "right_kind": right_kind,
        "right_arity": right_arity,
        "layout": layout,
        "left_relation_count": len(left),
        "right_relation_count": len(right),
        "factor_pairs": len(left) * len(right),
        "distinct_projected_relations": len(projections),
        "target_pair_count": target_pairs,
        "target_representable": bool(target_pairs),
    }


def all_controls() -> list[dict[str, object]]:
    configs = (
        ("HORN", 3, "AFFINE", 4, "ONE_LEFT"),
        ("AFFINE", 3, "HORN", 4, "ONE_LEFT"),
        ("HORN", 4, "AFFINE", 3, "TWO_LEFT"),
        ("AFFINE", 4, "HORN", 3, "TWO_LEFT"),
    )
    return [record(*config) for config in configs]


def write_artifact() -> dict[str, object]:
    rows = all_controls()
    output = {
        "format": "two-bridge-horn-affine-exhaustive-v1",
        "target": "positive-exact-one-3",
        "target_points": sorted(TARGET),
        "records": rows,
        "all_orientations_represent": all(row["target_representable"] for row in rows),
        "all_orientations_reject": all(not row["target_representable"] for row in rows),
        "explicit_witness": {
            "layout": "ONE_LEFT",
            "left_kind": "HORN",
            "right_kind": "AFFINE",
            "left_points": [0, 3, 4],
            "right_points": [2, 4, 9, 15],
            "left_equations": ["x = z0", "x -> not z1"],
            "right_equations": ["y xor z1 = 0", "w xor z0 xor z1 = 1"],
            "projection": sorted(TARGET),
        },
        "source_sha256": _source_hashes(),
        "scope": "Two existential Boolean bridges, two factors, one Horn and one affine; no claim about three or more bridges or other languages.",
    }
    (HERE / "TWO_BRIDGE_FACTOR_RESULTS.json").write_text(
        json.dumps(output, indent=2) + "\n", encoding="utf-8"
    )
    return output


if __name__ == "__main__":
    print(json.dumps(write_artifact(), indent=2))
