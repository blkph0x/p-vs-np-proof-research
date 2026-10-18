"""Independent replay of the nonlinear objective-compression control."""

from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path

from explicit_code_family import generate_columns, parameters

HERE = Path(__file__).resolve().parent


def direct_weight(forms, assignment):
    return sum((form & assignment).bit_count() & 1 for form in forms)


def direct_digits(weight, count):
    return tuple((weight >> bit) & 1 for bit in range(max(1, count.bit_length())))


def digest(path):
    return sha256(path.read_bytes()).hexdigest()


def run():
    payload = json.loads((HERE / 'NONLINEAR_WEIGHT_COMPRESSION_RESULTS.json').read_text(encoding='utf-8'))
    assert payload['status'] == 'NONLINEAR_WEIGHT_COMPRESSION_CHECK_PASS'
    assert payload['degrees_checked'] == [7, 8, 9]

    # Exhaustive independent control on a small form system.
    small_forms = (1, 2, 3, 5, 9, 17, 7)
    for assignment in range(32):
        weight = direct_weight(small_forms, assignment)
        digits = direct_digits(weight, len(small_forms))
        assert sum((1 << bit) * value for bit, value in enumerate(digits)) == weight
        assert int(weight <= 3) == int(sum(digits[bit] << bit for bit in range(len(digits))) <= 3)

    reviewed = []
    sample_assignments = (0, 1, 2, 3, 5, 17, 31)
    for saved in payload['records']:
        degree = saved['field_degree']
        spec = parameters(degree)
        _, forms = generate_columns(degree)
        assert len(forms) == saved['source_forms'] == spec['columns']
        expected_rows = max(1, len(forms).bit_length())
        assert expected_rows == saved['nonlinear_digit_rows']
        for assignment in sample_assignments:
            weight = direct_weight(forms, assignment)
            digits = direct_digits(weight, len(forms))
            assert sum((1 << bit) * value for bit, value in enumerate(digits)) == weight
        reviewed.append({'field_degree': degree, 'source_forms': len(forms),
                         'nonlinear_digit_rows': expected_rows,
                         'sample_assignments': len(sample_assignments)})

    source = {name: digest(HERE / name) for name in
              ('explicit_code_family.py', 'nonlinear_weight_compression.py',
               'run_nonlinear_weight_compression.py', 'NONLINEAR_WEIGHT_COMPRESSION_REVIEW.py')}
    review = {
        'status': 'VERIFIED_INDEPENDENT_NONLINEAR_WEIGHT_COMPRESSION',
        'degrees_checked': [7, 8, 9],
        'rows': reviewed,
        'small_cube_assignments_checked': 32,
        'explicit_sample_assignments_checked': len(sample_assignments),
        'threshold_control': True,
        'source_hashes': source,
        'scope': 'Boundary control only: arbitrary nonlinear objective rows can compress weight digits, but no SAT solver or P-versus-NP claim.',
    }
    (HERE / 'NONLINEAR_WEIGHT_COMPRESSION_REVIEW.json').write_text(
        json.dumps(review, indent=2) + '\n', encoding='utf-8')
    (HERE / 'NONLINEAR_WEIGHT_COMPRESSION_REVIEW.md').write_text(
        '# Independent nonlinear compression review\n\n'
        'A separate implementation exhaustively checks the binary-digit identity '
        'on 32 assignments and samples seven assignments from each k=7, 8 and 9 '
        'explicit family. The exact objective is recovered with 14, 16 and 18 '
        'nonlinear digit rows. A one-row threshold control is also checked. This '
        'is a scope boundary, not a solver or P-versus-NP result: row evaluation '
        'still contains the underlying source-form computation.\n', encoding='utf-8')
    print(json.dumps({'status': review['status'], 'degrees': review['degrees_checked'],
                      'nonlinear_digit_rows': [row['nonlinear_digit_rows'] for row in reviewed],
                      'small_cube_assignments': 32}))


if __name__ == '__main__':
    run()
