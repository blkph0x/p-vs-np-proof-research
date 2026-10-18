import itertools
import unittest

import vertex_separation as vs


class VertexSeparationTests(unittest.TestCase):
    def test_path_and_star_controls(self):
        path = [(i, i + 1) for i in range(7)]
        self.assertEqual(vs.optimal_order(8, path)['width'], 1)
        star = [(0, i) for i in range(1, 8)]
        self.assertEqual(vs.optimal_order(8, star)['width'], 1)
        _, bad = vs.order_records(8, star, list(range(1, 8)) + [0])
        self.assertEqual(bad, 7)
        bipartite = [(i, 4 + j) for i in range(4) for j in range(2)]
        greedy = vs.greedy_order(6, bipartite)
        _, greedy_width = vs.order_records(6, bipartite, greedy)
        self.assertEqual(greedy, list(range(6)))
        self.assertEqual(greedy_width, 4)
        self.assertLessEqual(vs.optimal_order(6, bipartite)['width'], 2)

    def test_cycle_and_complete_controls(self):
        cycle = [(i, (i + 1) % 8) for i in range(8)]
        complete = [(u, v) for u in range(6) for v in range(u + 1, 6)]
        self.assertEqual(vs.optimal_order(8, cycle)['width'], 2)
        self.assertEqual(vs.optimal_order(6, complete)['width'], 5)

    def test_dp_matches_permutations(self):
        edges = [(0, 1), (1, 2), (2, 3), (0, 3), (1, 3)]
        expected = min(vs.order_records(4, edges, order)[1]
                       for order in itertools.permutations(range(4)))
        self.assertEqual(vs.optimal_order(4, edges)['width'], expected)

    def test_formula_is_always_satisfiable(self):
        edges = [(0, 1), (1, 2), (2, 3)]
        clauses = vs.monotone_two_cnf(4, edges)
        all_ones = 15
        self.assertTrue(all(((all_ones >> (lit - 1)) & 1) for clause in clauses for lit in clause))

    def test_mutated_certificate_rejected(self):
        edges = [(0, 1), (1, 2), (2, 3)]
        result = vs.optimal_order(4, edges)
        result['width'] += 1
        self.assertFalse(vs.verify_certificate(4, edges, result)['valid'])

    def test_bad_inputs_fail_closed(self):
        with self.assertRaises(ValueError):
            vs.validate_graph(3, [(0, 3)])
        with self.assertRaises(ValueError):
            vs.validate_graph(3, [(0, 1), (1, 0)])


if __name__ == '__main__':
    unittest.main()
