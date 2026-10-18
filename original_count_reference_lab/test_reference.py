import copy
from itertools import combinations, product
import random
import unittest

from reference import solve, verify
from independent_oracles import bitset_truth_count, sliding_count


def truth_count(n, clauses):
    return sum(all(any(bool(bits[abs(lit)-1]) == (lit > 0) for lit in c)
                   for c in clauses) for bits in product((0, 1), repeat=n))


class ReferenceTests(unittest.TestCase):
    def check(self, n, clauses, expected=None):
        result = solve(n, clauses)
        self.assertEqual(result['status'], 'EXACT')
        self.assertEqual(result['count'], truth_count(n, clauses) if expected is None else expected)
        self.assertTrue(verify(n, clauses, result)['valid'])
        return result

    def test_exhaustive_two_variable_formulas(self):
        clauses = [[], [1], [-1], [2], [-2], [1, 2], [1, -2], [-1, 2], [-1, -2]]
        for selected in product((0, 1), repeat=len(clauses)):
            self.check(2, [c for flag, c in zip(selected, clauses) if flag])

    def test_random_original_formulas(self):
        rng = random.Random(2026101801)
        for _ in range(300):
            n = rng.randrange(1, 9)
            clauses = [[rng.choice((-1, 1))*rng.randrange(1, n+1)
                        for _ in range(rng.randrange(0, 6))]
                       for _ in range(rng.randrange(0, 15))]
            self.check(n, clauses)

    def test_unused_repeated_tautology(self):
        self.check(256, [], 1 << 256)
        self.check(4, [[1, 2, 3], [1, 2, 3]], 14)
        self.check(8, [[1, 1], [2, -2]], 128)
        self.check(0, [[]], 0)
        self.check(0, [], 1)

    def test_component_and_disappearing_variable_counts(self):
        self.check(9, [[1, 2, 3], [4, 5, 6]], 7*7*8)
        self.check(5, [[1], [1, 2], [3, 4]], 12)
        self.check(5, [[1, 2], [1, 3]], 20)

    def test_closed_form_large_families(self):
        self.check(72, [[3*i+1, 3*i+2, 3*i+3] for i in range(24)], 7**24)
        self.check(16, list(combinations(range(1, 17), 2)), 17)
        a, b = 2, 7
        for _ in range(2, 41):
            a, b = b, 3*b+2*a
        self.check(81, [[2*i+1, 2*i+2, 2*i+3] for i in range(40)], b)

    def test_original_input_binding(self):
        r = self.check(2, [[1]])
        self.assertFalse(verify(2, [[1], []], r)['valid'])
        self.assertFalse(verify(3, [[1]], r)['valid'])
        # Even forging the input hash cannot make incomplete root coverage valid.
        import reference
        bad = copy.deepcopy(r)
        bad['certificate']['input_sha256'] = reference.request_hash(2, [[1], []])
        self.assertFalse(verify(2, [[1], []], bad)['valid'])

    def test_recurrence_mutations(self):
        for n, clauses in [(5, [[1, 2], [1, 3]]), (6, [[1, 2], [3, 4]]), (4, [[1], [2, 3]])]:
            r = self.check(n, clauses)
            mutations = []
            bad = copy.deepcopy(r); bad['count'] += 1; mutations.append(bad)
            bad = copy.deepcopy(r); bad['certificate']['free'] += 1; mutations.append(bad)
            for i, node in enumerate(r['certificate']['nodes']):
                bad = copy.deepcopy(r); bad['certificate']['nodes'][i]['count'] += 1; mutations.append(bad)
                if node['kind'] == 'branch':
                    bad = copy.deepcopy(r); bad['certificate']['nodes'][i]['children'].reverse(); mutations.append(bad)
                    bad = copy.deepcopy(r); bad['certificate']['nodes'][i]['free'][0] += 1; mutations.append(bad)
                if node['kind'] == 'components':
                    bad = copy.deepcopy(r); bad['certificate']['nodes'][i]['children'].pop(); mutations.append(bad)
                if node['kind'] == 'unit':
                    bad = copy.deepcopy(r); bad['certificate']['nodes'][i]['child'] = i; mutations.append(bad)
            for bad in mutations:
                self.assertFalse(verify(n, clauses, bad)['valid'])

    def test_caps_and_strict_inputs(self):
        for caps in ({'max_states': 0}, {'max_work': 0}, {'max_depth': 0}, {'max_count_bits': 1}):
            r = solve(5, [[1, 2], [1, 3]], **caps)
            self.assertEqual(r['status'], 'UNKNOWN')
            self.assertIsNone(r['certificate'])
            self.assertIsNone(r['count'])
        for n, clauses in [(True, []), (1, [[True]]), (1, [[0]]), (1, [[2]])]:
            with self.assertRaises(ValueError):
                solve(n, clauses)

    def test_independent_bitset_and_sliding_oracles(self):
        rng = random.Random(2026101802)
        for n in range(10):
            for _ in range(20):
                clauses = [[rng.choice((-1, 1))*rng.randrange(1, n+1)
                            for _ in range(rng.randrange(0, 5))]
                           for _ in range(rng.randrange(0, 12))] if n else [[]]
                self.assertEqual(bitset_truth_count(n, clauses)['count'], truth_count(n, clauses))
        for m in range(1, 8):
            for _ in range(10):
                clauses = [[rng.choice((-1, 1))*(i+j+1) for j in range(3)] for i in range(m)]
                self.assertEqual(sliding_count(m+2, clauses)['count'], truth_count(m+2, clauses))


if __name__ == '__main__':
    unittest.main()
