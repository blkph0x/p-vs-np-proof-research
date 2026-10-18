"""Generate explicit concatenated-code family certificates."""

from __future__ import annotations

from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path

from explicit_code_family import parameters, verify_sampled_transforms

HERE = Path(__file__).resolve().parent


def digest(path):
    return sha256(path.read_bytes()).hexdigest()


def run():
    before = digest(HERE / 'explicit_code_family.py')
    degrees = [7, 8, 9]
    records = []
    for degree in degrees:
        record = verify_sampled_transforms(degree, transform_count=6)
        assert record['parameters'] == parameters(degree)
        records.append(record)
    after = digest(HERE / 'explicit_code_family.py')
    assert before == after
    payload = {
        'status': 'EXPLICIT_CODE_FAMILY_CHECK_PASS',
        'timestamp_utc': datetime.now(timezone.utc).isoformat(),
        'degrees_checked': degrees,
        'records': records,
        'source_hash': before,
        'scope': 'Explicit deterministic concatenated-code certificates; route-specific lower bound only.',
    }
    (HERE / 'EXPLICIT_CODE_FAMILY_RESULTS.json').write_text(
        json.dumps(payload, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({
        'status': payload['status'], 'degrees': degrees,
        'rank_values': [record['parameters']['binary_rank'] for record in records],
        'column_counts': [record['parameters']['columns'] for record in records],
        'state_lower_bounds': [record['parameters']['state_lower_bound'] for record in records],
    }))


if __name__ == '__main__':
    run()
