"""Generate natural-generator objective obstruction certificates."""

from __future__ import annotations

from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path

from explicit_objective_pullback import classify_natural_map

HERE = Path(__file__).resolve().parent


def digest(path):
    return sha256(path.read_bytes()).hexdigest()


def run():
    before = {name: digest(HERE / name) for name in
              ('explicit_code_family.py', 'explicit_objective_pullback.py')}
    degrees = [7, 8, 9]
    records = [classify_natural_map(degree) for degree in degrees]
    after = {name: digest(HERE / name) for name in before}
    assert before == after
    payload = {
        'status': 'EXPLICIT_OBJECTIVE_PULLBACK_CHECK_PASS',
        'timestamp_utc': datetime.now(timezone.utc).isoformat(),
        'degrees_checked': degrees,
        'records': records,
        'source_hashes_before': before,
        'source_hashes_after': after,
        'scope': 'Natural free-message generator map only; constrained/nonlinear maps remain open.',
    }
    (HERE / 'EXPLICIT_OBJECTIVE_PULLBACK_RESULTS.json').write_text(
        json.dumps(payload, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'status': payload['status'], 'degrees': degrees,
                      'defects': [record['defect'] for record in records],
                      'pairs': [record['pair'] for record in records]}))


if __name__ == '__main__':
    run()
