"""Isolated tiny audit of labelled two-terminal/Eulerian joins; not a stable solver.

The reference oracle enumerates at most 2^8 edge subsets. The candidate primitive
uses lifted shortest paths and a label-space closure, with an explicit tiny-state
guard. No top-level research solver or artifact is modified.
"""
from heapq import heappop, heappush
from itertools import combinations, product
import math
import random
import unittest


def _word_properties(edges, word):
    boundary = label = weight = 0
    for j, (u, v, edge_label, edge_weight) in enumerate(edges):
        if word >> j & 1:
            boundary ^= (1 << u) ^ (1 << v)
            label ^= edge_label
            weight += edge_weight
    return boundary, label, weight


def _lift_paths(n, adjacency, label_count, source, stats):
    distances = [math.inf] * (n * label_count)
    words = [None] * (n * label_count)
    start = source * label_count
    distances[start], words[start] = 0, 0
    queue = [(0, start)]
    stats['lift_runs'] += 1
    while queue:
        distance, state = heappop(queue)
        if distance != distances[state]:
            continue
        vertex, label = divmod(state, label_count)
        for other, edge_id, edge_label, edge_weight in adjacency[vertex]:
            stats['lift_relaxation_attempts'] += 1
            next_state = other * label_count + (label ^ edge_label)
            candidate = distance + edge_weight
            if candidate < distances[next_state]:
                distances[next_state] = candidate
                words[next_state] = words[state] ^ (1 << edge_id)
                heappush(queue, (candidate, next_state))
    return distances, words


def _build_tables(n, edges, p):
    if type(n) is not int or n < 0 or type(p) is not int or not 0 <= p <= 8:
        raise ValueError('invalid tiny audit dimensions')
    labels = 1 << p
    if n * labels > 4096:
        raise ValueError('tiny executable audit state guard exceeded')
    edges = tuple(edges)
    adjacency = [[] for _ in range(n)]
    for j, edge in enumerate(edges):
        if len(edge) != 4 or any(type(value) is not int for value in edge):
            raise ValueError('edges require four integer fields')
        u, v, label, weight = edge
        if not (0 <= u < n and 0 <= v < n and 0 <= label < labels and weight >= 0):
            raise ValueError('invalid vertex, label, or nonnegative weight')
        adjacency[u].append((v, j, label, weight))
        if u != v:
            adjacency[v].append((u, j, label, weight))
    stats = {'lift_runs': 0, 'lift_states_per_run': n * labels,
             'lift_relaxation_attempts': 0, 'label_relaxation_attempts': 0}
    lifted = [_lift_paths(n, adjacency, labels, source, stats) for source in range(n)]
    closed_cost = [math.inf] * labels
    closed_word = [None] * labels
    closed_cost[0], closed_word[0] = 0, 0
    for source, (distances, words) in enumerate(lifted):
        for label in range(1, labels):
            index = source * labels + label
            if distances[index] < closed_cost[label]:
                closed_cost[label], closed_word[label] = distances[index], words[index]
    # This label-space closure permits disconnected cycles with different starts.
    eulerian_cost = [math.inf] * labels
    eulerian_word = [None] * labels
    eulerian_cost[0], eulerian_word[0] = 0, 0
    queue = [(0, 0)]
    while queue:
        distance, state = heappop(queue)
        if distance != eulerian_cost[state]:
            continue
        for label in range(1, labels):
            if closed_cost[label] == math.inf:
                continue
            stats['label_relaxation_attempts'] += 1
            destination = state ^ label
            candidate = distance + closed_cost[label]
            if candidate < eulerian_cost[destination]:
                eulerian_cost[destination] = candidate
                eulerian_word[destination] = eulerian_word[state] ^ closed_word[label]
                heappush(queue, (candidate, destination))
    for label, distance in enumerate(eulerian_cost):
        if distance != math.inf:
            assert _word_properties(edges, eulerian_word[label]) == (0, label, distance)
    return {'n': n, 'p': p, 'label_count': labels, 'edges': edges, 'lifted': lifted,
            'closed_cost': closed_cost, 'closed_word': closed_word,
            'eulerian_cost': eulerian_cost, 'eulerian_word': eulerian_word, 'stats': stats}


def _pair_join(tables, u, v, target):
    if u == v or not 0 <= u < tables['n'] or not 0 <= v < tables['n']:
        raise ValueError('two distinct graph terminals are required')
    if not 0 <= target < tables['label_count']:
        raise ValueError('target label out of range')
    distances, words = tables['lifted'][u]
    candidates = []
    for label in range(tables['label_count']):
        path_state = v * tables['label_count'] + label
        correction = target ^ label
        if distances[path_state] == math.inf or tables['eulerian_cost'][correction] == math.inf:
            continue
        cost = distances[path_state] + tables['eulerian_cost'][correction]
        word = words[path_state] ^ tables['eulerian_word'][correction]
        candidates.append((cost, word))
    if not candidates:
        return None, None
    cost, word = min(candidates)
    assert _word_properties(tables['edges'], word) == ((1 << u) ^ (1 << v), target, cost)
    return cost, word


def _nonempty_zero_eulerian(n, edges, p):
    """Exact edge-pinning wrapper, isolated here solely for tiny validation."""
    best = None
    for pinned, (u, v, label, weight) in enumerate(edges):
        remaining = edges[:pinned] + edges[pinned + 1:]
        tables = _build_tables(n, remaining, p)
        if u == v:
            cost, word = tables['eulerian_cost'][label], tables['eulerian_word'][label]
            if cost == math.inf:
                continue
        else:
            cost, word = _pair_join(tables, u, v, label)
            if cost is None:
                continue
        original_word = 1 << pinned
        for j in range(len(remaining)):
            if word >> j & 1:
                original_word |= 1 << (j if j < pinned else j + 1)
        candidate = weight + cost, original_word
        if best is None or candidate < best:
            best = candidate
    if best is None:
        return None, None
    assert best[1] and _word_properties(edges, best[1]) == (0, 0, best[0])
    return best


def _edge_subset_oracle(edges, nonempty=False):
    if len(edges) > 8:
        raise ValueError('exhaustive oracle is restricted to eight edges')
    costs = {}
    for word in range(1 if nonempty else 0, 1 << len(edges)):
        boundary, label, cost = _word_properties(edges, word)
        key = boundary, label
        if key not in costs or cost < costs[key]:
            costs[key] = cost
    return costs


class LabelledJoinPrimitiveTest(unittest.TestCase):
    def check_all_requested_labels(self, n, edges, p):
        tables = _build_tables(n, edges, p)
        oracle = _edge_subset_oracle(edges)
        labels = 1 << p
        for label in range(labels):
            cost = tables['eulerian_cost'][label]
            self.assertEqual(None if cost == math.inf else cost, oracle.get((0, label)))
        for u, v in combinations(range(n), 2):
            for label in range(labels):
                cost, word = _pair_join(tables, u, v, label)
                self.assertEqual(cost, oracle.get(((1 << u) ^ (1 << v), label)))
                if cost is not None:
                    self.assertEqual(_word_properties(edges, word), ((1 << u) ^ (1 << v), label, cost))
        self.assertEqual(tables['stats']['lift_runs'], n)
        self.assertLessEqual(tables['stats']['lift_relaxation_attempts'], 2 * n * len(edges) * labels)
        self.assertLessEqual(tables['stats']['label_relaxation_attempts'], labels * (labels - 1))
        return tables

    def test_all_one_bit_labelled_simple_graphs_through_four_vertices(self):
        cases = 0
        for n in range(5):
            possible = list(combinations(range(n), 2))
            for choices in product(range(3), repeat=len(possible)):
                edges = tuple((u, v, choice - 1, 1) for (u, v), choice in zip(possible, choices) if choice)
                self.check_all_requested_labels(n, edges, 1)
                cases += 1
        self.assertEqual(cases, 761)

    def test_seeded_weighted_multigraphs_with_zero_costs_and_parallel_edges(self):
        rng = random.Random(20261018)
        for index in range(120):
            n, p = rng.randrange(1, 6), rng.randrange(4)
            edges = tuple((rng.randrange(n), rng.randrange(n), rng.randrange(1 << p), rng.randrange(6))
                          for _ in range(rng.randrange(9)))
            self.check_all_requested_labels(n, edges, p)
            if index < 40:
                expected = _edge_subset_oracle(edges, nonempty=True).get((0, 0))
                self.assertEqual(_nonempty_zero_eulerian(n, edges, p)[0], expected)

    def test_disconnected_cycle_defeats_a_single_labelled_path(self):
        edges = ((0, 1, 0, 1), (2, 3, 1, 1), (3, 4, 0, 1), (4, 2, 0, 1))
        tables = self.check_all_requested_labels(5, edges, 1)
        self.assertEqual(tables['lifted'][0][0][1 * 2 + 1], math.inf)
        self.assertEqual(_pair_join(tables, 0, 1, 1), (4, 15))

    def test_even_connected_graph_can_need_a_disconnected_selected_correction(self):
        edges = ((0, 1, 0, 1), (2, 3, 1, 1), (3, 4, 0, 1), (4, 2, 0, 1), (1, 2, 0, 100))
        tables = self.check_all_requested_labels(5, edges, 1)
        self.assertEqual(tables['lifted'][0][0][1 * 2 + 1], 204)
        self.assertEqual(_pair_join(tables, 0, 1, 1), (4, 15))

    def test_eulerian_label_closure_combines_different_components(self):
        edges = ((0, 1, 1, 1), (1, 2, 0, 1), (2, 0, 0, 1),
                 (3, 4, 2, 1), (4, 5, 0, 1), (5, 3, 0, 1))
        tables = self.check_all_requested_labels(6, edges, 2)
        self.assertEqual(tables['closed_cost'][3], math.inf)
        self.assertEqual(tables['eulerian_cost'][3], 6)
        self.assertEqual(tables['eulerian_word'][3], 63)

    def test_nonempty_walk_does_not_certify_nonzero_eulerian_edge_set(self):
        forest = ((0, 1, 0, 1),)
        self.assertEqual((1 << 0) ^ (1 << 0), 0)  # Out-and-back walk cancels.
        self.assertEqual(_build_tables(2, forest, 0)['eulerian_cost'][0], 0)
        self.assertEqual(_nonempty_zero_eulerian(2, forest, 0), (None, None))
        zero_loop = ((0, 0, 0, 0),)
        self.assertEqual(_nonempty_zero_eulerian(1, zero_loop, 0), (0, 1))
        two_cycles = ((0, 1, 1, 1), (1, 2, 0, 1), (2, 0, 0, 1),
                      (3, 4, 1, 1), (4, 5, 0, 1), (5, 3, 0, 1))
        self.assertEqual(_nonempty_zero_eulerian(6, two_cycles, 1), (6, 63))

    def test_binary_encoded_weights_use_exact_integer_arithmetic(self):
        huge = 10 ** 100
        edges = ((0, 1, 1, huge + 1), (0, 2, 0, huge), (2, 1, 0, 1))
        tables = self.check_all_requested_labels(3, edges, 1)
        self.assertEqual(_pair_join(tables, 0, 1, 0)[0], huge + 1)
        self.assertIsInstance(_pair_join(tables, 0, 1, 0)[0], int)

    def test_negative_weights_bad_labels_and_oversized_audits_are_rejected(self):
        for edges in [((0, 1, 0, -1),), ((0, 1, 2, 1),), ((0, 2, 0, 1),), ((0, 1, True, 1),)]:
            with self.assertRaises(ValueError):
                _build_tables(2, edges, 1)
        with self.assertRaises(ValueError):
            _build_tables(100, (), 8)
        with self.assertRaises(ValueError):
            _build_tables(2, (), True)


if __name__ == '__main__':
    unittest.main()
