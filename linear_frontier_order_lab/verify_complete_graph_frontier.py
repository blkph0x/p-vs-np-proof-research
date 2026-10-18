"""Independent replay of the complete-graph affine frontier certificate."""
from __future__ import annotations

from hashlib import sha256
import itertools
import json
import math
from pathlib import Path
import random

ROOT = Path(__file__).resolve().parent


def edges(vertices):
    return tuple(itertools.combinations(range(vertices), 2))


def rank(values):
    pivots = {}
    for value in values:
        value = int(value)
        while value:
            pivot = value.bit_length() - 1
            if pivot in pivots:
                value ^= pivots[pivot]
            else:
                pivots[pivot] = value
                break
    return len(pivots)


def components(vertices, edge_values):
    parent = list(range(vertices))

    def find(value):
        while parent[value] != value:
            parent[value] = parent[parent[value]]
            value = parent[value]
        return value

    for left, right in edge_values:
        a, b = find(left), find(right)
        if a != b:
            parent[a] = b
    return len({find(value) for value in range(vertices)})


def lambda_for_subset(vertices, subset):
    all_edges = edges(vertices); chosen = set(tuple(edge) for edge in subset)
    other = [edge for edge in all_edges if edge not in chosen]
    as_columns = lambda values: ((1 << left) | (1 << right) for left, right in values)
    return rank(as_columns(chosen)) + rank(as_columns(other)) - (vertices - 1)


def smallest_clique_vertices(edge_count):
    if type(edge_count) is not int or edge_count < 0:
        raise AssertionError('invalid edge count')
    if edge_count == 0:
        return 0
    smallest = 1
    while smallest * (smallest - 1) // 2 < edge_count:
        smallest += 1
    return smallest


def cutwise_minimum_lambda(vertices, cut_size):
    m = vertices * (vertices - 1) // 2
    if type(cut_size) is not int or not 0 <= cut_size <= m:
        raise AssertionError('invalid cut size')
    distance = min(cut_size, m - cut_size)
    return 0 if distance == 0 else smallest_clique_vertices(distance) - 1


def parameters(vertices):
    m = vertices * (vertices - 1) // 2; half = m // 2
    smallest = smallest_clique_vertices(half)
    bound = smallest - 1
    return {'vertices': vertices, 'columns': m, 'half_cut_edges': half,
            'smallest_clique_vertices': smallest,
            'half_cut_lambda_lower_bound': bound,
            'full_rank': vertices - 1, 'state_lower_bound': 1 << bound}


def order_digest(order):
    digest = sha256()
    for left, right in order:
        digest.update(bytes((left, right)))
    return digest.hexdigest()


def order_width(vertices, order):
    all_edges = edges(vertices)
    if tuple(sorted(order)) != all_edges:
        raise AssertionError('invalid order')
    cuts = [lambda_for_subset(vertices, order[:cut])
            for cut in range(1, len(order))]
    return max(cuts), cuts[len(order) // 2 - 1]


def sampled_orders(vertices):
    all_edges = list(edges(vertices)); rng = random.Random(20261018 + vertices)
    orders = [tuple(all_edges), tuple(reversed(all_edges))]
    for _ in range(3):
        current = list(all_edges); rng.shuffle(current); orders.append(tuple(current))
    return tuple(orders)


def exhaustive_half_cut(vertices):
    all_edges = edges(vertices); half = len(all_edges) // 2
    minimum = None; witness = None; maximum_components = 0
    for indices in itertools.combinations(range(len(all_edges)), half):
        subset = tuple(all_edges[index] for index in indices)
        value = lambda_for_subset(vertices, subset)
        if minimum is None or value < minimum:
            minimum, witness = value, subset
        maximum_components = max(maximum_components, components(vertices, subset))
    return {'minimum_lambda': minimum,
            'witness': [list(edge) for edge in witness],
            'subsets_checked': math.comb(len(all_edges), half),
            'maximum_subset_components': maximum_components}


def exhaustive_cutwise_minima(vertices):
    all_edges = edges(vertices); minima = []
    for cut_size in range(len(all_edges) + 1):
        minimum = None
        for indices in itertools.combinations(range(len(all_edges)), cut_size):
            subset = tuple(all_edges[index] for index in indices)
            value = lambda_for_subset(vertices, subset)
            minimum = value if minimum is None else min(minimum, value)
        minima.append(minimum)
    return {'vertices': vertices,
            'minimum_lambda_by_cut': minima,
            'subsets_checked': 1 << len(all_edges)}


def verify_record(record):
    try:
        vertices = record['parameters']['vertices']
        if record['parameters'] != parameters(vertices):
            return False
        expected = exhaustive_half_cut(vertices)
        if record['exhaustive'] != expected:
            return False
        for saved, order in zip(record['sampled_orders'], sampled_orders(vertices)):
            width, half = order_width(vertices, order)
            if saved != {'digest': order_digest(order), 'width': width,
                         'half_cut_lambda': half}:
                return False
        return len(record['sampled_orders']) == 5
    except (KeyError, TypeError, ValueError, IndexError, AssertionError):
        return False


def main():
    artifact = json.loads((ROOT / 'COMPLETE_GRAPH_FRONTIER_RESULTS.json').read_text(encoding='utf-8'))
    assert artifact['all_checks_passed']
    assert artifact['vertices_checked'] == [4, 5, 6, 7]
    assert [row['vertices'] for row in artifact['formula_sweep']] == list(range(4, 65))
    assert all(row == parameters(row['vertices']) for row in artifact['formula_sweep'])
    expected_cutwise = [
        {'vertices': vertices,
         'minimum_lambda_by_cut': [
             cutwise_minimum_lambda(vertices, cut_size)
             for cut_size in range(vertices * (vertices - 1) // 2 + 1)]}
        for vertices in range(4, 65)]
    assert artifact['cutwise_formula'] == expected_cutwise
    assert artifact['cutwise_controls'] == [exhaustive_cutwise_minima(vertices)
                                            for vertices in range(4, 7)]
    assert all(verify_record(record) for record in artifact['records'])
    forged = json.loads(json.dumps(artifact['records'][0]))
    forged['parameters']['half_cut_lambda_lower_bound'] += 1
    assert not verify_record(forged)
    assert artifact['adversarial'] == {'forged_bound_rejected': True}
    print(json.dumps({'independent_checks_passed': True,
                      'vertices': artifact['vertices_checked'],
                      'formula_sweep': len(artifact['formula_sweep']),
                      'state_bound_at_64': artifact['formula_sweep'][-1]['state_lower_bound']}))


if __name__ == '__main__':
    main()
