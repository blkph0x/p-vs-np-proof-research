"""Independent matching enumeration and adversarial primal/dual certificate tests."""
from copy import deepcopy
from itertools import combinations, product
import random
import sys
import unittest
from unittest.mock import patch

from matching_certificate import (certified_maximum_weight_matching,
                                  verify_matching_certificate)


def enumerate_matching_weight(vertices, edges):
    """Explicitly branch over skipping or matching the first remaining vertex."""
    weights = {frozenset((u, v)): weight for u, v, weight in edges}

    def visit(remaining):
        if not remaining:
            return 0
        first, rest = remaining[0], remaining[1:]
        best = visit(rest)
        for index, other in enumerate(rest):
            edge = frozenset((first, other))
            if edge in weights:
                best = max(best, weights[edge] + visit(rest[:index] + rest[index + 1:]))
        return best

    return visit(tuple(vertices))


def triangle_certificate():
    return {'schema': 'integer_matching_dual_v1', 'matching': [[0, 1]],
            'vertex_duals': [{'vertex': j, 'twice_value': 0} for j in range(3)],
            'odd_set_duals': [{'vertices': [0, 1, 2], 'value': 1}]}


class MatchingCertificateTest(unittest.TestCase):
    def check_instance(self, vertices, edges):
        certificate = certified_maximum_weight_matching(vertices, edges)
        checked = verify_matching_certificate(vertices, edges, certificate)
        self.assertTrue(checked['valid'], checked['errors'])
        self.assertEqual(checked['matching_weight'], enumerate_matching_weight(vertices, edges))
        self.assertEqual(checked['twice_dual_objective'], 2 * checked['matching_weight'])
        self.assertEqual(checked['perfect'], checked['matched_vertices'] == len(vertices))
        return certificate, checked

    def test_all_complete_graph_weights_from_signed_integer_alphabet_through_four_vertices(self):
        cases = 0
        for n in range(5):
            vertices = tuple(range(n))
            pairs = tuple(combinations(vertices, 2))
            for weights in product((-2, 0, 3), repeat=len(pairs)):
                edges = tuple((u, v, weight) for (u, v), weight in zip(pairs, weights))
                self.check_instance(vertices, edges)
                cases += 1
        self.assertEqual(cases, 761)

    def test_seeded_sparse_graphs_and_general_nonperfect_matchings(self):
        rng = random.Random(20261018)
        for _ in range(100):
            vertices = tuple(3 * j - 7 for j in range(rng.randrange(1, 9)))
            edges = tuple((u, v, rng.randrange(-7, 12)) for u, v in combinations(vertices, 2)
                          if rng.randrange(3))
            self.check_instance(vertices, edges)
        _, checked = self.check_instance((0, 1, 2, 3), ((0, 1, 5), (0, 2, 4), (0, 3, 3)))
        self.assertFalse(checked['perfect'])
        self.assertEqual(checked['matching_weight'], 5)
        self.assertEqual(checked['matched_vertices'], 2)

    def test_triangle_requires_an_odd_set_dual(self):
        vertices, edges = (0, 1, 2), ((0, 1, 1), (1, 2, 1), (0, 2, 1))
        certificate, checked = self.check_instance(vertices, edges)
        self.assertFalse(checked['perfect'])
        self.assertTrue(any(row['value'] > 0 for row in certificate['odd_set_duals']))
        self.assertTrue(verify_matching_certificate(vertices, edges, triangle_certificate())['valid'])
        without_blossom = deepcopy(certificate)
        without_blossom['odd_set_duals'] = []
        self.assertFalse(verify_matching_certificate(vertices, edges, without_blossom)['valid'])

    def test_empty_isolated_negative_and_large_integer_graphs(self):
        cases = [((), ()), ((10,), ()), ((-1, 3, 8), ()),
                 ((0, 1, 2), ((0, 1, -5), (1, 2, -1))),
                 ((0, 1, 2, 3), ((0, 1, 10 ** 60), (2, 3, 10 ** 60 + 1),
                                  (0, 2, 2 * 10 ** 60 + 5)))]
        for vertices, edges in cases:
            self.check_instance(vertices, edges)

    def test_verifier_accepts_general_crossing_odd_sets(self):
        # Weak duality does not require the producer's laminar blossom structure.
        vertices, edges = (0, 1, 2, 3), ((0, 1, 1), (2, 3, 1))
        certificate = {'schema': 'integer_matching_dual_v1', 'matching': [[0, 1], [2, 3]],
                       'vertex_duals': [{'vertex': j, 'twice_value': 0} for j in vertices],
                       'odd_set_duals': [{'vertices': [0, 1, 2], 'value': 1},
                                         {'vertices': [1, 2, 3], 'value': 1}]}
        self.assertTrue(verify_matching_certificate(vertices, edges, certificate)['valid'])

    def test_tampered_duals_and_matching_are_rejected(self):
        vertices, edges = (0, 1, 2), ((0, 1, 1), (1, 2, 1), (0, 2, 1))
        base = triangle_certificate()
        changes = [
            lambda c: c.update(schema='other'),
            lambda c: c['vertex_duals'][0].update(twice_value=-1),
            lambda c: c['vertex_duals'][0].update(twice_value=True),
            lambda c: c['vertex_duals'][0].update(twice_value=0.5),
            lambda c: c['vertex_duals'][0].update(twice_value=1),
            lambda c: c['vertex_duals'].pop(),
            lambda c: c['vertex_duals'].append(deepcopy(c['vertex_duals'][0])),
            lambda c: c['vertex_duals'][0].update(vertex=4),
            lambda c: c['vertex_duals'][0].update(vertex=True),
            lambda c: c['odd_set_duals'][0].update(value=-1),
            lambda c: c['odd_set_duals'][0].update(value=True),
            lambda c: c['odd_set_duals'][0].update(value=0.5),
            lambda c: c['odd_set_duals'][0].update(value=2),
            lambda c: c['odd_set_duals'][0].update(vertices=[0, 1]),
            lambda c: c['odd_set_duals'][0].update(vertices=[0]),
            lambda c: c['odd_set_duals'][0].update(vertices=[0, 1, 1]),
            lambda c: c['odd_set_duals'][0].update(vertices=[0, 1, 4]),
            lambda c: c['odd_set_duals'][0].update(vertices=[0, 1, True]),
            lambda c: c['odd_set_duals'].append(deepcopy(c['odd_set_duals'][0])),
            lambda c: c.update(matching=[]),
            lambda c: c.update(matching=[[0, 1], [1, 2]]),
            lambda c: c.update(matching=[[0, 1], [1, 0]]),
            lambda c: c.update(matching=[[0, 0]]),
            lambda c: c.update(matching=[[0, 4]]),
            lambda c: c.update(matching=[[0, True]]),
            lambda c: c.update(matching=[[0, 1, 2]]),
        ]
        for index, change in enumerate(changes):
            certificate = deepcopy(base)
            change(certificate)
            with self.subTest(change=index):
                result = verify_matching_certificate(vertices, edges, certificate)
                self.assertFalse(result['valid'])
                self.assertTrue(result['errors'])

    def test_malformed_certificate_structures_fail_closed(self):
        vertices, edges = (0, 1, 2), ((0, 1, 1), (1, 2, 1), (0, 2, 1))
        malformed = [None, [], {}, {'schema': 'integer_matching_dual_v1'}]
        for field in ['matching', 'vertex_duals', 'odd_set_duals']:
            for value in [None, 3, [None], ['bad']]:
                certificate = triangle_certificate()
                certificate[field] = value
                malformed.append(certificate)
        for certificate in malformed:
            self.assertFalse(verify_matching_certificate(vertices, edges, certificate)['valid'])

    def test_wrong_graph_and_malformed_inputs_are_rejected(self):
        certificate = triangle_certificate()
        invalid_graphs = [
            ((0, 1, 2), ((0, 1, 2), (1, 2, 1), (0, 2, 1))),
            ((0, 1, 2), ((1, 2, 1), (0, 2, 1))),
            ((0, 1, 2, 3), ((0, 1, 1), (1, 2, 1), (0, 2, 1))),
            ((0, 1, 1, 2), ((0, 1, 1),)),
            ((0, True, 2), ((0, 1, 1),)),
            ((0, 1, 2), ((0, 0, 1),)),
            ((0, 1, 2), ((0, 3, 1),)),
            ((0, 1, 2), ((0, 1, 1), (1, 0, 1))),
            ((0, 1, 2), ((0, 1, True),)),
            ((0, 1, 2), ((0, 1, 1.0),)),
            ((0, 1, 2), ((0, 1),)),
        ]
        for vertices, edges in invalid_graphs:
            self.assertFalse(verify_matching_certificate(vertices, edges, certificate)['valid'])
        # A certificate applies to the mathematical instance, independent of edge orientation/order.
        self.assertTrue(verify_matching_certificate((2, 1, 0),
                        ((2, 0, 1), (2, 1, 1), (1, 0, 1)), certificate)['valid'])

    def test_profile_observer_is_restored_on_success_failure_and_unsupported_internals(self):
        previous = sys.getprofile()

        def existing_observer(frame, event, arg):
            pass

        sys.setprofile(existing_observer)
        try:
            self.check_instance((0, 1), ((0, 1, 2),))
            self.assertIs(sys.getprofile(), existing_observer)
            with patch('networkx.max_weight_matching', side_effect=RuntimeError('forced failure')):
                with self.assertRaisesRegex(RuntimeError, 'forced failure'):
                    certified_maximum_weight_matching((0, 1), ((0, 1, 2),))
            self.assertIs(sys.getprofile(), existing_observer)
            with patch('networkx.max_weight_matching', return_value=set()):
                with self.assertRaisesRegex(RuntimeError, 'expected final blossom duals'):
                    certified_maximum_weight_matching((0, 1), ((0, 1, 2),))
            self.assertIs(sys.getprofile(), existing_observer)
        finally:
            sys.setprofile(previous)


if __name__ == '__main__':
    unittest.main()
