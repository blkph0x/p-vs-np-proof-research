"""Independent replay for the hidden-XOR pair artifact."""
from __future__ import annotations

import json
from hashlib import sha256
from itertools import product
from pathlib import Path


HERE = Path(__file__).resolve().parent


def canonical(clause):
    values = {int(literal) for literal in clause}
    assert 0 not in values and all(-literal not in values for literal in values)
    return tuple(sorted(values, key=lambda literal: (abs(literal), literal < 0)))


def excluded(clause, support):
    values = {abs(literal) - 1: (0 if literal > 0 else 1)
              for literal in clause}
    if set(values) != set(support):
        return None
    return tuple(values[variable] for variable in support)


def independent_blocks(clauses):
    groups = {}
    for index, clause in enumerate(clauses):
        clause = canonical(clause)
        if len(clause) != 3 or len({abs(literal) for literal in clause}) != 3:
            continue
        support = tuple(sorted(abs(literal) - 1 for literal in clause))
        groups.setdefault(support, []).append((index, clause))
    blocks = []
    for support, items in sorted(groups.items()):
        if len(items) != 4:
            continue
        assignments = [excluded(clause, support) for _, clause in items]
        if len(set(assignments)) != 4:
            continue
        parities = {sum(bits) & 1 for bits in assignments}
        if len(parities) != 1:
            continue
        rhs = 1 - next(iter(parities))
        blocks.append({"support": support, "rhs": rhs,
                       "clause_indices": tuple(index for index, _ in items)})
    return blocks


def independent_pairs(clauses):
    blocks = independent_blocks(clauses)
    pairs = []
    for left_id, left in enumerate(blocks):
        for right_id in range(left_id + 1, len(blocks)):
            right = blocks[right_id]
            overlap = set(left["support"]) & set(right["support"])
            support = tuple(sorted(set(left["support"]) ^ set(right["support"])))
            if len(overlap) != 1 or len(support) != 4:
                continue
            pairs.append({"kind": "HIDDEN_XOR_PAIR", "support": support,
                          "rhs": left["rhs"] ^ right["rhs"],
                          "block_ids": (left_id, right_id),
                          "eliminated": next(iter(overlap))})
    return blocks, pairs


def jsonable(candidate):
    return {"kind": candidate["kind"], "support": list(candidate["support"]),
            "rhs": candidate["rhs"], "block_ids": list(candidate["block_ids"]),
            "eliminated": candidate["eliminated"]}


def review():
    artifact = json.loads((HERE / "INDIRECT_XOR_RESULTS.json").read_text(encoding="utf-8"))
    positive_blocks, positive_pairs = independent_pairs(artifact["positive_clauses"])
    assert len(positive_blocks) == 2
    assert [jsonable(candidate) for candidate in positive_pairs] == artifact["positive_candidates"]
    candidate = jsonable(positive_pairs[0])
    assert candidate["support"] == [0, 1, 2, 3]
    assert candidate["rhs"] == 1
    for bits in product((0, 1), repeat=5):
        left = (bits[0] + bits[1] + bits[4]) & 1
        right = (bits[4] + bits[2] + bits[3]) & 1
        if left == 0 and right == 1:
            assert (bits[0] + bits[1] + bits[2] + bits[3]) & 1 == 1

    _, mutated_pairs = independent_pairs(artifact["mutated_clauses"])
    _, disjoint_pairs = independent_pairs(artifact["disjoint_clauses"])
    assert mutated_pairs == []
    assert disjoint_pairs == []
    expected_sources = {"indirect_xor.py", "review_indirect_xor.py",
                        "run_indirect_xor.py", "INDIRECT_XOR_REPORT.md",
                        "../test_indirect_xor.py"}
    assert set(artifact["source_hashes"]) == expected_sources
    for name, digest in artifact["source_hashes"].items():
        assert sha256((HERE / name).read_bytes()).hexdigest() == digest
    return {"status": "PASS", "local_blocks": len(positive_blocks),
            "derived_pairs": len(positive_pairs), "negative_pairs": 0,
            "source_hashes_match": True}


if __name__ == "__main__":
    print(json.dumps(review(), indent=2, sort_keys=True))
