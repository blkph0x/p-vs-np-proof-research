"""Exact minimum-pathwidth order discovery for small mixed instances."""
from __future__ import annotations


def boundary(adj: tuple[int, ...], subset: int) -> int:
    return sum(bool(subset >> v & 1 and adj[v] & ~subset)
               for v in range(len(adj)))


def discover(adj: tuple[int, ...]) -> dict[str, object]:
    """Subset-DP order oracle with a reconstructable optimal order."""
    n = len(adj)
    if n == 0:
        return {"width": 0, "order": [], "subsets": 1, "transitions": 0}
    size = 1 << n
    dp = [n + 1] * size
    choice = [-1] * size
    dp[0] = 0
    boundaries = [boundary(adj, subset) for subset in range(size)]
    transitions = 0
    for subset in range(1, size):
        rest = subset
        best = n + 1
        chosen = -1
        while rest:
            bit = rest & -rest
            prev = subset ^ bit
            value = max(dp[prev], boundaries[subset])
            transitions += 1
            if value < best:
                best, chosen = value, bit.bit_length() - 1
            rest ^= bit
        dp[subset] = best
        choice[subset] = chosen
    subset = size - 1
    reverse = []
    while subset:
        v = choice[subset]
        if v < 0:
            raise AssertionError("missing order predecessor")
        reverse.append(v)
        subset ^= 1 << v
    order = tuple(reversed(reverse))
    return {"width": dp[-1], "order": list(order),
            "subsets": size, "transitions": transitions}


def order_width(adj: tuple[int, ...], order: tuple[int, ...]) -> int:
    subset = 0
    best = 0
    for v in order:
        subset |= 1 << v
        best = max(best, boundary(adj, subset))
    return best
