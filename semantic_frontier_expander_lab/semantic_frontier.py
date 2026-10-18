"""Semantic frontier certificates for bounded-degree graph CNFs.

The construction follows the subfunction-width argument for graph CNFs: an
almost-induced matching across a balanced variable cut gives pairwise distinct
residual Boolean functions, even after semantic quotienting.
"""
from __future__ import annotations

from itertools import combinations
from math import gcd
from pathlib import Path
import random


ROOT = Path(__file__).resolve().parent


def validate_graph(n, edges):
    if type(n) is not int or n < 2:
        raise ValueError('vertex count must be an integer >= 2')
    checked = set()
    for edge in edges:
        if type(edge) not in (tuple, list) or len(edge) != 2:
            raise ValueError('edge pair required')
        u, v = edge
        if type(u) is not int or type(v) is not int or not 0 <= u < n or not 0 <= v < n or u == v:
            raise ValueError('invalid edge')
        if u > v:
            u, v = v, u
        if (u, v) in checked:
            raise ValueError('duplicate edge')
        checked.add((u, v))
    if any(not any(v in edge for edge in checked) for v in range(n)):
        raise ValueError('isolated vertex')
    return tuple(sorted(checked))


def adjacency_masks(n, edges):
    adjacency = [0] * n
    for u, v in validate_graph(n, edges):
        adjacency[u] |= 1 << v
        adjacency[v] |= 1 << u
    return tuple(adjacency)


def mask_vertices(mask):
    while mask:
        bit = mask & -mask
        yield bit.bit_length() - 1
        mask ^= bit


def neighborhood_mask(adjacency, subset):
    result = 0
    for vertex in mask_vertices(subset):
        result |= adjacency[vertex]
    return result


def closed_neighborhood_mask(adjacency, vertex):
    return adjacency[vertex] | (1 << vertex)


def expansion_certificate(n, edges):
    """Return the exact open-neighborhood expansion through half-size sets."""
    adjacency = adjacency_masks(n, edges)
    best_num, best_den = None, None
    witness = None
    checked = 0
    for size in range(1, n // 2 + 1):
        for vertices in combinations(range(n), size):
            subset = sum(1 << vertex for vertex in vertices)
            neighborhood = neighborhood_mask(adjacency, subset)
            numerator, denominator = neighborhood.bit_count(), size
            checked += 1
            if (best_num is None or numerator * best_den < best_num * denominator):
                divisor = gcd(numerator, denominator)
                best_num, best_den = numerator // divisor, denominator // divisor
                witness = {'vertices': list(vertices),
                           'neighborhood_size': numerator}
    return {'epsilon_numerator': best_num,
            'epsilon_denominator': best_den,
            'witness': witness,
            'subsets_checked': checked,
            'maximum_degree': max(map(int.bit_count, adjacency))}


def theorem_lower_bound(n, maximum_degree, epsilon_numerator, epsilon_denominator):
    denominator = epsilon_denominator * 16 * maximum_degree
    numerator = epsilon_numerator * n
    return (numerator + denominator - 1) // denominator


def productive_sequence(n, edges, order):
    """Construct the paper's almost-induced matching at the half cut."""
    edges = validate_graph(n, edges)
    if type(order) not in (tuple, list) or sorted(order) != list(range(n)):
        raise ValueError('order must be a permutation')
    adjacency = adjacency_masks(n, edges)
    prefix = sum(1 << vertex for vertex in order[:n // 2])
    suffix = ((1 << n) - 1) ^ prefix
    blocked = 0
    pairs = []
    while True:
        available_a = prefix & ~blocked
        neighbors = neighborhood_mask(adjacency, available_a)
        available_b = neighbors & suffix & ~blocked
        if not available_a or not available_b:
            break
        chosen_a = None
        chosen_b = None
        for a in mask_vertices(available_a):
            candidates = adjacency[a] & available_b
            if candidates:
                chosen_a = a
                chosen_b = next(mask_vertices(candidates))
                break
        if chosen_a is None:
            break
        pairs.append((chosen_a, chosen_b))
        blocked |= (closed_neighborhood_mask(adjacency, chosen_a) |
                    closed_neighborhood_mask(adjacency, chosen_b))
    return pairs


def verify_productive_sequence(n, edges, order, pairs):
    edges = set(validate_graph(n, edges))
    prefix = set(order[:n // 2])
    suffix = set(order[n // 2:])
    seen_a, seen_b = set(), set()
    for index, (a, b) in enumerate(pairs):
        if a not in prefix or b not in suffix or tuple(sorted((a, b))) not in edges:
            return False
        if a in seen_a or b in seen_b:
            return False
        for old_a, old_b in pairs[:index]:
            if tuple(sorted((a, old_a))) in edges:
                return False
            if tuple(sorted((a, old_b))) in edges:
                return False
            if tuple(sorted((old_a, b))) in edges:
                return False
        seen_a.add(a)
        seen_b.add(b)
    return True


def evaluate_graph_cnf(n, edges, assignment):
    return all(assignment[u] or assignment[v] for u, v in validate_graph(n, edges))


def verify_residual_separation(n, edges, pairs):
    """Check the 2^ell explicit residual-separation witnesses."""
    ell = len(pairs)
    if ell > 20:
        raise ValueError('finite witness replay cap exceeded')
    a_vertices = {a for a, _ in pairs}
    b_vertices = {b for _, b in pairs}
    all_vertices = set(range(n))
    prefix_other = all_vertices - b_vertices
    suffix_all = all_vertices - a_vertices
    checks = 0
    for pattern in range(1 << ell):
        prefix_assignment = {vertex: True for vertex in prefix_other}
        for index, (a, _) in enumerate(pairs):
            prefix_assignment[a] = bool(pattern & (1 << index))
        for index, (_, b) in enumerate(pairs):
            suffix_assignment = {vertex: True for vertex in suffix_all}
            suffix_assignment[b] = False
            assignment = dict(prefix_assignment)
            assignment.update(suffix_assignment)
            expected = bool(pattern & (1 << index))
            if evaluate_graph_cnf(n, edges, assignment) != expected:
                return {'valid': False, 'patterns_checked': checks}
            checks += 1
    return {'valid': True, 'patterns_checked': checks}


def controls():
    cube = [(i, i ^ (1 << bit)) for i in range(8) for bit in range(3)
            if i < (i ^ (1 << bit))]
    petersen = ([(i, (i + 1) % 5) for i in range(5)] +
                [(5 + i, 5 + ((i + 2) % 5)) for i in range(5)] +
                [(i, 5 + i) for i in range(5)])
    fano_lines = [(0, 1, 3), (1, 2, 4), (2, 3, 5), (3, 4, 6),
                  (4, 5, 0), (5, 6, 1), (6, 0, 2)]
    heawood = [(point, 7 + line) for line, triple in enumerate(fano_lines)
               for point in triple]
    cyclic_bipartite = [(left, 8 + (left + shift) % 8)
                        for left in range(8) for shift in (0, 1, 3)]
    return [
        {'name': 'cube_3_regular', 'n': 8, 'edges': cube},
        {'name': 'petersen_3_regular', 'n': 10, 'edges': petersen},
        {'name': 'heawood_3_regular', 'n': 14, 'edges': heawood},
        {'name': 'cyclic_bipartite_16', 'n': 16, 'edges': cyclic_bipartite},
    ]


def sampled_orders(n, seed):
    rng = random.Random(seed)
    orders = [tuple(range(n)), tuple(reversed(range(n)))]
    orders.extend(tuple(rng.sample(range(n), n)) for _ in range(12))
    return tuple(orders)

