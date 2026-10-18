"""Exact GF(2) information width and small-instance order optimization."""

from __future__ import annotations

from hashlib import sha256
import json


def validate_matrix(matrix):
    if type(matrix) not in (list, tuple) or not matrix:
        raise ValueError("nonempty binary matrix required")
    rows = [list(row) for row in matrix]
    width = len(rows[0])
    if width == 0 or any(len(row) != width for row in rows):
        raise ValueError("rectangular matrix required")
    if any(bit not in (0, 1) for row in rows for bit in row):
        raise ValueError("binary entries required")
    return rows


def column_vectors(matrix):
    matrix = validate_matrix(matrix)
    return [sum(matrix[r][c] << r for r in range(len(matrix)))
            for c in range(len(matrix[0]))]


def vector_rank(vectors):
    basis = {}
    for value in vectors:
        value = int(value)
        while value:
            pivot = value.bit_length() - 1
            if pivot in basis:
                value ^= basis[pivot]
            else:
                basis[pivot] = value
                break
    return len(basis)


def rank_subset(columns, subset):
    return vector_rank(columns[index] for index in range(len(columns)) if subset >> index & 1)


def cut_lambda(columns, subset):
    all_mask = (1 << len(columns)) - 1
    return rank_subset(columns, subset) + rank_subset(columns, all_mask ^ subset) - rank_subset(columns, all_mask)


def order_records(matrix, order):
    matrix = validate_matrix(matrix)
    columns = column_vectors(matrix)
    n = len(columns)
    if type(order) not in (list, tuple) or sorted(order) != list(range(n)):
        raise ValueError("order must be a permutation")
    subset = 0
    records = []
    for position, variable in enumerate(order, 1):
        subset |= 1 << variable
        records.append({'cut': position, 'subset': subset,
                        'rank_past': rank_subset(columns, subset),
                        'rank_future': rank_subset(columns, ((1 << n) - 1) ^ subset),
                        'rank_all': rank_subset(columns, (1 << n) - 1),
                        'lambda': cut_lambda(columns, subset) if position < n else 0})
    width = max((record['lambda'] for record in records[:-1]), default=0)
    return records, width


def optimal_order(matrix):
    """Exact bottleneck DP; exponential in n and intended only as an oracle."""
    matrix = validate_matrix(matrix)
    columns = column_vectors(matrix)
    n = len(columns)
    full = (1 << n) - 1
    best = {0: (0, ())}
    for subset in range(1 << n):
        if subset not in best:
            continue
        prior_width, prior_order = best[subset]
        for variable in range(n):
            bit = 1 << variable
            if subset & bit:
                continue
            next_subset = subset | bit
            cut = 0 if next_subset == full else cut_lambda(columns, next_subset)
            candidate = (max(prior_width, cut), prior_order + (variable,))
            old = best.get(next_subset)
            if old is None or candidate < old:
                best[next_subset] = candidate
    width, order = best[full]
    records, replay_width = order_records(matrix, order)
    assert width == replay_width
    return {'status': 'EXACT', 'order': list(order), 'width': width,
            'records': records, 'state_count': len(best)}


def verify_order_certificate(matrix, result):
    try:
        matrix = validate_matrix(matrix)
        if type(result) is not dict or result.get('status') != 'EXACT':
            return {'valid': False, 'errors': ['missing exact result']}
        expected = optimal_order(matrix)
        records, width = order_records(matrix, result['order'])
        if result['width'] != expected['width']:
            return {'valid': False, 'errors': ['nonoptimal order certificate']}
        if records != result['records'] or width != result['width']:
            return {'valid': False, 'errors': ['cut rank replay mismatch']}
        return {'valid': True, 'width': width, 'order': list(result['order']), 'errors': []}
    except (ValueError, TypeError, IndexError, KeyError):
        return {'valid': False, 'errors': ['malformed certificate']}


def digest(value):
    return sha256(json.dumps(value, sort_keys=True, separators=(',', ':')).encode()).hexdigest()
