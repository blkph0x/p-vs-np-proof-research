"""Exhaustive controls for the supplied small-terminal perturbation route."""
from fractions import Fraction
import copy
import itertools
import random
import unittest

import small_terminal_perturbation as s
from labelled_tjoin import solve_tjoin, verify_tjoin


def oracle(rows, u_columns, labels, target, weights, require_nonzero=True):
    best = None
    for word in range(1 << len(labels)):
        if require_nonzero and word == 0:
            continue
        z = 0
        for j, label in enumerate(labels):
            if word >> j & 1:
                z ^= label
        b = 0
        row_count = max([0, target.bit_length(), *(col.bit_length() for col in rows),
                         *(col.bit_length() for col in u_columns)])
        for i in range(row_count):
            bit = sum((word >> j) & 1 for j, column in enumerate(rows) if column >> i & 1) & 1
            b |= bit << i
        for i, col in enumerate(u_columns):
            if z >> i & 1:
                b ^= col
        if b != target:
            continue
        cost = sum(w for j, w in enumerate(weights) if word >> j & 1)
        candidate = (cost, word)
        if best is None or candidate < best:
            best = candidate
    return best


def matrix_rows(columns, u_columns, labels, row_count):
    result = []
    for i in range(row_count):
        base = sum(1 << j for j, column in enumerate(columns) if column >> i & 1)
        perturbation = 0
        for a, u_column in enumerate(u_columns):
            if u_column >> i & 1:
                perturbation ^= sum(1 << j for j, label in enumerate(labels) if label >> a & 1)
        result.append(base ^ perturbation)
    return result


def original_oracle(rows, target, weights, require_nonzero=True):
    best = None
    for word in range(1 << len(weights)):
        if require_nonzero and not word:
            continue
        if any((row & word).bit_count() & 1 != (target >> i) & 1
               for i, row in enumerate(rows)):
            continue
        candidate = (sum(w for j, w in enumerate(weights) if word >> j & 1), word)
        if best is None or candidate < best:
            best = candidate
    return best


class SmallTerminalPerturbationTests(unittest.TestCase):
    def check(self, rows, u, labels, target, weights=None, require_nonzero=True, **kwargs):
        weights = [1] * len(labels) if weights is None else weights
        expected = oracle(rows, u, labels, target, weights, require_nonzero)
        result = s.solve_perturbation(rows, u, labels, target, weights=weights,
                                      require_nonzero=require_nonzero, **kwargs)
        self.assertEqual(result['status'], 'EXACT', result)
        actual = None if result['weight'] is None else (result['weight'], result['word'])
        self.assertEqual(None if expected is None else actual[0], None if expected is None else expected[0])
        if actual is not None:
            self.assertEqual(s._direct_properties(tuple(rows), tuple(u), tuple(labels),
                                                   tuple(weights), target, actual[1],
                                                   max([0, target.bit_length(), *(x.bit_length() for x in rows),
                                                        *(x.bit_length() for x in u)]))[0], True)
        checked = s.verify_perturbation(rows, u, labels, target, result,
                                        weights=weights, p=kwargs.get('p'),
                                        require_nonzero=require_nonzero)
        self.assertTrue(checked['valid'], checked)
        return result

    def test_one_edge_inconsistent_branch_is_rejected(self):
        # B=[1,1]^T, U=[1,1]^T, V=[1], hence H=B+UV=0.
        result = self.check([3], [3], [1], 1, require_nonzero=False)
        self.assertIsNone(result['word'])
        self.assertIsNone(result['weight'])
        self.assertEqual(result['stats']['completed_branches'], 2)

    def test_triangle_wrong_label_path(self):
        # The direct edge has the wrong label; the two-edge path is optimal.
        rows = [3, 5, 6]
        result = self.check(rows, [1], [1, 0, 0], 3,
                            weights=[1, 1, 1], require_nonzero=True)
        self.assertEqual((result['weight'], result['word']), (2, 6))

    def test_disconnected_cycle_correction(self):
        # u-v supplies the boundary; a disconnected labelled triangle supplies
        # the required odd label and cannot be found by one labelled walk.
        rows = [3, 12, 24, 20]
        labels = [0, 1, 0, 0]
        edges = [(0, 1, 0, 1), (2, 3, 1, 1), (3, 4, 0, 1), (2, 4, 0, 1)]
        result = solve_tjoin(5, edges, 1, terminals=[0, 1], target=1)
        self.assertEqual((result['weight'], result['word']), (4, 15))
        self.assertTrue(verify_tjoin(5, edges, 1, result, terminals=[0, 1], target=1)['valid'])

    def test_exhaustive_tiny_perturbations(self):
        rng = random.Random(2026101819)
        for _ in range(220):
            r = rng.randrange(1, 5)
            m = rng.randrange(0, 7)
            p = rng.randrange(0, 3)
            rows = []
            for _ in range(m):
                support = rng.sample(range(r), rng.randrange(min(2, r) + 1))
                rows.append(sum(1 << i for i in support))
            u = [rng.randrange(1 << r) for _ in range(p)]
            labels = [rng.randrange(1 << p) for _ in range(m)]
            weights = [rng.randrange(4) for _ in range(m)]
            target = rng.randrange(1 << r)
            for nonempty in (False, True):
                self.check(rows, u, labels, target, weights=weights,
                           require_nonzero=nonempty, p=p)

    def test_free_variables_and_zero_rank(self):
        # A zero B column is a graph loop at the ground vertex and remains a
        # selectable free coordinate; p=0 is a valid perturbation dimension.
        result = self.check([0, 1], [], [0, 0], 1, weights=[0, 3], p=0)
        self.assertEqual(result['word'], 2)
        self.assertTrue(self.check([0, 1], [], [0, 0], 0, weights=[0, 3], p=0,
                                   require_nonzero=True)['weight'] == 0)
        # When every V label is zero, the number of U columns still determines
        # p if the caller omits it.
        inferred = self.check([1], [1], [0], 1, weights=[2], require_nonzero=False)
        self.assertEqual(inferred['weight'], 2)

    def test_branch_cap_is_unknown_and_certificate_tampering_rejected(self):
        result = s.solve_perturbation([3], [3], [1], 0, limits={'max_branches': 1})
        self.assertEqual(result['status'], 'UNKNOWN')
        self.assertIsNone(result['certificate'])
        exact = self.check([3, 5], [1], [1, 0], 0, weights=[2, 1], p=1)
        bad = copy.deepcopy(exact)
        bad['certificate']['branches'][0]['rhs'] ^= 1
        self.assertFalse(s.verify_perturbation([3, 5], [1], [1, 0], 0, bad,
                                                weights=[2, 1], p=1)['valid'])

    def test_original_matrix_binding_and_mutations(self):
        columns, u, labels, weights, row_count = [3, 5, 6], [1], [1, 0, 0], [1, 2, 1], 3
        original = matrix_rows(columns, u, labels, row_count)
        result = s.solve_original(original, columns, u, labels, 3, weights=weights,
                                  row_count=row_count, p=1)
        self.assertEqual(result['status'], 'EXACT')
        self.assertEqual((result['weight'], result['word']), original_oracle(original, 3, weights))
        self.assertTrue(s.verify_original(original, columns, u, labels, 3, result,
                                          weights=weights, row_count=row_count, p=1)['valid'])
        changed = copy.deepcopy(result)
        changed['certificate']['original_rows'][0] ^= 1
        self.assertFalse(s.verify_original(original, columns, u, labels, 3, changed,
                                           weights=weights, row_count=row_count, p=1)['valid'])
        changed = copy.deepcopy(result)
        changed['certificate']['perturbation']['branches'][0]['rhs'] ^= 1
        self.assertFalse(s.verify_original(original, columns, u, labels, 3, changed,
                                           weights=weights, row_count=row_count, p=1)['valid'])
        with self.assertRaises(ValueError):
            s.solve_original(original, [1, 5, 6], u, labels, 3, weights=weights,
                             row_count=row_count, p=1)

    def test_random_original_matrix_adapter_and_cap(self):
        rng = random.Random(2026101820)
        for _ in range(120):
            r = rng.randrange(1, 5)
            m = rng.randrange(0, 7)
            p = rng.randrange(0, 3)
            columns = []
            for __ in range(m):
                support = rng.sample(range(r), rng.randrange(min(2, r) + 1))
                columns.append(sum(1 << i for i in support))
            u = [rng.randrange(1 << r) for __ in range(p)]
            labels = [rng.randrange(1 << p) for __ in range(m)]
            weights = [rng.randrange(4) for __ in range(m)]
            original = matrix_rows(columns, u, labels, r)
            target = rng.randrange(1 << r)
            for nonempty in (False, True):
                result = s.solve_original(original, columns, u, labels, target,
                                           weights=weights, row_count=r, p=p,
                                           require_nonzero=nonempty)
                self.assertEqual(result['status'], 'EXACT', result)
                expected = original_oracle(original, target, weights, nonempty)
                actual = None if result['weight'] is None else (result['weight'], result['word'])
                self.assertEqual(None if actual is None else actual[0],
                                 None if expected is None else expected[0])
                self.assertTrue(s.verify_original(original, columns, u, labels, target, result,
                                                  weights=weights, row_count=r, p=p,
                                                  require_nonzero=nonempty)['valid'])
        capped = s.solve_original([1], [1], [1], [0], 1, weights=[1],
                                  row_count=1, p=1, require_nonzero=False,
                                  limits={'max_branches': 1})
        self.assertEqual(capped['status'], 'UNKNOWN')
        self.assertTrue(s.verify_original([1], [1], [1], [0], 1, capped,
                                          weights=[1], row_count=1, p=1,
                                          require_nonzero=False)['valid'])


if __name__ == '__main__':
    unittest.main()
