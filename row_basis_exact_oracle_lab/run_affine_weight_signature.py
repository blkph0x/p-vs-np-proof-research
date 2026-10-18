"""Generate affine Walsh-signature records for the explicit code families."""

from __future__ import annotations

from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path

from affine_weight_signature import minimum_nonzero_rows_for_target, signature
from explicit_code_family import generate_columns, parameters

HERE = Path(__file__).resolve().parent


def digest(path):
    return sha256(path.read_bytes()).hexdigest()


def run():
    source_names = ('explicit_code_family.py', 'affine_weight_signature.py')
    before = {name: digest(HERE / name) for name in source_names}
    degrees = [7, 8, 9]
    records = []
    for degree in degrees:
        spec = parameters(degree)
        _, rows = generate_columns(degree)
        affine_rows = [(row, 0) for row in rows]
        weights = [1] * len(rows)
        aggregated = signature(affine_rows, spec['binary_rank'], weights)
        minimum = minimum_nonzero_rows_for_target(
            affine_rows, spec['binary_rank'], weights)
        assert len(rows) == spec['columns']
        assert len(aggregated) == len(rows) == minimum
        records.append({'field_degree': degree,
                        'binary_rank': spec['binary_rank'],
                        'columns': len(rows),
                        'distinct_signature_entries': len(aggregated),
                        'minimum_nonzero_rows': minimum})
    after = {name: digest(HERE / name) for name in source_names}
    assert before == after
    payload = {
        'status': 'AFFINE_WEIGHT_SIGNATURE_CHECK_PASS',
        'timestamp_utc': datetime.now(timezone.utc).isoformat(),
        'degrees_checked': degrees,
        'records': records,
        'source_hashes_before': before,
        'source_hashes_after': after,
        'scope': 'Exact full-objective equality for affine integer-weight row encodings; signed controls included.',
    }
    (HERE / 'AFFINE_WEIGHT_SIGNATURE_RESULTS.json').write_text(
        json.dumps(payload, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'status': payload['status'], 'degrees': degrees,
                      'minimum_nonzero_rows': [
                          record['minimum_nonzero_rows'] for record in records]}))


if __name__ == '__main__':
    run()
