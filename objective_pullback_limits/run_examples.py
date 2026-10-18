"""Save original maps, cost-preservation proofs and independent finite oracles."""
import hashlib
import json
from pathlib import Path
import random
import time

from objective_pullback import classify, verify
from test_objective_pullback import oracle


def main():
    directory = Path(__file__).resolve().parent
    paths = [directory / name for name in
             ("objective_pullback.py", "test_objective_pullback.py", "run_examples.py")]
    hashes = lambda: {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}
    before, start = hashes(), time.perf_counter()
    requests = [
        ("Hamming_overlap", [1, 2, 3], 2, [1, 1, 1]),
        ("disjoint_replication", [1, 1, 2, 2, 2, 0], 2, [1]*6),
        ("zero_cost_overlap", [1, 2, 3, 0], 2, [4, 5, 0, 9]),
        ("no_outputs", [], 3, []),
        ("no_inputs", [0, 0], 0, [1, 5]),
        ("zero_objective", [7, 6], 3, [0, 0]),
    ]
    rng = random.Random(2026101808)
    for index in range(150):
        m, n = rng.randrange(7), rng.randrange(9)
        rows = [rng.randrange(1 << m) for _ in range(n)]
        weights = [rng.choice([0, 1, 7, 10**50]) for _ in rows]
        requests.append(("seeded_"+str(index), rows, m, weights))
    for index in range(30):
        m, n = rng.randrange(1, 7), rng.randrange(1, 9)
        weights = [rng.randrange(4) for _ in range(n)]
        rows = [(1 << rng.randrange(m)) if w else rng.randrange(1 << m)
                for w in weights]
        requests.append(("seeded_additive_"+str(index), rows, m, weights))
    cases = []
    for name, rows, m, weights in requests:
        result = classify(rows, m, weights)
        reference, costs = oracle(rows, m, weights)
        if result["additive"] != reference or not verify(rows, m, weights, result)["valid"]:
            raise ArithmeticError("incorrect result: "+name)
        if reference and result["unary_costs"] != costs:
            raise ArithmeticError("incorrect objective: "+name)
        cases.append({"name": name, "rows": rows, "input_dimension": m,
                      "output_weights": weights, "certificate": result,
                      "exhaustive_oracle_additive": reference, "verified": True})
    replay = json.loads(json.dumps(cases))
    for c in replay:
        if not verify(c["rows"], c["input_dimension"], c["output_weights"], c["certificate"])["valid"]:
            raise ArithmeticError("serialized evidence failed")
    if before != hashes():
        raise ArithmeticError("source changed during audit")
    result = {"scope": "unrestricted linear map with nonnegative integer output costs",
              "case_count": len(cases), "all_agree_with_oracle": True,
              "serialized_replay_passed": True,
              "additive_cases": sum(c["certificate"]["additive"] for c in cases),
              "nonadditive_cases": sum(not c["certificate"]["additive"] for c in cases),
              "original_assignments_enumerated": sum(1 << c["input_dimension"] for c in cases),
              "exhaustive_unit_test_matrix_weight_cases":
                  sum(2**(m*n+n) for m in range(4) for n in range(4)),
              "source_sha256": before, "sources_unchanged": True,
              "seconds": time.perf_counter()-start, "cases": cases}
    (directory / "RESULTS.json").write_text(json.dumps(result, indent=2)+"\n", encoding="utf-8")
    print(json.dumps({key: value for key, value in result.items() if key != "cases"}))


if __name__ == "__main__":
    main()
