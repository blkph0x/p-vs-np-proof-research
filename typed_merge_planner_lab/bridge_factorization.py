"""Exhaustive one-bridge Horn/affine factorization controls."""
from __future__ import annotations

from hashlib import sha256
import json
from itertools import product
from pathlib import Path


HERE = Path(__file__).resolve().parent


def tuples(arity):
    return tuple(product((0, 1), repeat=arity))


def and_closed(relation):
    relation = frozenset(relation)
    return all(tuple(x & y for x, y in zip(a, b)) in relation
               for a in relation for b in relation)


def minority_closed(relation):
    relation = frozenset(relation)
    return all(tuple(x ^ y ^ z for x, y, z in zip(a, b, c)) in relation
               for a in relation for b in relation for c in relation)


def enumerate_relations(arity, kind):
    universe = tuples(arity)
    predicate = and_closed if kind == "HORN" else minority_closed
    result = []
    for mask in range(1 << len(universe)):
        relation = frozenset(universe[index] for index in range(len(universe))
                             if mask >> index & 1)
        if predicate(relation):
            result.append(relation)
    return tuple(result)


def exact_one_target():
    return frozenset(row for row in tuples(3) if sum(row) == 1)


def project_pair(left, right, layout):
    """Project ∃z from either (abz,c z) or (a z,bcz)."""
    target = tuples(3)
    if layout == "TWO_LEFT":
        return frozenset((a, b, c) for a, b, c in target
                         if any((a, b, z) in left and (c, z) in right
                                for z in (0, 1)))
    if layout == "TWO_RIGHT":
        return frozenset((a, b, c) for a, b, c in target
                         if any((a, z) in left and (b, c, z) in right
                                for z in (0, 1)))
    raise ValueError("unknown layout")


def search_config(left_kind, left_arity, right_kind, right_arity, layout):
    left = enumerate_relations(left_arity, left_kind)
    right = enumerate_relations(right_arity, right_kind)
    projections = set()
    target = exact_one_target()
    target_pairs = 0
    for left_relation in left:
        for right_relation in right:
            projection = project_pair(left_relation, right_relation, layout)
            projections.add(projection)
            if projection == target:
                target_pairs += 1
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


def all_controls():
    return [
        search_config("HORN", 3, "AFFINE", 2, "TWO_LEFT"),
        search_config("AFFINE", 3, "HORN", 2, "TWO_LEFT"),
        search_config("HORN", 2, "AFFINE", 3, "TWO_RIGHT"),
        search_config("AFFINE", 2, "HORN", 3, "TWO_RIGHT"),
    ]


def save_artifact():
    records = all_controls()
    if any(record["target_representable"] for record in records):
        raise AssertionError("one-bridge target unexpectedly represented")
    sources = {}
    for path in (HERE / "bridge_factorization.py", HERE / "run_bridge_factorization.py",
                 HERE / "BRIDGE_FACTOR_THEOREM.md", HERE / "BRIDGE_FACTOR_REVIEW.py",
                 HERE / "test_bridge_factorization.py"):
        sources[path.name] = sha256(path.read_bytes()).hexdigest()
    output = {
        "format": "one-bridge-horn-affine-exhaustive-v1",
        "target": "positive-exact-one-3",
        "target_tuples": [list(row) for row in sorted(exact_one_target())],
        "records": records,
        "all_orientations_reject": True,
        "source_sha256": sources,
        "scope": "One existential Boolean bridge, two factors, one Horn and one affine; no claim about more bridges or other languages.",
    }
    (HERE / "BRIDGE_FACTOR_RESULTS.json").write_text(json.dumps(output, indent=2) + "\n",
                                                        encoding="utf-8")
    return output


if __name__ == "__main__":
    print(json.dumps(save_artifact(), indent=2))
