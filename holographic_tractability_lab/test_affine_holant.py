import copy
from fractions import Fraction
from hashlib import sha256
from itertools import product
import json
from math import comb
from pathlib import Path
import random
import unittest

from affine_holant import (Budget, Exhausted, formula_network, pack, ratio,
                           solve_affine, solve_formula, transformed_network,
                           verify_affine, verify_formula)

I = [[1, 0], [0, 1]]
H = [[1, 1], [1, -1]]
S = [[1, 2], [1, 3]]
BASES = [I, H, S, [[Fraction(2, 3), Fraction(-1, 7)], [1, Fraction(4, 5)]]]


def brute(network):
    total = Fraction(0)
    for word in range(1 << network['edges']):
        value = Fraction(1)
        for node in network['rows'] + network['columns']:
            local = sum(((word >> e) & 1) << j for j, e in enumerate(node['ports']))
            value *= ratio(node['values'][local])
        total += value
    return total


def formula_oracle(n, clauses, mode):
    total = 0
    for word in range(1 << n):
        weight = 1
        for clause in clauses:
            true = sum(bool(word >> (abs(lit)-1) & 1) == (lit > 0) for lit in clause)
            weight *= int(true > 0) if mode == 'sat' else (comb(len(clause)-1, true-1) if true else 0)
        total += weight
    return total


def inverse(matrix):
    a, b = map(ratio, matrix[0])
    c, d = map(ratio, matrix[1])
    return [[d/(a*d-b*c), -b/(a*d-b*c)], [-c/(a*d-b*c), a/(a*d-b*c)]]


def random_affine_network(rng, edges):
    net = {'edges': edges}
    for side in ('rows', 'columns'):
        order = list(range(edges))
        rng.shuffle(order)
        nodes = []
        while order:
            ports = order[:rng.randint(1, 4)]
            order = order[len(ports):]
            k = len(ports)
            equations = [(rng.randrange(1 << k), rng.randrange(2)) for _ in range(rng.randrange(3))]
            linear = rng.randrange(1 << k)
            quadratic = [(i, j) for i in range(k) for j in range(i+1, k) if rng.randrange(2)]
            scale = Fraction(rng.choice([-3, -1, 1, 2]), rng.choice([1, 2, 5]))
            values = []
            for x in range(1 << k):
                feasible = all(((a & x).bit_count() & 1) == b for a, b in equations)
                sign = ((linear & x).bit_count() + sum((x >> i & 1)*(x >> j & 1) for i, j in quadratic)) & 1
                values.append(pack(scale*(-1 if sign else 1)) if feasible else [0, 1])
            nodes.append({'ports': ports, 'values': values})
        if not nodes:
            nodes = [{'ports': [], 'values': [[rng.choice([-2, 1, 3]), 2]]}]
        net[side] = nodes
    return net


def equality_graph(size, shifts):
    rows = [[] for _ in range(size)]
    columns = [[] for _ in range(size)]
    e = 0
    for i in range(size):
        for shift in shifts:
            rows[i].append(e)
            columns[(i+shift) % size].append(e)
            e += 1
    def nodes(port_lists):
        return [{'ports': p, 'values': [int(x in (0, (1 << len(p))-1)) for x in range(1 << len(p))]} for p in port_lists]
    return {'edges': e, 'rows': nodes(rows), 'columns': nodes(columns)}


class AffineTests(unittest.TestCase):
    def checked(self, net, matrix=I, expected=None, **caps):
        result = solve_affine(net, matrix, **caps)
        self.assertEqual(result['status'], 'EXACT', result)
        self.assertTrue(verify_affine(net, matrix, result, **caps)['valid'])
        if expected is not None:
            self.assertEqual(ratio(result['value']), expected)
        return result

    def test_all_quadratic_phases_through_four_variables(self):
        cases = 0
        for k in range(5):
            terms = [1 << i for i in range(k)] + [(1 << i) | (1 << j) for i in range(k) for j in range(i+1, k)]
            for coefficients in range(1 << len(terms)):
                values = [(-1) ** sum(int((x & term) == term) for j, term in enumerate(terms) if coefficients >> j & 1) for x in range(1 << k)]
                net = {'edges': k, 'rows': [{'ports': list(range(k)), 'values': values}],
                       'columns': [{'ports': [i], 'values': [1, 1]} for i in range(k)]}
                self.checked(net, expected=sum(values))
                cases += 1
        self.assertEqual(cases, 1099)

    def test_seeded_full_contractions_and_basis_inverses(self):
        rng = random.Random(181026)
        for case in range(240):
            target = random_affine_network(rng, rng.randrange(10))
            t = BASES[case % len(BASES)]
            original = transformed_network(target, inverse(t))
            expected = brute(target)
            self.assertEqual(brute(original), expected)
            self.checked(original, t, expected)

    def test_nonplanar_and_large_transformed_positive_family(self):
        # size3/all shifts is exactly K3,3; size40 remains bounded-degree.
        for size, shifts in ((3, [0, 1, 2]), (40, [0, 1, 7])):
            target = equality_graph(size, shifts)
            original = transformed_network(target, inverse(S))
            self.assertEqual(solve_affine(original, I)['status'], 'UNSUPPORTED')
            result = self.checked(original, S, 2)
            self.assertEqual(len(result['certificate']['solution']['basis']), 1)

    def test_original_sat_slack_polarity_shared_repeated_contradictory(self):
        formulas = [[], [[]], [[1]], [[1], [-1]], [[1, 2, 3]], [[1, 2, 3]]*2,
                    [[1, -1]], [[1, 1]], [[1, 2], [-1, 3], [-2, -3]]]
        formulas += [[list(signs)] for signs in product(*[(i, -i) for i in (1, 2, 3)])]
        for clauses in formulas:
            for mode in ('sat', 'slack'):
                net = formula_network(3, clauses, mode)
                expected = formula_oracle(3, clauses, mode)
                self.assertEqual(brute(net), expected)
                for matrix in (I, H, S):
                    self.assertEqual(brute(transformed_network(net, matrix)), expected)
                    result = solve_affine(net, matrix)
                    if result['status'] == 'EXACT':
                        self.assertEqual(ratio(result['value']), expected)
                        self.assertTrue(verify_affine(net, matrix, result)['valid'])
                    else:
                        self.assertEqual(result['status'], 'UNSUPPORTED')
        self.assertEqual(formula_oracle(3, [[1, 2, 3]], 'sat'), 7)
        self.assertEqual(formula_oracle(3, [[1, 2, 3]], 'slack'), 10)
        self.assertEqual(formula_oracle(3, [[1, 2, 3]]*2, 'slack'), 16)

    def test_unsigned_support_and_signed_cancellation_distinct(self):
        net = {'edges': 1, 'rows': [{'ports': [0], 'values': [1, -1]}],
               'columns': [{'ports': [0], 'values': [1, 1]}]}
        self.checked(net, expected=0)
        self.assertEqual(sum(bool(x) for x in net['rows'][0]['values']), 2)
        self.checked({'edges': 0, 'rows': [], 'columns': []}, expected=1)
        self.checked(formula_network(200, []), expected=1 << 200)

    def test_nonaffine_support_and_cubic_phase_rejected(self):
        for values in ([0, 1, 1, 1], [1, 1, 1, 2], [1]*7+[-1]):
            k = len(values).bit_length()-1
            net = {'edges': k, 'rows': [{'ports': list(range(k)), 'values': values}],
                   'columns': [{'ports': [i], 'values': [1, 1]} for i in range(k)]}
            self.assertEqual(solve_affine(net)['status'], 'UNSUPPORTED')

    def test_certificate_mutations_rejected(self):
        net = {'edges': 3, 'rows': [{'ports': [0, 1, 2], 'values': [1, 1, 1, -1, 1, -1, -1, -1]}],
               'columns': [{'ports': [i], 'values': [1, 1]} for i in range(3)]}
        result = self.checked(net, expected=brute(net))
        mutations = []
        def altered(fn):
            changed = copy.deepcopy(result)
            fn(changed)
            mutations.append(changed)
        altered(lambda r: r.update(value=[99, 1]))
        altered(lambda r: r['certificate'].update(input_sha256='0'*64))
        altered(lambda r: r['certificate']['locals'][0].update(linear=1))
        altered(lambda r: r['certificate']['locals'][0].update(origin=True))
        altered(lambda r: r['certificate']['locals'][0]['basis'].__setitem__(0, 0))
        altered(lambda r: r['certificate']['locals'][0].update(quadratic=[[0, 1], [0, 1]]))
        altered(lambda r: r['certificate']['solution']['basis'].pop())
        altered(lambda r: r['certificate']['solution'].update(consistent=False))
        altered(lambda r: r['certificate'].update(polynomial=[]))
        altered(lambda r: r['certificate']['trace'][0].update(pair=[0, 0]))
        altered(lambda r: r['certificate']['trace'][0].update(after=[]))
        altered(lambda r: r['certificate'].update(gauss_sum=True))
        for mutation in mutations:
            self.assertFalse(verify_affine(net, I, mutation)['valid'], mutation)
        self.assertFalse(verify_affine(net, H, result)['valid'])
        changed = copy.deepcopy(net)
        changed['columns'][0]['values'] = [1, -1]
        self.assertFalse(verify_affine(changed, I, result)['valid'])
        wire_changed = copy.deepcopy(net)
        wire_changed['rows'][0]['ports'] = [1, 0, 2]
        self.assertFalse(verify_affine(wire_changed, I, result)['valid'])
        self.assertTrue(verify_affine(net, I, json.loads(json.dumps(result)))['valid'])

    def test_inconsistent_and_zero_certificates(self):
        net = formula_network(1, [[1], [-1]])
        result = self.checked(net, expected=0)
        self.assertFalse(result['certificate']['solution']['consistent'])
        changed = copy.deepcopy(result)
        changed['certificate']['solution'] = {'consistent': True, 'origin': 0, 'basis': []}
        self.assertFalse(verify_affine(net, I, changed)['valid'])
        zero_net = formula_network(2, [[]])
        zero = self.checked(zero_net, expected=0)
        zero['certificate']['node'] = True
        self.assertFalse(verify_affine(zero_net, I, zero)['valid'])

    def test_budgets_unknown_and_invalid_inputs(self):
        net = equality_graph(3, [0, 1, 2])
        for caps in ({'max_edges': 8}, {'max_entries': 1}, {'max_work': 1}, {'max_integer_bits': 0}):
            result = solve_affine(net, H, **caps)
            self.assertEqual(result['status'], 'UNKNOWN')
            self.assertIsNone(result['value'])
            self.assertIsNone(result['certificate'])
        good = self.checked(net, H, 2)
        self.assertEqual(verify_affine(net, H, good, max_work=1)['status'], 'UNKNOWN')
        for basis in ([[1, 2], [2, 4]], [[True, 0], [0, 1]], [[1.0, 0], [0, 1]]):
            with self.assertRaises(ValueError):
                solve_affine(net, basis)
        for caps in ({'max_work': True}, {'max_work': -1}, {'made_up': 5}):
            with self.assertRaises(ValueError):
                solve_affine(net, **caps)
        broken = copy.deepcopy(net)
        broken['rows'][0]['ports'][0] = broken['rows'][0]['ports'][1]
        with self.assertRaises(ValueError):
            solve_affine(broken)
        with self.assertRaises(ValueError):
            formula_network(2, [[True]])

    def test_large_integer_binary_hash_and_exact_rationals(self):
        big = 1 << 15000
        net = {'edges': 1, 'rows': [{'ports': [0], 'values': [[big, 3], [-big, 3]]}],
               'columns': [{'ports': [0], 'values': [[1, big], [1, big]]}]}
        result = self.checked(net, expected=0)
        changed = copy.deepcopy(net)
        changed['rows'][0]['values'][0][0] += 1
        self.assertFalse(verify_affine(changed, I, result)['valid'])
        self.assertEqual(solve_affine(net, max_integer_bits=14999)['status'], 'UNKNOWN')

    def test_formula_wrapper_binds_external_request(self):
        clauses = [[1], [-2], [1], [3]]
        for mode in ('sat', 'slack'):
            result = solve_formula(4, clauses, H, mode=mode)
            self.assertEqual(result['value'], [2, 1])
            self.assertTrue(verify_formula(4, clauses, H, result, mode=mode)['valid'])
            self.assertFalse(verify_formula(4, [[1], [2], [1], [3]], H, result, mode=mode)['valid'])
            self.assertFalse(verify_formula(5, clauses, H, result, mode=mode)['valid'])
        self.assertEqual(solve_formula(10**12, [], H)['status'], 'UNKNOWN')
        self.assertEqual(verify_formula(10**12, [], H, result)['status'], 'UNKNOWN')

    def test_saved_original_requests_certificates_and_source_hashes(self):
        here = Path(__file__).resolve().parent
        if not (here/'RESULTS.json').exists():
            self.skipTest('saved experiment not produced yet')
        saved = json.loads((here/'RESULTS.json').read_text(encoding='utf-8'))
        for name, expected in saved['source_sha256'].items():
            self.assertEqual(sha256((here/name).read_bytes()).hexdigest(), expected)
        exact = 0
        for case in saved['cases']:
            request, result, caps = case['request'], case['result'], case['caps']
            if result['status'] != 'EXACT':
                self.assertIsNone(result['value'])
                self.assertIsNone(result['certificate'])
                continue
            if request['kind'] == 'network':
                checked = verify_affine(request['network'], request['basis'], result, **caps)
            else:
                checked = verify_formula(request['n'], request['clauses'], request['basis'], result, mode=request['mode'], **caps)
            self.assertTrue(checked['valid'], case['name'])
            self.assertEqual(result['value'], case['reference']['value'])
            exact += 1
        self.assertEqual(exact, 15)


if __name__ == '__main__':
    unittest.main()
