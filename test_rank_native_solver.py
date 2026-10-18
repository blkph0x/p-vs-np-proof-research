"""Independent enumeration and adversarial replay tests for syndrome compression."""
import copy
import itertools
import json
import random
import unittest

from rank_native_solver import solve_rank_native, verify_rank_native


def rows_from_columns(columns, r):
    return [sum(((column >> i) & 1) << j for j, column in enumerate(columns)) for i in range(r)]


def oracle(rows, n, target, nonzero):
    weights = [word.bit_count() for word in range(1 if nonzero else 0, 1 << n)
               if sum(((word & row).bit_count() % 2) << i for i, row in enumerate(rows)) == target]
    return min(weights) if weights else None


class RankNativeTests(unittest.TestCase):
    def check(self, columns, r, target=0, nonzero=True, transform=None):
        rows = rows_from_columns(columns, r)
        result = solve_rank_native(rows, len(columns), target=target, require_nonzero=nonzero,
                                   row_transform=transform, max_states=256)
        self.assertEqual(result['status'], 'EXACT')
        self.assertEqual(result['distance'], oracle(rows, len(columns), target, nonzero))
        self.assertTrue(verify_rank_native(rows, len(columns), json.loads(json.dumps(result)),
                                           target=target, require_nonzero=nonzero)['valid'])
        return result

    def test_exhaustive_three_row_matrices_and_affine_targets(self):
        # Every 3-row binary matrix with at most 3 coordinates; 9,360 requests.
        for n in range(4):
            for columns in itertools.product(range(8), repeat=n):
                for target in range(8):
                    for nonzero in (False, True):
                        self.check(columns, 3, target, nonzero)

    def test_seeded_four_and_five_row_affine_instances(self):
        rng = random.Random(9341)
        for _ in range(90):
            r, n = rng.choice((4, 5)), rng.randrange(4, 11)
            columns = [rng.randrange(1 << r) for _ in range(n)]
            for target in (0, rng.randrange(1 << r)):
                for nonzero in (False, True):
                    self.check(columns, r, target, nonzero)

    def test_nonempty_zero_syndrome_requires_separate_state(self):
        # No graph coordinates: the only nonzero solution uses both equal columns.
        result = self.check([7, 7], 3)
        self.assertEqual(result['distance'], 2)
        self.assertEqual(result['graph_case_count'], 3)
        self.assertEqual(result['exception_rank'], 1)
        self.check([7], 3)  # no nonzero homogeneous solution
        self.check([7, 7], 3, nonzero=False)

    def test_dependent_distinct_exception_columns_and_graph_cycles(self):
        # 7 xor 25 = 30; the three distinct heavy columns have rank 2.
        result = self.check([7, 25, 30, 1, 2, 3], 5)
        self.assertEqual(result['exception_rank'], 2)
        self.assertEqual(result['distance'], 3)
        self.check([7, 25, 30, 1, 2, 3], 5, target=17)

    def test_large_exception_count_small_rank(self):
        columns = [7] * 80 + [1, 2, 4]
        rows = rows_from_columns(columns, 3)
        result = solve_rank_native(rows, len(columns), target=7, require_nonzero=False, max_states=2)
        self.assertEqual(result['distance'], 1)
        self.assertEqual(result['state_count'], 2)
        self.assertEqual(len(result['branches']), 2)
        self.assertLess(result['dp_transitions'], 3 * len(columns))
        self.assertEqual(len(result['exceptional_coordinates']), 80)

    def test_invertible_row_transform_preserves_requested_coset(self):
        columns = [7, 25, 30, 1, 2, 3]
        for target in range(32):
            self.check(columns, 5, target, False, [3, 2, 4, 12, 24])

    def test_caps_unknown_and_exact_boundaries(self):
        rows = rows_from_columns([7, 25, 30, 1, 2, 3], 5)
        exact = solve_rank_native(rows, 6)
        for options, reason in (({'max_states': 3}, 'STATE_LIMIT'),
                                ({'max_dp_transitions': 0}, 'DP_LIMIT'),
                                ({'max_dp_transitions': 3}, 'DP_LIMIT'),
                                ({'max_graph_calls': 0}, 'GRAPH_LIMIT'),
                                ({'max_graph_calls': 2}, 'GRAPH_LIMIT')):
            result = solve_rank_native(rows, 6, **options)
            self.assertEqual(result['status'], 'UNKNOWN')
            self.assertIsNone(result['distance'])
            self.assertEqual(result['stop_reason'], reason)
            self.assertTrue(verify_rank_native(rows, 6, result)['valid'])
        boundary = solve_rank_native(rows, 6, max_states=4,
                                     max_dp_transitions=exact['dp_transitions'],
                                     max_graph_calls=exact['graph_case_count'])
        self.assertEqual(boundary['status'], 'EXACT')
        self.assertEqual(boundary['distance'], 3)

    def test_tampering_rejected(self):
        rows = rows_from_columns([7, 25, 30, 1, 2, 3], 5)
        result = solve_rank_native(rows, 6)
        mutations = [lambda x: x.update(distance=2),
                     lambda x: x.update(exception_rank=1),
                     lambda x: x.update(state_count=3),
                     lambda x: x.update(dp_transitions=x['dp_transitions'] + 1),
                     lambda x: x['dp_layers'][-1].pop(),
                     lambda x: x['dp_layers'][1][0].__setitem__(1, 2),
                     lambda x: x['exception_witnesses'][0].__setitem__(2, 0),
                     lambda x: x['branches'].pop(),
                     lambda x: x['branches'][0].update(nonzero_graph_required=False),
                     lambda x: x['limits'].update(max_states=0),
                     lambda x: x.update(target=True),
                     lambda x: x.update(require_nonzero=1),
                     lambda x: x.update(dp_complete=1),
                     lambda x: x.update(graph_case_count=True)]
        for mutate in mutations:
            broken = copy.deepcopy(result)
            mutate(broken)
            self.assertFalse(verify_rank_native(rows, 6, broken)['valid'])
        self.assertFalse(verify_rank_native(rows, 6, result, target=1)['valid'])
        self.assertFalse(verify_rank_native(rows, 6, result, require_nonzero=False)['valid'])

    def test_invalid_inputs(self):
        for options in ({'max_states': -1}, {'max_dp_transitions': True},
                        {'max_graph_calls': 1.5}, {'target': True},
                        {'target': 8}, {'require_nonzero': 1},
                        {'row_transform': [1, 1, 4]}):
            with self.assertRaises(ValueError):
                solve_rank_native([1, 2, 4], 3, **options)


if __name__ == '__main__':
    unittest.main()
