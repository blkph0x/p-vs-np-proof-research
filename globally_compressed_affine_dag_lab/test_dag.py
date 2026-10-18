"""Baseline invariant regressions, adapted without changing the frozen source."""
import copy
from fractions import Fraction
import itertools
import random
import unittest

import dag


def assignment(ids, bits):
    return sum(((bits >> j) & 1) << v for j, v in enumerate(ids))


def evaluate_factor(factor, word):
    if factor['kind'] == 'or':
        return Fraction(any(bool((word >> (abs(lit)-1)) & 1) == (lit > 0)
                            for lit in factor['literals']))
    if any((word & mask).bit_count() % 2 != rhs for mask, rhs in factor['equations']):
        return Fraction(0)
    parity = sum((word & mask) == mask for mask in factor['phase']) % 2
    return dag.rational(factor['scalar']) * (-1 if parity else 1)


def evaluate_message(piece, word):
    if piece['zero'] or any((word & mask).bit_count() % 2 != rhs for mask, rhs in piece['equations']):
        return Fraction(0)
    parity = sum((word & mask) == mask for mask in piece['phase']) % 2
    return dag.rational(piece['scalar']) * (-1 if parity else 1)


def oracle(n, factors):
    total = Fraction(0)
    for word in range(1 << n):
        product = Fraction(1)
        for factor in factors:
            product *= evaluate_factor(factor, word)
        total += product
    return total


def check_all_messages(test, factors, result):
    checked = 0
    for node in result['certificate']['nodes']:
        scopes = [dag.source_terms(factors[i])[0] for i in node['factor_ids']]
        variables = sorted(set(itertools.chain.from_iterable(scopes)))
        boundary = node['boundary']
        internal = sorted(set(variables) - set(boundary))
        for bits in range(1 << len(boundary)):
            fixed = assignment(boundary, bits)
            expected = Fraction(0)
            for rest in range(1 << len(internal)):
                word = fixed | assignment(internal, rest)
                product = Fraction(1)
                for i in node['factor_ids']:
                    product *= evaluate_factor(factors[i], word)
                expected += product
            actual = sum((evaluate_message(piece, fixed) for piece in node['messages']), Fraction(0))
            test.assertEqual(actual, expected)
            checked += 1
    return checked


def affine(scope, equations=(), phase=(), scalar=1):
    return {'kind': 'affine', 'scope': list(scope), 'equations': [list(row) for row in equations],
            'phase': list(phase), 'scalar': dag.pack(scalar)}


class TestGloballyCompressedDAG(unittest.TestCase):
    def assert_formula(self, n, clauses, **kwargs):
        factors = [{'kind': 'or', 'literals': list(c)} for c in clauses]
        result = dag.solve_formula(n, clauses, **kwargs)
        self.assertEqual(result['status'], 'EXACT', result)
        self.assertEqual(result['count'], oracle(n, factors))
        self.assertTrue(dag.verify_formula(n, clauses, result, **kwargs)['valid'])
        check_all_messages(self, factors, result)
        return result

    def test_original_count_normalization_and_free_variables(self):
        for n, clauses in [(0, []), (4, []), (3, [[]]), (4, [[1, -1, 2]]),
                           (4, [[1, 1, -2], [2, 2]]), (3, [[1], [-1]]),
                           (6, [[1, 2], [-3, 4], [5, -5]])]:
            self.assert_formula(n, clauses)

    def test_random_original_formula_and_every_boundary(self):
        rng = random.Random(2026101851)
        for _ in range(100):
            n = rng.randrange(1, 7)
            clauses = [[rng.choice((-1, 1))*rng.randrange(1, n+1)
                        for __ in range(rng.randrange(5))] for ___ in range(rng.randrange(9))]
            self.assert_formula(n, clauses)

    def test_signed_native_affine_and_or(self):
        factors = [affine([0, 1, 2], [[3, 1]], [3, 4], Fraction(-3, 2)),
                   {'kind': 'or', 'literals': [2, -3, 4]},
                   affine([3, 4], [], [24], Fraction(2, 3))]
        result = dag.solve_factors(6, factors)
        self.assertEqual(result['status'], 'EXACT')
        self.assertEqual(dag.rational(result['value']), oracle(6, factors))
        self.assertTrue(dag.verify_factors(6, factors, result)['valid'])
        check_all_messages(self, factors, result)

    def test_random_native_mixed_messages(self):
        rng = random.Random(2026101852)
        for _ in range(60):
            n = rng.randrange(1, 6)
            factors = []
            for __ in range(rng.randrange(1, 6)):
                scope = sorted(rng.sample(range(n), rng.randrange(n+1)))
                if rng.randrange(2):
                    factors.append({'kind': 'or', 'literals': [(v+1)*rng.choice((-1, 1)) for v in scope]})
                else:
                    mask = sum(1 << v for v in scope)
                    rows = [[rng.randrange(1 << n) & mask, rng.randrange(2)] for ___ in range(rng.randrange(3))]
                    phase = [0] if rng.randrange(2) else []
                    phase += [1 << v for v in scope if rng.randrange(2)]
                    phase += [(1 << u) | (1 << v) for u, v in itertools.combinations(scope, 2) if rng.randrange(2)]
                    factors.append(affine(scope, rows, phase, Fraction(rng.randrange(-2, 3), rng.randrange(1, 4))))
            result = dag.solve_factors(n, factors)
            self.assertEqual(result['status'], 'EXACT')
            self.assertEqual(dag.rational(result['value']), oracle(n, factors))
            self.assertTrue(dag.verify_factors(n, factors, result)['valid'])
            check_all_messages(self, factors, result)

    def test_negative_zero_and_phase_multiplicity(self):
        for factors in [[affine([0, 1], [], [0], 3)],
                        [affine([0], [], [1])],
                        [affine([0, 1], [], [3, 3], -2)],
                        [affine([0, 1], [[3, 0], [3, 1]], [], -7)]]:
            result = dag.solve_factors(3, factors)
            self.assertEqual(dag.rational(result['value']), oracle(3, factors))
            self.assertTrue(dag.verify_factors(3, factors, result)['valid'])

    def test_shared_requests_and_coefficient_merge(self):
        result = self.assert_formula(2, [[1, 2], [1, 2]])
        self.assertGreater(result['stats']['marginal_cache_hits'], 0)
        self.assertEqual(result['stats']['products'], 4)
        self.assertEqual(result['count'], 3)

    def test_products_charged_before_merge_and_caps_unknown(self):
        for cap in [{'max_products': 3}, {'max_terms': 1}, {'max_nodes': 1}, {'max_work': 0},
                    {'max_variables': 1}, {'max_factors': 1}, {'max_integer_bits': 1},
                    {'boundary_caps': {'max_work': 0}}]:
            result = dag.solve_formula(2, [[1, 2], [1, 2]], **cap)
            self.assertEqual(result['status'], 'UNKNOWN', cap)
            self.assertIsNone(result['certificate'])
            self.assertIsNone(result['count'])
        result = dag.solve_formula(100, [], max_integer_bits=99)
        self.assertEqual(result['status'], 'UNKNOWN')

    def test_verifier_caps_unknown(self):
        result = dag.solve_formula(2, [[1, 2], [1, 2]])
        for cap in [{'max_products': 3}, {'max_terms': 1}, {'max_nodes': 1}, {'max_work': 0},
                    {'boundary_caps': {'max_work': 0}}]:
            checked = dag.verify_formula(2, [[1, 2], [1, 2]], result, **cap)
            self.assertFalse(checked['valid'])
            self.assertEqual(checked['status'], 'UNKNOWN')

    def test_omitted_original_clause_and_external_binding(self):
        result = dag.solve_formula(1, [[1]])
        for n, clauses in [(1, [[1], []]), (1, [[-1]]), (2, [[1]])]:
            self.assertFalse(dag.verify_formula(n, clauses, result)['valid'])
        changed = copy.deepcopy(result)
        clauses = [[1], []]
        binding = dag.digest({'n': 1, 'factors': [{'kind': 'or', 'literals': c} for c in clauses], 'order': [0, 1]})
        changed['request_sha256'] = changed['certificate']['request_sha256'] = binding
        self.assertFalse(dag.verify_formula(1, clauses, changed)['valid'])

    def test_partition_projection_and_total_tampering(self):
        clauses = [[1, 2], [-1, 3], [2, -3]]
        original = dag.solve_formula(4, clauses)
        mutators = [lambda r: r['certificate']['nodes'][-1]['factor_ids'].pop(),
                    lambda r: r['certificate']['nodes'][-1]['children'].__setitem__(1, 0),
                    lambda r: r['certificate']['nodes'][0]['boundary'].clear(),
                    lambda r: r['certificate']['nodes'][0]['active'].append(3),
                    lambda r: r['certificate']['nodes'][-1]['requests'].pop(),
                    lambda r: r['certificate']['free_variables'].clear(),
                    lambda r: r.__setitem__('count', r['count']+1),
                    lambda r: r['certificate']['value'].__setitem__(0, 999)]
        for mutate in mutators:
            changed = copy.deepcopy(original)
            mutate(changed)
            self.assertFalse(dag.verify_formula(4, clauses, changed)['valid'])

    def test_marginal_and_merge_tampering(self):
        clauses = [[1, 2], [1, 2]]
        original = dag.solve_formula(3, clauses)
        for target in ('request', 'proof', 'merge', 'orphan'):
            changed = copy.deepcopy(original)
            if target == 'request':
                changed['certificate']['marginals'][0]['request']['active'].append(2)
            elif target == 'proof':
                changed['certificate']['marginals'][0]['result']['message']['scalar'][0] += 1
            elif target == 'merge':
                changed['certificate']['nodes'][0]['messages'][0]['scalar'][0] += 1
            else:
                changed['certificate']['marginals'].append(copy.deepcopy(changed['certificate']['marginals'][0]))
            self.assertFalse(dag.verify_formula(3, clauses, changed)['valid'])

    def test_typed_metadata_and_untrusted_convenience_key(self):
        original = dag.solve_formula(2, [[1, 2], [1, 2]])
        changed = copy.deepcopy(original)
        changed['certificate']['nodes'][0]['boundary'][0] = False
        self.assertFalse(dag.verify_formula(2, [[1, 2], [1, 2]], changed)['valid'])
        changed = copy.deepcopy(original)
        changed['value'][0] = float(changed['value'][0])
        self.assertFalse(dag.verify_formula(2, [[1, 2], [1, 2]], changed)['valid'])
        changed = copy.deepcopy(original)
        for record in changed['certificate']['marginals']:
            record['result']['key'] = 'untrusted and ignored'
            record['result']['stats'] = {'work': -999999}
        self.assertTrue(dag.verify_formula(2, [[1, 2], [1, 2]], changed)['valid'])

    def test_invalid_inputs_and_orders(self):
        for n, clauses in [(True, []), (1, [[True]]), (1, [[0]]), (1, [[2]])]:
            with self.assertRaises(ValueError): dag.solve_formula(n, clauses)
        for order in [[0], [0, 0], [False, 1], 7]:
            with self.assertRaises(ValueError): dag.solve_formula(2, [[1], [2]], order=order)
        self.assert_formula(3, [[1, 2], [-2, 3]], order=[1, 0])

    def test_wide_native_compact_elimination(self):
        n = 80
        factors = [affine(list(range(n)), [[(1 << n)-1, 0]], [], Fraction(-3, 5))]
        result = dag.solve_factors(n, factors)
        self.assertEqual(result['status'], 'EXACT')
        self.assertEqual(dag.rational(result['value']), Fraction(-3, 5)*(1 << 79))
        self.assertTrue(dag.verify_factors(n, factors, result)['valid'])
        self.assertEqual(result['stats']['peak_terms'], 1)

    def test_unit_streaming_retained_and_transient_counts(self):
        clauses = [[1], [1]]
        result = self.assert_formula(1, clauses, max_terms=1)
        self.assertEqual(result['count'], 1)
        self.assertTrue(all(len(node['messages']) == 1 for node in result['certificate']['nodes']))
        self.assertEqual(result['stats']['peak_terms'], 1)
        self.assertGreaterEqual(result['stats']['peak_generated_input_terms'], 2)
        self.assertGreaterEqual(result['stats']['compression_peak_live_pieces'], 2)
        self.assertEqual(result['stats']['compression_peak_retained_pieces'], 1)
        self.assertEqual(result['stats']['products'], 1)

    def test_compression_limits_are_aggregate_across_nodes(self):
        clauses = [[1], [1]]
        exact = self.assert_formula(1, clauses)
        mappings = {'max_inputs': 'incoming_pieces', 'max_generated': 'generated_pieces',
                    'max_pairs': 'attempted_pairs', 'max_steps': 'steps', 'max_work': 'work'}
        for cap, statistic in mappings.items():
            total = exact['stats']['compression_'+statistic]
            self.assertGreater(total, 0)
            result = dag.solve_formula(1, clauses, compression_caps={cap: total-1})
            self.assertEqual(result['status'], 'UNKNOWN', (cap, result))
            self.assertIsNone(result['certificate'])
        checked = dag.verify_formula(1, clauses, exact)
        for cap, statistic in mappings.items():
            total = checked['stats']['compression_'+statistic]
            self.assertGreater(total, 0)
            result = dag.verify_formula(1, clauses, exact, compression_caps={cap: total-1})
            self.assertEqual(result['status'], 'UNKNOWN', (cap, result))
        self.assertEqual(dag.solve_formula(1, clauses, max_work=exact['stats']['work']-1)['status'], 'UNKNOWN')

    def test_compression_proofs_are_required_and_source_bound(self):
        clauses = [[1], [1, 2], [-2, 3]]
        original = self.assert_formula(4, clauses)
        changed = copy.deepcopy(original)
        changed['certificate']['nodes'][0]['compression'] = None
        self.assertFalse(dag.verify_formula(4, clauses, changed)['valid'])
        changed = copy.deepcopy(original)
        changed['certificate']['nodes'][0]['compression']['messages'] = []
        self.assertFalse(dag.verify_formula(4, clauses, changed)['valid'])
        changed = copy.deepcopy(original)
        del changed['certificate']['nodes'][0]['compression']['certificate']
        self.assertFalse(dag.verify_formula(4, clauses, changed)['valid'])
        changed = copy.deepcopy(original)
        changed['certificate']['nodes'][0]['compression'] = copy.deepcopy(changed['certificate']['nodes'][-1]['compression'])
        self.assertFalse(dag.verify_formula(4, clauses, changed)['valid'])

    def test_compressor_statistics_are_not_trusted(self):
        clauses = [[1], [1]]
        original = dag.solve_formula(1, clauses)
        expected = dag.verify_formula(1, clauses, original)
        changed = copy.deepcopy(original)
        for node in changed['certificate']['nodes']:
            node['compression']['stats'] = {key: -9999 for key in dag.COMPRESSION_COUNTERS}
        actual = dag.verify_formula(1, clauses, changed)
        self.assertTrue(actual['valid'])
        self.assertEqual(actual['stats'], expected['stats'])

    def test_failed_pair_discovery_is_metered(self):
        result = self.assert_formula(3, [[1, 2], [1, 3]])
        self.assertGreater(result['stats']['compression_failed_pairs'], 0)
        self.assertGreaterEqual(result['stats']['compression_attempted_pairs'], result['stats']['compression_failed_pairs'])
        self.assertGreater(result['stats']['compression_work'], 0)
        self.assertGreater(result['stats']['work'], result['stats']['compression_work'])

    def test_new_format_is_distinct_from_frozen_baseline(self):
        result = dag.solve_formula(1, [[1]])
        self.assertEqual(result['certificate']['format'], 'globally-compressed-affine-dag-v1')
        changed = copy.deepcopy(result)
        changed['certificate']['format'] = 'compressed-affine-dag-v1'
        self.assertFalse(dag.verify_formula(1, [[1]], changed)['valid'])


if __name__ == '__main__':
    unittest.main()
