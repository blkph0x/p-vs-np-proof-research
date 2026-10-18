"""Executable positive-1-in-3 to mixed Horn/affine reduction control."""
from __future__ import annotations

from itertools import combinations, product


HORN_WITNESS = frozenset(((0, 0, 0), (1, 1, 0), (0, 0, 1)))
AFFINE_WITNESS = frozenset(((0, 1, 0, 0), (0, 0, 1, 0),
                            (1, 0, 0, 1), (1, 1, 1, 1)))


def _validate(clauses: tuple[tuple[int, int, int], ...], variables: int) -> None:
    if variables < 0:
        raise ValueError("negative variable count")
    for clause in clauses:
        if len(clause) != 3 or len(set(clause)) != 3:
            raise ValueError("each exact-one clause needs three distinct variables")
        if any(not isinstance(v, int) or v < 0 or v >= variables for v in clause):
            raise ValueError("clause variable outside declared range")


def original_sat(clauses: tuple[tuple[int, int, int], ...], variables: int) -> bool:
    _validate(clauses, variables)
    return any(all(sum(bits[v] for v in clause) == 1 for clause in clauses)
               for bits in product((0, 1), repeat=variables))


def transformed_sat(clauses: tuple[tuple[int, int, int], ...], variables: int) -> bool:
    """Brute-force the transformed instance, including all fresh bridge bits."""
    _validate(clauses, variables)
    bridge_count = 2 * len(clauses)
    for bits in product((0, 1), repeat=variables + bridge_count):
        valid = True
        for index, (x, y, w) in enumerate(clauses):
            z0, z1 = bits[variables + 2 * index: variables + 2 * index + 2]
            if (bits[x], z0, z1) not in HORN_WITNESS:
                valid = False
                break
            if (bits[y], bits[w], z0, z1) not in AFFINE_WITNESS:
                valid = False
                break
        if valid:
            return True
    return False


def all_three_subsets(variables: int) -> tuple[tuple[int, int, int], ...]:
    return tuple(combinations(range(variables), 3))
