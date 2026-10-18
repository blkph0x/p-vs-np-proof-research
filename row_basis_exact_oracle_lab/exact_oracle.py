"""Exact small-rank row-basis oracle for binary column-weight objectives."""

from __future__ import annotations

from functools import reduce


def validate(rows, n):
    if type(n) is not int or n < 0:
        raise ValueError('nonnegative coordinate count required')
    if type(rows) not in (list, tuple):
        raise ValueError('row sequence required')
    checked = tuple(rows)
    if any(type(row) is not int or row < 0 or row.bit_length() > n for row in checked):
        raise ValueError('invalid binary row')
    return checked


def rank(vectors):
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


def transforms(r):
    """Yield every invertible r-by-r binary row transform."""
    if type(r) is not int or r < 0 or r > 8:
        raise ValueError('transform enumeration supports ranks 0 through 8')
    values = range(1 << r)

    def extend(prefix, span):
        if len(prefix) == r:
            yield tuple(prefix)
            return
        for row in values:
            if row in span:
                continue
            next_span = span | {member ^ row for member in span}
            yield from extend(prefix + [row], next_span)

    yield from extend([], {0})


def apply(rows, transform):
    rows = tuple(rows)
    return tuple(reduce(
                     int.__xor__,
                     (rows[j] for j in range(len(rows)) if combination >> j & 1),
                     0)
                 for combination in transform)


def score(rows, n):
    weights = [sum((row >> column) & 1 for row in rows) for column in range(n)]
    return (sum(weight > 2 for weight in weights),
            sum(max(0, weight - 2) for weight in weights), sum(weights))


def exceptional_stats(rows, n):
    """Return (exception count, exceptional-column rank, excess, total weight)."""
    rows = validate(rows, n)
    columns = [sum(((row >> column) & 1) << index for index, row in enumerate(rows))
               for column in range(n)]
    exceptional = [column for column in columns if column.bit_count() > 2]
    return (len(exceptional), rank(exceptional),
            sum(max(0, column.bit_count() - 2) for column in columns),
            sum(column.bit_count() for column in columns))


def exact_optimum(rows, n, *, max_transforms=None):
    rows = validate(rows, n)
    r = len(rows)
    if r > 4 and max_transforms is None:
        raise ValueError('uncapped exact enumeration is limited to rank four')
    if max_transforms is not None and (type(max_transforms) is not int or max_transforms < 1):
        raise ValueError('positive transform cap required')
    best = None
    evaluated = 0
    for transform in transforms(r):
        if max_transforms is not None and evaluated >= max_transforms:
            return {'status': 'UNKNOWN', 'reason': 'transform cap',
                    'transforms_evaluated': evaluated}
        transformed = apply(rows, transform)
        candidate = (score(transformed, n), tuple(transform), transformed)
        evaluated += 1
        if best is None or candidate[:2] < best[:2]:
            best = candidate
    objective, transform, transformed = best
    return {'status': 'EXACT', 'objective': list(objective),
            'row_transform': list(transform), 'transformed_rows': list(transformed),
            'transforms_evaluated': evaluated, 'global_optimality_checked': True}


def exact_parameter_optimum(rows, n, *, max_transforms=None):
    """Minimize exceptional-column rank before count, then tie-break lexicographically."""
    rows = validate(rows, n)
    r = len(rows)
    if r > 4 and max_transforms is None:
        raise ValueError('uncapped exact enumeration is limited to rank four')
    if max_transforms is not None and (type(max_transforms) is not int or max_transforms < 1):
        raise ValueError('positive transform cap required')
    best = None
    evaluated = 0
    for transform in transforms(r):
        if max_transforms is not None and evaluated >= max_transforms:
            return {'status': 'UNKNOWN', 'reason': 'transform cap',
                    'transforms_evaluated': evaluated}
        transformed = apply(rows, transform)
        stats = exceptional_stats(transformed, n)
        candidate = ((stats[1], stats[0], stats[2], stats[3]), tuple(transform), transformed, stats)
        evaluated += 1
        if best is None or candidate[:2] < best[:2]:
            best = candidate
    objective, transform, transformed, stats = best
    return {'status': 'EXACT', 'objective': list(objective), 'stats': list(stats),
            'row_transform': list(transform), 'transformed_rows': list(transformed),
            'transforms_evaluated': evaluated, 'global_optimality_checked': True}


def verify_exact(rows, n, result):
    try:
        rows = validate(rows, n)
        if type(result) is not dict or result.get('status') != 'EXACT':
            return {'valid': False, 'errors': ['missing exact result']}
        transform = tuple(result['row_transform'])
        if len(transform) != len(rows) or rank(transform) != len(rows):
            return {'valid': False, 'errors': ['singular transform']}
        transformed = apply(rows, transform)
        objective = score(transformed, n)
        if list(transformed) != result['transformed_rows'] or list(objective) != result['objective']:
            return {'valid': False, 'errors': ['certificate arithmetic mismatch']}
        optimum = exact_optimum(rows, n)
        if optimum['status'] != 'EXACT' or result['objective'] != optimum['objective']:
            return {'valid': False, 'errors': ['nonoptimal objective']}
        return {'valid': True, 'errors': [], 'transforms_evaluated': optimum['transforms_evaluated']}
    except (ValueError, KeyError, TypeError, IndexError):
        return {'valid': False, 'errors': ['malformed certificate']}
