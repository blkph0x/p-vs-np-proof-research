"""Generate symmetry-certified high-rank family records."""

from __future__ import annotations

from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path

from projective_family import verify_family, closed_form

HERE = Path(__file__).resolve().parent


def digest(path):
    return sha256(path.read_bytes()).hexdigest()


def transform_for(rank_value):
    return tuple((1 << i) | ((1 << (i + 1)) if i + 1 < rank_value else 0)
                 for i in range(rank_value))


def run():
    before = digest(HERE / 'projective_family.py')
    ranks = [4, 5, 6, 7, 8, 12]
    records = []
    for rank_value in ranks:
        expected = closed_form(rank_value)
        checked = verify_family(rank_value, transform_for(rank_value))
        assert checked == expected
        records.append({'rank': rank_value, 'closed_form': expected,
                        'transform': list(transform_for(rank_value))})
    after = digest(HERE / 'projective_family.py')
    assert before == after
    payload = {'status': 'PROJECTIVE_FAMILY_CHECK_PASS',
               'timestamp_utc': datetime.now(timezone.utc).isoformat(),
               'ranks_checked': ranks, 'records': records, 'source_hash': before,
               'scope': 'Exact symmetry family; no hardness or P-versus-NP claim.'}
    (HERE / 'PROJECTIVE_FAMILY_RESULTS.json').write_text(
        json.dumps(payload, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'status': payload['status'], 'ranks': ranks,
                      'rank6_states': records[2]['closed_form']['native_state_count'],
                      'rank12_columns': records[-1]['closed_form']['columns'],
                      'rank12_states': records[-1]['closed_form']['native_state_count']}))


if __name__ == '__main__':
    run()
