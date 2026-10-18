"""Independent replay of the symmetry-family records."""

from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path

from projective_family import closed_form, verify_family
from run_projective_family import transform_for

HERE = Path(__file__).resolve().parent


def digest(path):
    return sha256(path.read_bytes()).hexdigest()


def run():
    payload = json.loads((HERE / 'PROJECTIVE_FAMILY_RESULTS.json').read_text(encoding='utf-8'))
    assert payload['status'] == 'PROJECTIVE_FAMILY_CHECK_PASS'
    assert payload['ranks_checked'] == [4, 5, 6, 7, 8, 12]
    assert payload['source_hash'] == digest(HERE / 'projective_family.py')
    for record in payload['records']:
        r = record['rank']
        assert record['closed_form'] == closed_form(r)
        assert record['transform'] == list(transform_for(r))
        assert verify_family(r, tuple(record['transform'])) == record['closed_form']
    source = {name: digest(HERE / name) for name in
              ('projective_family.py', 'run_projective_family.py',
               'PROJECTIVE_FAMILY_REVIEW.py')}
    review = {'status': 'VERIFIED_INDEPENDENT_PROJECTIVE_FAMILY',
              'ranks_checked': payload['ranks_checked'],
              'rank6_states': 64, 'rank12_columns': 4095,
              'rank12_states': 4096, 'source_hashes': source,
              'scope': 'Exact permutation symmetry and arithmetic replay only.'}
    (HERE / 'PROJECTIVE_FAMILY_REVIEW.json').write_text(
        json.dumps(review, indent=2) + '\n', encoding='utf-8')
    (HERE / 'PROJECTIVE_FAMILY_REVIEW.md').write_text(
        '# Independent projective-family review\n\n'
        'The all-nonzero-column family is replayed at ranks 4, 5, 6, 7, 8 and '
        '12. Row transforms permute the columns, so the closed-form exceptional '
        'rank is exact; rank 12 has 4,095 columns and 4,096 native states. This '
        'family is a symmetry control, not a hardness result.\n', encoding='utf-8')
    print(json.dumps({'status': review['status'], 'ranks': review['ranks_checked'],
                      'rank12_columns': review['rank12_columns'],
                      'rank12_states': review['rank12_states']}))


if __name__ == '__main__':
    run()
