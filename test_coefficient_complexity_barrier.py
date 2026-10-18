import importlib.util
import random
import sys
import unittest
from itertools import combinations, product
from pathlib import Path


MODULE = Path(__file__).with_name("coefficient_complexity_barrier.py")
SPEC = importlib.util.spec_from_file_location("coefficient_complexity_barrier_test", MODULE)
barrier = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = barrier
SPEC.loader.exec_module(barrier)


class CoefficientBarrierTests(unittest.TestCase):
    def assert_equivalent(self, instance):
        direct = barrier.exact_cover_count(instance)
        encoded = barrier.encoded_coefficient(instance)
        self.assertEqual(encoded, direct, instance)
        self.assertLessEqual(encoded.bit_length(), barrier.coefficient_bit_bound(len(instance.triples)))
        for selection in range(1 << len(instance.triples)):
            chosen = tuple((0, exponent) for i, exponent in enumerate(instance.exponents)
                           if selection >> i & 1)
            self.assertEqual(sum(exponent for _, exponent in chosen) == instance.target,
                             barrier.exact_cover(instance, selection))

    def test_all_two_by_two_by_two_families(self):
        possible = tuple((a, 2 + b, 4 + c) for a, b, c in product(range(2), repeat=3))
        families = selections = positive = 0
        for mask in range(1 << len(possible)):
            triples = [triple for i, triple in enumerate(possible) if mask >> i & 1]
            instance = barrier.encode_x3c(6, triples)
            self.assert_equivalent(instance)
            families += 1
            selections += 1 << len(triples)
            positive += barrier.exact_cover_count(instance) > 0
        self.assertEqual((families, selections, positive), (256, 6561, 175))

    def test_small_general_families_and_duplicates(self):
        possible = tuple(combinations(range(6), 3))
        checked = 0
        for size in range(4):
            for triples in combinations(possible, size):
                self.assert_equivalent(barrier.encode_x3c(6, triples))
                checked += 1
        duplicate = barrier.encode_x3c(3, ((0, 1, 2), (0, 1, 2)))
        self.assertEqual(barrier.encoded_coefficient(duplicate), 2)
        self.assertEqual(checked, 1351)

    def test_general_binomial_multiplicity(self):
        self.assertEqual(barrier.binomial_coefficient(((0, 1), (0, 1)), 1), 2)
        self.assertEqual(barrier.binomial_coefficient(((2, 2),), 2), 2)
        self.assertEqual(barrier.binomial_coefficient(((1, 3), (0, 2)), 3), 2)
        self.assertEqual(barrier.binomial_coefficient(((1, 3), (0, 2)), 5), 1)

    def test_seeded_digit_no_carry_controls(self):
        rng = random.Random(2026101918)
        for _ in range(200):
            n = 3 * rng.randrange(0, 5)
            m = rng.randrange(0, 8) if n else 0
            triples = []
            for _ in range(m):
                triples.append(tuple(sorted(rng.sample(range(n), 3))) if n else ())
            instance = barrier.encode_x3c(n, triples)
            self.assert_equivalent(instance)

    def test_bit_accounting_and_target(self):
        instance = barrier.encode_x3c(6, ((0, 1, 2), (3, 4, 5)))
        self.assertEqual(instance.base, 3)
        self.assertEqual(instance.target, sum(3 ** i for i in range(6)))
        self.assertTrue(all(exponent.bit_length() <= 6 * instance.base.bit_length()
                            for exponent in instance.exponents))
        self.assertEqual(barrier.encoded_coefficient(instance), 1)

    def test_malformed_inputs(self):
        for args in [(-1, ()), (1, ()), (4, ()), (True, ())]:
            with self.assertRaises(ValueError):
                barrier.encode_x3c(*args)
        for triples in [((0, 1),), ((0, 1, 1),), ((0, 1, 6),), ((0, 1, -1),),
                        ((0, 1, True),), ((0, 1, 2.0),)]:
            with self.assertRaises(ValueError):
                barrier.encode_x3c(6, triples)
        for target in (-1, True, 1.0):
            with self.assertRaises(ValueError):
                barrier.binomial_coefficient((), target)


if __name__ == "__main__":
    unittest.main()
