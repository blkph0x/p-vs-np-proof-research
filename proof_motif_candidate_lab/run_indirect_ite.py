"""Generate and independently review compact-ITE motif certificates."""
from __future__ import annotations

import json
from hashlib import sha256
from pathlib import Path

from indirect_ite import detect_compact_ite
from review_indirect_ite import review


HERE = Path(__file__).resolve().parent


def compact_ite(z, c, a, b):
    return [(-(c + 1), -(a + 1), z + 1),
            (-(c + 1), a + 1, -(z + 1)),
            (c + 1, -(b + 1), z + 1),
            (c + 1, b + 1, -(z + 1))]


def source_hashes():
    names = ("indirect_ite.py", "review_indirect_ite.py", "run_indirect_ite.py",
             "INDIRECT_ITE_REPORT.md", "../test_indirect_ite.py")
    return {name: sha256((HERE / name).read_bytes()).hexdigest() for name in names}


def main():
    positive = compact_ite(0, 1, 2, 3) + compact_ite(4, 5, 6, 7)
    mutated = list(positive)
    mutated[0] = (1, mutated[0][1], mutated[0][2])
    mutated[4] = (6, mutated[4][1], mutated[4][2])
    decoy = list(compact_ite(0, 1, 2, 3))
    decoy[1] = (-1, 2, 3)
    payload = {
        "schema": "indirect_ite_v1",
        "positive_clauses": [list(clause) for clause in positive],
        "positive_candidates": detect_compact_ite(positive),
        "mutated_clauses": [list(clause) for clause in mutated],
        "decoy_clauses": [list(clause) for clause in decoy],
        "source_hashes": source_hashes(),
        "interpretation": "Exact four-clause 3-CNF ITE recognition; semantic role search is constant-size.",
    }
    (HERE / "INDIRECT_ITE_RESULTS.json").write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    result = review()
    (HERE / "INDIRECT_ITE_REVIEW.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
