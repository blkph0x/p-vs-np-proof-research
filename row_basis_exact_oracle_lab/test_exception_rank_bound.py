import unittest

from exception_rank_bound import low_weight_count, theorem_parameters, union_bound, verify_bound


class ExceptionRankBoundTests(unittest.TestCase):
    def test_low_weight_count(self):
        self.assertEqual(low_weight_count(6), 22)
        self.assertEqual(low_weight_count(32), 529)

    def test_union_bound_is_strictly_below_one(self):
        for rank_value in (6, 7, 8, 16, 32):
            self.assertLess(union_bound(rank_value), 1)
            self.assertEqual(verify_bound(rank_value)['minimum_native_states'], 2 ** rank_value)

    def test_asymptotic_parameters(self):
        parameters = theorem_parameters(32)
        self.assertEqual(parameters['columns'], 16 * 32 * 32 + 32)
        self.assertEqual(parameters['minimum_native_states'], 2 ** 32)
        self.assertTrue(parameters['n_at_most_17_r_squared'])


if __name__ == '__main__':
    unittest.main()
