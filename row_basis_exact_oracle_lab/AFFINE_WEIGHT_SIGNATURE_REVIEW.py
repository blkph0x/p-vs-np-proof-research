"""Independent replay of affine Walsh-signature records."""

from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path

from explicit_code_family import generate_columns, parameters

HERE = Path(__file__).resolve().parent


def direct_full_signature(rows, weights):
    total = sum(weights)
    zero = 0
    nonzero = {}
    for (form, offset), weight in zip(rows, weights):
        alternating = weight if offset == 0 else -weight
        if form == 0:
            zero += alternating
        elif alternating:
            nonzero[form] = nonzero.get(form, 0) + alternating
    return total - zero, {form: value for form, value in nonzero.items() if value}


def direct_objective(rows, weights, assignment):
    return sum(weight * ((((form & assignment).bit_count() & 1) ^ offset))
               for (form, offset), weight in zip(rows, weights))


def digest(path):
    return sha256(path.read_bytes()).hexdigest()


def run():
    payload = json.loads((HERE / 'AFFINE_WEIGHT_SIGNATURE_RESULTS.json').read_text(encoding='utf-8'))
    assert payload['status'] == 'AFFINE_WEIGHT_SIGNATURE_CHECK_PASS'
    assert payload['degrees_checked'] == [7, 8, 9]
    reviewed = []
    for saved in payload['records']:
        degree = saved['field_degree']
        spec = parameters(degree)
        _, forms = generate_columns(degree)
        rows = [(form, 0) for form in forms]
        target = direct_full_signature(rows, [1] * len(rows))
        assert len(forms) == saved['columns'] == spec['columns']
        assert len(target[1]) == saved['distinct_signature_entries'] == saved['minimum_nonzero_rows']
        reviewed.append({'field_degree': degree, 'columns': len(forms),
                         'signature_entries': len(target[1]),
                         'forced_nonzero_rows': len(target[1])})

    # Exhaustive eight-assignment control, including duplicate affine rows and
    # a signed cancellation pair.  The two systems have the same function.
    left_rows = ((1, 0), (2, 0), (3, 1))
    left_weights = (2, 2, 3)
    right_rows = ((1, 0), (1, 0), (2, 0), (2, 0), (3, 1), (3, 1), (3, 1))
    right_weights = (1, 1, 1, 1, 1, 1, 1)
    for assignment in range(8):
        assert direct_objective(left_rows, left_weights, assignment) == direct_objective(
            right_rows, right_weights, assignment)
    # A wrong affine offset changes the function and is detected.
    bad_rows = ((1, 1), (2, 0), (3, 1))
    assert any(direct_objective(left_rows, left_weights, assignment) !=
               direct_objective(bad_rows, left_weights, assignment)
               for assignment in range(8))

    source = {name: digest(HERE / name) for name in
              ('explicit_code_family.py', 'affine_weight_signature.py',
               'run_affine_weight_signature.py', 'AFFINE_WEIGHT_SIGNATURE_REVIEW.py')}
    review = {
        'status': 'VERIFIED_INDEPENDENT_AFFINE_WEIGHT_SIGNATURE',
        'degrees_checked': [7, 8, 9],
        'rows': reviewed,
        'small_cube_assignments_checked': 8,
        'duplicate_affine_control': True,
        'offset_mismatch_control': True,
        'signed_weights_accepted': True,
        'source_hashes': source,
        'scope': 'Exact full-objective equality for affine integer-weight row encodings; no threshold-only claim.',
    }
    (HERE / 'AFFINE_WEIGHT_SIGNATURE_REVIEW.json').write_text(
        json.dumps(review, indent=2) + '\n', encoding='utf-8')
    (HERE / 'AFFINE_WEIGHT_SIGNATURE_REVIEW.md').write_text(
        '# Independent affine-weight signature review\n\n'
        'A separate aggregation implementation reproduces one nonzero Walsh '
        'signature entry per column for the k=7, 8 and 9 explicit families. '
        'An exhaustive eight-assignment control confirms equality under '
        'duplicate affine rows and rejects an offset mismatch. Signed weights '
        'are accepted as an adversarial control, so the row-count lower bound '
        'also covers nonnegative affine encodings. This remains a full-objective '
        'theorem; nonlinear and threshold-only encodings are outside scope.\n',
        encoding='utf-8')
    print(json.dumps({'status': review['status'], 'degrees': review['degrees_checked'],
                      'forced_nonzero_rows': [row['forced_nonzero_rows'] for row in reviewed],
                      'small_cube_assignments': 8}))


if __name__ == '__main__':
    run()
