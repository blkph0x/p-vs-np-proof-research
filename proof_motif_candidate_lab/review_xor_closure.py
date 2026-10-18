"""Independent replay for bounded XOR-chain closure."""
from __future__ import annotations

import json
from hashlib import sha256
from itertools import product
from pathlib import Path


HERE = Path(__file__).resolve().parent


def excluded(clause, support):
    values = {abs(literal) - 1: (0 if literal > 0 else 1)
              for literal in clause}
    if set(values) != set(support):
        return None
    return tuple(values[variable] for variable in support)


def blocks(clauses):
    groups = {}
    for index, clause in enumerate(clauses):
        if len(clause) != 3 or len({abs(literal) for literal in clause}) != 3:
            continue
        support = tuple(sorted(abs(literal) - 1 for literal in clause))
        groups.setdefault(support, []).append((index, clause))
    result = []
    for support, items in sorted(groups.items()):
        if len(items) != 4:
            continue
        values = [excluded(clause, support) for _, clause in items]
        if len(set(values)) != 4 or len({sum(value) & 1 for value in values}) != 1:
            continue
        result.append({"support": list(support),
                       "rhs": 1 - (sum(values[0]) & 1),
                       "clause_indices": [index for index, _ in items]})
    return result


def key(relation):
    return tuple(relation["support"]), relation["rhs"]


def combine(left, right, max_support):
    overlap = set(left["support"]) & set(right["support"])
    if len(overlap) != 1:
        return None
    support = sorted(set(left["support"]) ^ set(right["support"]))
    if not support or len(support) > max_support:
        return None
    proof = sorted(set(left["proof_blocks"]) ^ set(right["proof_blocks"]))
    if not proof:
        return None
    return {"support": support, "rhs": left["rhs"] ^ right["rhs"],
            "proof_blocks": proof,
            "depth": max(left["depth"], right["depth"]) + 1}


def closure(clauses, max_rounds, max_support, max_relations):
    source = blocks(clauses)
    known = {}
    for index, block in enumerate(source):
        relation = {"support": block["support"], "rhs": block["rhs"],
                    "proof_blocks": [index], "depth": 0}
        known[key(relation)] = relation
    frontier = list(known.values())
    frontier_counts = [len(frontier)]
    for round_index in range(1, max_rounds + 1):
        additions = {}
        for left in frontier:
            for right in list(known.values()):
                candidate = combine(left, right, max_support)
                if candidate is None or key(candidate) in known or key(candidate) in additions:
                    continue
                additions[key(candidate)] = candidate
                if len(additions) > max_relations:
                    return "UNKNOWN_CAP", frontier_counts, source, []
        if not additions:
            break
        known.update(additions)
        frontier = list(additions.values())
        frontier_counts.append(len(frontier))
    relations = [known[item] for item in sorted(known)]
    return "BOUNDED_COMPLETE", frontier_counts, source, relations


def review():
    artifact = json.loads((HERE / "XOR_CLOSURE_RESULTS.json").read_text(encoding="utf-8"))
    params = artifact["parameters"]
    status, counts, source, relations = closure(
        artifact["positive_clauses"], params["max_rounds"],
        params["max_support"], params["max_relations"])
    assert status == artifact["positive_result"]["status"]
    assert counts == artifact["positive_result"]["frontier_counts"]
    assert relations == artifact["positive_result"]["relations"]
    target = [relation for relation in relations
              if relation["support"] == [0, 1, 2, 3, 4, 5, 14]]
    assert len(target) == 1
    assert target[0]["proof_blocks"] == [0, 1, 2, 3, 4]
    mutated = closure(artifact["mutated_clauses"], params["max_rounds"],
                      params["max_support"], params["max_relations"])
    assert not any(relation["support"] == [0, 1, 2, 3, 4, 5, 14]
                   for relation in mutated[3])
    capped = closure(artifact["branching_clauses"], 2, 8, 10)
    assert capped[0] == "UNKNOWN_CAP"
    expected_sources = {"xor_closure.py", "review_xor_closure.py",
                        "run_xor_closure.py", "XOR_CLOSURE_REPORT.md",
                        "../test_xor_closure.py"}
    assert set(artifact["source_hashes"]) == expected_sources
    for name, digest in artifact["source_hashes"].items():
        assert sha256((HERE / name).read_bytes()).hexdigest() == digest
    return {"status": "PASS", "chain_relations": len(relations),
            "target_proof_blocks": target[0]["proof_blocks"],
            "mutated_target_found": False, "branching_status": capped[0],
            "source_hashes_match": True}


if __name__ == "__main__":
    print(json.dumps(review(), indent=2, sort_keys=True))

