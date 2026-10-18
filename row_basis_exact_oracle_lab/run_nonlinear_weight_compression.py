"""Generate nonlinear objective-compression boundary records."""

from __future__ import annotations

from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path

from explicit_code_family import generate_columns, parameters
from nonlinear_weight_compression import digit_count

HERE = Path(__file__).resolve().parent


def digest(path):
    return sha256(path.read_bytes()).hexdigest()


def run():
    source_names = ('explicit_code_family.py', 'nonlinear_weight_compression.py')
    before = {name: digest(HERE / name) for name in source_names}
    degrees = [7, 8, 9]
    records = []
    for degree in degrees:
        spec = parameters(degree)
        _, forms = generate_columns(degree)
        rows = digit_count(len(forms))
        assert len(forms) == spec['columns']
        records.append({'field_degree': degree, 'binary_rank': spec['binary_rank'],
                        'source_forms': len(forms), 'nonlinear_digit_rows': rows,
                        'compression_ratio': len(forms) / rows})
    after = {name: digest(HERE / name) for name in source_names}
    assert before == after
    payload = {
        'status': 'NONLINEAR_WEIGHT_COMPRESSION_CHECK_PASS',
        'timestamp_utc': datetime.now(timezone.utc).isoformat(),
        'degrees_checked': degrees,
        'records': records,
        'source_hashes_before': before,
        'source_hashes_after': after,
        'scope': 'Exact identity control for unrestricted nonlinear objective rows; no solver or P-versus-NP claim.',
    }
    (HERE / 'NONLINEAR_WEIGHT_COMPRESSION_RESULTS.json').write_text(
        json.dumps(payload, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'status': payload['status'], 'degrees': degrees,
                      'nonlinear_digit_rows': [r['nonlinear_digit_rows'] for r in records]}))


if __name__ == '__main__':
    run()
