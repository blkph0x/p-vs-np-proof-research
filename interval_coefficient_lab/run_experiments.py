import hashlib
import itertools
import json
from pathlib import Path
import random
import sys
from datetime import datetime, timezone

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "packed_cost_exact_matching"))
import packing
from intervals import solve, verify, separated_blocks, separated_block_modular_witness


def main():
    paths = [HERE / name for name in ("intervals.py", "test_intervals.py", "THEOREM.md", "run_experiments.py")]
    paths.append(HERE.parent / "packed_cost_exact_matching" / "packing.py")
    hashes = {str(path.relative_to(HERE.parent)).replace("\\", "/"): hashlib.sha256(path.read_bytes()).hexdigest() for path in paths}
    cases = []

    def record(name, choices, target, expected, extra=None):
        proof = solve(choices, target, max_intervals=256, max_total_intervals=20000, max_spans=100000)
        check = verify(choices, target, proof)
        if proof["status"] == "EXACT":
            assert check["status"] == "VERIFIED" and proof["feasible"] == expected
        else:
            assert "feasible" not in proof and check["status"] == "UNKNOWN"
        row = {"name": name, "choices": choices, "target": target, "reference_feasible": expected,
               "proof": proof, "verification": check}
        if extra:
            row.update(extra)
        cases.append(row)
        return row

    modular_witnesses = 0
    for q in (2, 4, 8, 32, 128, 256):
        choices, target = separated_blocks(q)
        moduli = sorted(set([1, 2, 3, target//2+1, target-1, target]))
        residues = []
        for modulus in moduli:
            bits = separated_block_modular_witness(q, modulus)
            weight = sum(pair[b] for pair, b in zip(choices, bits))
            assert weight != target and weight % modulus == target % modulus
            residues.append({"modulus": modulus, "bits": bits, "actual_weight": weight})
            modular_witnesses += 1
        record("separated_blocks_%d" % q, choices, target, False,
               {"family": "separated_blocks", "q": q, "separate_modular_witnesses": residues})
    for q in (1, 4, 8, 12, 20):
        choices = [[0, 4**i] for i in range(q)]
        target = sum(pair[1] for pair in choices)
        record("base_four_%d" % q, choices, target, True,
               {"family": "base_four", "q": q, "reference_witness": [1]*q,
                "full_interval_count": 1 << (q-1)})

    rng = random.Random(98413)
    formulas = [(3, [[1], [-1], [2, 3]], "packed_gap")]
    formulas += [(3, [[sign*variable for sign, variable in zip(signs, (1, 2, 3))]
                      for signs in itertools.product((-1, 1), repeat=3)], "all_eight_clauses")]
    for i in range(28):
        n = rng.randrange(2, 7)
        clauses = []
        for _ in range(rng.randrange(1, 10)):
            variables = rng.sample(range(1, n+1), rng.randrange(1, min(3, n)+1))
            clauses.append([v*rng.choice((-1, 1)) for v in variables])
        formulas.append((n, clauses, "random_%d" % i))
    for count in (2, 4, 8, 16):
        formulas.append((3*count, [[3*j+1, 3*j+2, 3*j+3] for j in range(count)],
                         "independent_ternary_%d" % count))
    original_assignments = 0
    for n, clauses, name in formulas:
        encoding = packing.encode(n, clauses)
        assert packing.verify_encoding(n, clauses, encoding)
        if name.startswith("independent_ternary_"):
            witness = (1 << n)-1
            assert packing.satisfied(n, clauses, witness)
            reference = {"method": "explicit original satisfying assignment", "assignment": witness}
        else:
            satisfying = [bits for bits in range(1 << n)
                          if all(any(bool((bits >> (abs(literal)-1)) & 1) == (literal > 0)
                                     for literal in clause) for clause in clauses)]
            original_assignments += 1 << n
            witness = satisfying[0] if satisfying else None
            reference = {"method": "complete original Boolean enumeration", "assignments": 1 << n,
                         "satisfying_assignments": satisfying}
        extra = {"family": "packed_sat", "n": n, "clauses": clauses, "encoding": encoding, "reference": reference}
        if witness is not None:
            bits = packing.encode_solution(encoding, witness)
            matching = packing.matching_for_choices(bits)
            assert packing.verify_matching(encoding, matching)["valid"]
            extra["original_matching_witness"] = matching
        row = record(name, encoding["choice_weights"], encoding["target"], witness is not None, extra)
        if row["proof"]["status"] == "EXACT" and row["proof"]["feasible"]:
            matching = packing.matching_for_choices(row["proof"]["witness"])
            assert packing.verify_matching(encoding, matching)["valid"]
            row["interval_matching_witness"] = matching
    assert all(hashlib.sha256(path.read_bytes()).hexdigest() == hashes[str(path.relative_to(HERE.parent)).replace("\\", "/")] for path in paths)
    result = {"created_utc": datetime.now(timezone.utc).isoformat(), "source_sha256": hashes,
              "limits": {"max_intervals": 256, "max_total_intervals": 20000, "max_spans": 100000},
              "summary": {"cases": len(cases), "exact": sum(c["proof"]["status"] == "EXACT" for c in cases),
                          "unknown": sum(c["proof"]["status"] == "UNKNOWN" for c in cases),
                          "original_assignments_enumerated": original_assignments,
                          "modular_witnesses": modular_witnesses}, "cases": cases}
    (HERE / "RESULTS.json").write_text(json.dumps(result, indent=2)+"\n", encoding="utf-8")
    print(json.dumps(result["summary"]))


if __name__ == "__main__":
    main()
