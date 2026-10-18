from itertools import combinations
import unittest

from capacity import dictionary_count, dictionary_product, enumerate_directions, existence_bound, pair_span_boolean_points, small_two_piece_coverage


class CapacityTests(unittest.TestCase):
    def test_exact_dictionary_by_independent_truth_enumeration(self):
        for n, expected in enumerate([1, 4, 24, 240, 4320]):
            self.assertEqual(len(enumerate_directions(n)['directions']), expected)
            self.assertEqual(dictionary_count(n), expected)

    def test_closed_product_matches_dimension_recurrence(self):
        for n in range(65):
            self.assertEqual(dictionary_count(n), dictionary_product(n))

    def test_coordinate_injection_and_small_coverage(self):
        for n in range(4):
            row = small_two_piece_coverage(n)
            self.assertLessEqual(row['max_boolean_points_in_pair_span'], 4)
            self.assertEqual(row['two_piece_boolean_functions'], row['total_boolean_functions'])
        # This signed pair has only zero among the Boolean vertices of its span.
        self.assertEqual(pair_span_boolean_points((1, -1, 0), (0, 1, -1)), {0})

    def test_exact_inequality_and_enumeration_guards(self):
        for n in range(1, 17):
            row = existence_bound(n)
            k = row['some_boolean_function_requires_at_least']-1
            self.assertLess(k*row['per_piece_exponent_bound'], 1 << n)
            self.assertLess(2*(row['dictionary_directions']+1), 1 << row['per_piece_exponent_bound'])
        with self.assertRaises(ValueError):
            enumerate_directions(5)
        with self.assertRaises(ValueError):
            small_two_piece_coverage(4)


if __name__ == '__main__':
    unittest.main()
