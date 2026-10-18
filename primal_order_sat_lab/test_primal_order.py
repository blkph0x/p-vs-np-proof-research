import unittest
from itertools import permutations

import primal_order as po


class PrimalOrderTests(unittest.TestCase):
    def test_clause_scopes_match_primal_edges(self):
        clauses = [[1, 2, -3], [3, 4], [1], []]
        self.assertEqual(po.primal_edges(4, clauses), ((0, 1), (0, 2), (1, 2), (2, 3)))

    def test_chain_order_and_sat_certificate(self):
        clauses = [[-(i + 1), i + 2] for i in range(7)]
        result = po.solve(8, clauses)
        self.assertEqual(result['status'], 'EXACT')
        self.assertTrue(result['sat'])
        self.assertEqual(result['width'], 1)
        self.assertTrue(po.verify(8, clauses, result)['valid'])

    def test_star_order_is_found(self):
        clauses = [[i + 1, 8] for i in range(7)]
        result = po.solve(8, clauses)
        self.assertEqual(result['status'], 'EXACT')
        self.assertTrue(result['sat'])
        self.assertEqual(result['width'], 1)
        self.assertTrue(po.verify(8, clauses, result)['valid'])

    def test_complete_primal_graph_width(self):
        clauses = [[i + 1, j + 1] for i in range(6) for j in range(i + 1, 6)]
        result = po.solve(6, clauses)
        self.assertEqual(result['width'], 5)
        self.assertTrue(result['sat'])
        self.assertEqual(result['sat'], po.brute_sat(6, clauses))

    def test_unsat_and_empty_clause(self):
        clauses = [[1]] + [[-(i + 1), i + 2] for i in range(7)] + [[-8]]
        result = po.solve(8, clauses)
        self.assertFalse(result['sat'])
        self.assertEqual(result['sat'], po.brute_sat(8, clauses))
        empty = po.solve(4, [[]])
        self.assertFalse(empty['sat'])
        self.assertTrue(po.verify(4, [[]], empty)['valid'])

    def test_search_cap_fails_closed(self):
        result = po.solve(12, [[i + 1, j + 1] for i in range(12) for j in range(i + 1, 12)],
                          max_subsets=20)
        self.assertEqual(result['status'], 'UNKNOWN')
        self.assertEqual(result['reason'], 'subset cap')

    def test_order_search_matches_all_5_factorial_orders(self):
        clauses = [[1, 2, 3], [-2, 4], [3, 5]]
        exhaustive_width = min(po.order_records(5, clauses, order)[1]
                               for order in permutations(range(5)))
        result = po.solve(5, clauses)
        self.assertEqual(result['status'], 'EXACT')
        self.assertEqual(result['width'], exhaustive_width)
        self.assertTrue(po.verify(5, clauses, result)['valid'])


if __name__ == '__main__':
    unittest.main()
