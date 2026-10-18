"""A boundary control for unrestricted nonlinear objective maps.

Given source forms whose Boolean values have Hamming weight ``h(u)``, define
one nonlinear row for each binary digit of ``h`` and assign it weight ``2**j``.
The resulting weighted sum equals ``h`` exactly, but evaluating a row still
requires the underlying forms.  This is a control against overextending the
Walsh lower bounds to arbitrary nonlinear encodings.
"""

from __future__ import annotations


def validate_forms(forms):
    forms = tuple(forms)
    if any(type(form) is not int or form < 0 for form in forms):
        raise ValueError('nonnegative integer forms required')
    return forms


def source_weight(forms, assignment):
    forms = validate_forms(forms)
    return sum((form & assignment).bit_count() & 1 for form in forms)


def digit_count(form_count):
    if type(form_count) is not int or form_count < 0:
        raise ValueError('nonnegative form count required')
    return max(1, form_count.bit_length())


def nonlinear_row_values(forms, assignment):
    """Return the nonlinear binary-digit row values for one assignment."""
    weight = source_weight(forms, assignment)
    return tuple((weight >> bit) & 1 for bit in range(digit_count(len(tuple(forms)))))


def compressed_objective(forms, assignment):
    values = nonlinear_row_values(forms, assignment)
    return sum((1 << bit) * value for bit, value in enumerate(values))


def threshold_row(forms, assignment, threshold):
    """One nonlinear decision row for the threshold ``source_weight <= threshold``."""
    if type(threshold) is not int or threshold < 0:
        raise ValueError('nonnegative integer threshold required')
    return int(source_weight(forms, assignment) <= threshold)
