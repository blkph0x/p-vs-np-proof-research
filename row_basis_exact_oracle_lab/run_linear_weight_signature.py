"""Generate exact signature records for the explicit code families."""

from __future__ import annotations

from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path

from explicit_code_family import generate_columns, parameters
from linear_weight_signature import minimum_positive_rows_for_target, signature

HERE = Path(__file__).resolve().parent


def digest(path):
    return sha256(path.read_bytes()).hexdigest()


def run():
    before = {name: digest(HERE / name) for name in
              ('explicit_code_family.py', 'linear_weight_signature.py')}
    degrees = [7, 8, 9]
    records = []
    for degree in degrees:
        spec = parameters(degree)
        _, rows = generate_columns(degree)
        weights = [1] * len(rows)
        aggregated = signature(rows, spec['binary_rank'], weights)
        minimum = minimum_positive_rows_for_target(rows, spec['binary_rank'], weights)
        assert len(rows) == spec['columns']
        assert len(aggregated) == len(rows) == minimum
        records.append({'field_degree': degree, 'binary_rank': spec['binary_rank'],
                        'columns': len(rows), 'distinct_signature_entries': len(aggregated),
                        'minimum_positive_rows': minimum})
    after = {name: digest(HERE / name) for name in before}
    assert before == after
    payload = {
        'status': 'LINEAR_WEIGHT_SIGNATURE_CHECK_PASS',
        'timestamp_utc': datetime.now(timezone.utc).isoformat(),
        'degrees_checked': degrees,
        'records': records,
        'source_hashes_before': before,
        'source_hashes_after': after,
        'scope': 'Exact full-objective equality for homogeneous nonnegative linear encodings.',
    }
    (HERE / 'LINEAR_WEIGHT_SIGNATURE_RESULTS.json').write_text(
        json.dumps(payload, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'status': payload['status'], 'degrees': degrees,
                      'minimum_positive_rows': [record['minimum_positive_rows'] for record in records]}))


if __name__ == '__main__':
    run()
