"""Walsh signatures for affine binary row costs.

Rows are pairs ``(form, offset)`` representing the affine bit
``(form dot assignment) xor offset``.  The implementation accepts integer
weights, including signed controls; the nonnegative-cost case is the usual
application.
"""

from __future__ import annotations


def validate(rows, dimension, weights):
    if type(dimension) is not int or dimension < 0:
        raise ValueError('nonnegative dimension required')
    rows, weights = tuple(rows), tuple(weights)
    if len(rows) != len(weights):
        raise ValueError('one weight per row required')
    normalized = []
    for row in rows:
        if (not isinstance(row, (tuple, list)) or len(row) != 2 or
                type(row[0]) is not int or row[0] < 0 or
                row[0].bit_length() > dimension or
                type(row[1]) is not int or row[1] not in (0, 1)):
            raise ValueError('rows must be (binary form, bit offset) pairs')
        normalized.append((row[0], row[1]))
    if any(type(weight) is not int for weight in weights):
        raise ValueError('integer weights required')
    return tuple(normalized), weights


def signature(rows, dimension, weights):
    """Return the nonzero Walsh coefficients as alternating row weights.

    For form ``a`` the returned value is
    ``sum(weight * (-1)**offset)`` over all rows with that form.  Zero-weight
    rows and the constant form are omitted from this nonzero signature.
    """
    rows, weights = validate(rows, dimension, weights)
    result = {}
    for (form, offset), weight in zip(rows, weights):
        if form and weight:
            sign = 1 if offset == 0 else -1
            result[form] = result.get(form, 0) + sign * weight
    return {form: value for form, value in result.items() if value}


def full_signature(rows, dimension, weights):
    """Return the Fourier data determining the complete objective function.

    The constant Fourier coefficient is represented by its numerator
    ``sum(weights) - alternating_weight(form=0)``; all nonzero coefficients
    are represented by their alternating weights.  The common factor 1/2 and
    signs are irrelevant for equality.
    """
    rows, weights = validate(rows, dimension, weights)
    total = sum(weights)
    alternating_zero = 0
    nonzero = {}
    for (form, offset), weight in zip(rows, weights):
        sign = 1 if offset == 0 else -1
        alternating = sign * weight
        if form == 0:
            alternating_zero += alternating
        elif alternating:
            nonzero[form] = nonzero.get(form, 0) + alternating
    nonzero = {form: value for form, value in nonzero.items() if value}
    return total - alternating_zero, nonzero


def objective(rows, weights, assignment):
    return sum(weight * ((((form & assignment).bit_count() & 1) ^ offset))
               for (form, offset), weight in zip(rows, weights))


def exact_signature_equality(rows_a, weights_a, rows_b, weights_b, dimension):
    return full_signature(rows_a, dimension, weights_a) == full_signature(
        rows_b, dimension, weights_b)


def signature_difference(rows_a, weights_a, rows_b, weights_b, dimension):
    left_constant, left = full_signature(rows_a, dimension, weights_a)
    right_constant, right = full_signature(rows_b, dimension, weights_b)
    keys = sorted(set(left) | set(right))
    return {
        'constant_numerator': left_constant - right_constant,
        'nonzero': {key: left.get(key, 0) - right.get(key, 0)
                    for key in keys if left.get(key, 0) != right.get(key, 0)},
    }


def minimum_nonzero_rows_for_target(rows, dimension, weights):
    """Lower bound for any exact affine representation of this target.

    Each row contributes to only one Walsh form, so every nonzero target
    signature entry needs at least one nonzero-weight candidate row.  This is
    a row-count bound; for nonnegative weights those rows are positive
    cost-bearing rows.
    """
    return len(signature(rows, dimension, weights))
