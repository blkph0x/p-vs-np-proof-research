import itertools
import unittest

import frontier


class FrontierOrderTests(unittest.TestCase):
    def test_rank_and_cut_formula(self):
        matrix = [[1, 0, 1], [0, 1, 1]]
        cols = frontier.column_vectors(matrix)
        self.assertEqual(frontier.vector_rank(cols), 2)
        self.assertEqual(frontier.cut_lambda(cols, 0b011), 1)

    def test_crossing_pairs_bad_and_interleaved_orders(self):
        matrix = [[int(c == i or c == 6 + i) for c in range(12)] for i in range(6)]
        bad, bad_width = frontier.order_records(matrix, list(range(12)))
        good = frontier.optimal_order(matrix)
        self.assertEqual(bad_width, 6)
        self.assertEqual(good['width'], 1)
        self.assertEqual(frontier.verify_order_certificate(matrix, good)['valid'], True)
        alternate = [6, 0, 7, 1, 8, 2, 9, 3, 10, 4, 11, 5]
        alternate_records, alternate_width = frontier.order_records(matrix, alternate)
        alternate_result = {'status': 'EXACT', 'order': alternate, 'width': alternate_width,
                            'records': alternate_records}
        self.assertEqual(alternate_width, 1)
        self.assertTrue(frontier.verify_order_certificate(matrix, alternate_result)['valid'])

    def test_repeated_rows_have_one_bit_width(self):
        matrix = [[1] * 10 for _ in range(7)]
        result = frontier.optimal_order(matrix)
        self.assertEqual(result['width'], 1)
        self.assertTrue(frontier.verify_order_certificate(matrix, result)['valid'])

    def test_dp_matches_all_orders_on_small_matrix(self):
        matrix = [[1, 1, 0, 1], [0, 1, 1, 1], [1, 0, 1, 0]]
        expected = min(frontier.order_records(matrix, order)[1]
                       for order in itertools.permutations(range(4)))
        self.assertEqual(frontier.optimal_order(matrix)['width'], expected)

    def test_mutated_certificate_rejected(self):
        matrix = [[1, 0, 1], [0, 1, 1]]
        result = frontier.optimal_order(matrix)
        result['width'] += 1
        self.assertFalse(frontier.verify_order_certificate(matrix, result)['valid'])

    def test_bad_inputs_fail_closed(self):
        with self.assertRaises(ValueError):
            frontier.validate_matrix([[1, 2]])
        with self.assertRaises(ValueError):
            frontier.order_records([[1, 0]], [1, 0, 2])


if __name__ == '__main__':
    unittest.main()
