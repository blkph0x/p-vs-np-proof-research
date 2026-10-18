"""Independent replay of BACKDOOR_RESULTS.json.

This reviewer intentionally does not call the backdoor solver.  It checks the
saved relations and any claimed SAT witness by direct enumeration.
"""
from __future__ import annotations

import hashlib
import itertools
import json
from pathlib import Path


HERE = Path(__file__).resolve().parent


def brute(n, constraints):
    return [bits for bits in itertools.product((0, 1), repeat=n)
            if all(tuple(bits[v] for v in scope) in relation
                   for scope, relation in constraints)]


def main() -> None:
    artifact = json.loads((HERE / "BACKDOOR_RESULTS.json").read_text(encoding="utf-8"))
    assert artifact["schema"] == "strong_schaefer_backdoor_v1"
    names = tuple(artifact["source_sha256"])
    actual_hashes = {name: hashlib.sha256((HERE / name).read_bytes()).hexdigest()
                     for name in names}
    assert actual_hashes == artifact["source_sha256"]
    for case in artifact["cases"]:
        constraints = tuple((tuple(row["scope"]),
                             frozenset(tuple(x) for x in row["relation"]))
                            for row in case["constraints"])
        solutions = brute(case["n"], constraints)
        result = case["result"]
        if case["expected_status"] == "UNKNOWN":
            assert result["status"] == "UNKNOWN"
            continue
        expected = "SAT" if solutions else "UNSAT"
        assert result["status"] == expected
        if expected == "SAT":
            witness = tuple(result["witness"])
            assert witness in solutions
    print(json.dumps({"status": "PASS", "cases": len(artifact["cases"]),
                      "source_sha256": artifact["source_sha256"]}))


if __name__ == "__main__":
    main()
