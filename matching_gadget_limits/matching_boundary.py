"""Exact small-graph terminal-deletion signatures and alternating-path evidence.

This is a bounded exhaustive reference, not a general efficient matching solver.
The mathematical theorem is independent of these finite checks.
"""
from functools import lru_cache


def _graph(n, edges, terminals):
    if type(n) is not int or not 0 <= n <= 10:
        raise ValueError("exhaustive reference is restricted to 0 <= n <= 10")
    edges = tuple(tuple(edge) for edge in edges)
    terminals = tuple(terminals)
    if any(len(edge) != 3 or any(type(value) is not int for value in edge)
           or not 0 <= edge[0] < edge[1] < n for edge in edges):
        raise ValueError("edges must be integer (u,v,weight) with 0 <= u < v < n")
    if any(type(v) is not int or not 0 <= v < n for v in terminals) or len(set(terminals)) != len(terminals):
        raise ValueError("terminals must be distinct graph vertices")
    return edges, terminals


def verify_matching(n, edges, terminals, deleted, matching):
    edges, terminals = _graph(n, edges, terminals)
    if type(deleted) is not int or deleted < 0 or deleted.bit_length() > len(terminals):
        return False
    removed = {v for j, v in enumerate(terminals) if deleted >> j & 1}
    covered = set()
    for edge_id in matching:
        if type(edge_id) is not int or not 0 <= edge_id < len(edges):
            return False
        u, v, _ = edges[edge_id]
        if u in removed or v in removed or u in covered or v in covered:
            return False
        covered.update((u, v))
    return covered == set(range(n)) - removed


def boundary_signature(n, edges, terminals):
    edges, terminals = _graph(n, edges, terminals)
    adjacency = [[] for _ in range(n)]
    for edge_id, (u, v, weight) in enumerate(edges):
        adjacency[u].append((v, weight, edge_id))
        adjacency[v].append((u, weight, edge_id))

    @lru_cache(None)
    def optimum(remaining):
        if not remaining:
            return 0, ()
        if remaining.bit_count() % 2:
            return None
        bit = remaining & -remaining
        u = bit.bit_length() - 1
        best = None
        for v, weight, edge_id in adjacency[u]:
            if remaining >> v & 1:
                suffix = optimum(remaining ^ bit ^ (1 << v))
                if suffix is not None:
                    candidate = weight + suffix[0], tuple(sorted((edge_id,) + suffix[1]))
                    if best is None or candidate < best:
                        best = candidate
        return best

    output = {}
    for deleted in range(1 << len(terminals)):
        remaining = (1 << n) - 1
        for j, vertex in enumerate(terminals):
            if deleted >> j & 1:
                remaining ^= 1 << vertex
        result = optimum(remaining)
        if result is not None:
            if not verify_matching(n, edges, terminals, deleted, result[1]):
                raise ArithmeticError("enumerated perfect matching failed replay")
            output[deleted] = {"cost": result[0], "matching": list(result[1])}
    return output


def exchange_failure(feasible, arity):
    feasible = frozenset(feasible)
    for A in sorted(feasible):
        for B in sorted(feasible):
            difference = A ^ B
            for e in range(arity):
                if not difference >> e & 1:
                    continue
                candidates = [f for f in range(arity) if f != e and difference >> f & 1]
                if not any(A ^ (1 << e) ^ (1 << f) in feasible for f in candidates):
                    return {"A": A, "B": B, "e": e, "candidate_f": candidates,
                            "rejected_neighbors": [A ^ (1 << e) ^ (1 << f) for f in candidates]}
    return None


def even_delta_audit(feasible, arity):
    feasible = tuple(sorted(set(feasible)))
    parities = sorted({value.bit_count() % 2 for value in feasible})
    failure = exchange_failure(feasible, arity)
    return {"nonempty": bool(feasible), "parities": parities,
            "exchange_failure": failure,
            "is_even_delta_matroid": bool(feasible) and len(parities) == 1 and failure is None}


def two_sided_exchange_failure(feasible, arity):
    """Necessary threshold law; weaker than ordinary even symmetric exchange."""
    feasible = frozenset(feasible)
    for A in sorted(feasible):
        for B in sorted(feasible):
            difference = A ^ B
            for e in range(arity):
                if not difference >> e & 1:
                    continue
                candidates = [f for f in range(arity) if f != e and difference >> f & 1]
                neighbors = [{"f": f, "A": A ^ (1 << e) ^ (1 << f),
                              "B": B ^ (1 << e) ^ (1 << f)} for f in candidates]
                if not any(row["A"] in feasible or row["B"] in feasible for row in neighbors):
                    return {"A": A, "B": B, "e": e, "rejected_neighbor_pairs": neighbors}
    return None


def threshold_support_audit(feasible, arity):
    feasible = tuple(sorted(set(feasible)))
    parities = sorted({value.bit_count() % 2 for value in feasible})
    failure = two_sided_exchange_failure(feasible, arity)
    return {"nonempty": bool(feasible), "parities": parities,
            "two_sided_exchange_failure": failure,
            "passes_necessary_threshold_conditions": len(parities) <= 1 and failure is None,
            "sufficient_for_matching_realizability_claimed": False}


def alternating_exchange(n, edges, terminals, A, B, e, matching_A, matching_B):
    """Construct and independently replay the simultaneous two-endpoint flip."""
    edges, terminals = _graph(n, edges, terminals)
    if (not verify_matching(n, edges, terminals, A, matching_A) or
            not verify_matching(n, edges, terminals, B, matching_B) or
            type(e) is not int or not 0 <= e < len(terminals) or not (A ^ B) >> e & 1):
        raise ValueError("invalid source matchings or exchange element")
    symmetric_edges = set(matching_A) ^ set(matching_B)
    adjacency = [[] for _ in range(n)]
    for edge_id in symmetric_edges:
        u, v, _ = edges[edge_id]
        adjacency[u].append((v, edge_id))
        adjacency[v].append((u, edge_id))
    start = terminals[e]
    if len(adjacency[start]) != 1:
        raise ArithmeticError("exchange vertex must be an alternating-path endpoint")
    current, previous, path = start, None, []
    while True:
        available = [(v, edge_id) for v, edge_id in adjacency[current] if edge_id != previous]
        if not available:
            break
        if len(available) != 1:
            raise ArithmeticError("alternating path branched")
        current, previous = available[0]
        path.append(previous)
        if len(path) > len(edges):
            raise ArithmeticError("endpoint walk failed to terminate")
    if current == start or current not in terminals:
        raise ArithmeticError("path did not end at a distinct terminal")
    f = terminals.index(current)
    if not (A ^ B) >> f & 1:
        raise ArithmeticError("other endpoint not in the symmetric boundary difference")
    neighbor_A, neighbor_B = A ^ (1 << e) ^ (1 << f), B ^ (1 << e) ^ (1 << f)
    flipped_A = sorted(set(matching_A) ^ set(path))
    flipped_B = sorted(set(matching_B) ^ set(path))
    if (not verify_matching(n, edges, terminals, neighbor_A, flipped_A) or
            not verify_matching(n, edges, terminals, neighbor_B, flipped_B)):
        raise ArithmeticError("flipped matchings failed independent vertex coverage")
    old_cost = sum(edges[j][2] for j in matching_A) + sum(edges[j][2] for j in matching_B)
    new_cost = sum(edges[j][2] for j in flipped_A) + sum(edges[j][2] for j in flipped_B)
    if old_cost != new_cost:
        raise ArithmeticError("simultaneous flip failed cost conservation")
    return {"A": A, "B": B, "e": e, "f": f, "path_edges": path,
            "neighbor_A": neighbor_A, "neighbor_B": neighbor_B,
            "matching_neighbor_A": flipped_A, "matching_neighbor_B": flipped_B,
            "old_total_cost": old_cost, "new_total_cost": new_cost,
            "both_matchings_verified": True}


def encode_double_rail(logical_mask, logical_arity):
    return sum(3 << (2 * j) for j in range(logical_arity) if logical_mask >> j & 1)


def valid_domain(logical_arity):
    return [encode_double_rail(mask, logical_arity) for mask in range(1 << logical_arity)]


def encoded_and(inputs):
    if type(inputs) is not int or inputs < 1:
        raise ValueError("AND must have at least one input")
    return [encode_double_rail(mask | ((int(mask == (1 << inputs) - 1)) << inputs), inputs + 1)
            for mask in range(1 << inputs)]


def bipartite_cost_example(weights):
    """Four terminals 0..3 and two mandatory internal vertices 4,5."""
    return [(terminal, internal, weight) for terminal, weight in enumerate(weights)
            for internal in (4, 5)]
