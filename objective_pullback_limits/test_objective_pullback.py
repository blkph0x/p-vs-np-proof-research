import copy
import itertools
import json
import random
import unittest

from objective_pullback import classify, verify


def oracle(rows, m, weights):
    # Independently evaluate each output bit as a sum of input bits mod two.
    values = []
    for z in range(1 << m):
        bits = [(z >> j) & 1 for j in range(m)]
        values.append(sum(w * (sum(bits[j] for j in range(m) if (r >> j) & 1) % 2)
                          for r, w in zip(rows, weights)))
    unary = [values[1 << j] for j in range(m)]
    additive = all(v == sum(unary[j] for j in range(m) if (z >> j) & 1)
                   for z, v in enumerate(values))
    return additive, unary


class ObjectiveTests(unittest.TestCase):
    def test_exhaustive(self):
        for m in range(4):
            for n in range(4):
                for rows in itertools.product(range(1 << m), repeat=n):
                    for weights in itertools.product(range(2), repeat=n):
                        expected, costs = oracle(rows, m, weights)
                        c = classify(rows, m, weights)
                        self.assertEqual(c["additive"], expected)
                        self.assertTrue(verify(rows, m, weights, c)["valid"])
                        if expected:
                            self.assertEqual(c["unary_costs"], costs)

    def test_seeded_integer_weights(self):
        rng = random.Random(2026101808)
        for _ in range(150):
            m, n = rng.randrange(7), rng.randrange(9)
            rows = [rng.randrange(1 << m) for _ in range(n)]
            weights = [rng.choice([0, 1, 7, 10**50]) for _ in rows]
            c = classify(rows, m, weights)
            self.assertEqual(c["additive"], oracle(rows, m, weights)[0])
            self.assertTrue(verify(rows, m, weights, json.loads(json.dumps(c)))["valid"])

    def test_nonadditive_certificate_tampering(self):
        rows, weights = [1, 2, 3], [1, 1, 1]
        good = classify(rows, 2, weights)
        self.assertEqual(good["values"], [2, 2, 2])
        self.assertEqual(good["defect"], 2)
        for key, value in [("pair", [0, 0]), ("pair", [0, True]),
                           ("values", [2, 2, 4]), ("defect", 0),
                           ("input_hash", "wrong"), ("additive", 0)]:
            bad = copy.deepcopy(good)
            bad[key] = value
            self.assertFalse(verify(rows, 2, weights, bad)["valid"])

    def test_additive_zero_weight_outputs(self):
        c = classify([1, 2, 3, 0], 2, [4, 5, 0, 100])
        self.assertEqual(c["unary_costs"], [4, 5])
        c["unary_costs"][0] = 3
        self.assertFalse(verify([1, 2, 3, 0], 2, [4, 5, 0, 100], c)["valid"])

    def test_caps_and_invalid_inputs(self):
        self.assertEqual(classify([], 10**9, [], max_columns=10)["status"], "UNKNOWN")
        self.assertEqual(verify([], 10**9, [], {}, max_columns=10)["status"], "UNKNOWN")
        for rows, m, costs in [([3], 1, [1]), ([1], 1, [-1]), ([True], 1, [1]),
                               ([1], 1, []), ([1], True, [1])]:
            with self.assertRaises(ValueError):
                classify(rows, m, costs)

    def test_integers_beyond_decimal_conversion_limit(self):
        for rows, m, weights in [([1], 1, [1 << 15000]),
                                 ([1 << 15000], 15001, [1]),
                                 ([3], 2, [1 << 15000])]:
            c = classify(rows, m, weights)
            self.assertEqual(c["status"], "EXACT")
            self.assertTrue(verify(rows, m, weights, c)["valid"])

    def test_scope_counterexamples(self):
        # Restrict z to {00,11}: XOR has additive zero cost on this domain.
        self.assertFalse(classify([3], 2, [1])["additive"])
        self.assertEqual([((3 & z).bit_count() & 1) for z in (0, 3)], [0, 0])
        # Signed output costs or affine offsets can cancel identical XORs.
        for z in range(4):
            parity = (3 & z).bit_count() & 1
            self.assertEqual(parity - parity, 0)
            self.assertEqual(parity + (1 - parity), 1)


if __name__ == "__main__":
    unittest.main(verbosity=2)
