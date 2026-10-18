"""Original polynomial oracles, structural adversaries, and certificate mutations."""
from collections import Counter
from copy import deepcopy
from itertools import combinations, combinations_with_replacement, product
import json
from pathlib import Path
import random
import sys
import unittest

import structure as subject

PACKING_SOURCE = Path(__file__).resolve().parent.parent / "packed_cost_exact_matching"
if str(PACKING_SOURCE) not in sys.path:
    sys.path.insert(0, str(PACKING_SOURCE))
import packing


def polynomial_coefficient(pairs, target):
    """Independent exact sparse product, counting both branches even if equal."""
    counts = {0: 1}
    for pair in pairs:
        updated = Counter()
        for exponent, count in counts.items():
            for weight in pair:
                if exponent + weight <= target:
                    updated[exponent + weight] += count
        counts = updated
    return counts.get(target, 0)


def independent_truth_slack_count(n, clauses):
    """Direct original assignments plus explicitly enumerated per-clause slack bits."""
    total = 0
    for values in product((0, 1), repeat=n):
        extensions = 1
        for clause in clauses:
            false = sum(values[abs(lit) - 1] != int(lit > 0) for lit in clause)
            bound = len(clause) - 1
            extensions *= sum(false + sum(slacks) == bound for slacks in product((0, 1), repeat=bound))
        total += extensions
    return total


def solve(n, clauses, order=None, **limits):
    original = packing.encode(n, clauses)
    pairs, target = original["choice_weights"], original["target"]
    local_pairs, local_target = subject.expected_packing(n, clauses)
    assert (pairs, target) == (local_pairs, local_target)
    order = list(range(n)) if order is None else order
    result = subject.solve_structure(n, clauses, pairs, target, order=order, **limits)
    return original, order, result


class StructureTests(unittest.TestCase):
    def test_slack_multiplicity_duplicate_clauses_and_unused_variables(self):
        for n, clauses, expected in ((3, [[1, 2, 3]], 10),
                                     (3, [[1, 2, 3], [1, 2, 3]], 16),
                                     (4, [[1, 2, 3]], 20),
                                     (1, [[1], [-1]], 0), (0, [], 1), (5, [], 32)):
            enc, order, result = solve(n, clauses)
            self.assertEqual(result["status"], "EXACT")
            self.assertEqual(result["coefficient"], expected)
            self.assertEqual(expected, polynomial_coefficient(enc["choice_weights"], enc["target"]))
            self.assertTrue(subject.verify_structure(n, clauses, enc["choice_weights"], enc["target"], result, order=order)["valid"])

    def test_exhaustive_one_and_two_clause_formulas(self):
        count = 0
        for n in range(4):
            pool = []
            for size in range(1, min(3, n) + 1):
                for variables in combinations(range(1, n + 1), size):
                    pool.extend([list(c) for c in product(*[(v, -v) for v in variables])])
            for size in range(3):
                for chosen in combinations_with_replacement(range(len(pool)), size):
                    clauses = [pool[j] for j in chosen]
                    enc, order, result = solve(n, clauses)
                    expected = polynomial_coefficient(enc["choice_weights"], enc["target"])
                    self.assertEqual(result["coefficient"], expected)
                    self.assertEqual(expected, independent_truth_slack_count(n, clauses))
                    self.assertTrue(subject.verify_structure(n, clauses, enc["choice_weights"], enc["target"], result, order=order)["valid"])
                    count += 1
        self.assertEqual(count, 430)

    def test_seeded_original_polynomials_and_order_invariance(self):
        rng = random.Random(641)
        for _ in range(100):
            n = rng.randrange(1, 6)
            clauses = [[v * rng.choice((-1, 1)) for v in rng.sample(range(1, n + 1), rng.randint(1, min(n, 3)))]
                       for _ in range(rng.randrange(5))]
            enc, order, first = solve(n, clauses)
            rng.shuffle(order)
            second = subject.solve_structure(n, clauses, enc["choice_weights"], enc["target"], order=order)
            expected = polynomial_coefficient(enc["choice_weights"], enc["target"])
            self.assertEqual((first["coefficient"], second["coefficient"]), (expected, expected))
            self.assertTrue(subject.verify_structure(n, clauses, enc["choice_weights"], enc["target"], second, order=order)["valid"])

    def test_disjoint_clauses_exponential_sparse_support_but_width_two(self):
        for m in range(1, 6):
            clauses = [[3 * j + 1, 3 * j + 2, 3 * j + 3] for j in range(m)]
            enc, order, result = solve(3 * m, clauses)
            self.assertEqual(result["coefficient"], 10 ** m)
            self.assertEqual(result["stats"]["width"], 2)
            sparse = packing.solve_choices(enc["choice_weights"], enc["target"], max_states=4000)
            self.assertEqual(sparse["status"], "EXACT")
            self.assertEqual(len(sparse["layers"][-1]), enc["target"] + 1)
        m = 24
        clauses = [[3*j + 1, 3*j + 2, 3*j + 3] for j in range(m)]
        enc, _, result = solve(3*m, clauses)
        self.assertEqual(result["coefficient"], 10 ** m)
        self.assertEqual(result["stats"]["peak_bucket_states"], 8)
        self.assertEqual(packing.solve_choices(enc["choice_weights"], enc["target"], max_states=4096)["status"], "UNKNOWN")

    def test_connected_width_two_chain_and_transfer_recurrence(self):
        previous, current = 2, 10
        for m in range(1, 41):
            clauses = [[2*j + 1, 2*j + 2, 2*j + 3] for j in range(m)]
            enc, order, result = solve(2*m + 1, clauses)
            self.assertEqual(result["coefficient"], current)
            self.assertEqual(result["stats"]["width"], 2)
            self.assertTrue(subject.verify_structure(2*m + 1, clauses, enc["choice_weights"], enc["target"], result, order=order)["valid"])
            previous, current = current, 4*current + 6*previous

    def test_shared_variables_cannot_be_independently_summed(self):
        _, _, contradiction = solve(1, [[1], [-1]])
        self.assertEqual(contradiction["coefficient"], 0)
        self.assertEqual(independent_truth_slack_count(1, [[1]]) * independent_truth_slack_count(1, [[-1]]), 1)

    def test_order_matters_and_dense_easy_control_is_unknown(self):
        n = 10
        clauses = [[1, v] for v in range(2, n+1)]
        _, _, bad = solve(n, clauses, max_bucket_states=64)
        enc, good_order, good = solve(n, clauses, list(range(1, n)) + [0], max_bucket_states=64)
        self.assertEqual(bad["status"], "UNKNOWN")
        self.assertIsNone(bad["coefficient"])
        self.assertEqual(good["coefficient"], 2 ** (n-1) + 1)
        self.assertEqual(good["stats"]["width"], 1)
        self.assertTrue(subject.verify_structure(n, clauses, enc["choice_weights"], enc["target"], good,
                                                order=good_order, max_bucket_states=64)["valid"])
        dense = [list(c) for c in combinations(range(1, 17), 2)]
        _, _, unknown = solve(16, dense, max_bucket_states=256)
        self.assertEqual(unknown["status"], "UNKNOWN")
        self.assertIsNone(unknown["positive"])

    def test_exact_budget_boundaries_and_verification_unknown(self):
        n, clauses = 5, [[1, 2, 3], [3, 4, 5]]
        enc, order, result = solve(n, clauses)
        args = (n, clauses, enc["choice_weights"], enc["target"])
        for cap, statistic in (("max_bucket_states", "peak_bucket_states"),
                               ("max_table_entries", "table_entries"),
                               ("max_arithmetic", "arithmetic"),
                               ("max_structure_work", "structure_work")):
            exact = result["stats"][statistic]
            self.assertEqual(subject.solve_structure(*args, order=order, **{cap: exact})["status"], "EXACT")
            self.assertEqual(subject.solve_structure(*args, order=order, **{cap: exact-1})["status"], "UNKNOWN")
            checked = subject.verify_structure(*args, result, order=order, **{cap: exact-1})
            self.assertFalse(checked["valid"])
            self.assertEqual(checked["status"], "UNKNOWN")

    def test_certificate_mutations_and_external_request_binding(self):
        n, clauses = 3, [[1, 2, 3], [-1, 2]]
        enc, order, original = solve(n, clauses)
        args = (n, clauses, enc["choice_weights"], enc["target"])
        mutations = []
        bad = deepcopy(original); bad["steps"][0]["table"][0] += 1; mutations.append(bad)
        bad = deepcopy(original); bad["steps"][0]["scope"] = [1]; mutations.append(bad)
        bad = deepcopy(original); bad["steps"][0]["bucket"].append(0); mutations.append(bad)
        bad = deepcopy(original); bad["stats"]["width"] = 0; mutations.append(bad)
        bad = deepcopy(original); bad["coefficient"] += 1; mutations.append(bad)
        bad = deepcopy(original); bad["positive"] = 1; mutations.append(bad)
        bad = deepcopy(original); bad["steps"][0]["table"][0] = True; mutations.append(bad)
        bad = deepcopy(original); bad["order"][0] = False; mutations.append(bad)
        bad = deepcopy(original); bad["final_factors"] = []; mutations.append(bad)
        for bad in mutations:
            self.assertEqual(subject.verify_structure(*args, bad, order=order)["status"], "INVALID")
        self.assertEqual(subject.verify_structure(*args, original, order=list(reversed(order)))["status"], "INVALID")
        self.assertEqual(subject.verify_structure(n, clauses, enc["choice_weights"], enc["target"]+1,
                                                original, order=order)["status"], "INVALID")
        wrong_pairs = deepcopy(enc["choice_weights"]); wrong_pairs[0][0] += 1
        self.assertEqual(subject.verify_structure(n, clauses, wrong_pairs, enc["target"], original, order=order)["status"], "INVALID")

    def test_validation_json_and_large_count_bit_bound(self):
        enc, order, result = solve(256, [])
        self.assertEqual(result["coefficient"], 1 << 256)
        self.assertEqual(result["stats"]["peak_count_bits"], 257)
        replay = json.loads(json.dumps(result))
        self.assertTrue(subject.verify_structure(256, [], enc["choice_weights"], 0, replay, order=order)["valid"])
        for n, clauses, order in ((True, [], []), (1, [[True]], [0]), (1, [[1, -1]], [0]),
                                  (1, [[]], [0]), (1, [[1]], [True]), (2, [], [0, 0])):
            with self.assertRaises(ValueError):
                subject.solve_structure(n, clauses, [], 0, order=order)
        self.assertEqual(subject.solve_structure(10**9, [], [], 0, order=[])["status"], "UNKNOWN")
        with self.assertRaises(ValueError):
            subject.solve_structure(0, [], [], 0, order=[], max_arithmetic=True)

    def test_original_unsat_and_planted_high_interaction_controls(self):
        clauses = [list(c) for c in product((1, -1), (2, -2), (3, -3))]
        enc, order, result = solve(3, clauses)
        self.assertEqual(result["coefficient"], 0)
        self.assertEqual(independent_truth_slack_count(3, clauses), 0)
        self.assertTrue(subject.verify_structure(3, clauses, enc["choice_weights"], enc["target"], result, order=order)["valid"])
        for n, seed in ((24, 24018), (32, 32018)):
            rng = random.Random(seed)
            assignment = rng.getrandbits(n)
            clauses = []
            for _ in range(4*n):
                clause = [v*rng.choice((-1, 1)) for v in rng.sample(range(1, n+1), 3)]
                if not any(bool(assignment >> (abs(lit)-1) & 1) == (lit > 0) for lit in clause):
                    clause[0] = abs(clause[0]) * (1 if assignment >> (abs(clause[0])-1) & 1 else -1)
                clauses.append(clause)
            enc, order, unknown = solve(n, clauses, max_bucket_states=256)
            self.assertTrue(packing.satisfied(n, clauses, assignment))
            bits = packing.encode_solution(enc, assignment)
            self.assertTrue(packing.verify_matching(enc, packing.matching_for_choices(bits))["valid"])
            self.assertEqual(unknown["status"], "UNKNOWN")
            self.assertIsNone(unknown["coefficient"])


if __name__ == "__main__":
    unittest.main()
