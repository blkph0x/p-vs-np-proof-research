"""Closed-form exact family containing every nonzero binary column vector."""

from __future__ import annotations

from exact_oracle import apply, exceptional_stats, rank, score


def rows_from_family(rank_value):
    if type(rank_value) is not int or rank_value < 1:
        raise ValueError('positive rank required')
    n = (1 << rank_value) - 1
    return tuple(sum(1 << column for column in range(n) if (column + 1) >> row & 1)
                 for row in range(rank_value))


def closed_form(rank_value):
    if type(rank_value) is not int or rank_value < 4:
        raise ValueError('the full-rank exceptional proof starts at rank four')
    r = rank_value
    q = (1 << r) - 1 - r - r * (r - 1) // 2
    total = r * (1 << (r - 1))
    excess = total - r * r - 2 * q
    return {'rank': r, 'columns': (1 << r) - 1,
            'objective': [q, excess, total],
            'stats': [q, r, excess, total],
            'native_state_count': 1 << r}


def verify_family(rank_value, transform=None):
    expected = closed_form(rank_value)
    rows = rows_from_family(rank_value)
    if transform is None:
        transform = tuple(1 << i for i in range(rank_value))
    transform = tuple(transform)
    if len(transform) != rank_value or rank(transform) != rank_value:
        raise ValueError('transform must be invertible')
    transformed = apply(rows, transform)
    columns = [sum(((row >> column) & 1) << index for index, row in enumerate(transformed))
               for column in range(expected['columns'])]
    assert sorted(columns) == list(range(1, 1 << rank_value))
    assert list(score(transformed, expected['columns'])) == expected['objective']
    assert list(exceptional_stats(transformed, expected['columns'])) == expected['stats']
    return expected
