"""Independent replay of the two-bridge Horn/affine search."""
from hashlib import sha256
import json
from itertools import product
from pathlib import Path


HERE = Path(__file__).resolve().parent
TARGET = frozenset(point for point in range(8) if point.bit_count() == 1)


def closed(mask, arity, kind):
    active = [x for x in range(1 << arity) if mask >> x & 1]
    if kind == "HORN":
        return all(mask >> (x & y) & 1 for x in active for y in active)
    if kind == "AFFINE":
        if not active:
            return True
        base = active[0]
        translated = {x ^ base for x in active}
        return all((x ^ y) in translated for x in translated for y in translated)
    raise ValueError(kind)


def relations(arity, kind):
    return tuple(mask for mask in range(1 << (1 << arity))
                 if closed(mask, arity, kind))


def project(left, right, layout):
    result = set()
    for x, y, w in product((0, 1), repeat=3):
        for z in range(4):
            z0, z1 = z & 1, (z >> 1) & 1
            if layout == "ONE_LEFT":
                lp = x | z0 << 1 | z1 << 2
                rp = y | w << 1 | z0 << 2 | z1 << 3
            elif layout == "TWO_LEFT":
                lp = x | y << 1 | z0 << 2 | z1 << 3
                rp = w | z0 << 1 | z1 << 2
            else:
                raise ValueError(layout)
            if left >> lp & 1 and right >> rp & 1:
                result.add(x | y << 1 | w << 2)
                break
    return frozenset(result)


def record(lk, la, rk, ra, layout):
    left, right = relations(la, lk), relations(ra, rk)
    projections = set()
    hits = 0
    for l in left:
        for r in right:
            p = project(l, r, layout)
            projections.add(p)
            hits += p == TARGET
    return {"left_kind": lk, "left_arity": la, "right_kind": rk,
            "right_arity": ra, "layout": layout,
            "left_relation_count": len(left), "right_relation_count": len(right),
            "factor_pairs": len(left) * len(right),
            "distinct_projected_relations": len(projections),
            "target_pair_count": hits, "target_representable": bool(hits)}


def main():
    artifact = json.loads((HERE / "TWO_BRIDGE_FACTOR_RESULTS.json").read_text(encoding="utf-8"))
    configs = [("HORN", 3, "AFFINE", 4, "ONE_LEFT"),
               ("AFFINE", 3, "HORN", 4, "ONE_LEFT"),
               ("HORN", 4, "AFFINE", 3, "TWO_LEFT"),
               ("AFFINE", 4, "HORN", 3, "TWO_LEFT")]
    expected = [record(*c) for c in configs]
    assert artifact["records"] == expected
    assert artifact["all_orientations_represent"]
    assert not artifact["all_orientations_reject"]
    witness = artifact["explicit_witness"]
    witness_left = sum(1 << p for p in witness["left_points"])
    witness_right = sum(1 << p for p in witness["right_points"])
    assert project(witness_left, witness_right, witness["layout"]) == TARGET
    for name, digest in artifact["source_sha256"].items():
        assert sha256((HERE / name).read_bytes()).hexdigest() == digest
    result = {"status": "PASS", "records": len(expected),
              "all_orientations_represent": True,
              "all_orientations_reject": False, "source_hashes_match": True}
    (HERE / "TWO_BRIDGE_FACTOR_REVIEW.json").write_text(
        json.dumps(result, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(result))


if __name__ == "__main__":
    main()
