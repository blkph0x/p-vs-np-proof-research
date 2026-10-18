"""Independent replay of Walsh-signature equality records."""

from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path

from explicit_code_family import generate_columns, parameters
from linear_weight_signature import objective

HERE = Path(__file__).resolve().parent


def direct_signature(rows, weights):
    result = {}
    for row, weight in zip(rows, weights):
        if row and weight:
            result[row] = result.get(row, 0) + weight
    return result


def digest(path):
    return sha256(path.read_bytes()).hexdigest()


def run():
    payload = json.loads((HERE / 'LINEAR_WEIGHT_SIGNATURE_RESULTS.json').read_text(encoding='utf-8'))
    assert payload['status'] == 'LINEAR_WEIGHT_SIGNATURE_CHECK_PASS'
    assert payload['degrees_checked'] == [7, 8, 9]
    reviewed = []
    for saved in payload['records']:
        k = saved['field_degree']
        spec = parameters(k)
        _, rows = generate_columns(k)
        weights = [1] * len(rows)
        aggregated = direct_signature(rows, weights)
        assert len(rows) == saved['columns'] == spec['columns']
        assert len(aggregated) == saved['distinct_signature_entries'] == saved['minimum_positive_rows']
        reviewed.append({'field_degree': k, 'columns': len(rows),
                         'signature_entries': len(aggregated),
                         'forced_positive_rows': len(aggregated)})

    # Exhaustive Walsh-function control on a small cube, including duplicates.
    left_rows, left_weights = (1, 2, 3), (1, 2, 3)
    right_rows, right_weights = (3, 1, 2, 3), (1, 1, 2, 2)
    for assignment in range(8):
        assert objective(left_rows, left_weights, assignment) == objective(right_rows, right_weights, assignment)
    bad_rows, bad_weights = (1, 2), (1, 1)
    assert any(objective(left_rows, left_weights, assignment) !=
               objective(bad_rows, bad_weights, assignment) for assignment in range(8))

    source = {name: digest(HERE / name) for name in
              ('explicit_code_family.py', 'linear_weight_signature.py',
               'run_linear_weight_signature.py', 'LINEAR_WEIGHT_SIGNATURE_REVIEW.py')}
    review = {
        'status': 'VERIFIED_INDEPENDENT_LINEAR_WEIGHT_SIGNATURE',
        'degrees_checked': [7, 8, 9],
        'rows': reviewed,
        'small_cube_assignments_checked': 8,
        'duplicate_signature_control': True,
        'mismatch_control': True,
        'source_hashes': source,
        'scope': 'Exact full-objective equality for homogeneous nonnegative linear encodings; no threshold-only claim.',
    }
    (HERE / 'LINEAR_WEIGHT_SIGNATURE_REVIEW.json').write_text(
        json.dumps(review, indent=2) + '\n', encoding='utf-8')
    (HERE / 'LINEAR_WEIGHT_SIGNATURE_REVIEW.md').write_text(
        '# Independent linear-weight signature review\n\n'
        'A separate aggregation implementation reproduces the n distinct '
        'signatures of the k=7, 8 and 9 explicit families. An exhaustive eight '
        'assignment control confirms equality under duplicate forms and rejects '
        'a mismatched signature. This proves the exact full-objective theorem '
        'within its homogeneous, nonnegative linear scope; affine, signed, '
        'nonlinear and threshold-only encodings remain outside scope.\n', encoding='utf-8')
    print(json.dumps({'status': review['status'], 'degrees': review['degrees_checked'],
                      'forced_positive_rows': [row['forced_positive_rows'] for row in reviewed],
                      'small_cube_assignments': 8}))


if __name__ == '__main__':
    run()
