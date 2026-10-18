"""Generate the bounded XOR-chain closure artifact."""
from __future__ import annotations

import json
from hashlib import sha256
from itertools import product
from pathlib import Path

from miner import lit, norm_clause
from review_xor_closure import review
from xor_closure import bounded_closure


HERE = Path(__file__).resolve().parent


def parity_block(support, rhs):
    return [norm_clause(tuple(lit(variable, bit == 0)
                             for variable, bit in zip(support, bits)))
            for bits in product((0, 1), repeat=3) if sum(bits) & 1 != rhs]


def chain_blocks():
    return [(0, 1, 10)] + [(9 + index, index + 1, 10 + index)
                           for index in range(1, 5)]


def source_hashes():
    names = ("xor_closure.py", "review_xor_closure.py", "run_xor_closure.py",
             "XOR_CLOSURE_REPORT.md", "../test_xor_closure.py")
    return {name: sha256((HERE / name).read_bytes()).hexdigest() for name in names}


def main():
    supports = chain_blocks()
    positive = []
    for index, support in enumerate(supports):
        positive.extend(parity_block(support, index & 1))
    mutated = list(positive)
    block_size = 4
    mutated[2 * block_size] = norm_clause((-mutated[2 * block_size][0],)
                                           + mutated[2 * block_size][1:])
    branching = []
    for index in range(8):
        branching.extend(parity_block((0, 2 * index + 1, 2 * index + 2), index & 1))
    parameters = {"max_rounds": 4, "max_support": 8, "max_relations": 4096}
    payload = {
        "schema": "xor_closure_v1",
        "parameters": parameters,
        "positive_clauses": [list(clause) for clause in positive],
        "positive_result": bounded_closure(positive, **parameters),
        "mutated_clauses": [list(clause) for clause in mutated],
        "branching_clauses": [list(clause) for clause in branching],
        "source_hashes": source_hashes(),
        "interpretation": "Bounded one-overlap XOR closure with explicit UNKNOWN relation cap.",
    }
    (HERE / "XOR_CLOSURE_RESULTS.json").write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    result = review()
    (HERE / "XOR_CLOSURE_REVIEW.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
