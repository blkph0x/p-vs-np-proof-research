"""Generate the hidden-XOR pair artifact and run its independent review."""
from __future__ import annotations

import json
from hashlib import sha256
from itertools import product
from pathlib import Path

from indirect_xor import detect_hidden_xor_pairs
from miner import norm_clause, lit
from review_indirect_xor import review


HERE = Path(__file__).resolve().parent
ROOT = HERE.parent


def parity_block(support, rhs):
    clauses = []
    for bits in product((0, 1), repeat=len(support)):
        if sum(bits) & 1 != rhs:
            clauses.append(norm_clause(tuple(lit(variable, bit == 0)
                                             for variable, bit in zip(support, bits))))
    return clauses


def source_hashes():
    names = ("indirect_xor.py", "review_indirect_xor.py", "run_indirect_xor.py",
             "INDIRECT_XOR_REPORT.md", "../test_indirect_xor.py")
    return {name: sha256((HERE / name).read_bytes()).hexdigest() for name in names}


def main():
    first = parity_block((0, 1, 4), 0)
    second = parity_block((4, 2, 3), 1)
    positive = first + second
    mutated = list(positive)
    mutated[len(first)] = norm_clause((-mutated[len(first)][0],) + mutated[len(first)][1:])
    disjoint = first + parity_block((5, 6, 7), 1)
    payload = {
        "schema": "indirect_xor_pair_v1",
        "positive_clauses": [list(clause) for clause in positive],
        "positive_candidates": detect_hidden_xor_pairs(positive),
        "mutated_clauses": [list(clause) for clause in mutated],
        "disjoint_clauses": [list(clause) for clause in disjoint],
        "source_hashes": source_hashes(),
        "interpretation": "One shared-variable parity equation is cancelled; bounded one-step discovery only.",
    }
    (HERE / "INDIRECT_XOR_RESULTS.json").write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    result = review()
    (HERE / "INDIRECT_XOR_REVIEW.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
