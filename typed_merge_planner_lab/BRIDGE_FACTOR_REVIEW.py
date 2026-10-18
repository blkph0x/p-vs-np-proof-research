"""Independent replay of the one-bridge Horn/affine search."""
from hashlib import sha256
import json
from itertools import product
from pathlib import Path


HERE = Path(__file__).resolve().parent


def tuples(arity):
    return tuple(product((0, 1), repeat=arity))


def closure(relation, kind):
    relation = frozenset(relation)
    if kind == "HORN":
        return all(tuple(a[i] & b[i] for i in range(len(a))) in relation
                   for a in relation for b in relation)
    return all(tuple(a[i] ^ b[i] ^ c[i] for i in range(len(a))) in relation
               for a in relation for b in relation for c in relation)


def enumerate_relations(arity, kind):
    universe = tuples(arity)
    return tuple(frozenset(universe[i] for i in range(len(universe)) if mask >> i & 1)
                 for mask in range(1 << len(universe)) if closure(
                     frozenset(universe[i] for i in range(len(universe)) if mask >> i & 1), kind))


def project(left, right, layout):
    if layout == "TWO_LEFT":
        return frozenset((a, b, c) for a, b, c in tuples(3)
                         if any((a, b, z) in left and (c, z) in right for z in (0, 1)))
    return frozenset((a, b, c) for a, b, c in tuples(3)
                     if any((a, z) in left and (b, c, z) in right for z in (0, 1)))


def record(left_kind, left_arity, right_kind, right_arity, layout):
    left = enumerate_relations(left_arity, left_kind)
    right = enumerate_relations(right_arity, right_kind)
    target = frozenset(row for row in tuples(3) if sum(row) == 1)
    projections = set()
    target_pairs = 0
    for l in left:
        for r in right:
            projection = project(l, r, layout)
            projections.add(projection)
            target_pairs += projection == target
    return {"left_kind": left_kind, "left_arity": left_arity,
            "right_kind": right_kind, "right_arity": right_arity,
            "layout": layout, "left_relation_count": len(left),
            "right_relation_count": len(right), "factor_pairs": len(left) * len(right),
            "distinct_projected_relations": len(projections),
            "target_pair_count": target_pairs,
            "target_representable": bool(target_pairs)}


def main():
    artifact = json.loads((HERE / "BRIDGE_FACTOR_RESULTS.json").read_text(encoding="utf-8"))
    configs = [("HORN", 3, "AFFINE", 2, "TWO_LEFT"),
               ("AFFINE", 3, "HORN", 2, "TWO_LEFT"),
               ("HORN", 2, "AFFINE", 3, "TWO_RIGHT"),
               ("AFFINE", 2, "HORN", 3, "TWO_RIGHT")]
    expected = [record(*config) for config in configs]
    assert artifact["records"] == expected
    assert artifact["all_orientations_reject"]
    assert all(not row["target_representable"] for row in expected)
    for name, digest in artifact["source_sha256"].items():
        assert sha256((HERE / name).read_bytes()).hexdigest() == digest
    output = {"status": "PASS", "records": len(expected),
              "all_orientations_reject": True, "source_hashes_match": True}
    (HERE / "BRIDGE_FACTOR_REVIEW.json").write_text(json.dumps(output, indent=2) + "\n",
                                                     encoding="utf-8")
    print(json.dumps(output))


if __name__ == "__main__":
    main()
