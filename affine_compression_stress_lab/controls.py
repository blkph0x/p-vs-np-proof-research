"""Complete original-CNF stress controls with independent structural counts."""
from itertools import combinations, product
from math import factorial
import random


def cubic_graph(vertices, seed):
    if type(vertices) is not int or vertices < 4 or vertices % 2:
        raise ValueError('positive even vertex count at least four')
    rng = random.Random(seed)
    for attempt in range(10000):
        stubs = [v for v in range(vertices) for _ in range(3)]
        rng.shuffle(stubs)
        edges = [tuple(sorted(stubs[i:i+2])) for i in range(0, len(stubs), 2)]
        if any(u == v for u, v in edges) or len(set(edges)) != len(edges):
            continue
        edges.sort()
        adjacency = [set() for _ in range(vertices)]
        for u, v in edges:
            adjacency[u].add(v); adjacency[v].add(u)
        seen, queue = {0}, [0]
        for v in queue:
            for u in sorted(adjacency[v]-seen):
                seen.add(u); queue.append(u)
        if len(seen) == vertices:
            return edges, attempt+1
    raise RuntimeError('bounded graph generation exhausted')


def parity_control(vertices, total_parity, seed, shuffled=False):
    edges, attempts = cubic_graph(vertices, seed)
    rng = random.Random(seed+1)
    charges = [rng.randrange(2) for _ in range(vertices-1)]
    charges.append((sum(charges) % 2) ^ total_parity)
    clauses, blocks = [], []
    for vertex in range(vertices):
        incident = [i for i, edge in enumerate(edges) if vertex in edge]
        assert len(incident) == 3
        block = []
        for bits in product((0, 1), repeat=3):
            if sum(bits) % 2 != charges[vertex]:
                block.append([-(e+1) if bit else e+1 for e, bit in zip(incident, bits)])
        blocks.append(block); clauses.extend(block)
    if shuffled:
        random.Random(seed+2).shuffle(clauses)
    return dict(name=f'cubic_parity_v{vertices}_charge{total_parity}_'+('shuffled' if shuffled else 'grouped'),
                kind='cubic_parity', n=len(edges), clauses=clauses, vertices=vertices,
                edges=[list(e) for e in edges], charges=charges, seed=seed,
                generator_attempts=attempts, shuffled=shuffled,
                expected_count=0 if total_parity else 1 << (len(edges)-vertices+1))


def pigeonhole_control(pigeons, holes):
    if holes < 1 or pigeons not in (holes, holes+1):
        raise ValueError('controls cover bijection and one-extra-pigeon cases')
    variable = lambda p, h: p*holes+h+1
    clauses = [[variable(p, h) for h in range(holes)] for p in range(pigeons)]
    clauses += [[-variable(p, h), -variable(q, h)]
                for h in range(holes) for p, q in combinations(range(pigeons), 2)]
    return dict(name=f'pigeonhole_{pigeons}_into_{holes}', kind='pigeonhole',
                n=pigeons*holes, clauses=clauses, pigeons=pigeons, holes=holes,
                expected_count=factorial(holes) if pigeons == holes else 0)


def verify_control(case):
    """Reconstruct original clauses and count from explicit source structure."""
    clauses = case['clauses']
    if case['kind'] == 'pigeonhole':
        p, h = case['pigeons'], case['holes']
        assert case['n'] == p*h and p in (h, h+1)
        wanted = [[i*h+j+1 for j in range(h)] for i in range(p)]
        for j in range(h):
            for i in range(p):
                for k in range(i+1, p):
                    wanted.append([-(i*h+j+1), -(k*h+j+1)])
        assert clauses == wanted
        count = factorial(h) if p == h else 0
        evidence = {'pigeons': p, 'holes': h,
                    'proof': 'sum of row lower bounds exceeds column upper bounds, or equality forces a bijection'}
    elif case['kind'] == 'cubic_parity':
        v, edges, charges = case['vertices'], case['edges'], case['charges']
        assert case['n'] == len(edges) and len(charges) == v
        assert all(type(q) is int and q in (0, 1) for q in charges)
        assert all(type(a) is int and type(b) is int and 0 <= a < b < v for a, b in edges)
        assert len(set(map(tuple, edges))) == len(edges)
        incidence = [[i for i, e in enumerate(edges) if vertex in e] for vertex in range(v)]
        assert all(len(row) == 3 for row in incidence)
        seen, tree = {0}, []
        while len(seen) < v:
            crossing = next(((i, a, b) for i, (a, b) in enumerate(edges) if (a in seen) != (b in seen)), None)
            assert crossing is not None, 'graph must be connected'
            i, a, b = crossing
            seen.update((a, b)); tree.append(i)
        wanted = []
        for vertex, ids in enumerate(incidence):
            for word in range(8):
                if word.bit_count() % 2 != charges[vertex]:
                    wanted.append(tuple(-(e+1) if word >> j & 1 else e+1 for j, e in enumerate(ids)))
        assert sorted(map(tuple, clauses)) == sorted(wanted), 'every original XOR clause occurrence must be present'
        # Independently check matrix rank and augmented consistency, not just the formula name.
        basis, contradictory = {}, False
        for ids, rhs in zip(incidence, charges):
            mask = sum(1 << i for i in ids)
            while mask:
                pivot = mask.bit_length()-1
                if pivot not in basis:
                    basis[pivot] = (mask, rhs); break
                other, value = basis[pivot]
                mask ^= other; rhs ^= value
            if mask == 0 and rhs:
                contradictory = True
        assert len(basis) == v-1
        assert contradictory == bool(sum(charges) % 2)
        count = 0 if contradictory else 1 << (len(edges)-len(basis))
        evidence = {'spanning_tree_edge_ids': tree, 'rank': len(basis),
                    'free_edge_variables': len(edges)-len(basis), 'charge_parity': sum(charges) % 2,
                    'proof': 'connected incidence rank V-1; each XOR3 block is exactly its four forbidden assignments'}
    else:
        raise ValueError('unknown control kind')
    assert case['expected_count'] == count
    return dict(valid=True, count=count, evidence=evidence)


def fixed_controls():
    return [parity_control(v, charge, 20261018+v, shuffled)
            for v in (8, 20, 40, 80) for charge in (0, 1) for shuffled in (False, True)] + [
                pigeonhole_control(p, h) for h in (3, 4, 5) for p in (h, h+1)]
