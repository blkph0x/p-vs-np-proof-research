"""Unit controls for the non-graphic core construction."""
import unittest

from run_experiments import fano_restriction, generate_columns, rank_values, distance


class NonGraphicCoreTests(unittest.TestCase):
    def test_fano_restriction(self):
        columns = tuple(range(1, 8)) + (8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18)
        self.assertTrue(fano_restriction(columns))
        self.assertEqual(rank_values(columns), 5)

    def test_deterministic_generation_and_distance(self):
        first = generate_columns(18, 9, 20261018)
        second = generate_columns(18, 9, 20261018)
        self.assertEqual(first, second)
        self.assertIsNotNone(first)
        self.assertTrue(fano_restriction(first))
        self.assertEqual(rank_values(first), 9)
        self.assertGreaterEqual(distance(first, 9), 1)

    def test_dimension_validation(self):
        with self.assertRaises(ValueError):
            generate_columns(7, 3, 1)
        with self.assertRaises(ValueError):
            generate_columns(8, 8, 1)


if __name__ == "__main__":
    unittest.main()
