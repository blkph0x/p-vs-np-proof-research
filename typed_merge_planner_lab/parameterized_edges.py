"""Parameterized affine/cardinality edges for the typed planner.

The affine+cardinality pair contains binary-code minimum distance.  This
module does not weaken that hardness statement.  It exposes two explicit
parameterized routes for a supplied generator matrix:

* enumerate all nonzero messages when the row-space dimension k is small;
* enumerate coordinate supports up to a supplied distance d.  The latter is
  an XP bound O(n**d poly(k,n)), not an FPT claim.
"""
from __future__ import annotations

from dataclasses import dataclass
from itertools import combinations
from math import comb
from typing import Iterable


def _validate_matrix(matrix: Iterable[Iterable[int]]) -> tuple[tuple[int, ...], int]:
    rows = tuple(tuple(row) for row in matrix)
    n = len(rows[0]) if rows else 0
    if any(len(row) != n for row in rows):
        raise ValueError("generator rows must be rectangular")
    if any(bit not in (0, 1) for row in rows for bit in row):
        raise ValueError("generator entries must be binary")
    return rows, n


def _row_bits(rows: tuple[tuple[int, ...], ...]) -> tuple[int, ...]:
    return tuple(sum(bit << i for i, bit in enumerate(row)) for row in rows)


def _basis(rows: tuple[int, ...], n: int) -> tuple[int, ...]:
    """Return an independent row basis, with pivots in descending order."""
    basis: list[int] = []
    for row in rows:
        value = row
        for pivot in basis:
            value = min(value, value ^ pivot)
        if value:
            pivot = value.bit_length() - 1
            insert = 0
            while insert < len(basis) and basis[insert].bit_length() - 1 > pivot:
                insert += 1
            basis.insert(insert, value)
            for i, other in enumerate(basis):
                if i != insert and ((other >> pivot) & 1):
                    basis[i] = other ^ value
    return tuple(basis)


def _null_vector(equations: Iterable[int], variables: int) -> int | None:
    """Return a nonzero vector in the homogeneous nullspace, if one exists."""
    rows = [equation for equation in equations if equation]
    pivots: dict[int, int] = {}
    pivot_row = 0
    for column in range(variables - 1, -1, -1):
        pivot = next((i for i in range(pivot_row, len(rows))
                      if (rows[i] >> column) & 1), None)
        if pivot is None:
            continue
        rows[pivot_row], rows[pivot] = rows[pivot], rows[pivot_row]
        for i in range(len(rows)):
            if i != pivot_row and ((rows[i] >> column) & 1):
                rows[i] ^= rows[pivot_row]
        pivots[column] = pivot_row
        pivot_row += 1
    free = [column for column in range(variables) if column not in pivots]
    if not free:
        return None
    vector = 1 << free[0]
    # Rows are reduced, so each pivot equation determines its pivot from the
    # chosen free variables.  There are no right-hand sides in this system.
    for column, row in sorted(pivots.items()):
        if (rows[row] & vector).bit_count() & 1:
            vector |= 1 << column
    return vector


def _word(basis: tuple[int, ...], message: int) -> int:
    value = 0
    for i, row in enumerate(basis):
        if message >> i & 1:
            value ^= row
    return value


def _matrix_certificate(matrix, basis, n, distance, word, message, *, method, **extra):
    return {"method": method, "n": n, "input_rows": [list(row) for row in matrix],
            "row_space_dimension": len(basis), "basis_rows": list(basis),
            "distance": distance, "word": word, "message": message, **extra}


def minimum_distance_by_dimension(matrix: Iterable[Iterable[int]]) -> dict[str, object]:
    """Find the exact nonzero codeword of minimum weight by message enumeration."""
    matrix, n = _validate_matrix(matrix)
    basis = _basis(_row_bits(matrix), n)
    k = len(basis)
    if not k:
        return _matrix_certificate(matrix, basis, n, None, None, None,
                                   method="DIMENSION_ENUMERATION", status="ZERO_CODE",
                                   enumerated_messages=0)
    best = None
    for message in range(1, 1 << k):
        word = _word(basis, message)
        candidate = (word.bit_count(), message, word)
        if best is None or candidate < best:
            best = candidate
    distance, message, word = best
    return _matrix_certificate(matrix, basis, n, distance, word, message,
                               method="DIMENSION_ENUMERATION", status="EXACT",
                               enumerated_messages=(1 << k) - 1)


def minimum_distance_by_weight(matrix: Iterable[Iterable[int]], max_distance: int) -> dict[str, object]:
    """Search supports up to max_distance, returning an exact witness or a bound."""
    matrix, n = _validate_matrix(matrix)
    if type(max_distance) is not int or max_distance < 0:
        raise ValueError("max_distance must be a nonnegative integer")
    basis = _basis(_row_bits(matrix), n)
    k = len(basis)
    checked = 0
    if not k:
        return _matrix_certificate(matrix, basis, n, None, None, None,
                                   method="DISTANCE_SUPPORT_ENUMERATION", status="ZERO_CODE",
                                   max_distance=max_distance, supports_checked=0)
    for size in range(1, min(max_distance, n) + 1):
        for support in combinations(range(n), size):
            checked += 1
            support_set = set(support)
            equations = []
            for coordinate in range(n):
                if coordinate in support_set:
                    continue
                equations.append(sum(((row >> coordinate) & 1) << i
                                     for i, row in enumerate(basis)))
            message = _null_vector(equations, k)
            if message is None:
                continue
            word = _word(basis, message)
            weight = word.bit_count()
            if 0 < weight <= max_distance:
                return _matrix_certificate(
                    matrix, basis, n, weight, word, message,
                    method="DISTANCE_SUPPORT_ENUMERATION", status="EXACT",
                    max_distance=max_distance, support=list(support),
                    supports_checked=checked)
    return _matrix_certificate(
        matrix, basis, n, None, None, None,
        method="DISTANCE_SUPPORT_ENUMERATION", status="CERTIFIED_ABOVE_BOUND",
        max_distance=max_distance, lower_bound=max_distance + 1,
        supports_checked=checked)


def parameterized_pair_status(type_a: str, type_b: str, *, code_dimension: int | None = None,
                              code_length: int | None = None,
                              distance_bound: int | None = None) -> dict[str, object]:
    """Return conservative planner metadata for the affine/cardinality edge."""
    if {type_a, type_b} != {"AFFINE", "CARDINALITY"}:
        return {"route": "NOT_THIS_HARD_PAIR", "cost": "not-applicable"}
    if code_dimension is not None:
        if type(code_dimension) is not int or code_dimension < 0:
            raise ValueError("code_dimension must be a nonnegative integer")
        return {"route": "PARAMETERIZED_DIMENSION_ENUMERATION", "parameter": "k",
                "k": code_dimension, "message_branches": max(0, (1 << code_dimension) - 1),
                "cost": "2^k * poly(n,k)"}
    if distance_bound is not None:
        if type(distance_bound) is not int or distance_bound < 0:
            raise ValueError("distance_bound must be a nonnegative integer")
        if code_length is None:
            return {"route": "XP_DISTANCE_REQUIRES_LENGTH", "parameter": "d",
                    "cost": "unknown-without-n"}
        if type(code_length) is not int or code_length < 0:
            raise ValueError("code_length must be a nonnegative integer")
        supports = sum(comb(code_length, size)
                       for size in range(min(distance_bound, code_length) + 1))
        return {"route": "XP_DISTANCE_SUPPORT_ENUMERATION", "parameter": "d",
                "d": distance_bound, "n": code_length, "supports": supports,
                "cost": "O(sum_{s<=d} C(n,s) * poly(n,k))"}
    return {"route": "KNOWN_NP_HARD", "reason": "MINIMUM_DISTANCE",
            "cost": "superpolynomial-unless-parameterized"}
