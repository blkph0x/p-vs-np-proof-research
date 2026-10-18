"""Independent replay for the compact-ITE artifact."""
from __future__ import annotations

import json
from hashlib import sha256
from itertools import combinations, permutations, product
from pathlib import Path


HERE = Path(__file__).resolve().parent


def clause_value(clause, assignment):
    return any((literal > 0) == bool(assignment[abs(literal) - 1])
               for literal in clause)


def groups(clauses):
    by_support = {}
    for index, clause in enumerate(clauses):
        if len(clause) != 3 or len({abs(literal) for literal in clause}) != 3:
            continue
        support = tuple(sorted(abs(literal) - 1 for literal in clause))
        by_support.setdefault(support, []).append(index)
    seen = set()
    out = []
    for left, right in combinations(sorted(by_support), 2):
        support = tuple(sorted(set(left) | set(right)))
        if len(support) != 4:
            continue
        indices = tuple(sorted(index for key, values in by_support.items()
                              if set(key) <= set(support)
                              for index in values))
        key = (support, indices)
        if len(indices) == 4 and key not in seen:
            seen.add(key)
            out.append((support, indices))
    return out


def valid_assignments(clauses, support, indices):
    positions = {variable: index for index, variable in enumerate(support)}
    result = set()
    for bits in product((0, 1), repeat=4):
        assignment = {variable: bits[position]
                      for variable, position in positions.items()}
        if all(clause_value(clauses[index], assignment) for index in indices):
            result.add(bits)
    return result


def expected_ite(support, roles):
    positions = {variable: index for index, variable in enumerate(support)}
    z, c, a, b = roles
    return {bits for bits in product((0, 1), repeat=4)
            if bits[positions[z]] == (bits[positions[a]]
                                      if bits[positions[c]]
                                      else bits[positions[b]])}


def independent_candidates(clauses):
    out = []
    for support, indices in groups(clauses):
        actual = valid_assignments(clauses, support, indices)
        for roles in permutations(support, 4):
            if actual == expected_ite(support, roles):
                out.append({"kind": "COMPACT_ITE", "support": list(support),
                            "z": roles[0], "c": roles[1], "a": roles[2],
                            "b": roles[3], "clause_indices": list(indices)})
    return out


def review():
    artifact = json.loads((HERE / "INDIRECT_ITE_RESULTS.json").read_text(encoding="utf-8"))
    positive = independent_candidates(artifact["positive_clauses"])
    assert positive == artifact["positive_candidates"]
    assert len(positive) == 2
    assert independent_candidates(artifact["mutated_clauses"]) == []
    assert independent_candidates(artifact["decoy_clauses"]) == []
    expected_sources = {"indirect_ite.py", "review_indirect_ite.py",
                        "run_indirect_ite.py", "INDIRECT_ITE_REPORT.md",
                        "../test_indirect_ite.py"}
    assert set(artifact["source_hashes"]) == expected_sources
    for name, digest in artifact["source_hashes"].items():
        assert sha256((HERE / name).read_bytes()).hexdigest() == digest
    return {"status": "PASS", "positive_blocks": len(positive),
            "mutated_blocks": 0, "decoy_blocks": 0,
            "source_hashes_match": True}


if __name__ == "__main__":
    print(json.dumps(review(), indent=2, sort_keys=True))

