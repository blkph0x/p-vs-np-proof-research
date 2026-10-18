import importlib.util
import random
import sys
import unittest
from itertools import combinations, product
from pathlib import Path


MODULE = Path(__file__).with_name("randomized_isolation.py")
SPEC = importlib.util.spec_from_file_location("randomized_isolation_test", MODULE)
iso = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = iso
SPEC.loader.exec_module(iso)


class RandomizedIsolationTests(unittest.TestCase):
    def test_pairwise_uniformity_of_linear_hashes(self):
        n, r = 3, 2
        for difference in range(1, 1 << n):
            counts = [0] * (1 << r)
            for rows in iso.all_matrices(n, r):
                counts[iso.hash_value(rows, difference)] += 1
            self.assertEqual(counts, [2 ** (n * r - r)] * (1 << r))

    def test_exact_probability_for_every_small_set(self):
        n = 3
        checked = 0
        for mask in range(1, 1 << (1 << n)):
            assignments = tuple(x for x in range(1 << n) if mask >> x & 1)
            r = iso.choose_rank(len(assignments))
            success, total = iso.exact_isolation_probability(assignments, n, r)
            mu, lower = iso.second_moment_bound(len(assignments), r)
            self.assertGreaterEqual(success / total, lower - 1e-15)
            self.assertGreaterEqual(success / total, 3 / 16 - 1e-15)
            checked += 1
        self.assertEqual(checked, 255)

    def test_second_moment_formula_and_rank_range(self):
        for size in range(1, 65):
            r = iso.choose_rank(size)
            mu, lower = iso.second_moment_bound(size, r)
            self.assertGreaterEqual(mu, 1 / 4)
            self.assertLessEqual(mu, 1 / 2)
            self.assertGreaterEqual(lower, 3 / 16 - 1e-15)

    def test_cnf_models_and_unique_hash_survivors(self):
        cases = [
            (2, [[1], [-2]], (1,)),
            (2, [[1, 2]], (1, 2, 3)),
            (2, [[1, -1]], (0, 1, 2, 3)),
            (2, [[], [1]], ()),
        ]
        for n, clauses, expected in cases:
            self.assertEqual(iso.models(n, clauses), expected)
        result = iso.isolate_cnf(2, [[1, 2]], (1, 2), 1)
        self.assertEqual(result.survivors, (1,))

    def test_seeded_hash_replay(self):
        rng = random.Random(2026101920)
        for n in range(1, 7):
            for _ in range(40):
                assignments = tuple(x for x in range(1 << n) if rng.randrange(2))
                if not assignments:
                    assignments = (rng.randrange(1 << n),)
                r = iso.choose_rank(len(assignments))
                rows = iso.random_hash(n, r, rng)
                target = rng.randrange(1 << r)
                direct = tuple(x for x in assignments
                               if all(((row & x).bit_count() & 1) == ((target >> i) & 1)
                                      for i, row in enumerate(rows)))
                self.assertEqual(iso.survivors(assignments, rows, target), direct)

    def test_malformed_inputs(self):
        for n, r in [(-1, 1), (1, -1), (True, 1)]:
            with self.assertRaises(ValueError):
                list(iso.all_matrices(n, r))
        for size in [0, -1, True, 1.0]:
            with self.assertRaises(ValueError):
                iso.choose_rank(size)
        for n, clauses in [(1, [[0]]), (1, [[2]]), (1, [None]), (True, [])]:
            with self.assertRaises(ValueError):
                iso.models(n, clauses)


if __name__ == "__main__":
    unittest.main()

