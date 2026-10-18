"""Save original formulas, exact packed graphs, bounded DP proofs and honest caps."""
from datetime import datetime, timezone
import hashlib
import itertools
import json
from pathlib import Path
import random
import time

from packing import (encode, encode_solution, matching_for_choices, solve_choices,
                     verify_choices, verify_encoding, verify_matching)

HERE = Path(__file__).resolve().parent
SOURCES = ("packing.py", "test_packing.py", "run_experiments.py", "THEOREM.md")


def hashes():
    return {name: hashlib.sha256((HERE/name).read_bytes()).hexdigest() for name in SOURCES}


def oracle(n, clauses):
    if n > 8:
        raise ValueError("original truth-table oracle cap")
    satisfying = []
    for bits in itertools.product((0, 1), repeat=n):
        if all(any(bits[abs(x)-1] == int(x > 0) for x in c) for c in clauses):
            satisfying.append(sum(b << i for i, b in enumerate(bits)))
    return {"kind": "original_assignment_enumeration", "satisfiable": bool(satisfying),
            "satisfying_assignments": satisfying, "assignments_checked": 1 << n}


def run_case(name, n, clauses, *, known_witness=None):
    data = encode(n, clauses)
    if not verify_encoding(n, clauses, data):
        raise ArithmeticError("original formula binding failed")
    if known_witness is None:
        reference = oracle(n, clauses)
        witness = reference["satisfying_assignments"][0] if reference["satisfiable"] else None
    else:
        if not all(any(bool(known_witness & (1 << (abs(x)-1))) == (x > 0) for x in c) for c in clauses):
            raise ArithmeticError("invalid independent SAT witness")
        reference = {"kind": "explicit_original_sat_witness", "satisfiable": True,
                     "assignment": known_witness, "assignments_checked": 1}
        witness = known_witness
    reference_matching = None
    if witness is not None:
        reference_matching = matching_for_choices(encode_solution(data, witness))
        if not verify_matching(data, reference_matching)["valid"]:
            raise ArithmeticError("satisfying assignment extension failed")
    start = time.perf_counter()
    dp = solve_choices(data["choice_weights"], data["target"], max_states=512, max_transitions=200000)
    elapsed = time.perf_counter()-start
    checked, solution_matching = None, None
    if dp["status"] == "EXACT":
        checked = verify_choices(data["choice_weights"], data["target"], dp)
        if not checked["valid"] or dp["feasible"] != reference["satisfiable"]:
            raise ArithmeticError("packed decision disagrees with original formula")
        if dp["feasible"]:
            solution_matching = matching_for_choices(dp["choice_bits"])
            if not verify_matching(data, solution_matching)["valid"]:
                raise ArithmeticError("exact matching failed original-input checks")
    elif dp["status"] != "UNKNOWN" or "feasible" in dp:
        raise ArithmeticError("invalid incomplete status")
    low_bits = [int(pair[1] < pair[0]) for pair in data["choice_weights"]]
    low_matching = matching_for_choices(low_bits)
    low = verify_matching(data, low_matching, exact=False)
    if not low["valid"]:
        raise ArithmeticError("ordinary minimum witness failed")
    high = sum(max(pair) for pair in data["choice_weights"])
    request = {"n": n, "clauses": clauses}
    return {"name": name, "original_request": request,
            "original_request_sha256": hashlib.sha256(json.dumps(request, sort_keys=True).encode()).hexdigest(),
            "encoding": data, "encoding_verified": True, "reference": reference,
            "reference_matching": reference_matching, "bounded_dp": dp,
            "dp_certificate_verification": checked, "solution_matching": solution_matching,
            "ordinary_minimum_cost": low["cost"], "ordinary_minimum_matching": low_matching,
            "ordinary_maximum_cost": high,
            "max_weight_bits": max([0]+[w.bit_length() for pair in data["choice_weights"] for w in pair]),
            "target_bits": data["target"].bit_length(), "seconds": elapsed}


def replay(cases):
    exact, unknown, matchings = 0, 0, 0
    for c in cases:
        request, data, dp = c["original_request"], c["encoding"], c["bounded_dp"]
        if hashlib.sha256(json.dumps(request, sort_keys=True).encode()).hexdigest() != c["original_request_sha256"]:
            raise ArithmeticError("original request hash changed")
        if not verify_encoding(request["n"], request["clauses"], data):
            raise ArithmeticError("original formula encoding failed on replay")
        if dp["status"] == "EXACT":
            if not verify_choices(data["choice_weights"], data["target"], dp)["valid"]:
                raise ArithmeticError("exact prefix-cost certificate failed replay")
            exact += 1
        elif dp["status"] == "UNKNOWN" and "feasible" not in dp:
            unknown += 1
        else:
            raise ArithmeticError("invalid saved status")
        for key in ("reference_matching", "solution_matching", "ordinary_minimum_matching"):
            if c[key] is not None:
                if not verify_matching(data, c[key], exact=(key != "ordinary_minimum_matching"))["valid"]:
                    raise ArithmeticError("saved original graph witness failed")
                matchings += 1
    return {"cases": len(cases), "exact_dp_proofs": exact, "honest_unknown": unknown,
            "matching_witnesses_checked": matchings, "all_replayed": True}


def main():
    before, start = hashes(), time.perf_counter()
    named = [("empty", 0, []), ("unit_SAT", 1, [[1]]),
             ("unit_UNSAT", 1, [[1], [-1]]),
             ("minmax_gap_UNSAT", 3, [[1], [-1], [2, 3]]),
             ("coupled_SAT", 3, [[1, 2, 3], [-1, 2, 3]]),
             ("all_polarities_UNSAT", 3, [[s*(i+1) for i, s in enumerate(signs)]
                    for signs in itertools.product((-1, 1), repeat=3)])]
    cases = [run_case(*entry) for entry in named]
    rng = random.Random(2026101902)
    for i in range(20):
        n = rng.randrange(1, 5)
        clauses = [[v*rng.choice((-1, 1)) for v in rng.sample(range(1, n+1), rng.randrange(1, min(3, n)+1))]
                   for _ in range(rng.randrange(6))]
        cases.append(run_case("seeded_"+str(i), n, clauses))
    for k in (1, 2, 3, 4, 5, 6, 8, 10):
        clauses = [[2*i+1, 2*i+2] for i in range(k)]
        cases.append(run_case("easy_SAT_state_growth_"+str(k), 2*k, clauses,
                              known_witness=(1 << (2*k))-1))
    replayed = replay(json.loads(json.dumps(cases)))
    if before != hashes():
        raise ArithmeticError("source changed during experiment")
    result = {"schema": "packed_exact_matching_controls_v1", "finished_utc": datetime.now(timezone.utc).isoformat(),
              "scope": "correct encoding to exact binary-weight matching, not ordinary minimum matching",
              "seed": 2026101902, "limits": {"max_states": 512, "max_transitions": 200000},
              "source_sha256": before, "source_unchanged_during_run": True, "cases": cases,
              "serialized_replay": replayed, "seconds": time.perf_counter()-start,
              "summary": {**replayed, "reference_SAT": sum(c["reference"]["satisfiable"] for c in cases),
                          "reference_UNSAT": sum(not c["reference"]["satisfiable"] for c in cases),
                          "assignments_checked": sum(c["reference"]["assignments_checked"] for c in cases)}}
    (HERE/"RESULTS.json").write_text(json.dumps(result, separators=(",", ":"))+"\n", encoding="utf-8")
    print(json.dumps(result["summary"]))


if __name__ == "__main__":
    main()
