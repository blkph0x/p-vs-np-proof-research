"""Independent GL(3,2), equivalence, strict-descent and budget audits."""
from copy import deepcopy
from itertools import product
import random
import unittest

from row_basis_discovery import (discover_row_basis, objective,
                                 verify_row_basis_result)


def rows_from_columns(columns, r=3):
    return tuple(sum(1 << j for j, column in enumerate(columns) if column >> i & 1)
                 for i in range(r))


def apply_transform(rows, transform):
    result = []
    for mask in transform:
        value = 0
        for i, row in enumerate(rows):
            if mask >> i & 1:
                value ^= row
        result.append(value)
    return tuple(result)


def independent_score(rows, n):
    weights = [sum((row >> j) & 1 for row in rows) for j in range(n)]
    return (sum(weight >= 3 for weight in weights),
            sum(weight - 2 for weight in weights if weight >= 3), sum(weights))


def gl3():
    matrices = []
    for rows in product(range(1, 8), repeat=3):
        span = {0}
        for row in rows:
            span |= {x ^ row for x in tuple(span)}
        if len(span) == 8:
            matrices.append(rows)
    return matrices


GL3 = gl3()


def trap_rows():
    # Identity exposes value 7 twice. A single XOR exposes 3,5,6 three times.
    # The global best can expose value 1, which occurs only once.
    counts = {1: 1, 2: 4, 3: 3, 4: 4, 5: 3, 6: 3, 7: 2}
    columns = [value for value, count in counts.items() for _ in range(count)]
    return rows_from_columns(columns), len(columns)


class RowBasisDiscoveryTest(unittest.TestCase):
    def check_result(self, rows, n, result):
        self.assertTrue(verify_row_basis_result(rows, n, result)['valid'])
        self.assertEqual(tuple(result['transformed_check_rows']), apply_transform(rows, result['row_transform']))
        self.assertEqual(tuple(result['objective']), independent_score(result['transformed_check_rows'], n))
        self.assertLessEqual(tuple(result['objective']), independent_score(rows, n))
        self.assertFalse(result['global_optimum_claimed'])
        work = result['work']
        self.assertLessEqual(work['candidate_evaluations'], result['limits']['max_candidate_evaluations'])
        self.assertEqual(work['candidate_evaluations'], work['setup_evaluations'] + work['neighbor_evaluations'])
        self.assertEqual(work['setup_evaluations'], 1 + work['restarts_started'])
        self.assertEqual(work['setup_column_bit_visits'],
                         sum(item['starting_objective'][2] for item in result['descents']))
        self.assertEqual(work['setup_objective_column_visits'], 3 * n * work['setup_evaluations'])
        self.assertEqual(work['row_integer_xors'],
                         2 * (work['restart_elementary_row_xors'] + work['descent_elementary_row_xors']))
        self.assertEqual(work['restart_elementary_row_xors'],
                         work['restarts_started'] * result['limits']['restart_moves'])
        for descent in result['descents']:
            previous = tuple(descent['starting_objective'])
            for move in descent['accepted_moves']:
                self.assertEqual(tuple(move['before']), previous)
                self.assertLess(tuple(move['after']), tuple(move['before']))
                previous = tuple(move['after'])
            self.assertEqual(previous, tuple(descent['ending_objective']))
        improvements = [tuple(item['objective']) for item in result['incumbent_improvements']]
        self.assertTrue(all(after < before for before, after in zip(improvements, improvements[1:])))

    def test_full_gl3_oracle_and_every_transform_certificate(self):
        self.assertEqual(len(GL3), 168)
        rows = rows_from_columns(range(8))
        for transform in GL3:
            changed = apply_transform(rows, transform)
            certificate = {'schema': 'row_basis_discovery_v1', 'n': 8, 'row_count': 3,
                           'row_transform': list(transform), 'transformed_check_rows': list(changed),
                           'original_objective': independent_score(rows, 8),
                           'objective': independent_score(changed, 8)}
            self.assertTrue(verify_row_basis_result(rows, 8, certificate)['valid'])
            self.assertEqual(certificate['objective'], (1, 1, 12))

    def test_finite_oracle_bounds_seeded_search_without_assuming_optimality(self):
        rng = random.Random(310218)
        for _ in range(24):
            columns = [value for value in range(8) for _ in range(rng.randrange(1, 5))]
            rows, n = rows_from_columns(columns), len(columns)
            optimum = min(independent_score(apply_transform(rows, p), n) for p in GL3)
            result = discover_row_basis(rows, n, max_candidate_evaluations=400,
                                       max_restarts=12, restart_moves=3, seed=123)
            self.check_result(rows, n, result)
            self.assertGreaterEqual(tuple(result['objective']), optimum)

    def test_strict_greedy_local_minimum_is_not_a_global_claim(self):
        rows, n = trap_rows()
        result = discover_row_basis(rows, n, max_restarts=0)
        self.check_result(rows, n, result)
        optimum = min(independent_score(apply_transform(rows, p), n) for p in GL3)
        self.assertEqual(result['original_objective'][0], 2)
        self.assertEqual(result['objective'][0], 2)
        self.assertEqual(optimum[0], 1)
        self.assertTrue(result['best_is_row_xor_local_minimum'])
        self.assertFalse(result['verification']['global_optimality_checked'])

    def test_budget_accounting_and_partial_neighborhood(self):
        rows, n = trap_rows()
        for budget in [1, 2, 6, 7, 8, 13, 30]:
            result = discover_row_basis(rows, n, max_candidate_evaluations=budget,
                                       max_restarts=10, restart_moves=2)
            self.check_result(rows, n, result)
            self.assertEqual(result['work']['candidate_evaluations'], budget)
            self.assertEqual(result['termination'], 'EVALUATION_LIMIT')
        partial = discover_row_basis(rows, n, max_candidate_evaluations=6, max_restarts=0)
        self.assertFalse(partial['best_is_row_xor_local_minimum'])
        complete = discover_row_basis(rows, n, max_candidate_evaluations=7, max_restarts=0)
        self.assertTrue(complete['best_is_row_xor_local_minimum'])

    def test_reproducibility_and_kernel_equivalence_on_small_matrices(self):
        rng = random.Random(20261018)
        for _ in range(40):
            n, r = rng.randrange(9), rng.randrange(6)
            rows = tuple(rng.randrange(1 << n) for _ in range(r))
            kwargs = {'max_candidate_evaluations': 120, 'max_restarts': 4,
                      'restart_moves': 3, 'seed': 481}
            first = discover_row_basis(rows, n, **kwargs)
            second = discover_row_basis(rows, n, **kwargs)
            self.check_result(rows, n, first)
            for key in ['row_transform', 'transformed_check_rows', 'objective', 'work', 'descents']:
                self.assertEqual(first[key], second[key])
            for word in range(1 << n):
                before = all((row & word).bit_count() % 2 == 0 for row in rows)
                after = all((row & word).bit_count() % 2 == 0 for row in first['transformed_check_rows'])
                self.assertEqual(before, after)

    def test_empty_zero_dependent_and_single_row_inputs(self):
        for rows, n in [((), 0), ((), 5), ((0,), 0), ((0, 0, 0), 4),
                        ((3,), 3), ((3, 3, 0), 3)]:
            result = discover_row_basis(rows, n, max_candidate_evaluations=100,
                                       max_restarts=2, restart_moves=2)
            self.check_result(rows, n, result)
            if len(rows) < 2:
                self.assertEqual(result['termination'], 'NO_ROW_XOR_MOVES')
                self.assertEqual(result['work']['candidate_evaluations'], 1)

    def test_objective_counts_excess_above_two(self):
        rows = rows_from_columns((0, 1, 3, 7, 15), r=4)
        self.assertEqual(objective(rows, 5), (2, 3, 10))

    def test_tampered_transform_matrix_and_scores_are_rejected(self):
        rows, n = trap_rows()
        base = discover_row_basis(rows, n, max_candidate_evaluations=100)
        changes = [lambda c: c.update(schema='wrong'), lambda c: c.update(n=n + 1),
                   lambda c: c.update(row_count=2),
                   lambda c: c.update(row_transform=[1, 1, 4]),
                   lambda c: c.update(row_transform=[1, 2]),
                   lambda c: c.update(row_transform=[1, 2, 8]),
                   lambda c: c.update(row_transform=[True, 2, 4]),
                   lambda c: c['transformed_check_rows'].__setitem__(0, c['transformed_check_rows'][0] ^ 1),
                   lambda c: c.update(objective=[0, 0, 0]),
                   lambda c: c.update(original_objective=[0, 0, 0]),
                   lambda c: c.update(objective=[True, 1, 12])]
        for change in changes:
            certificate = deepcopy(base)
            change(certificate)
            self.assertFalse(verify_row_basis_result(rows, n, certificate)['valid'])

    def test_invalid_inputs_and_limits(self):
        for rows, n in [((-1,), 3), ((8,), 3), ((True,), 3), ((1.5,), 3), ((1,), -1), ((1,), True)]:
            with self.assertRaises(ValueError):
                discover_row_basis(rows, n)
        for kwargs in [{'max_candidate_evaluations': 0}, {'max_candidate_evaluations': -1},
                       {'max_candidate_evaluations': True}, {'max_restarts': -1},
                       {'max_restarts': 1.5}, {'restart_moves': -1},
                       {'restart_moves': True}, {'seed': True}]:
            with self.assertRaises(ValueError):
                discover_row_basis((3, 5, 6), 3, **kwargs)


if __name__ == '__main__':
    unittest.main()
