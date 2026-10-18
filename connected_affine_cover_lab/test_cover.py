import unittest

from cover import (affine_info, contained_summary, explicit_max_support,
                   fib_count, lower_bound_pieces, satisfying_set,
                   verify_path_theorem_instance)


class ConnectedAffineCoverTests(unittest.TestCase):
    def test_path_counts(self):
        self.assertEqual([fib_count(n) for n in range(7)], [1, 2, 3, 5, 8, 13, 21])
        for n in range(1, 9):
            self.assertEqual(len(satisfying_set(n)), fib_count(n))

    def test_explicit_maximal_support(self):
        for n in range(1, 20):
            support = explicit_max_support(n)
            self.assertTrue(support <= satisfying_set(n))
            self.assertEqual(affine_info(support, n)['dimension'], (n + 1) // 2)

    def test_exhaustive_small_affine_controls(self):
        for n in range(0, 7):
            summary = contained_summary(n)
            self.assertEqual(summary['max_contained_dimension'], (n + 1) // 2)
            self.assertEqual(summary['max_contained_size'], 1 << ((n + 1) // 2))

    def test_lower_bound_is_integer_and_grows(self):
        values = [lower_bound_pieces(n) for n in range(1, 31)]
        self.assertTrue(all(v >= 1 for v in values))
        self.assertGreater(values[-1], values[0])

    def test_non_affine_and_malformed_supports_rejected(self):
        self.assertIsNone(affine_info({0, 1, 2}, 2))
        self.assertIsNone(affine_info(set(), 2))
        self.assertIsNone(affine_info({0, 4}, 2))

    def test_all_size_certificate(self):
        for n in [1, 2, 10, 50]:
            result = verify_path_theorem_instance(n)
            self.assertEqual(result['satisfying_count'], fib_count(n))
            self.assertEqual(result['explicit_dimension'], (n + 1) // 2)


if __name__ == '__main__':
    unittest.main()
