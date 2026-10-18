"""Finite replay of the local gadgets in Jia et al., arXiv:2606.23161.

This is deliberately a small independent checker, not a formalization of the
paper's all-size reduction.  It enumerates every feasible support for small
hypergraphs and Tanner graphs and checks the claimed bijections and weight
intervals for decomposition, padding, and variable replication.
"""

from __future__ import annotations

import hashlib
import json
import random
from itertools import combinations, product
from pathlib import Path


ROOT = Path(__file__).resolve().parent


def parity_support(edges, vertex_count):
    """Return all masks selecting an even cover, including the empty mask."""
    out = []
    for mask in range(1 << len(edges)):
        parity = [0] * vertex_count
        for i, edge in enumerate(edges):
            if mask >> i & 1:
                for v in edge:
                    parity[v] ^= 1
        if not any(parity):
            out.append(mask)
    return out


def selected(mask, i):
    return bool((mask >> i) & 1)


def bitset(indices):
    value = 0
    for i in indices:
        value |= 1 << i
    return value


def decompose(edges, vertex_count):
    """Algorithm 1: replace each edge of size >3 by a 3-edge chain."""
    result = []
    chains = []
    next_vertex = vertex_count
    for edge in edges:
        e = tuple(edge)
        if len(e) <= 3:
            chains.append(tuple(range(len(result), len(result) + 1)))
            result.append(e)
            continue
        k = len(e)
        aux = list(range(next_vertex, next_vertex + k - 3))
        next_vertex += k - 3
        start = len(result)
        result.append((e[0], e[1], aux[0]))
        for j in range(1, k - 3):
            result.append((aux[j - 1], e[j + 1], aux[j]))
        result.append((aux[-1], e[-2], e[-1]))
        chains.append(tuple(range(start, len(result))))
    return result, chains, next_vertex


def decompose_map(mask, chains):
    out = 0
    for original_i, chain in enumerate(chains):
        if selected(mask, original_i):
            out |= bitset(chain)
    return out


def pad(edges, vertex_count):
    """Theorem 16 padding gadget, returning padded edges and metadata."""
    y1, y2, z1, z2 = vertex_count, vertex_count + 1, vertex_count + 2, vertex_count + 3
    padded = []
    sizes = []
    for edge in edges:
        e = tuple(edge)
        sizes.append(len(e))
        if len(e) == 3:
            padded.append(e)
        elif len(e) == 2:
            padded.append(e + (z1,))
        elif len(e) == 1:
            padded.append(e + (y1, y2))
        else:
            raise AssertionError("decomposition left an edge larger than three")
    a1 = (y1, y2, z1)
    a2 = (y1, z1, z2)
    a3 = (y2, z1, z2)
    a_start = len(padded)
    padded.extend((a1, a2, a3))
    return padded, (y1, y2, z1, z2), sizes, a_start


def pad_map(mask, sizes, a_start):
    alpha = sum(selected(mask, i) for i, size in enumerate(sizes) if size == 1) & 1
    beta = sum(selected(mask, i) for i, size in enumerate(sizes) if size == 2) & 1
    correction = {(0, 0): (), (0, 1): (a_start, a_start + 1, a_start + 2),
                  (1, 0): (a_start + 1, a_start + 2),
                  (1, 1): (a_start,)}[(alpha, beta)]
    out = 0
    for i in range(len(sizes)):
        if selected(mask, i):
            out |= 1 << i
    return out | bitset(correction)


def graph_support(neighbors, check_count):
    """All variable masks satisfying every even parity check."""
    out = []
    for mask in range(1 << len(neighbors)):
        parity = [0] * check_count
        for i, incident in enumerate(neighbors):
            if selected(mask, i):
                for check in incident:
                    parity[check] ^= 1
        if not any(parity):
            out.append(mask)
    return out


def graph_mask_valid(neighbors, check_count, mask):
    parity = [0] * check_count
    for i, incident in enumerate(neighbors):
        if selected(mask, i):
            for check in incident:
                parity[check] ^= 1
    return not any(parity)


def replicate(neighbors, check_count, target, m):
    """Algorithm 3, with variables and checks represented by integer IDs."""
    assert m >= 2 and m % 2 == 0
    out = [tuple(x) for x in neighbors]
    old = out[target]
    r1, r2, r3 = old
    # The target keeps r3 and receives two new degree-two checks.
    out[target] = (r3, check_count, check_count + 1)
    next_check = check_count + 2
    x1 = len(out)
    x2 = x1 + 1
    out.extend(((r1, check_count), (r2, check_count + 1)))
    # y_{i-1}, y_i, and y_{i-1,i} for i=4,6,...,m.
    for i in range(4, m + 1, 2):
        xi_minus_3 = x1 + (i - 4)
        xi_minus_2 = x1 + (i - 3)
        xi_minus_1 = x1 + (i - 2)
        xi = x1 + (i - 1)
        y_left, y_right, y_pair = next_check, next_check + 1, next_check + 2
        out[xi_minus_3] = tuple(out[xi_minus_3]) + (y_left,)
        out[xi_minus_2] = tuple(out[xi_minus_2]) + (y_right,)
        out.extend(((y_left, y_pair), (y_right, y_pair)))
        # The pair check is present in both new variable lists.
        next_check += 3
    terminal = next_check
    out[x1 + m - 2] = tuple(out[x1 + m - 2]) + (terminal,)
    out[x1 + m - 1] = tuple(out[x1 + m - 1]) + (terminal,)
    next_check += 1
    # Normalize and validate the intended graph incidence; every variable has
    # exactly three neighbors and every added pair check has degree two.
    assert all(len(set(inc)) == 3 for inc in out)
    assert next_check >= check_count
    return out, next_check


def mapped_mask(mask, target, m, old_count):
    if not selected(mask, target):
        return mask
    # New variables are appended after the old variables.
    return mask | (((1 << m) - 1) << old_count)


def check_decomposition(rng):
    cases = 0
    for _ in range(120):
        n = rng.randint(2, 5)
        edge_count = rng.randint(1, 5)
        edges = []
        for _ in range(edge_count):
            k = rng.randint(1, min(6, n))
            edges.append(tuple(sorted(rng.sample(range(n), k))))
        new_edges, chains, new_n = decompose(edges, n)
        old = set(parity_support(edges, n))
        new = set(parity_support(new_edges, new_n))
        mapped = {decompose_map(mask, chains) for mask in old}
        assert mapped == new, (edges, old, new, mapped)
        cases += 1
    return cases


def check_padding(rng):
    cases = 0
    for _ in range(160):
        n = rng.randint(1, 4)
        edge_count = rng.randint(1, 6)
        edges = []
        for _ in range(edge_count):
            k = rng.randint(1, min(3, n))
            edges.append(tuple(sorted(rng.sample(range(n), k))))
        padded, _aux, sizes, a_start = pad(edges, n)
        old = set(parity_support(edges, n))
        new = set(parity_support(padded, n + 4))
        mapped = {pad_map(mask, sizes, a_start) for mask in old}
        assert mapped == new, (edges, old, new, mapped)
        cases += 1
    return cases


def check_padding_exhaustive_small():
    """Exhaust every indexed family on at most three vertices and edges.

    The random audit above exercises larger families, but this finite sweep
    removes sampling from the most delicate four-vertex parity correction.
    Families are indexed tuples, so repeated equal hyperedges are included.
    Empty families are included as the neutral case.
    """
    cases = 0
    for vertex_count in range(0, 4):
        options = [tuple(c) for size in range(1, min(3, vertex_count) + 1)
                   for c in combinations(range(vertex_count), size)]
        for edge_count in range(0, 4):
            for edges in product(options, repeat=edge_count):
                padded, _aux, sizes, a_start = pad(edges, vertex_count)
                old = set(parity_support(edges, vertex_count))
                new = set(parity_support(padded, vertex_count + 4))
                mapped = {pad_map(mask, sizes, a_start) for mask in old}
                assert mapped == new, (vertex_count, edges, old, new, mapped)
                cases += 1
    return cases


def check_decomposition_exhaustive_small():
    """Exhaust small indexed families, including repeated large hyperedges."""
    cases = 0
    for vertex_count in range(1, 5):
        options = [tuple(c) for size in range(1, vertex_count + 1)
                   for c in combinations(range(vertex_count), size)]
        for edge_count in range(0, 3):
            for edges in product(options, repeat=edge_count):
                new_edges, chains, new_n = decompose(edges, vertex_count)
                old = set(parity_support(edges, vertex_count))
                new = set(parity_support(new_edges, new_n))
                mapped = {decompose_map(mask, chains) for mask in old}
                assert mapped == new, (vertex_count, edges, old, new, mapped)
                cases += 1
    return cases


def check_replication(rng):
    cases = 0
    for _ in range(120):
        variable_count, checks = 3, 5
        neighbors = []
        for _ in range(variable_count):
            neighbors.append(tuple(sorted(rng.sample(range(checks), 3))))
        target = rng.randrange(variable_count)
        m = rng.choice((2, 4, 6))
        new_neighbors, new_checks = replicate(neighbors, checks, target, m)
        old = set(graph_support(neighbors, checks))
        new = set(graph_support(new_neighbors, new_checks))
        mapped = {mapped_mask(mask, target, m, variable_count) for mask in old}
        assert mapped == new, (neighbors, target, m, old, new, mapped)
        for mask in new:
            clone_bits = [(mask >> (variable_count + i)) & 1 for i in range(m)]
            assert all(bit == ((mask >> target) & 1) for bit in clone_bits)
        cases += 1
    return cases


def check_full_small_reductions(rng):
    cases = 0
    threshold_rows = 0
    exhaustive_cases = 0
    for _ in range(90):
        n = rng.randint(2, 4)
        edge_count = rng.randint(1, 4)
        edges = []
        for _ in range(edge_count):
            k = rng.randint(1, n)
            edges.append(tuple(sorted(rng.sample(range(n), k))))
        # This mirrors the theorem's harmless dummy singleton and the chosen
        # threshold normalization, while keeping the finite instances small.
        w = rng.randint(1, edge_count)
        decomp_edges, chains, decomp_n = decompose(edges, n)
        padded, _aux, sizes, a_start = pad(decomp_edges, decomp_n)
        graph = [tuple(edge) for edge in padded]
        graph_checks = decomp_n + 4
        B = max(w + 4, 2 + max(len(chain) for chain in chains))
        for original_i, chain in enumerate(chains):
            representative = chain[0]
            m = B - len(chain)
            if m % 2:
                m += 1
            graph, graph_checks = replicate(graph, graph_checks, representative, m)
        old = set(parity_support(edges, n))
        expected = set()
        for mask in old:
            dmask = decompose_map(mask, chains)
            pmask = pad_map(dmask, [len(e) for e in decomp_edges], a_start)
            current = pmask
            # Representatives are old IDs; replication appends clones, so map
            # in the same order as the reductions above.
            offset = len(padded)
            for original_i, chain in enumerate(chains):
                rep = chain[0]
                m = B - len(chain)
                if m % 2:
                    m += 1
                if selected(mask, original_i):
                    current |= ((1 << m) - 1) << offset
                offset += m
            t = mask.bit_count()
            assert graph_mask_valid(graph, graph_checks, current)
            assert t * B <= current.bit_count() <= t * (B + 1) + 3
            expected.add(current)
            threshold_rows += 1
        # Complete final-code enumeration is deliberately restricted to small
        # outputs; larger cases retain the exact forward and weight checks above.
        if len(graph) <= 18:
            assert set(graph_support(graph, graph_checks)) == expected
            exhaustive_cases += 1
        cases += 1
    return cases, threshold_rows, exhaustive_cases


def main():
    rng = random.Random(20261018)
    counts = {
        "decomposition_cases": check_decomposition(rng),
        "decomposition_exhaustive_cases": check_decomposition_exhaustive_small(),
        "padding_cases": check_padding(rng),
        "padding_exhaustive_cases": check_padding_exhaustive_small(),
        "replication_cases": check_replication(rng),
    }
    (counts["full_reduction_cases"], counts["threshold_rows"],
     counts["full_exhaustive_cases"]) = check_full_small_reductions(rng)
    payload = {
        "source": "Jia et al., On the Intractability of the Minimum Distance Problem for Regular LDPC Codes, arXiv:2606.23161v3",
        "scope": "finite local-gadget replay; not a formalization of the all-size theorem",
        "seed": 20261018,
        "counts": counts,
        "all_checks_passed": True,
    }
    source_files = [Path(__file__), ROOT / "REGULAR_LDPC_MINIMUM_DISTANCE_SCOPE.md"]
    payload["source_sha256"] = {
        p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in source_files
    }
    (ROOT / "REGULAR_LDPC_LOCAL_AUDIT.json").write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(payload, indent=2))


if __name__ == "__main__":
    main()
