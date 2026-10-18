"""Generate exact arithmetic records for the probabilistic rank bound."""

from __future__ import annotations

from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path

from exception_rank_bound import theorem_parameters, verify_bound

HERE = Path(__file__).resolve().parent


def digest(path):
    return sha256(path.read_bytes()).hexdigest()


def run():
    before = digest(HERE / 'exception_rank_bound.py')
    ranks = [6, 7, 8, 16, 32]
    records = [dict(verify_bound(r), **theorem_parameters(r)) for r in ranks]
    after = digest(HERE / 'exception_rank_bound.py')
    assert before == after
    payload = {
        'status': 'EXCEPTION_RANK_BOUND_CHECK_PASS',
        'timestamp_utc': datetime.now(timezone.utc).isoformat(),
        'ranks_checked': ranks,
        'records': records,
        'source_hash': before,
        'scope': 'Exact union-bound arithmetic; probabilistic existence theorem for one solver route.',
    }
    (HERE / 'EXCEPTION_RANK_BOUND_RESULTS.json').write_text(
        json.dumps(payload, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'status': payload['status'], 'ranks': ranks,
                      'minimum_rank6_states': records[0]['minimum_native_states'],
                      'rank32_columns': records[-1]['columns'],
                      'rank32_states': records[-1]['minimum_native_states']}))


if __name__ == '__main__':
    run()
