import copy
from fractions import Fraction as F
import random
import unittest

from crossing import (crossover_graph, deletion_signature, enc, four_port_identity,
                      matchgate_violations, ordinary_crossing, pairing_expansion,
                      q, request_hash, signed_crossing, solve_pfaffian, verify_pfaffian)


def skew(n, rng):
    a = [[F(0) for _ in range(n)] for _ in range(n)]
    for i in range(n):
        for j in range(i+1, n):
            a[i][j] = F(rng.randint(-4, 4), rng.randint(1, 5))
            a[j][i] = -a[i][j]
    return a


class CrossingTests(unittest.TestCase):
    def test_actual_planar_graph_signature(self):
        n, edges = crossover_graph()
        rows = deletion_signature(n, edges, [0, 1, 2, 3])
        self.assertEqual([q(row['value']) for row in rows], signed_crossing())
        # There are cancelling matchings as well as nonzero edge products.
        self.assertEqual(sorted(q(x['weight']) for x in rows[0]['matchings']), [-1, 1, 1])

    def test_matchgate_identities_and_order(self):
        self.assertEqual(four_port_identity(ordinary_crossing()), 2)
        self.assertTrue(matchgate_violations(ordinary_crossing()))
        self.assertEqual(matchgate_violations(signed_crossing()), [])
        adjacent = [F(int((s & 1) == ((s >> 1) & 1) and ((s >> 2) & 1) == ((s >> 3) & 1)))
                    for s in range(16)]
        self.assertEqual(matchgate_violations(adjacent), [])

    def test_global_cancellation(self):
        # Surrounding EQ4 permits just two assignments; both were valid.
        equality4 = [int(s in (0, 15)) for s in range(16)]
        self.assertEqual(sum(a*b for a, b in zip(equality4, ordinary_crossing())), 2)
        self.assertEqual(sum(a*b for a, b in zip(equality4, signed_crossing())), 0)

    def test_unary_rescaling_cannot_repair_crossing(self):
        for values in ((2, 3, 5, 7), (-1, 2, 3, 9), (F(1, 7), F(2, 3), -3, 5)):
            a0, a1, b0, b1 = values
            rescaled = [a0*b0, a0*b1, a1*b0, -a1*b1]
            self.assertEqual(rescaled[0]*rescaled[3], -rescaled[1]*rescaled[2])
            self.assertNotEqual(rescaled[0]*rescaled[3], rescaled[1]*rescaled[2])

    def test_pfaffian_against_pairings(self):
        rng = random.Random(20261018)
        for n in range(9):
            for _ in range(20):
                a = skew(n, rng)
                proof = solve_pfaffian(a)
                direct = sum((q(row['signed_product']) for row in pairing_expansion(a)), F(0))
                self.assertEqual(q(proof['value']), direct)
                self.assertEqual(verify_pfaffian(a, proof)['status'], 'VERIFIED')

    def test_zero_does_not_mean_no_matching(self):
        a = [[0, 1, 1, 0], [-1, 0, 0, 1], [-1, 0, 0, 1], [0, -1, -1, 0]]
        terms = pairing_expansion(a)
        self.assertEqual(len(terms), 2)
        self.assertEqual(sum(q(row['edge_product']) for row in terms), 2)
        self.assertEqual(solve_pfaffian(a)['value'], enc(0))

    def test_permutation_singular_odd_and_empty(self):
        cases = [[], [[0]], [[0, 0], [0, 0]],
                 [[0, 0, 2, 0], [0, 0, 0, 3], [-2, 0, 0, 0], [0, -3, 0, 0]]]
        for a, expected in zip(cases, (1, 0, 0, -6)):
            p = solve_pfaffian(a)
            self.assertEqual(q(p['value']), expected)
            self.assertEqual(verify_pfaffian(a, p)['status'], 'VERIFIED')

    def test_tampering_and_original_binding(self):
        a = skew(6, random.Random(9))
        proof = solve_pfaffian(a)
        bad = copy.deepcopy(proof)
        bad['value'][0] += 1
        self.assertEqual(verify_pfaffian(a, bad)['status'], 'REJECTED')
        bad = copy.deepcopy(proof)
        bad['steps'][0]['tail'][0][1][0] += 1
        self.assertEqual(verify_pfaffian(a, bad)['status'], 'REJECTED')
        bad = copy.deepcopy(proof)
        bad['steps'][0]['swap_with'] = 0
        self.assertEqual(verify_pfaffian(a, bad)['status'], 'REJECTED')
        b = copy.deepcopy(a)
        b[0][1] += 1
        b[1][0] -= 1
        self.assertEqual(verify_pfaffian(b, proof)['status'], 'REJECTED')
        self.assertNotEqual(request_hash(a), request_hash(b))

    def test_caps_and_invalid_input(self):
        a = skew(6, random.Random(2))
        for caps in ({'max_vertices': 5}, {'max_entry_bits': 0}):
            p = solve_pfaffian(a, **caps)
            self.assertEqual(p['status'], 'UNKNOWN')
            self.assertNotIn('value', p)
        self.assertEqual(verify_pfaffian(a, solve_pfaffian(a), max_vertices=5)['status'], 'UNKNOWN')
        for bad in ([[1]], [[0, 1], [1, 0]], [[0, 0.5], [-0.5, 0]]):
            with self.assertRaises(ValueError):
                solve_pfaffian(bad)
        self.assertEqual(request_hash([[0, [1, 2]], [[-2, 4], 0]]),
                         request_hash([[0, F(1, 2)], [-F(1, 2), 0]]))


if __name__ == '__main__':
    unittest.main()
