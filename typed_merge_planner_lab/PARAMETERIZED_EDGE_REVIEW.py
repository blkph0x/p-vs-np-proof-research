"""Independent direct replay of PARAMETERIZED_EDGE_RESULTS.json."""
from __future__ import annotations

import hashlib
import itertools
import json
from math import comb
from pathlib import Path


HERE = Path(__file__).resolve().parent


def brute(matrix):
    rows = tuple(tuple(row) for row in matrix)
    k, n = len(rows), (len(rows[0]) if rows else 0)
    answers = []
    for message in range(1, 1 << k):
        word = tuple(sum(((message >> i) & 1) * rows[i][j] for i in range(k)) % 2
                     for j in range(n))
        if any(word):
            answers.append((sum(word), word))
    return answers


def word_from_basis(basis, message):
    word = 0
    for index, row in enumerate(basis):
        if message >> index & 1:
            word ^= row
    return word


def main() -> None:
    artifact = json.loads((HERE / "PARAMETERIZED_EDGE_RESULTS.json").read_text(encoding="utf-8"))
    assert artifact["schema"] == "parameterized_affine_cardinality_v1"
    actual = {name: hashlib.sha256((HERE / name).read_bytes()).hexdigest()
              for name in artifact["source_sha256"]}
    assert actual == artifact["source_sha256"]
    for case in artifact["cases"]:
        answers = brute(case["matrix"])
        result = case["result"]
        if case["mode"] == "dimension":
            if answers:
                assert result["status"] == "EXACT"
                assert result["distance"] == min(weight for weight, _ in answers)
                assert result["word"].bit_count() == result["distance"]
                assert result["word"] == word_from_basis(result["basis_rows"], result["message"])
            else:
                assert result["status"] == "ZERO_CODE"
        else:
            bound = case["bound"]
            small = [weight for weight, _ in answers if weight <= bound]
            if small:
                assert result["status"] == "EXACT"
                assert result["distance"] == min(small)
                assert result["word"] == word_from_basis(result["basis_rows"], result["message"])
                assert result["word"].bit_count() == result["distance"]
            else:
                assert result["status"] == "CERTIFIED_ABOVE_BOUND"
                assert result["lower_bound"] == bound + 1
    routes = artifact["pair_routes"]
    assert routes["unparameterized"]["route"] == "KNOWN_NP_HARD"
    assert routes["dimension"]["message_branches"] == 31
    assert routes["distance"]["supports"] == sum(comb(6, s) for s in range(3))
    print(json.dumps({"status": "PASS", "cases": len(artifact["cases"]),
                      "source_sha256": artifact["source_sha256"]}))


if __name__ == "__main__":
    main()
