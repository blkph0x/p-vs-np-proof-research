import copy
from fractions import Fraction
from hashlib import sha256
from itertools import product
import json
from pathlib import Path
import random
import sys
import unittest

import boundary as b


def evaluate(message, word):
    if message['zero']:
        return Fraction(0)
    if any(((mask & word).bit_count() & 1) != rhs for mask, rhs in message['equations']):
        return Fraction(0)
    sign = sum((word & term) == term for term in message['phase']) & 1
    return b.ratio(message['scalar']) * (-1 if sign else 1)


def enumerate_marginal(n, retained, equations, phase, scalar=1, active=None):
    active = list(range(n)) if active is None else list(active)
    result = {bits: Fraction(0) for bits in product((0, 1), repeat=len(retained))}
    for values in product((0, 1), repeat=len(active)):
        word = sum(value << variable for variable, value in zip(active, values))
        if all(((word & mask).bit_count() & 1) == rhs for mask, rhs in equations):
            sign = sum((word & term) == term for term in phase) & 1
            result[tuple((word >> i) & 1 for i in retained)] += b.ratio(scalar) * (-1 if sign else 1)
    return result


def pair_family(k):
    # boundary (a_i,b_i), internals (s_i,t_i), all in original positions.
    retained = list(range(2*k))
    phase = []
    for i in range(k):
        a, c, s, t = 2*i, 2*i+1, 2*k+2*i, 2*k+2*i+1
        phase += [(1 << s) | (1 << t), (1 << s) | (1 << a), (1 << t) | (1 << c)]
    return dict(n=4*k, retained=retained, equations=[], phase=phase, scalar=1)


class BoundaryTests(unittest.TestCase):
    def checked(self, request, **caps):
        result = b.marginalize(**request, **caps)
        self.assertEqual(result['status'], 'EXACT', result)
        checked = b.verify_marginal(**request, result=result, **caps)
        self.assertTrue(checked['valid'], checked)
        return result

    def small(self, request):
        result = self.checked(request)
        original = {k: v for k, v in request.items() if k != 'order'}
        expected = enumerate_marginal(**original)
        for bits, value in expected.items():
            word = sum(bit << i for i, bit in zip(request['retained'], bits))
            self.assertEqual(evaluate(result['message'], word), value, (request, bits))
        return result

    def test_four_one_bit_and_pair_identities(self):
        first = self.small(dict(n=2, retained=[0], equations=[], phase=[3], scalar=1))
        self.assertEqual(first['message']['equations'], [[1, 0]])
        self.assertEqual(first['message']['scalar'], [2, 1])
        pair = self.small(pair_family(1))
        self.assertEqual(pair['message']['phase'], [3])
        self.assertEqual(pair['message']['scalar'], [2, 1])
        pinned = self.small(dict(n=4, retained=[0, 1, 2], equations=[(11, 0)], phase=[12], scalar=1))
        self.assertEqual(pinned['message']['phase'], [5, 6])
        zero = self.small(dict(n=1, retained=[], equations=[], phase=[1], scalar=1))
        self.assertTrue(zero['message']['zero'])

    def test_all_quadratic_phases_through_three_variables(self):
        count = 0
        for n in range(4):
            terms = [0] + [1 << i for i in range(n)] + [(1 << i) | (1 << j) for i in range(n) for j in range(i+1, n)]
            for coefficients in range(1 << len(terms)):
                phase = [term for j, term in enumerate(terms) if coefficients >> j & 1]
                for kept in range(1 << n):
                    retained = list(reversed([i for i in range(n) if kept >> i & 1]))
                    self.small(dict(n=n, retained=retained, equations=[], phase=phase, scalar=Fraction(-2, 3)))
                    count += 1
        self.assertEqual(count, 2 + 8 + 64 + 1024)

    def test_seeded_supports_sparse_active_ids_and_elimination_orders(self):
        rng = random.Random(20261019)
        for case in range(300):
            n = rng.randrange(8)
            active = [i for i in range(n) if rng.randrange(4)]
            retained = [i for i in active if rng.randrange(2)]
            rng.shuffle(retained)
            order = [i for i in active if i not in retained]
            rng.shuffle(order)
            masks = [sum(1 << i for i in active if rng.randrange(2)) for _ in range(rng.randrange(7))]
            equations = [(mask, rng.randrange(2)) for mask in masks]
            terms = [0] + [1 << i for i in active] + [(1 << i) | (1 << j) for i in active for j in active if i < j]
            phase = [term for term in terms if rng.randrange(2)]
            self.small(dict(n=n, retained=retained, active=active, order=order, equations=equations,
                            phase=phase, scalar=Fraction(rng.randrange(-3, 4), rng.randrange(1, 5))))

    def test_canonical_support_phase_keys_and_constant_sign(self):
        first = b.normalize_message(3, [2, 0, 1], [(3, 1), (6, 0)], [1, 3], 3)
        second = b.normalize_message(3, [2, 0, 1], [(5, 1), (3, 1), (6, 0), (0, 0)], [1, 3], 7)
        self.assertEqual(first['key'], second['key'])
        self.assertEqual(first['message']['free_ids'], [1])
        left = b.normalize_message(2, [0, 1], [(3, 0)], [1], 1)
        right = b.normalize_message(2, [0, 1], [(3, 0)], [2], 1)
        self.assertEqual(left['message'], right['message'])
        signed = b.normalize_message(1, [0], [(1, 1)], [1], 5)
        self.assertEqual(signed['message']['scalar'], [-5, 1])
        self.assertEqual(signed['message']['phase'], [])
        reordered = b.normalize_message(2, [1, 0], [(3, 0)], [1], 1)
        self.assertNotEqual(left['key'], reordered['key'])

    def test_empty_zero_inconsistent_dependent_and_unused_cases(self):
        cases = [dict(n=0, retained=[], equations=[], phase=[], scalar=Fraction(3, 7)),
                 dict(n=0, retained=[], equations=[], phase=[0], scalar=2),
                 dict(n=0, retained=[], equations=[(0, 1)], phase=[], scalar=1),
                 dict(n=4, retained=[1, 3], equations=[(2, 1), (2, 1), (0, 0)], phase=[1, 1, 10], scalar=0),
                 dict(n=3, retained=[1], equations=[(1, 0), (1, 1)], phase=[], scalar=1),
                 dict(n=5, retained=[3], active=[3], equations=[], phase=[], scalar=1)]
        for request in cases:
            self.small(request)
        unused = self.checked(dict(n=512, retained=[], equations=[], phase=[], scalar=1))
        self.assertEqual(unused['message']['scalar'], [1 << 512, 1])
        inactive = self.checked(dict(n=512, retained=[], active=[], equations=[], phase=[], scalar=1))
        self.assertEqual(inactive['message']['scalar'], [1, 1])

    def test_wide_signed_boundaries_without_truth_tables(self):
        for k in (1, 8, 64, 256):
            request = pair_family(k)
            result = self.checked(request)
            message = result['message']
            self.assertEqual(message['scalar'], [1 << k, 1])
            self.assertEqual(message['equations'], [])
            self.assertEqual(message['phase'], [(1 << (2*i)) | (1 << (2*i+1)) for i in range(k)])
            self.assertEqual(len(result['certificate']['steps']), 2*k)
        k = 256
        request = dict(n=2*k, retained=list(range(k)), equations=[],
                       phase=[(1 << i) | (1 << (k+i)) for i in range(k)], scalar=1)
        message = self.checked(request)['message']
        self.assertEqual(message['equations'], [[1 << i, 0] for i in range(k)])
        self.assertEqual(message['scalar'], [1 << k, 1])

    def test_closed_marginals_cross_checked_with_affine_evaluator(self):
        sys.path.insert(0, str(Path(__file__).resolve().parent.parent / 'holographic_tractability_lab'))
        import affine_holant as closed
        rng = random.Random(181027)
        for case in range(80):
            n = rng.randrange(7)
            equations = [(rng.randrange(1 << n), rng.randrange(2)) for _ in range(rng.randrange(5))]
            terms = [0] + [1 << i for i in range(n)] + [(1 << i) | (1 << j) for i in range(n) for j in range(i+1, n)]
            phase = [term for term in terms if rng.randrange(2)]
            scalar = Fraction(rng.choice((-3, -1, 1, 2)), rng.choice((1, 2, 5)))
            values = []
            for word in range(1 << n):
                feasible = all(((word & mask).bit_count() & 1) == rhs for mask, rhs in equations)
                sign = sum((word & term) == term for term in phase) & 1
                values.append(scalar * (-1 if sign else 1) if feasible else 0)
            net = {'edges': n, 'rows': [{'ports': list(range(n)), 'values': values}],
                   'columns': [{'ports': [i], 'values': [1, 1]} for i in range(n)]}
            reference = closed.solve_affine(net)
            self.assertEqual(reference['status'], 'EXACT')
            self.assertTrue(closed.verify_affine(net, [[1, 0], [0, 1]], reference)['valid'])
            result = self.checked(dict(n=n, retained=[], equations=equations, phase=phase, scalar=scalar))
            self.assertEqual(evaluate(result['message'], 0), closed.ratio(reference['value']))

    def test_external_original_input_binding_even_after_rehash(self):
        request = dict(n=3, retained=[1, 2], equations=[(3, 0)], phase=[5], scalar=1)
        result = self.checked(request)
        changes = [dict(retained=[2, 1]), dict(equations=[(3, 1)]), dict(phase=[1]),
                   dict(scalar=2), dict(active=[0, 1, 2], order=[0])]
        for change in changes[:-1]:
            other = {**request, **change}
            self.assertFalse(b.verify_marginal(**other, result=result)['valid'])
        other = {**request, 'phase': [1]}
        forged = copy.deepcopy(result)
        forged['certificate']['input_sha256'] = b.marginalize(**other)['certificate']['input_sha256']
        self.assertFalse(b.verify_marginal(**other, result=forged)['valid'])
        # Explicit default active/order describe the same original mathematical request.
        self.assertTrue(b.verify_marginal(**{**request, **changes[-1]}, result=result)['valid'])

    def test_trace_and_output_mutations_fail_closed(self):
        request = dict(n=4, retained=[0, 1], equations=[(5, 0)], phase=[12, 10], scalar=1)
        result = self.checked(request)
        mutations = []
        def mutate(fn):
            changed = copy.deepcopy(result); fn(changed); mutations.append(changed)
        mutate(lambda r: r['certificate']['steps'].pop())
        mutate(lambda r: r['certificate']['steps'].append(r['certificate']['steps'][0]))
        mutate(lambda r: r['certificate']['steps'][0].update(variable=0))
        mutate(lambda r: r['certificate']['steps'][0].update(variable=True))
        mutate(lambda r: r['certificate']['steps'][0].update(row=99))
        mutate(lambda r: r['certificate']['steps'][0].update(row=False))
        mutate(lambda r: r['certificate']['steps'].__setitem__(0, {'variable': 2, 'kind': 'free'}))
        mutate(lambda r: r['message'].update(zero=True))
        mutate(lambda r: r['message'].update(scalar=[99, 1]))
        mutate(lambda r: r['message'].update(phase=[0]))
        mutate(lambda r: r['message'].update(retained=[1, 0]))
        mutate(lambda r: r['message'].update(equations=[]))
        mutate(lambda r: r['message'].update(free_ids=[]))
        for changed in mutations:
            self.assertFalse(b.verify_marginal(**request, result=changed)['valid'], changed)
        changed = copy.deepcopy(result); changed['key'] = ['forged']; changed['stats'] = {}
        verified = b.verify_marginal(**request, result=changed)
        self.assertTrue(verified['valid'])
        self.assertEqual(verified['key'], b.message_key(verified['message']))
        self.assertTrue(b.verify_marginal(**request, result=json.loads(json.dumps(result)))['valid'])

    def test_caps_boundaries_and_huge_dimension_guards(self):
        request = pair_family(2)
        result = self.checked(request)
        for cap in ({'max_variables': 7}, {'max_steps': 3}, {'max_rows': 0}, {'max_terms': 5},
                    {'max_scalar_bits': 2}, {'max_work': 0}):
            stopped = b.marginalize(**request, **cap)
            self.assertEqual(stopped['status'], 'UNKNOWN')
            self.assertIsNone(stopped['message']); self.assertIsNone(stopped['certificate'])
        work = result['stats']['work']
        self.assertEqual(b.marginalize(**request, max_work=work)['status'], 'EXACT')
        self.assertEqual(b.marginalize(**request, max_work=work-1)['status'], 'UNKNOWN')
        verified = b.verify_marginal(**request, result=result)
        work = verified['stats']['work']
        self.assertTrue(b.verify_marginal(**request, result=result, max_work=work)['valid'])
        self.assertEqual(b.verify_marginal(**request, result=result, max_work=work-1)['status'], 'UNKNOWN')
        self.assertEqual(b.marginalize(10**12, [], [], [], 1)['status'], 'UNKNOWN')
        self.assertEqual(b.verify_marginal(10**12, [], [], [], 1, result)['status'], 'UNKNOWN')

    def test_invalid_inputs_and_large_exact_scalar_hash(self):
        request = dict(n=3, retained=[0], equations=[], phase=[], scalar=1)
        for change in (dict(n=True), dict(n=-1), dict(retained=[0, 0]), dict(retained=[False]),
                       dict(active=[1, 2]), dict(order=[0, 1]), dict(order=[1]),
                       dict(equations=[(1, True)]), dict(equations=[(True, 0)]),
                       dict(equations=[(8, 0)]), dict(phase=[7]), dict(phase=[True]),
                       dict(scalar=1.0), dict(scalar=[1, 0]), dict(active=[0], phase=[2])):
            with self.subTest(change=change), self.assertRaises(ValueError):
                b.marginalize(**{**request, **change})
        big = 1 << 15000
        result = self.checked(dict(n=2, retained=[1], equations=[(1, 1)], phase=[1], scalar=[1, big]))
        self.assertEqual(result['message']['scalar'], [-1, big])
        for caps in ({'max_work': True}, {'unknown': 1}):
            with self.assertRaises(ValueError): b.marginalize(**request, **caps)

    def test_saved_certificates_and_source_hashes(self):
        here = Path(__file__).resolve().parent
        if not (here / 'RESULTS.json').exists():
            self.skipTest('saved results not generated yet')
        saved = json.loads((here / 'RESULTS.json').read_text(encoding='utf-8'))
        for name, digest in saved['source_sha256'].items():
            self.assertEqual(sha256((here / name).read_bytes()).hexdigest(), digest)
        for case in saved['cases']:
            request, result = case['request'], case['result']
            if result['status'] == 'EXACT':
                self.assertTrue(b.verify_marginal(**request, result=result, **case['caps'])['valid'])
            else:
                self.assertEqual(result['status'], 'UNKNOWN')
                self.assertIsNone(result['message']); self.assertIsNone(result['certificate'])


if __name__ == '__main__':
    unittest.main()
