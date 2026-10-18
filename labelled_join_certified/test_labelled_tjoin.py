"""Exhaustive support oracles and certificate tampering for terminal subset DP."""
import copy
import itertools
import json
import random
import unittest

from labelled_tjoin import solve_tjoin, solve_nonempty, verify_tjoin, verify_nonempty


def oracle(edges, nonempty=False):
    result = {}
    for word in range(1 if nonempty else 0, 1 << len(edges)):
        boundary, label, weight = set(), 0, 0
        for j, (u, v, a, w) in enumerate(edges):
            if word >> j & 1:
                for vertex in (u, v):
                    if vertex in boundary:
                        boundary.remove(vertex)
                    else:
                        boundary.add(vertex)
                label ^= a
                weight += w
        key = tuple(sorted(boundary)), label
        if key not in result or weight < result[key]:
            result[key] = weight
    return result


class LabelledTjoinTests(unittest.TestCase):
    def test_all_labelled_simple_graphs_through_four_vertices(self):
        cases = requests = 0
        for n in range(5):
            pairs = list(itertools.combinations(range(n), 2))
            for choices in itertools.product(range(3), repeat=len(pairs)):
                edges = [(u, v, c - 1, 1) for (u, v), c in zip(pairs, choices) if c]
                expected = oracle(edges)
                for mask in range(1 << n):
                    terminals = [v for v in range(n) if mask >> v & 1]
                    for target in range(2):
                        answer = solve_tjoin(n, edges, 1, terminals=terminals, target=target)
                        self.assertEqual(answer['status'], 'EXACT')
                        self.assertEqual(answer['weight'], expected.get((tuple(terminals), target)))
                        requests += 1
                cases += 1
        self.assertEqual(cases, 761)
        self.assertEqual(requests, 23790)

    def test_random_weighted_multigraphs_and_nonempty(self):
        rng = random.Random(10618)
        for _ in range(100):
            n, p = rng.randrange(1, 7), rng.randrange(4)
            edges = [(rng.randrange(n), rng.randrange(n), rng.randrange(1 << p), rng.randrange(5))
                     for _ in range(rng.randrange(9))]
            expected = oracle(edges)
            for _ in range(4):
                terminals = [v for v in range(n) if rng.randrange(2)]
                target = rng.randrange(1 << p)
                answer = solve_tjoin(n, edges, p, terminals=terminals, target=target)
                self.assertEqual(answer['weight'], expected.get((tuple(terminals), target)))
            nonempty = solve_nonempty(n, edges, p)
            self.assertEqual(nonempty['status'], 'EXACT')
            self.assertEqual(nonempty['weight'], oracle(edges, True).get(((), 0)))
            self.assertTrue(verify_nonempty(n, edges, p, json.loads(json.dumps(nonempty)))['valid'])

    def test_four_terminals_need_label_allocation_and_disconnected_correction(self):
        edges = [(0, 1, 0, 1), (2, 3, 0, 1), (4, 4, 1, 2), (0, 2, 1, 50), (1, 3, 0, 50)]
        answer = solve_tjoin(5, edges, 1, terminals=[0, 1, 2, 3], target=1)
        self.assertEqual(answer['weight'], 4)
        self.assertEqual(answer['word'], 7)
        self.assertEqual(len(answer['dp_layers']), 8)

    def test_caps_and_huge_dimensions_fail_closed(self):
        edges = [(0, 1, 0, 1), (1, 2, 1, 1), (2, 3, 0, 1), (3, 0, 1, 1)]
        for limits in ({'max_dp_states': 1}, {'max_dp_transitions': 0}, {'max_states': 1},
                       {'max_relaxations': 0}, {'max_total_states': 0}):
            answer = solve_tjoin(4, edges, 1, terminals=[0, 1, 2, 3], limits=limits)
            self.assertEqual(answer['status'], 'UNKNOWN')
            self.assertIsNone(answer['weight'])
            self.assertTrue(verify_tjoin(4, edges, 1, answer, terminals=[0, 1, 2, 3])['valid'])
        huge = solve_tjoin(0, [], 10**9)
        self.assertEqual(huge['status'], 'UNKNOWN')
        partial = solve_nonempty(4, edges, 1, max_pin_cases=1)
        self.assertEqual(partial['status'], 'UNKNOWN')
        self.assertEqual(partial['upper_bound'], 4)
        self.assertIsNone(partial['weight'])
        self.assertTrue(verify_nonempty(4, edges, 1, partial)['valid'])

    def test_dp_and_request_tampering(self):
        edges = [(0, 1, 0, 1), (2, 3, 1, 2)]
        terminals = [0, 1, 2, 3]
        result = solve_tjoin(4, edges, 1, terminals=terminals, target=1)
        mutations = [lambda x: x.update(weight=2), lambda x: x.update(word=1),
                     lambda x: x['dp_layers'].pop(),
                     lambda x: x['dp_layers'][-1]['costs'].__setitem__(1, 2),
                     lambda x: x['dp_layers'][0]['costs'].__setitem__(1, 0),
                     lambda x: x.update(dp_transitions=0), lambda x: x.update(target=True),
                     lambda x: x.update(proof_kind='ODD_TERMINAL_COUNT'),
                     lambda x: x.update(terminals=[0, 1])]
        for mutate in mutations:
            bad = copy.deepcopy(result)
            mutate(bad)
            self.assertFalse(verify_tjoin(4, edges, 1, bad, terminals=terminals, target=1)['valid'])
        self.assertFalse(verify_tjoin(4, edges, 1, result, terminals=terminals, target=0)['valid'])
        limited = verify_tjoin(4, edges, 1, result, terminals=terminals, target=1,
                              verification_dp_transitions=0)
        self.assertEqual(limited['status'], 'UNKNOWN')

    def test_nonempty_pin_coverage_and_loop_semantics(self):
        edges = [(0, 0, 0, 0), (0, 1, 0, 7)]
        answer = solve_nonempty(2, edges, 0)
        self.assertEqual((answer['weight'], answer['word']), (0, 1))
        self.assertTrue(verify_nonempty(2, edges, 0, answer)['valid'])
        for mutate in (lambda x: x['cases'].pop(), lambda x: x['cases'][1].update(pin=0),
                       lambda x: x.update(word=0), lambda x: x.update(weight=True)):
            bad = copy.deepcopy(answer)
            mutate(bad)
            self.assertFalse(verify_nonempty(2, edges, 0, bad)['valid'])
        direct = solve_nonempty(2, edges, 0, terminals=[0, 1])
        self.assertEqual(direct['weight'], 7)
        direct['weight'] = True
        self.assertFalse(verify_nonempty(2, edges, 0, direct, terminals=[0, 1])['valid'])
        self.assertIsNone(solve_nonempty(2, [(0, 1, 0, 1)], 0)['weight'])
        self.assertIsNone(solve_nonempty(0, [], 0)['weight'])
        empty = solve_nonempty(0, [], 0)
        self.assertFalse(verify_nonempty(0, [], 0, empty, verification_state_limit=True)['valid'])

    def test_large_integer_weights(self):
        huge = 10**100
        edges = [(0, 1, 1, huge), (2, 3, 0, huge+1)]
        answer = solve_tjoin(4, edges, 1, terminals=[0, 1, 2, 3], target=1)
        self.assertEqual(answer['weight'], 2*huge+1)

    def test_verification_budget_is_separate_from_reachable_search_work(self):
        edges = [(0, 0, 0, 0)]
        answer = solve_tjoin(4, edges, 0, limits={'max_relaxations': 1})
        self.assertEqual(answer['status'], 'EXACT')
        self.assertEqual(answer['weight'], 0)
        exhausted = verify_tjoin(4, edges, 0, answer, verification_arc_limit=0)
        self.assertEqual(exhausted['status'], 'UNKNOWN')
        nonempty = solve_nonempty(4, edges, 0)
        exhausted = verify_nonempty(4, edges, 0, nonempty, verification_state_limit=0)
        self.assertEqual(exhausted['status'], 'UNKNOWN')
        stopped = solve_tjoin(4, edges, 0, limits={'max_verification_arcs': 3})
        self.assertEqual(stopped['status'], 'UNKNOWN')
        self.assertEqual(stopped['stop_reason'], 'VERIFICATION_ARC_LIMIT')

    def test_invalid_requests(self):
        edges = [(0, 1, 0, 1)]
        for options in ({'terminals': [0, 0]}, {'terminals': [2]}, {'target': True},
                        {'target': 2}, {'limits': {'max_dp_states': True}}, {'limits': {'unknown': 1}}):
            with self.assertRaises(ValueError):
                solve_tjoin(2, edges, 1, **options)


if __name__ == '__main__':
    unittest.main()
