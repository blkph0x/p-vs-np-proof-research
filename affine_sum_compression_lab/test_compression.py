"""Bounded original-assignment and adversarial certificate regressions."""
import copy
from fractions import Fraction
import itertools
import json
from pathlib import Path
import random
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parent))
import compression as c


def message(n, retained=None, equations=(), phase=(), scalar=1):
    retained = list(range(n)) if retained is None else retained
    result = c.boundary.normalize_message(n, retained, list(equations), list(phase), scalar)
    assert result['status'] == 'EXACT'
    return result['message']


def value(piece, word):
    if piece['zero'] or any((mask & word).bit_count() % 2 != rhs for mask, rhs in piece['equations']):
        return Fraction(0)
    sign = sum((word & term) == term for term in piece['phase']) % 2
    return Fraction(*piece['scalar']) * (-1 if sign else 1)


def check_case(n, retained, originals, **caps):
    result = c.compress(n, retained, originals, **caps)
    assert result['status'] == 'EXACT', result
    checked = c.verify_compression(n, retained, originals, json.loads(json.dumps(result)), **caps)
    assert checked['valid'], checked
    for bits in range(1 << len(retained)):
        word = sum(((bits >> j) & 1) << i for j, i in enumerate(retained))
        assert sum(value(p, word) for p in originals) == sum(value(p, word) for p in checked['messages'])
    return result


class CompressionTests(unittest.TestCase):
    def test_identical_addition_and_exact_cancellation(self):
        a = message(3, equations=[[3, 1]], phase=[4], scalar=Fraction(2, 3))
        b = message(3, equations=[[3, 1]], phase=[4], scalar=Fraction(-5, 7))
        result = check_case(3, [0, 1, 2], [a, b])
        self.assertEqual(result['messages'][0]['scalar'], [-1, 21])
        neg = copy.deepcopy(a); neg['scalar'][0] *= -1
        self.assertEqual(check_case(3, [0, 1, 2], [a, neg])['messages'], [])

    def test_exhaustive_parallel_cosets_phase_and_sign(self):
        # Common free coordinates 1,2: all 16 quadratic phases on each coset.
        monomials = [2, 4, 6]
        for bits0, bits1, sign in itertools.product(range(8), range(8), [-1, 1]):
            phases = [[term for i, term in enumerate(monomials) if bits >> i & 1] for bits in (bits0, bits1)]
            pieces = [message(3, equations=[[1, side]], phase=phases[side], scalar=1 if side == 0 else sign) for side in range(2)]
            result = check_case(3, [0, 1, 2], pieces)
            self.assertEqual(len(result['messages']), 1 if ((bits0 ^ bits1) & 4) == 0 else 2)

    def test_same_support_affine_phase_pinning(self):
        a = message(4, equations=[[3, 1]], phase=[12], scalar=Fraction(3, 5))
        b = message(4, equations=[[3, 1]], phase=[12, 4, 8], scalar=Fraction(-3, 5))
        result = check_case(4, list(range(4)), [a, b])
        self.assertEqual(len(result['messages']), 1)
        self.assertEqual(len(result['messages'][0]['equations']), 2)
        self.assertEqual(result['messages'][0]['scalar'], [6, 5])

    def test_nested_restricted_phase_and_both_orientations(self):
        outer = message(3, phase=[3], scalar=Fraction(7, 11))
        # On x0=1, x0*x1 equals x1, despite distinct global quadratic forms.
        inner = message(3, equations=[[1, 1]], phase=[2], scalar=Fraction(-7, 11))
        for pieces in ([outer, inner], [inner, outer]):
            result = check_case(3, [0, 1, 2], pieces)
            self.assertEqual(result['messages'], [message(3, equations=[[1, 0]], scalar=Fraction(7, 11))])
        wrong = message(3, equations=[[1, 1]], phase=[4], scalar=Fraction(-7, 11))
        self.assertEqual(len(check_case(3, [0, 1, 2], [outer, wrong])['messages']), 2)
        # A phase restriction equal to one makes equal raw coefficients cancel.
        epsilon_one = [message(3, phase=[1]), message(3, equations=[[1, 1]])]
        self.assertEqual(check_case(3, [0, 1, 2], epsilon_one)['messages'], [message(3, equations=[[1, 0]])])

    def test_higher_codimension_and_unequal_magnitude_not_merged(self):
        cases = [[message(3), message(3, equations=[[1, 0], [2, 0]], scalar=-1)],
                 [message(3, equations=[[1, 0]]), message(3, equations=[[1, 1]], scalar=2)]]
        for originals in cases:
            self.assertEqual(len(check_case(3, [0, 1, 2], originals)['messages']), 2)

    def test_seeded_original_sums(self):
        rng = random.Random(2026101907)
        for _ in range(180):
            n = rng.randrange(6)
            retained = rng.sample(range(n), rng.randrange(n+1))
            mask = sum(1 << i for i in retained)
            terms = [1 << i for i in retained] + [(1 << i) | (1 << j) for i in retained for j in retained if i < j]
            originals = [message(n, retained, [[rng.getrandbits(n) & mask, rng.randrange(2)] for _ in range(rng.randrange(4))],
                                 rng.sample(terms, rng.randrange(len(terms)+1)), Fraction(rng.randrange(-3, 4), rng.randrange(1, 5)))
                         for _ in range(rng.randrange(9))]
            check_case(n, retained, originals)

    def test_empty_zero_scalar_and_sparse_original_coordinates(self):
        self.assertEqual(check_case(0, [], [])['messages'], [])
        self.assertEqual(check_case(0, [], [message(0, scalar=3), message(0, scalar=-1)])['messages'][0]['scalar'], [2, 1])
        self.assertEqual(check_case(5, [4, 1], [message(5, [4, 1], scalar=0)])['messages'], [])
        check_case(7, [6, 2, 0], [message(7, [6, 2, 0], [[65, 0]], [4]), message(7, [6, 2, 0], [[65, 1]], [4])])

    def test_order_nonconfluence_and_streaming_peaks(self):
        pins = [message(3, equations=[[1 << i, word >> i & 1] for i in range(3)]) for word in range(8)]
        good = check_case(3, [0, 1, 2], pins)
        bad = check_case(3, [0, 1, 2], [pins[i] for i in [0, 1, 4, 6, 3, 7, 2, 5]])
        self.assertEqual([len(good['messages']), len(bad['messages'])], [1, 4])
        a = message(1)
        result = check_case(1, [0], [a, a], max_live_pieces=1)
        self.assertEqual(result['stats']['peak_retained_pieces'], 1)
        self.assertEqual(result['stats']['peak_live_pieces'], 2)
        self.assertEqual(result['stats']['peak_live_plus_pending_objects'], 3)
        self.assertEqual(result['stats']['peak_pending_generated_objects'], 1)
        failed = c.compress(1, [0], [a, a], max_steps=1)
        self.assertEqual(failed['status'], 'UNKNOWN')
        self.assertEqual(failed['stats']['peak_live_pieces'], 2)

    def test_exact_budget_boundaries_and_unknown_without_sum(self):
        originals = [message(2, equations=[[1, 0]]), message(2, equations=[[1, 1]])]
        baseline = c.compress(2, [0, 1], originals)
        for cap, stat in [('max_inputs', 'incoming_pieces'), ('max_generated', 'generated_pieces'),
                          ('max_pairs', 'attempted_pairs'), ('max_steps', 'steps'), ('max_work', 'work')]:
            count = baseline['stats'][stat]
            self.assertEqual(c.compress(2, [0, 1], originals, **{cap: count})['status'], 'EXACT')
            failed = c.compress(2, [0, 1], originals, **{cap: count-1})
            self.assertEqual((failed['status'], failed['messages'], failed['certificate']), ('UNKNOWN', None, None))
        checked = c.verify_compression(2, [0, 1], originals, baseline)
        work = checked['stats']['work']
        self.assertTrue(c.verify_compression(2, [0, 1], originals, baseline, max_work=work)['valid'])
        self.assertEqual(c.verify_compression(2, [0, 1], originals, baseline, max_work=work-1)['status'], 'UNKNOWN')
        self.assertEqual(c.compress(10**9, [], [])['status'], 'UNKNOWN')

    def test_original_coverage_metadata_and_mutations(self):
        originals = [message(2, equations=[[1, 0]]), message(2, equations=[[1, 1]])]
        baseline = c.compress(2, [0, 1], originals)
        for changed in [originals[:1], originals + [message(2)], list(reversed(originals))]:
            self.assertFalse(c.verify_compression(2, [0, 1], changed, baseline)['valid'])
        mutations = []
        for mutate in [lambda x: x['certificate'].__setitem__('input_sha256', '0'*64),
                       lambda x: x['certificate'].__setitem__('final_ids', []),
                       lambda x: x.__setitem__('messages', []),
                       lambda x: x['certificate']['events'][0].__setitem__('index', True),
                       lambda x: x['certificate']['events'][-1].__setitem__('left', 1),
                       lambda x: x['certificate']['events'][-1].__setitem__('id', 0),
                       lambda x: x['certificate']['events'][-1]['parameters'].__setitem__('row', 99),
                       lambda x: x['certificate']['events'][-1].__setitem__('rule', 'identical'),
                       lambda x: x['certificate']['events'].append(copy.deepcopy(x['certificate']['events'][-1]))]:
            candidate = copy.deepcopy(baseline); mutate(candidate); mutations.append(candidate)
        for forged in mutations:
            self.assertFalse(c.verify_compression(2, [0, 1], originals, forged)['valid'])
        bad = copy.deepcopy(originals); bad[0]['free_ids'] = [0, 1]
        with self.assertRaises(ValueError): c.compress(2, [0, 1], bad)

    def test_checker_does_not_call_producer_discovery_or_normalization(self):
        originals = [message(2), message(2, phase=[1])]
        baseline = c.compress(2, [0, 1], originals)
        old_discover, old_normalize = c._discover, c.boundary.normalize_message
        def forbidden(*args, **kwargs): raise AssertionError('producer routine called')
        try:
            c._discover = forbidden; c.boundary.normalize_message = forbidden
            self.assertTrue(c.verify_compression(2, [0, 1], originals, baseline)['valid'])
        finally:
            c._discover, c.boundary.normalize_message = old_discover, old_normalize

    def test_wide_symbolic_control_and_large_rational_binding(self):
        n = 256; retained = list(range(n))
        phase = [(1 << i) | (1 << (i+1)) for i in range(2, n, 2)]
        originals = [message(n, equations=[[1, 0]], phase=phase), message(n, equations=[[1, 1]], phase=phase+[2])]
        result = c.compress(n, retained, originals)
        self.assertTrue(c.verify_compression(n, retained, originals, result)['valid'])
        self.assertEqual(result['messages'], [message(n, phase=phase+[3])])
        huge = Fraction(1 << 15000, (1 << 15001)+1)
        originals = [message(0, scalar=huge), message(0, scalar=-huge)]
        result = c.compress(0, [], originals)
        self.assertTrue(c.verify_compression(0, [], originals, result)['valid'])
        self.assertEqual(result['messages'], [])


if __name__ == '__main__':
    unittest.main()
