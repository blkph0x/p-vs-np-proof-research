"""Independent replay of the semantic frontier expander certificate."""
from __future__ import annotations

from itertools import combinations
import json
from math import gcd
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def normalize(n, edges):
    checked = set()
    for u, v in edges:
        if u > v:
            u, v = v, u
        checked.add((u, v))
    return tuple(sorted(checked))


def adjacency(n, edges):
    result = [0] * n
    for u, v in normalize(n, edges):
        result[u] |= 1 << v
        result[v] |= 1 << u
    return tuple(result)


def vertices(mask):
    while mask:
        bit = mask & -mask
        yield bit.bit_length() - 1
        mask ^= bit


def neighborhood(adj, subset):
    result = 0
    for vertex in vertices(subset):
        result |= adj[vertex]
    return result


def expansion(n, edges):
    adj = adjacency(n, edges)
    best_num, best_den, witness = None, None, None
    checked = 0
    for size in range(1, n // 2 + 1):
        for chosen in combinations(range(n), size):
            subset = sum(1 << vertex for vertex in chosen)
            count = neighborhood(adj, subset).bit_count()
            checked += 1
            if best_num is None or count * best_den < best_num * size:
                divisor = gcd(count, size)
                best_num, best_den = count // divisor, size // divisor
                witness = {'vertices': list(chosen), 'neighborhood_size': count}
    return {'epsilon_numerator': best_num, 'epsilon_denominator': best_den,
            'witness': witness, 'subsets_checked': checked,
            'maximum_degree': max(map(int.bit_count, adj))}


def lower_bound(n, expansion_record):
    numerator = expansion_record['epsilon_numerator'] * n
    denominator = expansion_record['epsilon_denominator'] * 16 * expansion_record['maximum_degree']
    return (numerator + denominator - 1) // denominator


def productive(n, edges, order):
    adj = adjacency(n, edges)
    prefix = sum(1 << v for v in order[:n // 2])
    suffix = ((1 << n) - 1) ^ prefix
    blocked = 0
    pairs = []
    while True:
        available_a = prefix & ~blocked
        available_b = neighborhood(adj, available_a) & suffix & ~blocked
        if not available_a or not available_b:
            break
        selected = None
        for a in vertices(available_a):
            candidate = adj[a] & available_b
            if candidate:
                selected = (a, next(vertices(candidate)))
                break
        if selected is None:
            break
        a, b = selected
        pairs.append((a, b))
        blocked |= adj[a] | (1 << a) | adj[b] | (1 << b)
    return pairs


def productive_valid(n, edges, order, pairs):
    edge_set = set(normalize(n, edges)); prefix = set(order[:n // 2]); suffix = set(order[n // 2:])
    for i, (a, b) in enumerate(pairs):
        if a not in prefix or b not in suffix or tuple(sorted((a, b))) not in edge_set:
            return False
        for old_a, old_b in pairs[:i]:
            if tuple(sorted((a, old_a))) in edge_set or tuple(sorted((a, old_b))) in edge_set:
                return False
            if tuple(sorted((old_a, b))) in edge_set:
                return False
    return True


def cnf_value(n, edges, assignment):
    return all(assignment[u] or assignment[v] for u, v in normalize(n, edges))


def separation_valid(n, edges, pairs):
    ell = len(pairs); a_set = {a for a, _ in pairs}; b_set = {b for _, b in pairs}
    prefix_other = set(range(n)) - b_set; suffix_all = set(range(n)) - a_set
    checked = 0
    for pattern in range(1 << ell):
        prefix_assignment = {v: True for v in prefix_other}
        for i, (a, _) in enumerate(pairs):
            prefix_assignment[a] = bool(pattern & (1 << i))
        for i, (_, b) in enumerate(pairs):
            suffix_assignment = {v: True for v in suffix_all}; suffix_assignment[b] = False
            assignment = dict(prefix_assignment); assignment.update(suffix_assignment)
            if cnf_value(n, edges, assignment) != bool(pattern & (1 << i)):
                return False, checked
            checked += 1
    return True, checked


def main():
    artifact = json.loads((ROOT / 'RESULTS.json').read_text(encoding='utf-8'))
    assert artifact['all_checks_passed']
    rows = artifact['rows']; assert len(rows) == 4
    for row in rows:
        n, edges = row['n'], row['edges']
        expected_expansion = expansion(n, edges)
        assert row['expansion'] == expected_expansion
        assert row['theorem_lower_bound'] == lower_bound(n, expected_expansion)
        for saved in row['sampled_orders']:
            pairs = productive(n, edges, saved['order'])
            assert [list(pair) for pair in pairs] == saved['pairs']
            assert saved['productive_width'] == len(pairs)
            assert len(pairs) >= row['theorem_lower_bound']
            assert productive_valid(n, edges, saved['order'], pairs)
            valid, checked = separation_valid(n, edges, pairs)
            assert valid and checked == saved['separation']['patterns_checked']
    forged = json.loads(json.dumps(rows[0]))
    forged['theorem_lower_bound'] += 1
    assert not all(len(productive(forged['n'], forged['edges'], saved['order'])) >= forged['theorem_lower_bound']
                   for saved in forged['sampled_orders'])
    print(json.dumps({'independent_checks_passed': True,
                      'controls': len(rows),
                      'minimum_theorem_bound': min(row['theorem_lower_bound'] for row in rows),
                      'maximum_sampled_width': max(saved['productive_width']
                                                   for row in rows for saved in row['sampled_orders'])}))


if __name__ == '__main__':
    main()
