"""Sparse local tables for the virtual (r+2)-dimensional RM(r,m) witness.

This constructs one requested table; it does not enumerate all scopes or solve
the optimization problem. The proof and scope restrictions are in THEOREM.md.
"""
from fractions import Fraction
from itertools import combinations


def parameters(order):
    if type(order) is not int or order < 1:
        raise ValueError("order must be a positive integer")
    d = 1 << (order + 1)
    return d, (2 * d - 1) * (d - 1) // 3


def raw_numerators(points, order):
    """Permit oversized scopes for negative controls; return sparse atoms."""
    d, denominator = parameters(order)
    points = tuple(sorted(points))
    if any(type(x) is not int or x <= 0 for x in points):
        raise ValueError("coordinates must be positive integers")
    if len(set(points)) != len(points):
        raise ValueError("coordinates must be distinct")
    point_set = set(points)
    lines = {tuple(sorted((a, b, a ^ b))) for a, b in combinations(points, 2)
             if a ^ b in point_set}
    incidences = dict.fromkeys(points, 0)
    for line in lines:
        for a in line:
            incidences[a] += 1
    k = len(points)
    atoms = {(): denominator - (d - 1) * k + k * (k - 1) // 2 - len(lines)}
    atoms.update({(a,): d - k + incidences[a] for a in points})
    for a, b in combinations(points, 2):
        atom = tuple(sorted((a, b, a ^ b))) if a ^ b in point_set else (a, b)
        atoms[atom] = 1
    return atoms, denominator


def checked_table(points, order):
    points = tuple(points)
    d, _ = parameters(order)
    if len(points) > d:
        raise ValueError("scope exceeds the proved locality")
    atoms, denominator = raw_numerators(points, order)
    if any(value < 0 for value in atoms.values()):
        raise ValueError("negative atom")
    if sum(atoms.values()) != denominator:
        raise ValueError("normalization failed")
    return {atom: Fraction(value, denominator) for atom, value in atoms.items() if value}


def first_failure_scope(order):
    d, _ = parameters(order)
    # The anchor has its own coordinate. No two other points differ by it.
    return (1,) + tuple(x << 1 for x in range(1, d + 1))


def objective(order, ambient):
    d, _ = parameters(order)
    if type(ambient) is not int or ambient < order + 2:
        raise ValueError("ambient dimension must be at least order+2")
    reduced = Fraction(3 * ((1 << ambient) - 1), 2 * d - 1)
    return reduced, 1 + reduced, 1 << (ambient - order)
