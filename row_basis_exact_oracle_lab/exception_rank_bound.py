"""Elementary probabilistic lower bound for the exceptional-rank route."""

from __future__ import annotations

from fractions import Fraction


def low_weight_count(rank_value):
    """Number of vectors in F_2^r of weight at most two, including zero."""
    if type(rank_value) is not int or rank_value < 0:
        raise ValueError('nonnegative rank required')
    return 1 + rank_value + rank_value * (rank_value - 1) // 2


def union_bound(rank_value, multiplier=16):
    """Exact union-bound upper estimate for the bad random-column event.

    The construction uses m=multiplier*r^2 independent uniform columns.  The
    returned Fraction bounds the probability that some basis and nonzero
    linear functional contain every exceptional column in one hyperplane.
    """
    if type(rank_value) is not int or rank_value < 6:
        raise ValueError('the proved range starts at rank six')
    if type(multiplier) is not int or multiplier < 1:
        raise ValueError('positive integer multiplier required')
    r = rank_value
    low = low_weight_count(r)
    per_pair = Fraction(2 ** (r - 1) + low, 2 ** r)
    matrices = 2 ** (r * r)
    functionals = 2 ** r - 1
    return matrices * functionals * per_pair ** (multiplier * r * r)


def theorem_parameters(rank_value):
    """Return the explicit column and state exponents in the construction."""
    if type(rank_value) is not int or rank_value < 6:
        raise ValueError('the proved range starts at rank six')
    r = rank_value
    columns = 16 * r * r + r
    return {'rank': r, 'random_columns': 16 * r * r,
            'identity_columns': r, 'columns': columns,
            'minimum_native_states': 2 ** r,
            'n_at_most_17_r_squared': columns <= 17 * r * r}


def verify_bound(rank_value):
    """Check the proof inequalities using exact integer/rational arithmetic."""
    r = rank_value
    low = low_weight_count(r)
    # For r >= 6, low <= 3*2^(r-2), hence the per-pair probability <= 7/8.
    assert low <= 3 * 2 ** (r - 2)
    assert 2 * 7 ** 8 < 8 ** 8
    bound = union_bound(r)
    assert bound < 1
    # The simple displayed bound is also strict, without relying on floating point.
    simple = Fraction(2 ** (r * r + r), 2 ** (2 * r * r))
    assert bound < simple
    return {'rank': r, 'low_weight_count': low,
            'union_bound_numerator_bits': bound.numerator.bit_length(),
            'union_bound_denominator_bits': bound.denominator.bit_length(),
            'union_bound_lt_one': True,
            'columns': theorem_parameters(r)['columns'],
            'minimum_native_states': 2 ** r}
