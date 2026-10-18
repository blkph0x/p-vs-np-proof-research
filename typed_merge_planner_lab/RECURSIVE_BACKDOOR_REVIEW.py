"""Independent direct replay of the recursive backdoor artifact."""
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


def main():
    artifact = json.loads((HERE / "RECURSIVE_BACKDOOR_RESULTS.json").read_text(encoding="utf-8"))
    assert artifact["schema"] == "recursive_schaefer_backdoor_v1"
    hashes = {name: hashlib.sha256((HERE / name).read_bytes()).hexdigest()
              for name in artifact["source_sha256"]}
    assert hashes == artifact["source_sha256"]
    for case in artifact["cases"]:
        constraints = tuple((tuple(row["scope"]),
                             frozenset(tuple(bits) for bits in row["relation"]))
                            for row in case["constraints"])
        solutions = brute(case["n"], constraints)
        result = case["result"]
        if case["name"] == "sat_depth_one":
            assert result["status"] == "SAT"
            assert tuple(result["witness"]) in solutions
        elif case["name"] == "unsat_depth_one":
            assert result["status"] == "UNSAT"
            assert not solutions
        else:
            assert result["status"] == "UNKNOWN"
    print(json.dumps({"status": "PASS", "cases": len(artifact["cases"]),
                      "source_sha256": artifact["source_sha256"]}))


if __name__ == "__main__":
    main()
