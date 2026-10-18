import copy
from fractions import Fraction
from hashlib import sha256
from itertools import combinations
import json
from pathlib import Path
import random
import sys
import unittest

from reference import (equivalent_messages, marginalize_reference, rational,
                       verify_reference)


def assignments(ids):
    for word in range(1 << len(ids)):
        yield sum(((word >> i) & 1) << v for i, v in enumerate(ids))


def value(n, rows, phase, scalar, word):
    if any(((mask & word).bit_count() & 1) != rhs for mask, rhs in rows):
        return Fraction(0)
    return rational(scalar)*(-1)**sum((word & term) == term for term in phase)


def message_value(message, word):
    if message['zero']:
        return Fraction(0)
    return value(message['n'], message['equations'], message['phase'], message['scalar'], word)


def brute(n, keep, rows, phase, scalar, active=None):
    active = list(range(n)) if active is None else list(active)
    internal = [v for v in active if v not in keep]
    return {y: sum((value(n, rows, phase, scalar, y | z) for z in assignments(internal)), Fraction(0)) for y in assignments(keep)}


def wide_pair_request(k):
    # Internal s_i,t_i; retained a_i,b_i, interleaved original IDs.
    keep, phase = [], []
    for i in range(k):
        s, t, a, b = [4*i+j for j in range(4)]
        keep += [a, b]
        phase += [(1 << s) | (1 << t), (1 << s) | (1 << a), (1 << t) | (1 << b)]
    return dict(n=4*k, retained=keep, equations=[], phase=phase, scalar=[-3, 7])


class ReferenceTests(unittest.TestCase):
    def checked(self, n, keep, rows, phase, scalar=1, active=None):
        result = marginalize_reference(n, keep, rows, phase, scalar, active=active)
        self.assertEqual(result['status'], 'EXACT', result)
        self.assertTrue(verify_reference(n, keep, rows, phase, scalar, result, active=active)['valid'])
        return result

    def test_exhaustive_small_support_phase_boundary(self):
        count = 0
        for n in range(4):
            terms = [0] + [1 << v for v in range(n)] + [(1 << i) | (1 << j) for i, j in combinations(range(n), 2)]
            supports = [[]] + [[[mask, rhs]] for mask in range(1 << n) for rhs in (0, 1)] if n < 3 else [[], [[0, 1]], [[3, 0]], [[7, 1]]]
            for coefficient in range(1 << len(terms)):
                phase = [term for j, term in enumerate(terms) if coefficient >> j & 1]
                for keepmask in range(1 << n):
                    keep = [v for v in range(n) if keepmask >> v & 1]
                    for rows in supports:
                        result = self.checked(n, keep, rows, phase, Fraction(-3, 5))
                        expected = brute(n, keep, rows, phase, Fraction(-3, 5))
                        self.assertEqual({w: message_value(result['message'], w) for w in expected}, expected)
                        count += 1
        self.assertEqual(count, 4718)

    def test_seeded_active_support_and_signed_marginals(self):
        rng = random.Random(181026321)
        for case in range(400):
            n = rng.randrange(9)
            active = [v for v in range(n) if rng.randrange(4)]
            rng.shuffle(active)
            keep = [v for v in active if rng.randrange(2)]
            rng.shuffle(keep)
            rows = [[sum((1 << v) for v in active if rng.randrange(2)), rng.randrange(2)] for _ in range(rng.randrange(n+3))]
            terms = [0]+[1 << v for v in active]+[(1 << a) | (1 << b) for a, b in combinations(active, 2)]
            phase = [t for t in terms if rng.randrange(2)]
            scalar = Fraction(rng.choice([-3, -1, 0, 1, 2]), rng.choice([1, 3, 7]))
            result = self.checked(n, keep, rows, phase, scalar, active)
            expected = brute(n, keep, rows, phase, scalar, active)
            self.assertEqual({w: message_value(result['message'], w) for w in expected}, expected, case)

    def test_wide_pair_output_without_truth_tables(self):
        for k in (1, 12, 64):
            request = wide_pair_request(k)
            result = self.checked(request['n'], request['retained'], request['equations'], request['phase'], request['scalar'])
            message = result['message']
            self.assertEqual(message['equations'], [])
            self.assertEqual(message['scalar'], [-3*(1 << k), 7])
            self.assertEqual(message['phase'], sorted((1 << (4*i+2)) | (1 << (4*i+3)) for i in range(k)))
            self.assertEqual(result['certificate']['factor_power'], k)
            self.assertEqual(len(result['certificate']['pairs']), k)

    def test_wide_boundary_pins_and_inactive_free_counts(self):
        k = 96
        result = self.checked(2*k, list(range(k, 2*k)), [], [(1 << i) | (1 << (k+i)) for i in range(k)])
        self.assertEqual(result['message']['scalar'], [1 << k, 1])
        self.assertEqual(result['message']['equations'], [[1 << i, 0] for i in range(k, 2*k)])
        result = self.checked(500, [409, 3], [], [], [1, 7], active=[3, 100, 409])
        self.assertEqual(result['message']['scalar'], [2, 7])
        self.assertEqual(result['message']['free_ids'], [409, 3])
        self.assertEqual(self.checked(500, [], [], [], active=[])['message']['scalar'], [1, 1])

    def test_equivalence_restricts_phase_to_support(self):
        a = self.checked(3, [2, 0, 1], [[3, 1]], [5], 2)['message']
        b = copy.deepcopy(a)
        # Add the vanishing polynomial x2*(x0+x1+1) on x0+x1=1.
        p = set(b['phase'])
        for term in (5, 6, 4):
            p.symmetric_difference_update({term})
        b['phase'] = sorted(p)
        self.assertTrue(equivalent_messages(3, [2, 0, 1], a, b)['equivalent'])
        b['phase'].append(0)
        b['scalar'][0] *= -1
        self.assertTrue(equivalent_messages(3, [2, 0, 1], a, b)['equivalent'])
        b['scalar'][0] *= 3
        self.assertFalse(equivalent_messages(3, [2, 0, 1], a, b)['equivalent'])
        b = copy.deepcopy(a)
        b['equations'][0][1] ^= 1
        self.assertFalse(equivalent_messages(3, [2, 0, 1], a, b)['equivalent'])
        self.assertEqual(equivalent_messages(3, [0, 1, 2], a, a)['status'], 'INVALID')

    def test_zero_and_identity_edges(self):
        for n, keep, rows, phase, scalar in ((0, [], [], [], 1), (0, [], [], [0], 1),
                (1, [], [], [1], 1), (2, [1], [[1, 0], [1, 1]], [], 1),
                (2, [1], [], [], 0), (2, [0, 1], [[2, 1]], [1, 3], -2)):
            result = self.checked(n, keep, rows, phase, scalar)
            for word, expected in brute(n, keep, rows, phase, scalar).items():
                self.assertEqual(message_value(result['message'], word), expected)

    def test_proof_mutations_and_external_binding(self):
        request = wide_pair_request(2)
        n, keep, rows, phase, scalar = [request[k] for k in ('n', 'retained', 'equations', 'phase', 'scalar')]
        good = self.checked(n, keep, rows, phase, scalar)
        mutations = []
        def change(fn):
            bad = copy.deepcopy(good); fn(bad); mutations.append(bad)
        change(lambda r: r['certificate'].update(input_sha256='0'*64))
        change(lambda r: r['certificate']['parameter']['free_internal'].pop())
        change(lambda r: r['certificate']['parameter']['expressions'][0].__setitem__(1, 0))
        change(lambda r: r['certificate']['parameter'].update(boundary_equations=[[1 << keep[0], 0]]))
        change(lambda r: r['certificate'].update(initial_phase=[]))
        change(lambda r: r['certificate']['pairs'][0].update(pair=[keep[0], keep[1]]))
        change(lambda r: r['certificate']['pairs'][0].update(after=[]))
        change(lambda r: r['certificate'].update(factor_power=True))
        change(lambda r: r['message'].update(scalar=[999, 7]))
        change(lambda r: r['message'].update(phase=[]))
        for bad in mutations:
            self.assertFalse(verify_reference(n, keep, rows, phase, scalar, bad)['valid'])
        self.assertFalse(verify_reference(n, keep, rows, phase+[0], scalar, good)['valid'])
        self.assertFalse(verify_reference(n, keep[::-1], rows, phase, scalar, good)['valid'])
        self.assertTrue(verify_reference(n, keep, rows, phase, scalar, json.loads(json.dumps(good)))['valid'])

    def test_budget_and_malformed_inputs(self):
        request = wide_pair_request(3)
        args = [request[k] for k in ('n', 'retained', 'equations', 'phase', 'scalar')]
        for cap in ({'max_variables': 10}, {'max_work': 0}, {'max_terms': 1}, {'max_scalar_bits': 1}, {'max_steps': 1}):
            result = marginalize_reference(*args, **cap)
            self.assertEqual(result['status'], 'UNKNOWN')
            self.assertIsNone(result['message'])
            self.assertIsNone(result['certificate'])
        good = self.checked(*args)
        self.assertEqual(verify_reference(*args, good, max_work=0)['status'], 'UNKNOWN')
        for n, keep, rows, phase, scalar, active in ((True, [], [], [], 1, None),
                (3, [1, 1], [], [], 1, None), (3, [2], [[1, 0]], [], 1, [2]),
                (3, [], [], [7], 1, None), (3, [], [], [True], 1, None),
                (3, [], [[1, True]], [], 1, None), (3, [], [], [], [1, 0], None)):
            with self.assertRaises(ValueError):
                marginalize_reference(n, keep, rows, phase, scalar, active=active)
        self.assertEqual(marginalize_reference(10**12, [], [], [])['status'], 'UNKNOWN')

    def test_big_scalar_hash_and_sign(self):
        c = Fraction(-(1 << 15000), 3)
        result = self.checked(2, [1], [], [0], c)
        self.assertEqual(result['message']['scalar'], [1 << 15001, 3])
        self.assertFalse(verify_reference(2, [1], [], [0], c+1, result)['valid'])
        self.assertEqual(marginalize_reference(2, [1], [], [0], c, max_scalar_bits=14999)['status'], 'UNKNOWN')

    def test_crosscheck_one_bit_implementation(self):
        production = Path(__file__).resolve().parent.parent/'affine_boundary_lab'
        if not (production/'boundary.py').exists():
            self.skipTest('independent producer not present')
        sys.path.insert(0, str(production))
        import boundary
        rng = random.Random(342026)
        for case in range(220):
            n = rng.randrange(9)
            active = [v for v in range(n) if rng.randrange(4)]
            keep = [v for v in active if rng.randrange(2)]
            rng.shuffle(keep)
            rows = [[sum(1 << v for v in active if rng.randrange(2)), rng.randrange(2)] for _ in range(rng.randrange(5))]
            terms = [0]+[1 << v for v in active]+[(1 << a) | (1 << b) for a, b in combinations(active, 2)]
            phase = [t for t in terms if rng.randrange(2)]
            scalar = Fraction(rng.choice([-3, -1, 0, 1, 5]), rng.choice([1, 2, 7]))
            reference = self.checked(n, keep, rows, phase, scalar, active)
            result = boundary.marginalize(n, keep, rows, phase, scalar, active=active)
            self.assertEqual(result['status'], 'EXACT', result)
            self.assertTrue(boundary.verify_marginal(n, keep, rows, phase, scalar, result, active=active)['valid'])
            self.assertTrue(equivalent_messages(n, keep, reference['message'], result['message'])['equivalent'], (case, reference, result))
        request = wide_pair_request(64)
        reference = marginalize_reference(**request)
        result = boundary.marginalize(**request)
        self.assertTrue(equivalent_messages(request['n'], request['retained'], reference['message'], result['message'])['equivalent'])

    def test_saved_certificates_oracles_and_hashes(self):
        here = Path(__file__).resolve().parent
        if not (here/'RESULTS.json').exists():
            self.skipTest('saved experiment not present')
        saved = json.loads((here/'RESULTS.json').read_text(encoding='utf-8'))
        for name, digest in saved['source_sha256'].items():
            self.assertEqual(sha256((here/name).read_bytes()).hexdigest(), digest)
        for case in saved['cases']:
            request, result = case['request'], case['result']
            if result['status'] != 'EXACT':
                self.assertIsNone(result['message'])
                self.assertIsNone(result['certificate'])
                continue
            checked = verify_reference(request['n'], request['retained'], request['equations'], request['phase'],
                                       request.get('scalar', 1), result, active=request.get('active'), **case['caps'])
            self.assertTrue(checked['valid'], case['name'])
            if case['reference_message'] is not None:
                self.assertTrue(equivalent_messages(request['n'], request['retained'], result['message'], case['reference_message'])['equivalent'])
            for entry in case['explicit_oracle'] or []:
                self.assertEqual(message_value(result['message'], entry['boundary_word']), rational(entry['value']))


if __name__ == '__main__':
    unittest.main()
