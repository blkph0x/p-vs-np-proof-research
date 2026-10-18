"""Primal-graph width controls for the two-bridge exact-one gadget."""
from __future__ import annotations

from itertools import combinations


def _validate(clauses: tuple[tuple[int, int, int], ...], variables: int) -> None:
    if variables < 0:
        raise ValueError("negative variable count")
    for clause in clauses:
        if len(clause) != 3 or len(set(clause)) != 3:
            raise ValueError("each clause needs three distinct variables")
        if any(not isinstance(v, int) or v < 0 or v >= variables for v in clause):
            raise ValueError("clause variable outside declared range")


def _clique(adj: list[int], vertices: tuple[int, ...]) -> None:
    for u, v in combinations(vertices, 2):
        adj[u] |= 1 << v
        adj[v] |= 1 << u


def original_primal(clauses: tuple[tuple[int, int, int], ...], variables: int) -> tuple[int, ...]:
    _validate(clauses, variables)
    adj = [0] * variables
    for clause in clauses:
        _clique(adj, clause)
    return tuple(adj)


def transformed_primal(clauses: tuple[tuple[int, int, int], ...], variables: int) -> tuple[int, ...]:
    """Primal graph of the fixed H/A replacement, including fresh bridges."""
    _validate(clauses, variables)
    total = variables + 2 * len(clauses)
    adj = [0] * total
    for i, (x, y, w) in enumerate(clauses):
        z0, z1 = variables + 2 * i, variables + 2 * i + 1
        _clique(adj, (x, z0, z1))
        _clique(adj, (y, w, z0, z1))
    return tuple(adj)


def _boundary(adj: tuple[int, ...], subset: int) -> int:
    return sum(bool(subset >> v & 1 and adj[v] & ~subset) for v in range(len(adj)))


def exact_pathwidth(adj: tuple[int, ...]) -> int:
    """Subset DP for pathwidth; used only on small audit graphs."""
    n = len(adj)
    if n == 0:
        return 0
    size = 1 << n
    dp = [n + 1] * size
    dp[0] = 0
    boundary = [_boundary(adj, subset) for subset in range(size)]
    for subset in range(1, size):
        rest = subset
        best = n + 1
        while rest:
            bit = rest & -rest
            prev = subset ^ bit
            best = min(best, max(dp[prev], boundary[subset]))
            rest ^= bit
        dp[subset] = best
    return dp[-1]


def width_pair(clauses: tuple[tuple[int, int, int], ...], variables: int) -> tuple[int, int]:
    return (exact_pathwidth(original_primal(clauses, variables)),
            exact_pathwidth(transformed_primal(clauses, variables)))


def all_three_subsets(variables: int) -> tuple[tuple[int, int, int], ...]:
    return tuple(combinations(range(variables), 3))
