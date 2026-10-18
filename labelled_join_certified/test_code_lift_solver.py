import copy
import itertools
import json
import random
import unittest

from code_lift_solver import prepare_code, solve_code, verify_code


def rows_of(columns, r):
    return [sum(((column >> i) & 1) << j for j, column in enumerate(columns)) for i in range(r)]


def brute(rows, n, target, nonzero, weights=None):
    weights = [1] * n if weights is None else weights
    best = None
    for word in range(1 if nonzero else 0, 1 << n):
        syndrome = sum(((word & row).bit_count() % 2) << i for i, row in enumerate(rows))
        if syndrome == target:
            cost = sum(w for j, w in enumerate(weights) if word >> j & 1)
            best = cost if best is None else min(cost, best)
    return best


class CodeLiftTests(unittest.TestCase):
    def check(self, rows, n, graph_rows, target, nonzero, transform=None, weights=None):
        result = solve_code(rows, n, graph_rows, row_transform=transform, target=target,
                            require_nonzero=nonzero, weights=weights)
        self.assertEqual(result['status'], 'EXACT')
        self.assertEqual(result['distance'], brute(rows, n, target, nonzero, weights))
        checked = verify_code(rows, n, json.loads(json.dumps(result)), target=target,
                               require_nonzero=nonzero, weights=weights)
        self.assertTrue(checked['valid'], checked)
        return result

    def test_all_three_row_matrices_through_two_columns_all_targets(self):
        requests = 0
        for n in range(3):
            for columns in itertools.product(range(8), repeat=n):
                rows = rows_of(columns, 3)
                for target in range(8):
                    for nonzero in (False, True):
                        self.check(rows, n, 2, target, nonzero)
                        requests += 1
        self.assertEqual(requests, 1168)

    def test_seeded_weighted_codes_and_affine_requests(self):
        rng = random.Random(51018)
        for _ in range(75):
            n, g, p = rng.randrange(1, 10), rng.randrange(4), rng.randrange(4)
            low = [x for x in range(1 << g) if x.bit_count() <= 2]
            columns = [rng.choice(low) | (rng.randrange(1 << p) << g) for _ in range(n)]
            rows = rows_of(columns, g + p)
            weights = [rng.randrange(4) for _ in range(n)]
            for target in (0, rng.randrange(1 << (g + p))):
                for nonzero in (False, True):
                    self.check(rows, n, g, target, nonzero, weights=weights)

    def test_all_invertible_three_row_transforms_bind_original_target(self):
        def rank(rows):
            return len({(rows[0] if a & 1 else 0) ^ (rows[1] if a & 2 else 0)
                        ^ (rows[2] if a & 4 else 0) for a in range(8)}) == 8
        rows = [0b10101, 0b11010, 0b01110]
        count = 0
        for transform in itertools.product(range(8), repeat=3):
            if rank(transform):
                for target in (0, 5):
                    self.check(rows, 5, 2, target, True, transform)
                count += 1
        self.assertEqual(count, 168)

    def test_explicit_one_row_lift_and_pg_controls(self):
        columns = [i for i in range(1, 16) if i not in (7, 15)]
        self.assertEqual(self.check(rows_of(columns, 4), 13, 3, 0, True)['distance'], 3)
        pg = list(range(1, 16))
        self.assertEqual(self.check(rows_of(pg, 4), 15, 2, 0, True)['distance'], 3)
        with self.assertRaises(ValueError):
            solve_code(rows_of(pg, 4), 15, 3)

    def test_invalid_and_forged_normal_forms(self):
        rows = [3, 5, 6]
        answer = self.check(rows, 3, 2, 0, True)
        for mutate in (lambda x: x.update(distance=1), lambda x: x.update(word=0),
                       lambda x: x.update(target=True), lambda x: x.update(require_nonzero=1),
                       lambda x: x['transformed_rows'].__setitem__(0, 0),
                       lambda x: x['row_transform'].__setitem__(0, 0),
                       lambda x: x['weights'].__setitem__(0, 2),
                       lambda x: x.update(transformed_target=1),
                       lambda x: x.update(dimension=3)):
            bad = copy.deepcopy(answer)
            mutate(bad)
            self.assertFalse(verify_code(rows, 3, bad)['valid'])
        self.assertFalse(verify_code(rows, 3, answer, target=1)['valid'])
        self.assertFalse(verify_code(rows, 3, answer, require_nonzero=False)['valid'])
        self.assertFalse(verify_code(rows, 3, answer, weights=[2, 1, 1])['valid'])
        for options in ({'row_transform': [1, 1, 4]}, {'target': 8}, {'weights': [1]},
                        {'weights': [1, -1, 1]}, {'require_nonzero': 1}):
            with self.assertRaises(ValueError):
                solve_code(rows, 3, 2, **options)

    def test_unknown_and_zero_objective_nonzero_word(self):
        rows = [3, 5, 6]
        partial = solve_code(rows, 3, 2, max_pin_cases=1)
        self.assertEqual(partial['status'], 'UNKNOWN')
        self.assertIsNone(partial['distance'])
        self.assertEqual(partial['upper_bound'], 3)
        self.assertTrue(verify_code(rows, 3, partial)['valid'])
        zero = self.check([0], 1, 0, 0, True, weights=[0])
        self.assertEqual((zero['distance'], zero['word']), (0, 1))
        exhausted = verify_code([0], 1, zero, weights=[0], verification_state_limit=0)
        self.assertEqual(exhausted['status'], 'UNKNOWN')


if __name__ == '__main__':
    unittest.main()
