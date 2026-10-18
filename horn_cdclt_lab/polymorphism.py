"""Finite polymorphism audit for the fixed Horn/affine pair."""
from __future__ import annotations

from itertools import product


H = ((0, 0, 0), (1, 1, 0), (0, 0, 1))
A = ((0, 1, 0, 0), (0, 0, 1, 0), (1, 0, 0, 1), (1, 1, 1, 1))


def apply(table, inputs):
    index = sum((bit & 1) << i for i, bit in enumerate(inputs))
    return (table >> index) & 1


def preserves(relation, arity, table):
    """Test f(R^arity) subseteq R by direct finite enumeration."""
    target = set(relation)
    for rows in product(relation, repeat=arity):
        output = tuple(apply(table, tuple(row[col] for row in rows))
                       for col in range(len(relation[0])))
        if output not in target:
            return False
    return True


def all_operations(arity):
    if arity <= 0:
        raise ValueError("operation arity must be positive")
    table_count = 1 << (1 << arity)
    return range(table_count)


def common_operations(arity):
    return [table for table in all_operations(arity)
            if preserves(H, arity, table) and preserves(A, arity, table)]


def projection_table(arity, position):
    if not 0 <= position < arity:
        raise ValueError(position)
    return sum(((index >> position) & 1) << index for index in range(1 << arity))


def named_operations():
    return {
        "AND": (2, lambda bits: bits[0] & bits[1]),
        "OR": (2, lambda bits: bits[0] | bits[1]),
        "MAJORITY": (3, lambda bits: int(sum(bits) >= 2)),
        "MINORITY_XOR": (3, lambda bits: bits[0] ^ bits[1] ^ bits[2]),
        "CONST_0": (1, lambda bits: 0),
        "CONST_1": (1, lambda bits: 1),
    }


def named_table(arity, function):
    return sum(function(tuple((index >> i) & 1 for i in range(arity))) << index
               for index in range(1 << arity))


def named_preservation_matrix():
    matrix = {}
    for name, (arity, function) in named_operations().items():
        table = named_table(arity, function)
        matrix[name] = {
            "arity": arity,
            "table": table,
            "preserves_H": preserves(H, arity, table),
            "preserves_A": preserves(A, arity, table),
        }
    return matrix


def affine_odd_candidates(arity):
    """All affine operations preserving the odd-parity ternary relation.

    An affine operation is ``c XOR`` the parity of a selected input subset.  On
    three odd-parity rows it returns odd parity exactly when
    ``c XOR (selected_subset_size mod 2) == 1``.
    """
    out = []
    for constant in (0, 1):
        for support in range(1 << arity):
            if constant ^ (support.bit_count() & 1) != 1:
                continue
            table = 0
            for index in range(1 << arity):
                value = constant ^ ((index & support).bit_count() & 1)
                table |= value << index
            out.append((constant, support, table))
    return out


def affine_common_candidates(arity):
    """Affine odd-parity candidates surviving the H disjoint-support condition.

    For affine tables the H condition is equivalent to constant zero and a support
    of exactly one coordinate: a support of size at least two accepts two disjoint
    singleton inputs, while the empty support fails the odd-parity condition.
    """
    return [(constant, support, table) for constant, support, table
            in affine_odd_candidates(arity)
            if constant == 0 and support.bit_count() == 1]
