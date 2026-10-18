"""Walsh-signature equality for homogeneous linear additive costs."""

from __future__ import annotations


def validate(rows, dimension, weights):
    if type(dimension) is not int or dimension < 0:
        raise ValueError('nonnegative dimension required')
    rows, weights = tuple(rows), tuple(weights)
    if len(rows) != len(weights):
        raise ValueError('one weight per row required')
    if any(type(row) is not int or row < 0 or row.bit_length() > dimension for row in rows):
        raise ValueError('row exceeds dimension')
    if any(type(weight) is not int or weight < 0 for weight in weights):
        raise ValueError('nonnegative integer weights required')
    return rows, weights


def signature(rows, dimension, weights):
    """Aggregate positive costs by their nonzero binary linear functional."""
    rows, weights = validate(rows, dimension, weights)
    result = {}
    for row, weight in zip(rows, weights):
        if row and weight:
            result[row] = result.get(row, 0) + weight
    return result


def objective(rows, weights, assignment):
    return sum(weight * ((row & assignment).bit_count() & 1)
               for row, weight in zip(rows, weights))


def exact_signature_equality(rows_a, weights_a, rows_b, weights_b, dimension):
    left = signature(rows_a, dimension, weights_a)
    right = signature(rows_b, dimension, weights_b)
    return left == right


def signature_difference(rows_a, weights_a, rows_b, weights_b, dimension):
    left = signature(rows_a, dimension, weights_a)
    right = signature(rows_b, dimension, weights_b)
    keys = sorted(set(left) | set(right))
    return {key: left.get(key, 0) - right.get(key, 0)
            for key in keys if left.get(key, 0) != right.get(key, 0)}


def minimum_positive_rows_for_target(rows, dimension, weights):
    """Lower bound forced on any nonnegative exact linear-cost lift."""
    return len(signature(rows, dimension, weights))
