"""A polynomial-size XOR/AND circuit for the Hamming-weight objective.

The circuit first computes each source parity form and then adds those bits to
an L-bit accumulator with ripple carry, where L=max(1,n.bit_length()).  It is
an explicit circuit-computable realization of the nonlinear digit control;
the circuit is not claimed to make the surrounding SAT problem easy.
"""

from __future__ import annotations


def validate_forms(forms, dimension=None):
    forms = tuple(forms)
    if any(type(form) is not int or form < 0 for form in forms):
        raise ValueError('nonnegative integer forms required')
    if dimension is not None and (type(dimension) is not int or dimension < 0 or
                                  any(form.bit_length() > dimension for form in forms)):
        raise ValueError('form exceeds declared dimension')
    return forms


def accumulator_width(form_count):
    if type(form_count) is not int or form_count < 0:
        raise ValueError('nonnegative form count required')
    return max(1, form_count.bit_length())


def parity_bits(forms, assignment):
    forms = validate_forms(forms)
    if type(assignment) is not int or assignment < 0:
        raise ValueError('nonnegative assignment required')
    return tuple((form & assignment).bit_count() & 1 for form in forms)


def ripple_weight_bits(forms, assignment):
    """Evaluate the XOR/AND ripple circuit and return little-endian bits."""
    forms = validate_forms(forms)
    bits = [0] * accumulator_width(len(forms))
    for incoming in parity_bits(forms, assignment):
        carry = incoming
        for position in range(len(bits)):
            old = bits[position]
            bits[position] = old ^ carry       # XOR gate
            carry = old & carry                # AND gate
    return tuple(bits)


def output_value(bits):
    return sum(bit << position for position, bit in enumerate(bits))


def circuit_weight(forms, assignment):
    return output_value(ripple_weight_bits(forms, assignment))


def circuit_gate_counts(forms):
    """Return exact gate counts for a chain-parity plus ripple construction."""
    forms = validate_forms(forms)
    width = accumulator_width(len(forms))
    parity_xor = sum(max(0, form.bit_count() - 1) for form in forms)
    accumulator_xor = len(forms) * width
    accumulator_and = len(forms) * width
    return {'parity_xor_gates': parity_xor,
            'accumulator_xor_gates': accumulator_xor,
            'accumulator_and_gates': accumulator_and,
            'total_gates': parity_xor + accumulator_xor + accumulator_and,
            'output_bits': width}
