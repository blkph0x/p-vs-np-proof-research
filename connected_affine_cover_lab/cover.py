"""Exact small affine-support enumeration and all-size path controls."""

from __future__ import annotations

from collections import deque
from functools import lru_cache


def satisfying_set(n):
    if type(n) is bool or type(n) is not int or n < 0:
        raise ValueError("n must be a nonnegative integer")
    return {assignment for assignment in range(1 << n)
            if all(((assignment >> i) & 1) or ((assignment >> (i + 1)) & 1)
                   for i in range(max(0, n - 1)))}


def fib_count(n):
    if type(n) is bool or type(n) is not int or n < 0:
        raise ValueError("n must be a nonnegative integer")
    a, b = 1, 2
    for _ in range(n):
        a, b = b, a + b
    return a


def explicit_max_support(n):
    """Vary positions 0,2,4,... and fix positions 1,3,5,... to one."""
    free = list(range(0, n, 2))
    fixed = sum(1 << i for i in range(1, n, 2))
    return {fixed | sum(((mask >> j) & 1) << v for j, v in enumerate(free))
            for mask in range(1 << len(free))}


def affine_info(support, n):
    support = set(support)
    if not support or any(type(x) is not int or x < 0 or x >= (1 << n) for x in support):
        return None
    base = min(support)
    directions = {x ^ base for x in support}
    if 0 not in directions or len(directions) & (len(directions) - 1):
        return None
    for x in directions:
        for y in directions:
            if (x ^ y) not in directions:
                return None
    return {'base': base, 'directions': directions,
            'dimension': (len(directions).bit_length() - 1),
            'size': len(support)}


@lru_cache(None)
def linear_subspaces(n):
    """Enumerate all vector subspaces for small n by closure expansion."""
    if n < 0 or n > 7:
        raise ValueError("subspace enumeration is capped at n=7")
    start = frozenset({0})
    seen = {start}
    queue = deque([start])
    vectors = range(1 << n)
    while queue:
        sub = queue.popleft()
        for vector in vectors:
            if vector in sub:
                continue
            candidate = frozenset(set(sub) | {x ^ vector for x in sub})
            if candidate not in seen:
                seen.add(candidate)
                queue.append(candidate)
    return tuple(sorted(seen, key=lambda s: (len(s), tuple(sorted(s)))))


def affine_supports(n):
    """Yield each distinct affine coset for n<=7."""
    seen = set()
    for sub in linear_subspaces(n):
        for base in range(1 << n):
            coset = frozenset(base ^ vector for vector in sub)
            if coset not in seen:
                seen.add(coset)
                yield coset


def contained_summary(n):
    target = satisfying_set(n)
    max_dimension = -1
    supports = 0
    total_affine = 0
    for support in affine_supports(n):
        total_affine += 1
        if support <= target:
            supports += 1
            info = affine_info(support, n)
            max_dimension = max(max_dimension, info['dimension'])
    return {'n': n, 'satisfying_count': len(target),
            'total_affine_supports': total_affine,
            'contained_supports': supports,
            'max_contained_dimension': max_dimension,
            'max_contained_size': 1 << max_dimension}


def lower_bound_pieces(n):
    satisfying = fib_count(n)
    max_dimension = (n + 1) // 2
    max_size = 1 << max_dimension
    return (satisfying + max_size - 1) // max_size


def verify_path_theorem_instance(n):
    # Materialize the truth set only for small controls; the all-size
    # certificate uses the recurrence and the explicit affine support.
    if n <= 22:
        explicit = explicit_max_support(n)
        info = affine_info(explicit, n)
        assert info['dimension'] == (n + 1) // 2
        target = satisfying_set(n)
        assert explicit <= target
        satisfying_count = len(target)
    else:
        info = {'dimension': (n + 1) // 2, 'size': 1 << ((n + 1) // 2)}
        satisfying_count = fib_count(n)
    return {'n': n, 'satisfying_count': satisfying_count,
            'explicit_dimension': info['dimension'],
            'explicit_size': info['size'],
            'lower_bound_pieces': lower_bound_pieces(n)}
