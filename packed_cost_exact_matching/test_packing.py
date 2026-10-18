import copy
import itertools
import random
import unittest

from packing import (encode, encode_solution, matching_for_choices, satisfied,
                     solve_choices, verify_choices, verify_matching, verify_encoding)


def truth(clauses, assignment):
    return all(any((assignment[abs(x)-1] == 1) if x > 0 else (assignment[abs(x)-1] == 0)
                   for x in clause) for clause in clauses)


class PackingTests(unittest.TestCase):
    def check_formula(self, n, clauses):
        data = encode(n, clauses)
        self.assertTrue(verify_encoding(n, clauses, data))
        valid = [bits for bits in itertools.product((0, 1), repeat=n) if truth(clauses, bits)]
        found = []
        for bits in itertools.product((0, 1), repeat=len(data["choice_weights"])):
            cost = sum(pair[b] for pair, b in zip(data["choice_weights"], bits))
            if cost == data["target"]:
                self.assertTrue(truth(clauses, bits[:n]))
                self.assertTrue(verify_matching(data, matching_for_choices(bits))["valid"])
                found.append(bits[:n])
        self.assertEqual(set(found), set(valid))
        for bits in valid:
            assignment = sum(b << i for i, b in enumerate(bits))
            choices = encode_solution(data, assignment)
            self.assertTrue(verify_matching(data, matching_for_choices(choices))["valid"])
        result = solve_choices(data["choice_weights"], data["target"], max_states=20000)
        self.assertEqual(result["feasible"], bool(valid))
        self.assertTrue(verify_choices(data["choice_weights"], data["target"], result)["valid"])

    def test_exhaustive_small_formulas(self):
        self.check_formula(0, [])
        for n in (1, 2):
            clauses = []
            for size in range(1, n+1):
                for variables in itertools.combinations(range(1, n+1), size):
                    for signs in itertools.product((-1, 1), repeat=size):
                        clauses.append(tuple(v*s for v, s in zip(variables, signs)))
            for m in range(3):
                for request in itertools.product(clauses, repeat=m):
                    self.check_formula(n, request)

    def test_seeded_width_three_formulas(self):
        rng = random.Random(2026101901)
        for _ in range(35):
            clauses = []
            for _ in range(rng.randrange(4)):
                variables = rng.sample(range(1, 4), rng.randrange(1, 4))
                clauses.append([v*rng.choice((-1, 1)) for v in variables])
            self.check_formula(3, clauses)

    def test_cost_dp_against_all_binary_choices(self):
        rng = random.Random(773)
        for _ in range(250):
            pairs = [[rng.randrange(10), rng.randrange(10)] for _ in range(rng.randrange(9))]
            target = rng.randrange(45)
            possible = {sum(p[b] for p, b in zip(pairs, bits))
                        for bits in itertools.product((0, 1), repeat=len(pairs))}
            result = solve_choices(pairs, target)
            self.assertEqual(result["feasible"], target in possible)
            self.assertTrue(verify_choices(pairs, target, result)["valid"])

    def test_exact_target_gap_is_not_min_or_range(self):
        data = encode(3, [[1], [-1], [2, 3]])
        low = sum(min(pair) for pair in data["choice_weights"])
        high = sum(max(pair) for pair in data["choice_weights"])
        self.assertLess(low, data["target"])
        self.assertGreater(high, data["target"])
        self.assertFalse(solve_choices(data["choice_weights"], data["target"])["feasible"])
        minbits = [int(p[1] < p[0]) for p in data["choice_weights"]]
        self.assertTrue(verify_matching(data, matching_for_choices(minbits), exact=False)["valid"])
        self.assertFalse(verify_matching(data, matching_for_choices(minbits))["valid"])

    def test_budget_is_unknown(self):
        pairs = [[0, 1 << i] for i in range(20)]
        result = solve_choices(pairs, (1 << 20)-1, max_states=64)
        self.assertEqual(result["status"], "UNKNOWN")
        self.assertNotIn("feasible", result)
        self.assertEqual(verify_choices(pairs, (1 << 20)-1, result)["status"], "UNKNOWN")
        result = solve_choices([[0, 1]], 1, max_transitions=1)
        self.assertEqual(result["status"], "UNKNOWN")
        self.assertEqual(solve_choices([], 0, max_states=0)["status"], "UNKNOWN")

    def test_certificate_mutations(self):
        pairs, target = [[0, 1], [0, 4]], 5
        good = solve_choices(pairs, target)
        for key, value in [("layers", [[0], [0, 1], [0, 1, 4]]), ("feasible", False),
                           ("choice_bits", [0, 0]), ("choice_bits", [True, 1]),
                           ("transitions", 1), ("peak_states", 99), ("input_hash", "bad")]:
            bad = copy.deepcopy(good); bad[key] = value
            self.assertFalse(verify_choices(pairs, target, bad)["valid"])
        self.assertFalse(verify_choices([[0, 2], [0, 4]], target, good)["valid"])
        self.assertFalse(verify_choices(pairs, target+1, good)["valid"])
        self.assertEqual(verify_choices(pairs, target, good, max_transitions=0)["status"], "UNKNOWN")

    def test_matching_mutations(self):
        data = encode(2, [[1, -2]])
        support = matching_for_choices(encode_solution(data, 1))
        self.assertTrue(verify_matching(data, support)["valid"])
        for bad in (support[:-1], support+[support[0]], [True]+support[1:], [999]):
            self.assertFalse(verify_matching(data, bad)["valid"])

    def test_encoding_binds_original_formula_and_graph(self):
        good = encode(2, [[1, -2]])
        for key, value in [("target", 99), ("n", True), ("base", 5), ("vertices", 8),
                           ("choice_weights", [[0, 0]]*3), ("slack_clauses", [True])]:
            bad = copy.deepcopy(good); bad[key] = value
            self.assertFalse(verify_encoding(2, [[1, -2]], bad))
        self.assertFalse(verify_encoding(2, [[-1, 2]], good))
        bad = copy.deepcopy(good); bad["clauses"][0][0] = True
        self.assertFalse(verify_encoding(2, [[1, -2]], bad))
        bad = copy.deepcopy(good); bad["edges"][0][2] += 1
        self.assertFalse(verify_encoding(2, [[1, -2]], bad))

    def test_large_binary_weights(self):
        pairs = [[0, 1 << 15000], [0, 3]]
        target = (1 << 15000)+3
        result = solve_choices(pairs, target)
        self.assertTrue(verify_choices(pairs, target, result)["valid"])

    def test_polynomial_bitlength_not_small_magnitude(self):
        data = encode(3, [[1, 2, 3]]*64)
        self.assertEqual(data["vertices"], 4*(3+128))
        self.assertLessEqual(data["target"].bit_length(), 3*64)
        self.assertGreater(data["target"], 2**64)
        support = matching_for_choices(encode_solution(data, 7))
        self.assertTrue(verify_matching(data, support)["valid"])

    def test_empty_and_invalid_inputs(self):
        self.assertTrue(solve_choices([], 0)["feasible"])
        self.assertFalse(solve_choices([], 1)["feasible"])
        for n, clauses in [(True, []), (1, [[]]), (1, [[1, -1]]), (1, [[2]]), (1, [[True]])]:
            with self.assertRaises(ValueError):
                encode(n, clauses)
        for pairs, target in [([[0, -1]], 0), ([[0, True]], 0), ([[0]], 0), ([], -1)]:
            with self.assertRaises(ValueError):
                solve_choices(pairs, target)


if __name__ == "__main__":
    unittest.main(verbosity=2)
