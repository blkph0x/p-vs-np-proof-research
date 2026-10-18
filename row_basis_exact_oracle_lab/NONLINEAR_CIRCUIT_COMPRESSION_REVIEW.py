"""Independent replay of the explicit nonlinear circuit construction."""

from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path

from explicit_code_family import generate_columns, parameters

HERE = Path(__file__).resolve().parent


def direct_weight(forms, assignment):
    return sum((form & assignment).bit_count() & 1 for form in forms)


def independent_circuit(forms, assignment):
    width = max(1, len(forms).bit_length())
    accumulator = [0] * width
    for form in forms:
        incoming = (form & assignment).bit_count() & 1
        for position in range(width):
            old = accumulator[position]
            accumulator[position] = (old + incoming) & 1
            incoming = old & incoming
    return sum(bit << position for position, bit in enumerate(accumulator))


def independent_counts(forms):
    width = max(1, len(forms).bit_length())
    parity = sum(max(0, form.bit_count() - 1) for form in forms)
    return {'parity_xor_gates': parity,
            'accumulator_xor_gates': len(forms) * width,
            'accumulator_and_gates': len(forms) * width,
            'total_gates': parity + 2 * len(forms) * width,
            'output_bits': width}


def digest(path):
    return sha256(path.read_bytes()).hexdigest()


def run():
    payload = json.loads((HERE / 'NONLINEAR_CIRCUIT_COMPRESSION_RESULTS.json').read_text(encoding='utf-8'))
    assert payload['status'] == 'NONLINEAR_CIRCUIT_COMPRESSION_CHECK_PASS'
    assert payload['degrees_checked'] == [7, 8, 9]

    small_forms = (1, 2, 3, 5, 9, 17, 7)
    for assignment in range(32):
        assert independent_circuit(small_forms, assignment) == direct_weight(small_forms, assignment)

    reviewed = []
    samples = (0, 1, 2, 3, 5, 17, 31)
    for saved in payload['records']:
        degree = saved['field_degree']
        spec = parameters(degree)
        _, forms = generate_columns(degree)
        assert len(forms) == saved['source_forms'] == spec['columns']
        counts = independent_counts(forms)
        for key, value in counts.items():
            assert saved[key] == value
        for assignment in samples:
            assert independent_circuit(forms, assignment) == direct_weight(forms, assignment)
        reviewed.append({'field_degree': degree, 'source_forms': len(forms),
                         'output_bits': counts['output_bits'],
                         'total_gates': counts['total_gates'],
                         'sample_assignments': len(samples)})

    source = {name: digest(HERE / name) for name in
              ('explicit_code_family.py', 'nonlinear_circuit_compression.py',
               'run_nonlinear_circuit_compression.py',
               'NONLINEAR_CIRCUIT_COMPRESSION_REVIEW.py')}
    review = {
        'status': 'VERIFIED_INDEPENDENT_NONLINEAR_CIRCUIT_COMPRESSION',
        'degrees_checked': [7, 8, 9],
        'rows': reviewed,
        'small_cube_assignments_checked': 32,
        'explicit_sample_assignments_checked': len(samples),
        'source_hashes': source,
        'scope': 'Explicit polynomial-size XOR/AND circuit for Hamming weight; no SAT solver or P-versus-NP claim.',
    }
    (HERE / 'NONLINEAR_CIRCUIT_COMPRESSION_REVIEW.json').write_text(
        json.dumps(review, indent=2) + '\n', encoding='utf-8')
    (HERE / 'NONLINEAR_CIRCUIT_COMPRESSION_REVIEW.md').write_text(
        '# Independent nonlinear circuit-compression review\n\n'
        'A separate ripple-carry implementation exhaustively checks 32 small '
        'assignments and samples seven assignments from every k=7, 8 and 9 '
        'explicit family. It reproduces the exact gate counts and Hamming '
        'weight with 14, 16 and 18 output bits. This confirms a polynomial-size '
        'circuit-computable nonlinear boundary control; integrating the circuit '
        'into a SAT solver remains outside the result.\n', encoding='utf-8')
    print(json.dumps({'status': review['status'], 'degrees': review['degrees_checked'],
                      'output_bits': [row['output_bits'] for row in reviewed],
                      'total_gates': [row['total_gates'] for row in reviewed],
                      'small_cube_assignments': 32}))


if __name__ == '__main__':
    run()
