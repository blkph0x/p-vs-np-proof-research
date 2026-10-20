"""Exact local tables for the scoped virtual-dimension RM(2,m) construction.

The all-size proof is in REED_MULLER_VIRTUAL_DIMENSION_THEOREM.md. These
functions do not discover a decoder or determine a relaxation's optimum.
"""
from __future__ import annotations

from math import comb


def gaussian_two(dimension: int) -> int:
    """Number of codimension-two subspaces; zero below dimension two."""
    return 0 if dimension < 2 else ((1 << dimension) - 1) * ((1 << dimension) - 2) // 6


def binary_rank(points) -> int:
    basis = {}
    for point in points:
        while point:
            pivot = point.bit_length() - 1
            if pivot not in basis:
                basis[pivot] = point
                break
            point ^= basis[pivot]
    return len(basis)


def raw_atom_numerators(points, virtual_dimension: int) -> list[int]:
    """Formal inclusion-exclusion table, including beyond the proved range.

    A returned negative value is an obstruction, not an accepted probability.
    Bit i of an atom mask specifies that points[i] has value one.
    """
    points = tuple(points)
    if type(virtual_dimension) is not int or virtual_dimension < 3:
        raise ValueError("virtual dimension must be an integer at least three")
    if any(type(x) is not int or x <= 0 for x in points) or len(set(points)) != len(points):
        raise ValueError("scope points must be distinct positive binary vectors")
    values = [
        gaussian_two(virtual_dimension - binary_rank(
            points[i] for i in range(len(points)) if mask >> i & 1))
        for mask in range(1 << len(points))
    ]
    for i in range(len(points)):
        for mask in range(1 << len(points)):
            if not mask >> i & 1:
                values[mask] -= values[mask | (1 << i)]
    return values


def checked_scope_table(points, virtual_dimension: int) -> tuple[int, list[int]]:
    """Return denominator and integer atom masses within the proved range.

    Coordinates are nonpin points; the pin is always one. The theorem
    supplies support and overlap consistency. This function additionally
    checks normalization and nonnegativity, but does not replace that proof.
    """
    points = tuple(points)
    if type(virtual_dimension) is not int or virtual_dimension < 3:
        raise ValueError("virtual dimension must be an integer at least three")
    if len(points) > virtual_dimension + 4:
        raise ValueError("scope exceeds the proved locality of this construction")
    values = raw_atom_numerators(points, virtual_dimension)
    denominator = gaussian_two(virtual_dimension)
    if min(values) < 0 or sum(values) != denominator:
        raise ValueError("formal table failed exact probability checks")
    return denominator, values


def independent_empty_numerator(d: int) -> int:
    """t_d: empty atom on d+4 independent points; t_d=0 for d<2."""
    if d < 2:
        return 0
    polynomial = 32 * d**3 + 120 * d**2 + 76 * d - 33
    numerator = 81 * 3**d - 48 + (-1)**d * polynomial
    quotient, remainder = divmod(numerator, 1536)
    if remainder:
        raise ValueError("closed empty-atom expression is not integral")
    return quotient


def relation_coefficient(d: int, relation_dimension: int, support_size: int) -> int:
    """Coefficient of a relation subspace in the empty-atom expansion."""
    if relation_dimension == 0 and support_size == 0:
        return independent_empty_numerator(d)
    if relation_dimension == 1:
        return (-1)**support_size * independent_empty_numerator(d + 1 - support_size)
    if relation_dimension == 2:
        return (-1)**support_size * (
            independent_empty_numerator(d + 2 - support_size)
            - independent_empty_numerator(d + 1 - support_size))
    if relation_dimension == 3:
        remaining = d + 4 - support_size
        return (-1)**(d + 1) * (comb(remaining, 3) if remaining >= 3 else 0)
    raise ValueError("relation expansion requires dimension zero through three")


def empty_lower_bound(d: int) -> int:
    """Analytic high-rank lower bound for D>=3, in unnormalized units."""
    if d == 3:
        return 0
    if d == 4:
        return 3
    if d == 5:
        return 1
    if d == 6:
        return 14
    if d == 7:
        return 23
    if d < 8:
        raise ValueError("virtual dimension must be at least three")
    bound = (independent_empty_numerator(d)
             - 7 * independent_empty_numerator(d - 2)
             - 7 * (independent_empty_numerator(d - 3)
                    - independent_empty_numerator(d - 4)))
    if d % 2 == 0:
        bound -= comb(d - 2, 3)
    return bound


def first_failure_scope(d: int) -> tuple[tuple[int, ...], int]:
    """A D+5-point scope and negative atom mask, in ambient dimension D+1."""
    if type(d) is not int or d < 3:
        raise ValueError("virtual dimension must be an integer at least three")
    anchor_size = d - 3
    scope = tuple(1 << i for i in range(anchor_size))
    scope += tuple(i << anchor_size for i in range(1, 9))
    return scope, (1 << anchor_size) - 1
