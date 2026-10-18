"""Reproducible original-product queries and independent bounded count checks."""
from hashlib import sha256
from itertools import combinations, combinations_with_replacement, product
import json
from math import gcd
from pathlib import Path
import random
from time import perf_counter

import structure
from test_structure import packing, polynomial_coefficient, independent_truth_slack_count


DIRECTORY = Path(__file__).resolve().parent


def source_hashes():
    names = ("structure.py", "test_structure.py", "run_experiments.py", "THEOREM.md",
             "../packed_cost_exact_matching/packing.py")
    return {name: sha256((DIRECTORY / name).read_bytes()).hexdigest() for name in names}


def planted(n, seed):
    rng = random.Random(seed)
    assignment = rng.getrandbits(n)
    clauses = []
    for _ in range(4*n):
        clause = [v*rng.choice((-1, 1)) for v in rng.sample(range(1, n+1), 3)]
        if not any(bool(assignment >> (abs(lit)-1) & 1) == (lit > 0) for lit in clause):
            v = abs(clause[0])
            clause[0] = v if assignment >> (v-1) & 1 else -v
        clauses.append(clause)
    return clauses, assignment


def run():
    started, hashes = perf_counter(), source_hashes()
    totals = {"small_formulas": 0, "exact_coefficients_compared": 0,
              "original_choice_factors": 0, "original_logical_assignments": 0,
              "certificates_verified": 0}

    def small(n, clauses, order):
        original = packing.encode(n, clauses)
        pairs, target = original["choice_weights"], original["target"]
        if structure.expected_packing(n, clauses) != (pairs, target):
            raise ArithmeticError("local formula interpretation differs from original encoding")
        result = structure.solve_structure(n, clauses, pairs, target, order=order)
        if result["status"] != "EXACT":
            raise ArithmeticError("small control unexpectedly exceeded budget")
        check = structure.verify_structure(n, clauses, pairs, target, result, order=order)
        expected = polynomial_coefficient(pairs, target)
        truth = independent_truth_slack_count(n, clauses)
        if not check["valid"] or result["coefficient"] != expected or expected != truth:
            raise ArithmeticError("original polynomial, direct slack enumeration and certified count disagree")
        totals["small_formulas"] += 1
        totals["exact_coefficients_compared"] += 1
        totals["original_choice_factors"] += len(pairs)
        totals["original_logical_assignments"] += 1 << n
        totals["certificates_verified"] += 1

    for n in range(4):
        pool = []
        for width in range(1, min(n, 3)+1):
            for variables in combinations(range(1, n+1), width):
                pool.extend([list(c) for c in product(*[(v, -v) for v in variables])])
        for count in range(3):
            for indices in combinations_with_replacement(range(len(pool)), count):
                small(n, [pool[i] for i in indices], list(range(n)))
    exhaustive = totals["small_formulas"]
    rng = random.Random(2026101809)
    for _ in range(200):
        n = rng.randrange(1, 7)
        clauses = [[v*rng.choice((-1, 1)) for v in rng.sample(range(1, n+1), rng.randint(1, min(n, 3)))]
                   for _ in range(rng.randrange(6))]
        order = list(range(n)); rng.shuffle(order)
        small(n, clauses, order)

    controls = []

    def control(name, n, clauses, *, order=None, expected=None, assignment=None,
                limits=None, compare_sparse=False, note=None):
        original = packing.encode(n, clauses)
        if not packing.verify_encoding(n, clauses, original):
            raise ArithmeticError("original encoder failed its independent checker")
        order = list(range(n)) if order is None else order
        limits = {} if limits is None else limits
        pairs, target = original["choice_weights"], original["target"]
        result = structure.solve_structure(n, clauses, pairs, target, order=order, **limits)
        verified = None
        if result["status"] == "EXACT":
            verified = structure.verify_structure(n, clauses, pairs, target, result, order=order, **limits)
            if not verified["valid"] or expected is not None and result["coefficient"] != expected:
                raise ArithmeticError("named coefficient or certificate failed")
            totals["certificates_verified"] += 1
        oracles = {}
        if n <= 10:
            oracles["direct_original_assignments_and_slacks"] = independent_truth_slack_count(n, clauses)
            if result["status"] == "EXACT" and oracles["direct_original_assignments_and_slacks"] != result["coefficient"]:
                raise ArithmeticError("named logical/slack oracle disagrees")
        if len(pairs) <= 16:
            oracles["original_sparse_polynomial"] = polynomial_coefficient(pairs, target)
            if result["status"] == "EXACT" and oracles["original_sparse_polynomial"] != result["coefficient"]:
                raise ArithmeticError("named polynomial oracle disagrees")
        known = None
        if assignment is not None:
            if not all(any(bool(assignment >> (abs(lit)-1) & 1) == (lit > 0) for lit in c) for c in clauses):
                raise ArithmeticError("planted original assignment fails")
            bits = packing.encode_solution(original, assignment)
            matching = packing.matching_for_choices(bits)
            replay = packing.verify_matching(original, matching)
            if not replay["valid"] or replay["cost"] != target:
                raise ArithmeticError("known original exact-weight witness fails")
            known = {"assignment": assignment, "choice_bits": bits, "matching_edge_ids": matching,
                     "original_matching_verification": replay}
        normalized_min = sum(min(p) for p in pairs)
        deltas = [abs(a-b) for a, b in pairs]
        divisor = 0
        for d in deltas:
            divisor = gcd(divisor, d)
        shifted_target = target - normalized_min
        prechecks = {"monomial_shift": normalized_min, "differences": deltas,
                     "shifted_target": shifted_target, "difference_sum": sum(deltas), "gcd": divisor,
                     "interval_pass": 0 <= shifted_target <= sum(deltas),
                     "gcd_pass": shifted_target == 0 if divisor == 0 else shifted_target % divisor == 0}
        sparse = None
        if compare_sparse:
            sparse = packing.solve_choices(pairs, target, max_states=4096, max_transitions=1000000)
        controls.append({"name": name, "original_encoding": original, "external_order": order,
                         "limits": limits, "result": result, "verification": verified,
                         "independent_expected_coefficient": expected, "oracles": oracles,
                         "known_original_solution": known, "normalized_subset_sum_prechecks": prechecks,
                         "prior_sparse_reference": sparse, "note": note})

    control("one_ternary_multiplicity", 3, [[1, 2, 3]], expected=10)
    control("repeated_ternary_not_deduplicated", 3, [[1, 2, 3], [1, 2, 3]], expected=16)
    control("unused_logical_variable", 4, [[1, 2, 3]], expected=20)
    control("shared_contradictory_units", 1, [[1], [-1]], expected=0)
    control("original_gap_passes_interval_and_gcd", 3, [[1], [-1], [2, 3]], expected=0)
    control("all_eight_ternary_polarities_UNSAT", 3,
            [list(c) for c in product((1, -1), (2, -2), (3, -3))], expected=0, compare_sparse=True)
    m = 24
    control("disjoint_24_ternary_clauses", 3*m,
            [[3*j+1, 3*j+2, 3*j+3] for j in range(m)], expected=10**m,
            assignment=(1 << (3*m))-1, compare_sparse=True,
            note={"full_sparse_final_states": 2*(6**m-1)//5+1, "proof": "independent base-six digits0..5"})
    m = 40
    previous, current = 2, 10
    for _ in range(1, m):
        previous, current = current, 4*current + 6*previous
    control("connected_40_clause_width_two_chain", 2*m+1,
            [[2*j+1, 2*j+2, 2*j+3] for j in range(m)], expected=current,
            assignment=(1 << (2*m+1))-1, compare_sparse=True,
            note={"transfer_matrix": [[1, 3], [3, 3]], "C0": 2, "C1": 10})
    n = 10
    star = [[1, v] for v in range(2, n+1)]
    control("star_bad_external_order", n, star, expected=2**(n-1)+1, assignment=(1 << n)-1,
            limits={"max_bucket_states": 64})
    control("star_good_external_order", n, star, order=list(range(1, n))+[0],
            expected=2**(n-1)+1, assignment=(1 << n)-1, limits={"max_bucket_states": 64})
    n = 16
    control("complete_interaction_every_order_width15", n, [list(c) for c in combinations(range(1, n+1), 2)],
            expected=n+1, assignment=(1 << n)-1, limits={"max_bucket_states": 256},
            note="all orders have width n−1; positive 2CNF is easy despite this table obstruction")
    for n, seed in ((24, 24018), (32, 32018)):
        clauses, assignment = planted(n, seed)
        control(f"planted_mixed_3CNF_n{n}_m{4*n}", n, clauses, assignment=assignment,
                limits={"max_bucket_states": 256}, compare_sparse=True, note={"seed": seed})
    control("empty_product", 0, [], expected=1, assignment=0)
    control("256_unused_variables_preserve_all_choices", 256, [], expected=1 << 256, assignment=0)
    if source_hashes() != hashes:
        raise RuntimeError("source changed during experiment")
    summary = {**totals, "exhaustive_formulas": exhaustive, "seeded_formulas": 200,
               "named_controls": len(controls),
               "named_exact": sum(c["result"]["status"] == "EXACT" for c in controls),
               "named_unknown": sum(c["result"]["status"] == "UNKNOWN" for c in controls),
               "original_positive_witnesses": sum(c["known_original_solution"] is not None for c in controls)}
    result = {"format": "packed-clause-factor-count-experiment-v1", "source_sha256": hashes,
              "sources_unchanged_during_run": True, "summary": summary, "controls": controls,
              "elapsed_seconds": perf_counter()-started}
    (DIRECTORY / "RESULTS.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    return result


if __name__ == "__main__":
    print(json.dumps(run()["summary"]))
