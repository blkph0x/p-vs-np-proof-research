import unittest

import boundary_dp as dp


class BoundaryDPTests(unittest.TestCase):
    def test_chain_sat_and_width(self):
        clauses = [[-(i + 1), i + 2] for i in range(15)]
        result = dp.solve(16, clauses, list(range(16)))
        self.assertEqual(result['status'], 'EXACT')
        self.assertTrue(result['sat'])
        self.assertEqual(result['stats']['max_width'], 1)
        self.assertTrue(dp.verify(16, clauses, result)['valid'])

    def test_chain_unsat(self):
        clauses = [[1]] + [[-(i + 1), i + 2] for i in range(15)] + [[-16]]
        result = dp.solve(16, clauses, list(range(16)))
        self.assertFalse(result['sat'])
        self.assertFalse(dp.brute_sat(16, clauses))
        self.assertTrue(dp.verify(16, clauses, result)['valid'])

    def test_order_changes_width_not_answer(self):
        clauses = [[i + 1, 7 + i] for i in range(6)]
        bad = dp.solve(12, clauses, list(range(12)))
        good_order = [0, 6, 1, 7, 2, 8, 3, 9, 4, 10, 5, 11]
        good = dp.solve(12, clauses, good_order)
        self.assertEqual(bad['sat'], good['sat'])
        self.assertGreater(bad['stats']['max_width'], good['stats']['max_width'])
        self.assertTrue(dp.verify(12, clauses, good)['valid'])

    def test_dense_control_matches_brute_force(self):
        clauses = [[-(a + 1), -(b + 1), -(c + 1)]
                   for a in range(6) for b in range(a + 1, 6) for c in range(b + 1, 6)]
        result = dp.solve(6, clauses, list(range(6)))
        self.assertEqual(result['sat'], dp.brute_sat(6, clauses))
        self.assertTrue(dp.verify(6, clauses, result)['valid'])

    def test_mutation_rejected(self):
        result = dp.solve(4, [[1, 2], [-1, 3]], list(range(4)))
        result['states'][1][0] ^= 1
        self.assertFalse(dp.verify(4, [[1, 2], [-1, 3]], result)['valid'])

    def test_caps_and_invalid_inputs_fail_closed(self):
        clauses = [[-(i + 1), i + 2] for i in range(15)]
        self.assertEqual(dp.solve(16, clauses, list(range(16)), max_states=1)['status'], 'UNKNOWN')
        with self.assertRaises(ValueError):
            dp.solve(2, [[3]], [0, 1])

    def test_empty_clause_is_immediate_unsat(self):
        result = dp.solve(5, [[1, 2], []], [0, 1, 2, 3, 4])
        self.assertEqual(result['status'], 'EXACT')
        self.assertFalse(result['sat'])
        self.assertEqual(result['states'][0], [0])
        self.assertTrue(all(not states for states in result['states'][1:]))
        self.assertTrue(dp.verify(5, [[1, 2], []], result)['valid'])
        self.assertFalse(dp.brute_sat(5, [[1, 2], []]))


if __name__ == '__main__':
    unittest.main()
