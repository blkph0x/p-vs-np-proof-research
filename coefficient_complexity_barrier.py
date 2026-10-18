"""A source-bound complexity barrier for exact coefficient queries.

The compact product is a product of binomials with binary exponents.  The
X3C encoder below is parsimonious: its target coefficient is exactly the
number of exact covers.  It is a theorem about this query language, not a
claim that all algebraic SAT algorithms have been excluded.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class X3CCoefficientInstance:
    universe_size: int
    triples: tuple[tuple[int, int, int], ...]
    base: int
    exponents: tuple[int, ...]
    target: int


def encode_x3c(universe_size: int, triples) -> X3CCoefficientInstance:
    """Encode an explicit X3C instance as ``prod_i (1+z**e_i)``.

    The base is m+1, where m is the number of triples.  Consequently every
    digit sum is below the base, so equality with the all-ones target has no
    carries and is equivalent to exact coverage.
    """
    if type(universe_size) is not int or universe_size < 0 or universe_size % 3:
        raise ValueError("universe size must be a nonnegative multiple of three")
    canonical: list[tuple[int, int, int]] = []
    for triple in triples:
        values = tuple(triple)
        if len(values) != 3 or any(type(v) is not int for v in values):
            raise ValueError("every set must contain three integer elements")
        if len(set(values)) != 3 or any(v < 0 or v >= universe_size for v in values):
            raise ValueError("triple elements must be distinct and in range")
        canonical.append(tuple(sorted(values)))
    base = len(canonical) + 1
    powers = tuple(base ** i for i in range(universe_size))
    exponents = tuple(sum(powers[i] for i in triple) for triple in canonical)
    target = sum(powers)
    return X3CCoefficientInstance(universe_size, tuple(canonical), base,
                                  exponents, target)


def exact_cover(instance: X3CCoefficientInstance, selection: int) -> bool:
    if type(selection) is not int or selection < 0 or selection >> len(instance.triples):
        raise ValueError("selection is outside the instance")
    counts = [0] * instance.universe_size
    for index, triple in enumerate(instance.triples):
        if selection >> index & 1:
            for element in triple:
                counts[element] += 1
    return all(count == 1 for count in counts)


def exact_cover_count(instance: X3CCoefficientInstance) -> int:
    return sum(exact_cover(instance, selection)
               for selection in range(1 << len(instance.triples)))


def binomial_coefficient(factors, target: int) -> int:
    """Compute one coefficient by exact sparse dynamic programming."""
    if type(target) is not int or target < 0:
        raise ValueError("target must be a nonnegative integer")
    table = {0: 1}
    for factor in factors:
        if (type(factor) is not tuple or len(factor) != 2 or
                any(type(value) is not int or value < 0 for value in factor)):
            raise ValueError("factors must be pairs of nonnegative integers")
        left, right = factor
        updated = {}
        for exponent, count in table.items():
            if exponent + left <= target:
                updated[exponent + left] = updated.get(exponent + left, 0) + count
            if exponent + right <= target:
                updated[exponent + right] = updated.get(exponent + right, 0) + count
        table = updated
    return table.get(target, 0)


def encoded_coefficient(instance: X3CCoefficientInstance) -> int:
    return binomial_coefficient(tuple((0, exponent) for exponent in instance.exponents),
                                instance.target)


def coefficient_bit_bound(factor_count: int) -> int:
    """A selected-product coefficient has at most m+1 binary bits."""
    if type(factor_count) is not int or factor_count < 0:
        raise ValueError("factor count must be a nonnegative integer")
    return factor_count + 1

