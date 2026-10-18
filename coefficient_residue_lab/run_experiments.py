"""Save bounded exact coefficient/residue controls and original-input proofs."""
from collections import Counter
from datetime import datetime, timezone
from hashlib import sha256
from itertools import product
import json
from math import lcm
from pathlib import Path
import random
from time import perf_counter

from coefficient_residue import build_coefficient_proof, verify_choice_witness, verify_coefficient_proof


PRODUCER_LIMITS = {"max_states": 128, "max_total_states": 10000, "max_transitions": 100000}
VERIFICATION_LIMITS = {"max_states": 4096, "max_total_states": 100000, "max_transitions": 1000000}


def _hashes(directory):
    return {name: sha256((directory / name).read_bytes()).hexdigest() for name in (
        "coefficient_residue.py", "test_coefficient_residue.py", "run_experiments.py", "THEOREM.md")}


def run_experiments():
    directory = Path(__file__).resolve().parent
    before, started = _hashes(directory), perf_counter()
    cases = []
    totals = {"cases": 0, "queries": 0, "exact_queries": 0, "unknown_queries": 0,
              "verified_certificates": 0, "residue_witnesses": 0, "exact_weight_witnesses": 0,
              "independent_choice_words_enumerated": 0}

    def case(name, choices, target, query_moduli, *, explicit_witness=None, note=None):
        reference = None
        if len(choices) <= 8:
            counts = Counter(sum(pair[bit] for pair, bit in zip(choices, bits))
                             for bits in product((0, 1), repeat=len(choices)))
            reference = {"method": "bounded independent enumeration of original binary choices",
                         "choice_words": 1 << len(choices), "support_size": len(counts),
                         "coefficients": [list(item) for item in sorted(counts.items())],
                         "target_coefficient": counts[target]}
            totals["independent_choice_words_enumerated"] += 1 << len(choices)
        queries = []
        for label, modulus in query_moduli:
            query_started = perf_counter()
            result = build_coefficient_proof(choices, target, modulus=modulus, **PRODUCER_LIMITS)
            build_seconds = perf_counter() - query_started
            totals["queries"] += 1
            verification = None
            verify_seconds = 0
            if result["status"] == "EXACT":
                verify_started = perf_counter()
                verification = verify_coefficient_proof(choices, target, result["certificate"],
                                                        modulus=modulus, **VERIFICATION_LIMITS)
                verify_seconds = perf_counter() - verify_started
                if not verification["valid"]:
                    raise AssertionError("saved coefficient proof failed independent recurrence verification")
                totals["exact_queries"] += 1
                totals["verified_certificates"] += 1
                if reference is not None:
                    folded = Counter()
                    for exponent, count in reference["coefficients"]:
                        folded[exponent if modulus is None else exponent % modulus] += count
                    if dict(result["certificate"]["layers"][-1]) != dict(folded):
                        raise AssertionError("coefficient table disagrees with independent choice expansion")
                if result["witness"] is not None:
                    if not verify_choice_witness(choices, target, result["witness"], modulus=modulus)["valid"]:
                        raise AssertionError("original choice witness failed")
                    totals["exact_weight_witnesses" if modulus is None else "residue_witnesses"] += 1
            elif result["status"] == "UNKNOWN":
                totals["unknown_queries"] += 1
                if any(result[key] is not None for key in ("target_coefficient", "attainable", "certificate", "witness")):
                    raise AssertionError("unfinished query made a final claim")
            else:
                raise AssertionError("unexpected producer status")
            queries.append({"label": label, "modulus": modulus, "result": result,
                            "independent_verification": verification,
                            "build_seconds": build_seconds, "verify_seconds": verify_seconds})
        witness_check = None
        if explicit_witness is not None:
            witness_check = verify_choice_witness(choices, target, explicit_witness)
            if not witness_check["valid"]:
                raise AssertionError("independent positive-control witness failed")
        cases.append({"name": name, "choices": [list(pair) for pair in choices], "target": target,
                      "reference": reference, "queries": queries, "note": note,
                      "explicit_original_witness": explicit_witness,
                      "explicit_original_witness_verification": witness_check})
        totals["cases"] += 1

    moduli = [2, 3, 5, 7]
    case("separate_residue_false_positive", [(1, 6), (0, 36), (0, 36), (0, 36)], 36,
         [("exact coefficient", None)] + [(f"separate modulus {m}", m) for m in moduli]
         + [("one common residue witness", lcm(*moduli))],
         note="Separate witnesses have weights6,6,1,1. The lcm210 exceeds degree114 but no common witness exists.")
    rng = random.Random(20261018)
    for index in range(8):
        choices = [(rng.randrange(13), rng.randrange(13)) for _ in range(rng.randrange(1, 8))]
        target = rng.randrange(sum(max(pair) for pair in choices) + 3)
        case(f"seeded_small_{index}", choices, target,
             [("exact coefficient", None), ("separate modulus 3", 3),
              ("separate modulus 5", 5), ("joint lcm", 15)])
    case("non_coprime_joint_uses_lcm", [(0, 2), (1, 4), (0, 7)], 9,
         [("exact coefficient", None), ("separate modulus 4", 4),
          ("separate modulus 6", 6), ("joint lcm, not product", 12)])
    case("empty_product", [], 0, [("exact coefficient", None), ("modulus one", 1), ("modulus three", 3)])
    case("equal_choices_preserve_multiplicity", [(0, 0)] * 32, 0,
         [("exact coefficient", None), ("modulus seven", 7)],
         explicit_witness={"bits": [0] * 32, "total_weight": 0},
         note="Support has one exponent but coefficient is2^32; binary choices remain distinct.")
    for factor_count in (8, 12, 16, 24):
        choices = [(0, 1 << i) for i in range(factor_count)]
        target = (1 << factor_count) - 1
        case(f"easy_positive_joint_state_growth_{factor_count}", choices, target,
             [("exact coefficient", None)] + [(f"separate modulus {m}", m) for m in (17, 19, 23)]
             + [("joint lcm", lcm(17, 19, 23))],
             explicit_witness={"bits": [1] * factor_count, "total_weight": target},
             note="The all-one choice is an easy exact witness. UNKNOWN measures this sparse-table method, not inherent instance hardness.")
    after = _hashes(directory)
    if before != after:
        raise RuntimeError("source changed during experiment")
    result = {"schema": "binary_product_coefficient_residue_controls_v1",
              "finished_utc": datetime.now(timezone.utc).isoformat(),
              "scope": "Sparse and cyclic counted-layer controls; no general coefficient-query lower bound or P-versus-NP resolution.",
              "seed": 20261018, "producer_limits": PRODUCER_LIMITS,
              "verification_limits": VERIFICATION_LIMITS, "summary": totals, "cases": cases,
              "source_sha256": before, "source_unchanged_during_run": True,
              "seconds": perf_counter() - started}
    destination = directory / "RESULTS.json"
    destination.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    return result


if __name__ == "__main__":
    print(json.dumps(run_experiments()["summary"]))
