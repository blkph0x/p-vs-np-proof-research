"""Budgeted row-basis descent that optimizes exceptional rank first."""

from __future__ import annotations

import random


def validate(rows, n):
    if type(n) is not int or n < 0 or type(rows) not in (list, tuple):
        raise ValueError('invalid dimensions')
    rows = tuple(rows)
    if any(type(row) is not int or row < 0 or row.bit_length() > n for row in rows):
        raise ValueError('invalid binary row')
    return rows


def rank(values):
    pivots = {}
    for value in values:
        while value:
            pivot = value.bit_length() - 1
            if pivot in pivots:
                value ^= pivots[pivot]
            else:
                pivots[pivot] = value
                break
    return len(pivots)


def apply(rows, transform):
    return tuple(_xor_selected(rows, mask) for mask in transform)


def _xor_selected(rows, mask):
    value = 0
    for index, row in enumerate(rows):
        if mask >> index & 1:
            value ^= row
    return value


def objective(rows, n):
    rows = validate(rows, n)
    columns = [sum(((row >> column) & 1) << index for index, row in enumerate(rows))
               for column in range(n)]
    exceptional = [column for column in columns if column.bit_count() > 2]
    return (rank(exceptional), len(exceptional),
            sum(max(0, column.bit_count() - 2) for column in columns),
            sum(column.bit_count() for column in columns))


def verify(rows, n, result):
    try:
        original = validate(rows, n)
        transform = tuple(result['row_transform'])
        if len(transform) != len(original) or rank(transform) != len(original):
            raise ValueError('singular transform')
        transformed = apply(original, transform)
        expected = objective(transformed, n)
        if list(transformed) != result['transformed_rows'] or list(expected) != result['objective']:
            raise ValueError('certificate mismatch')
        return {'valid': True, 'errors': [], 'objective': list(expected)}
    except (ValueError, KeyError, TypeError, IndexError):
        return {'valid': False, 'errors': ['malformed or inconsistent certificate']}


def discover(rows, n, *, max_candidate_evaluations=30000, max_restarts=31,
             restart_moves=8, seed=20261018):
    original = validate(rows, n)
    if any(type(value) is not int or value < 0 for value in
           (max_candidate_evaluations, max_restarts, restart_moves)):
        raise ValueError('nonnegative limits required')
    if max_candidate_evaluations < 1 or type(seed) is not int:
        raise ValueError('invalid budget or seed')
    r = len(original)
    rng = random.Random(seed)
    best_rows = list(original)
    best_transform = [1 << index for index in range(r)]
    best_score = objective(best_rows, n)
    evaluations = 1
    local_minimum = False
    termination = 'RESTART_LIMIT'
    for restart in range(max_restarts + 1):
        if restart:
            if evaluations >= max_candidate_evaluations:
                termination = 'EVALUATION_LIMIT'; break
            current_rows, current_transform = list(best_rows), list(best_transform)
            for _ in range(restart_moves):
                destination = rng.randrange(r) if r else 0
                source = rng.randrange(r - 1) if r > 1 else 0
                if r > 1 and source >= destination:
                    source += 1
                if r > 1:
                    current_rows[destination] ^= current_rows[source]
                    current_transform[destination] ^= current_transform[source]
            score = objective(current_rows, n); evaluations += 1
        else:
            current_rows, current_transform, score = list(original), [1 << i for i in range(r)], best_score
        while True:
            chosen = None
            complete = True
            for destination in range(r):
                for source in range(r):
                    if destination == source:
                        continue
                    if evaluations >= max_candidate_evaluations:
                        complete = False; break
                    candidate_rows = list(current_rows)
                    candidate_transform = list(current_transform)
                    candidate_rows[destination] ^= candidate_rows[source]
                    candidate_transform[destination] ^= candidate_transform[source]
                    candidate_score = objective(candidate_rows, n)
                    evaluations += 1
                    key = (candidate_score, destination, source)
                    if candidate_score < score and (chosen is None or key < chosen[0]):
                        chosen = (key, candidate_rows, candidate_transform, candidate_score)
                if not complete:
                    break
            if chosen is None:
                if complete:
                    local_minimum = True
                else:
                    termination = 'EVALUATION_LIMIT'
                break
            _, current_rows, current_transform, score = chosen
        if score < best_score:
            best_rows, best_transform, best_score = list(current_rows), list(current_transform), score
        if termination == 'EVALUATION_LIMIT':
            break
    result = {'schema': 'rank_aware_discovery_v1', 'n': n, 'row_count': r,
              'row_transform': list(best_transform), 'transformed_rows': list(best_rows),
              'objective': list(best_score), 'limits': {
                  'max_candidate_evaluations': max_candidate_evaluations,
                  'max_restarts': max_restarts, 'restart_moves': restart_moves},
              'seed': seed, 'candidate_evaluations': evaluations,
              'termination': termination, 'global_optimum_claimed': False,
              'best_is_local_minimum': local_minimum}
    result['verification'] = verify(original, n, result)
    if not result['verification']['valid']:
        raise ArithmeticError(result['verification'])
    return result
