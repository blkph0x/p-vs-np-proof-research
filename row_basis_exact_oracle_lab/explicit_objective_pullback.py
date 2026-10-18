"""Check the natural generator map against additive unary objectives."""

from __future__ import annotations

from pathlib import Path
import sys

from explicit_code_family import digest_columns, generate_columns, parameters

HERE = Path(__file__).resolve().parent
PARENT = HERE.parent / 'objective_pullback_limits'
if str(PARENT) not in sys.path:
    sys.path.insert(0, str(PARENT))


def classify_natural_map(degree):
    """Return a compact obstruction for T(message)=the explicit codeword.

    The rows are output-coordinate masks, so each row is one binary linear
    functional of the free message bits.  A positive Hamming weight on an
    overlapping row creates a three-assignment additivity defect.
    """
    from objective_pullback import classify, verify

    spec = parameters(degree)
    modulus, rows = generate_columns(degree)
    weights = [1] * len(rows)
    certificate = classify(rows, spec['binary_rank'], weights)
    checked = verify(rows, spec['binary_rank'], weights, certificate)
    if certificate.get('status') != 'EXACT' or certificate.get('additive'):
        raise AssertionError('natural codeword map unexpectedly additive')
    if certificate.get('defect', 0) <= 0 or not checked.get('valid'):
        raise AssertionError('missing objective defect certificate')
    return {
        'field_degree': degree,
        'binary_rank': spec['binary_rank'],
        'columns': len(rows),
        'column_digest': digest_columns(rows, spec['binary_rank']),
        'pair': certificate['pair'],
        'values': certificate['values'],
        'defect': certificate['defect'],
        'verification': checked,
        'input_hash': certificate['input_hash'],
    }
