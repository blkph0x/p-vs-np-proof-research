"""Exact Tseitin CNF controls on small bounded-degree graphs.

For an edge variable x_e and vertex charge c_v, the local constraint is
XOR_{e incident to v} x_e = c_v.  The CNF contains one clause for every local
assignment with the wrong parity.  An odd total charge is an exact parity
certificate of unsatisfiability because every edge occurs at two vertices.
"""
from __future__ import annotations

from itertools import product


def normalize_edges(n, edges):
    if type(n) is not int or n < 2:
        raise ValueError("n must be an integer >= 2")
    checked = set()
    for edge in edges:
        if type(edge) not in (tuple, list) or len(edge) != 2:
            raise ValueError("edge pair required")
        u, v = edge
        if type(u) is not int or type(v) is not int or not 0 <= u < n or not 0 <= v < n:
            raise ValueError("edge endpoint outside graph")
        if u == v:
            raise ValueError("self-loop is not supported")
        if u > v:
            u, v = v, u
        if (u, v) in checked:
            raise ValueError("duplicate edge")
        checked.add((u, v))
    if any(not any(vertex in edge for edge in checked) for vertex in range(n)):
        raise ValueError("isolated vertex")
    return tuple(sorted(checked))


def connected(n, edges):
    edges = normalize_edges(n, edges)
    seen = {0}
    changed = True
    while changed:
        changed = False
        for u, v in edges:
            if u in seen and v not in seen:
                seen.add(v); changed = True
            elif v in seen and u not in seen:
                seen.add(u); changed = True
    return len(seen) == n


def incidence(n, edges):
    edges = normalize_edges(n, edges)
    result = [[] for _ in range(n)]
    for index, (u, v) in enumerate(edges, start=1):
        result[u].append(index)
        result[v].append(index)
    return tuple(tuple(row) for row in result)


def charges_are_valid(n, charges):
    return (type(charges) in (tuple, list) and len(charges) == n and
            all(value in (0, 1) for value in charges))


def tseitin_cnf(n, edges, charges):
    edges = normalize_edges(n, edges)
    if not charges_are_valid(n, charges):
        raise ValueError("charges must be a length-n 0/1 sequence")
    clauses = []
    for vertex, variables in enumerate(incidence(n, edges)):
        target = int(charges[vertex])
        for bits in product((0, 1), repeat=len(variables)):
            if sum(bits) % 2 == target:
                continue
            # This clause is false exactly on the forbidden local assignment.
            clauses.append(tuple(-variable if bit else variable
                                 for variable, bit in zip(variables, bits)))
    return len(edges), tuple(clauses)


def parity_certificate(n, edges, charges):
    edges = normalize_edges(n, edges)
    if not charges_are_valid(n, charges):
        raise ValueError("invalid charges")
    counts = [0] * len(edges)
    for variables in incidence(n, edges):
        for variable in variables:
            counts[variable - 1] += 1
    total_charge = sum(int(value) for value in charges) % 2
    return {
        "edge_occurrences": counts,
        "every_edge_occurs_twice": all(count == 2 for count in counts),
        "charge_sum_mod2": total_charge,
        "odd_charge": total_charge == 1,
        "parity_proves_unsat": all(count == 2 for count in counts) and total_charge == 1,
    }


def local_parity_satisfied(bits, target):
    return sum(bits) % 2 == target


def clause_satisfied(clause, assignment):
    return any(assignment[abs(literal) - 1] == (literal > 0)
               for literal in clause)


def graph_controls():
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
    return (
        {"name": "cube_3_regular", "n": 8, "edges": cube},
        {"name": "petersen_3_regular", "n": 10, "edges": petersen},
        {"name": "heawood_3_regular", "n": 14, "edges": heawood},
        {"name": "cyclic_bipartite_16", "n": 16, "edges": cyclic_bipartite},
    )


def mobius_ladder(n):
    """Return the cubic cycle-plus-opposite-matching graph for even n >= 6."""
    if type(n) is not int or n < 6 or n % 2:
        raise ValueError("the Mobius ladder size must be an even integer >= 6")
    cycle = [(vertex, (vertex + 1) % n) for vertex in range(n)]
    opposite = [(vertex, vertex + n // 2) for vertex in range(n // 2)]
    return tuple(sorted({tuple(sorted(edge)) for edge in cycle + opposite}))


def mobius_ladder_controls():
    """Return a deterministic even-size scaling family for the CDCL control."""
    return tuple({"name": f"mobius_ladder_{n}", "n": n,
                  "edges": mobius_ladder(n), "family": "mobius_ladder"}
                 for n in range(6, 22, 2))
