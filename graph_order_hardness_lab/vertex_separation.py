"""Exact vertex-separation width and small graph-layout certificates."""

from __future__ import annotations


def validate_graph(n, edges):
    if type(n) is not int or n < 0:
        raise ValueError("nonnegative vertex count required")
    if type(edges) not in (list, tuple):
        raise ValueError("edge list required")
    checked = set()
    for edge in edges:
        if type(edge) not in (list, tuple) or len(edge) != 2:
            raise ValueError("edge pair required")
        u, v = edge
        if type(u) is not int or type(v) is not int or not 0 <= u < n or not 0 <= v < n or u == v:
            raise ValueError("invalid edge")
        if u > v:
            u, v = v, u
        if (u, v) in checked:
            raise ValueError("duplicate edge")
        checked.add((u, v))
    return sorted(checked)


def adjacency(n, edges):
    adj = [0] * n
    for u, v in validate_graph(n, edges):
        adj[u] |= 1 << v
        adj[v] |= 1 << u
    return adj


def boundary_vertices(n, edges, subset):
    if type(subset) is not int or subset < 0 or subset >= (1 << n):
        raise ValueError("invalid prefix subset")
    adj = adjacency(n, edges)
    suffix = ((1 << n) - 1) ^ subset
    return tuple(i for i in range(n) if subset >> i & 1 and adj[i] & suffix)


def order_records(n, edges, order):
    validate_graph(n, edges)
    if type(order) not in (list, tuple) or sorted(order) != list(range(n)):
        raise ValueError("order must be a permutation")
    subset = 0
    records = []
    for cut, vertex in enumerate(order, 1):
        subset |= 1 << vertex
        boundary = boundary_vertices(n, edges, subset)
        records.append({'cut': cut, 'subset': subset,
                        'boundary': list(boundary), 'width': len(boundary)})
    width = max((record['width'] for record in records[:-1]), default=0)
    return records, width


def optimal_order(n, edges):
    """Exact bottleneck subset-DP, exponential by design."""
    edges = validate_graph(n, edges)
    best = {0: (0, ())}
    for subset in range(1 << n):
        if subset not in best:
            continue
        prior_width, prior_order = best[subset]
        for vertex in range(n):
            bit = 1 << vertex
            if subset & bit:
                continue
            nxt = subset | bit
            cut = 0 if nxt == (1 << n) - 1 else len(boundary_vertices(n, edges, nxt))
            candidate = (max(prior_width, cut), prior_order + (vertex,))
            if nxt not in best or candidate < best[nxt]:
                best[nxt] = candidate
    width, order = best[(1 << n) - 1]
    records, replay_width = order_records(n, edges, order)
    assert width == replay_width
    return {'status': 'EXACT', 'order': list(order), 'width': width,
            'records': records, 'state_count': len(best)}


def greedy_order(n, edges, policy='min_boundary'):
    """Polynomial local ordering heuristic; no optimality claim."""
    edges = validate_graph(n, edges)
    if policy not in ('min_boundary', 'min_degree'):
        raise ValueError('unknown greedy policy')
    adj = adjacency(n, edges)
    remaining = set(range(n))
    subset = 0
    order = []
    while remaining:
        choices = []
        for vertex in remaining:
            nxt = subset | (1 << vertex)
            if policy == 'min_boundary':
                score = 0 if nxt == (1 << n) - 1 else len(boundary_vertices(n, edges, nxt))
            else:
                score = sum(bool(adj[vertex] & (1 << other)) for other in remaining if other != vertex)
            choices.append((score, vertex))
        vertex = min(choices)[1]
        order.append(vertex)
        remaining.remove(vertex)
        subset |= 1 << vertex
    return order


def verify_certificate(n, edges, result):
    try:
        edges = validate_graph(n, edges)
        if type(result) is not dict or result.get('status') != 'EXACT':
            return {'valid': False, 'errors': ['missing exact result']}
        expected = optimal_order(n, edges)
        records, width = order_records(n, edges, result['order'])
        if width != expected['width'] or result['width'] != width:
            return {'valid': False, 'errors': ['nonoptimal width']}
        if records != result['records']:
            return {'valid': False, 'errors': ['boundary replay mismatch']}
        return {'valid': True, 'width': width, 'order': list(result['order']), 'errors': []}
    except (ValueError, TypeError, KeyError, IndexError):
        return {'valid': False, 'errors': ['malformed certificate']}


def monotone_two_cnf(n, edges):
    """Return the always-satisfiable clauses (x_u OR x_v) for a graph."""
    return [[u + 1, v + 1] for u, v in validate_graph(n, edges)]
