"""Independent representation, finite-oracle, exploration and budget checks."""
from itertools import product
import math
import random
import unittest

from row_basis_discovery import verify_row_basis_result
from row_basis_escape import anneal_row_basis


def rows_from_columns(columns, r=3):
    return tuple(sum(1 << j for j, column in enumerate(columns) if column >> i & 1)
                 for i in range(r))


def transformed(rows, matrix):
    output = []
    for mask in matrix:
        row = 0
        for i, value in enumerate(rows):
            if mask >> i & 1:
                row ^= value
        output.append(row)
    return tuple(output)


def score(rows, n):
    weights = [sum((row >> j) & 1 for row in rows) for j in range(n)]
    return (sum(w > 2 for w in weights), sum(max(0, w - 2) for w in weights), sum(weights))


def gl3():
    for candidate in product(range(1, 8), repeat=3):
        span = {0}
        for row in candidate:
            span |= {value ^ row for value in tuple(span)}
        if len(span) == 8:
            yield candidate


GL3 = tuple(gl3())


class RowBasisEscapeTest(unittest.TestCase):
    def check(self, rows, n, result):
        representation = result['representation']
        self.assertTrue(verify_row_basis_result(rows, n, representation)['valid'])
        self.assertEqual(tuple(representation['transformed_check_rows']),
                         transformed(rows, representation['row_transform']))
        self.assertEqual(tuple(representation['original_objective']), score(rows, n))
        self.assertEqual(tuple(representation['objective']), score(representation['transformed_check_rows'], n))
        self.assertLessEqual(tuple(representation['objective']), score(rows, n))
        self.assertFalse(result['global_optimum_claimed'])
        work = result['work']
        self.assertEqual(work['candidate_evaluations'], work['setup_evaluations'] + work['neighbor_evaluations'])
        self.assertEqual(work['setup_evaluations'], len(result['cycles']))
        self.assertLessEqual(work['candidate_evaluations'], result['parameters']['max_candidate_evaluations'])
        self.assertEqual(work['setup_column_bit_visits'], sum(cycle['starting_objective'][2] for cycle in result['cycles']))
        self.assertEqual(work['setup_objective_column_visits'], 3 * n * work['setup_evaluations'])
        self.assertEqual(work['setup_elementary_row_xors'],
                         max(0, len(result['cycles']) - 1) * result['parameters']['perturbation_moves'])
        self.assertEqual(work['neighbor_evaluations'], sum(cycle['neighbor_evaluations'] for cycle in result['cycles']))
        self.assertEqual(work['accepted_elementary_row_xors'], sum(cycle['accepted_moves'] for cycle in result['cycles']))
        improvements = [tuple(item['objective']) for item in result['incumbent_improvements']]
        self.assertTrue(all(right < left for left, right in zip(improvements, improvements[1:])))
        self.assertEqual(improvements[0], score(rows, n))
        self.assertEqual(improvements[-1], tuple(representation['objective']))

    def test_equal_budget_accounting_including_every_cycle_setup(self):
        rows = rows_from_columns(range(1, 8))
        for budget in [1, 2, 3, 4, 5, 7, 10, 31, 100]:
            result = anneal_row_basis(rows, 7, max_candidate_evaluations=budget)
            self.check(rows, 7, result)
            self.assertEqual(result['work']['candidate_evaluations'], budget)

    def test_annealing_escapes_the_proved_strict_greedy_trap(self):
        counts = {1: 1, 2: 4, 3: 3, 4: 4, 5: 3, 6: 3, 7: 2}
        columns = [value for value, count in counts.items() for _ in range(count)]
        rows, n = rows_from_columns(columns), len(columns)
        initial = score(rows, n)
        for destination in range(3):
            for source in range(3):
                if destination == source:
                    continue
                neighbor = list(rows)
                neighbor[destination] ^= neighbor[source]
                self.assertGreater(score(neighbor, n), initial)
        optimum = min(score(transformed(rows, p), n) for p in GL3)
        result = anneal_row_basis(rows, n, max_candidate_evaluations=1000)
        self.check(rows, n, result)
        self.assertEqual(initial[0], 2)
        self.assertEqual(optimum[0], 1)
        self.assertEqual(tuple(result['representation']['objective']), optimum)
        self.assertGreater(result['work']['accepted_lexicographic_worsenings'], 0)

    def test_seeded_cases_respect_exhaustive_gl3_optima(self):
        self.assertEqual(len(GL3), 168)
        rng = random.Random(28491)
        for _ in range(20):
            columns = [value for value in range(8) for _ in range(rng.randrange(1, 5))]
            rows, n = rows_from_columns(columns), len(columns)
            optimum = min(score(transformed(rows, p), n) for p in GL3)
            result = anneal_row_basis(rows, n, max_candidate_evaluations=300, seed=801)
            self.check(rows, n, result)
            self.assertGreaterEqual(tuple(result['representation']['objective']), optimum)

    def test_plateaus_are_traversed_without_fabricating_improvements(self):
        result = anneal_row_basis((0, 0, 0), 5, max_candidate_evaluations=100)
        self.check((0, 0, 0), 5, result)
        self.assertEqual(result['work']['accepted_plateau_moves'], result['work']['neighbor_evaluations'])
        self.assertEqual(result['work']['accepted_lexicographic_worsenings'], 0)
        self.assertEqual(result['representation']['row_transform'], [1, 2, 4])
        self.assertEqual(len(result['incumbent_improvements']), 1)

    def test_deterministic_seed_and_original_kernel_equivalence(self):
        rng = random.Random(8812)
        for _ in range(24):
            n, r = rng.randrange(8), rng.randrange(5)
            rows = tuple(rng.randrange(1 << n) for _ in range(r))
            first = anneal_row_basis(rows, n, max_candidate_evaluations=120, seed=99)
            second = anneal_row_basis(rows, n, max_candidate_evaluations=120, seed=99)
            self.check(rows, n, first)
            for key in ['representation', 'work', 'cycles', 'incumbent_improvements']:
                self.assertEqual(first[key], second[key])
            changed = first['representation']['transformed_check_rows']
            for word in range(1 << n):
                self.assertEqual(all((word & row).bit_count() % 2 == 0 for row in rows),
                                 all((word & row).bit_count() % 2 == 0 for row in changed))

    def test_empty_single_row_and_dependent_inputs(self):
        for rows, n in [((), 0), ((), 5), ((0,), 0), ((7,), 3), ((3, 3, 0), 3)]:
            result = anneal_row_basis(rows, n, max_candidate_evaluations=50)
            self.check(rows, n, result)
            if len(rows) < 2:
                self.assertEqual(result['work']['candidate_evaluations'], 1)

    def test_invalid_inputs_and_schedule_parameters(self):
        for rows, n in [((-1,), 3), ((8,), 3), ((True,), 3), ((1.0,), 3), ((1,), -1), ((1,), True)]:
            with self.assertRaises(ValueError):
                anneal_row_basis(rows, n)
        invalid = [{'max_candidate_evaluations': 0}, {'max_candidate_evaluations': True},
                   {'cycles': 0}, {'cycles': True}, {'perturbation_moves': -1},
                   {'perturbation_moves': True}, {'seed': True}]
        for key in ['start_temperature', 'end_temperature']:
            invalid += [{key: value} for value in [0, -1, math.inf, math.nan, True]]
        for kwargs in invalid:
            with self.assertRaises(ValueError):
                anneal_row_basis((3, 5, 6), 3, **kwargs)


if __name__ == '__main__':
    unittest.main()
