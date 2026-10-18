"""Independent replay of the saved rank-five exhaustive certificates."""

from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
PARENT = HERE.parent
if str(PARENT) not in sys.path:
    sys.path.insert(0, str(PARENT))
from exact_oracle import apply, exceptional_stats, rank, score
from rank_native_solver import verify_rank_native

GL5_SIZE = 9_999_360


def digest(path):
    return sha256(path.read_bytes()).hexdigest()


def replay(case, candidate, kind):
    rows = tuple(case['rows'])
    transform = tuple(candidate['row_transform'])
    assert len(transform) == 5 and rank(transform) == 5
    transformed = apply(rows, transform)
    stats = exceptional_stats(transformed, case['n'])
    assert list(transformed) == candidate.get('transformed_rows', list(transformed))
    assert candidate['exceptional_rank'] == stats[1]
    assert candidate['exceptional_count'] == stats[0]
    assert candidate['excess'] == stats[2]
    assert candidate['total'] == stats[3]
    if kind == 'count_first':
        assert candidate['objective'] == list(score(transformed, case['n']))
    else:
        assert candidate['objective'] == [stats[1], stats[0], stats[2], stats[3]]
    return list(stats)


def run():
    payload = json.loads((HERE / 'RANK5_RESULTS.json').read_text(encoding='utf-8'))
    assert payload['status'] == 'RANK5_EXHAUSTIVE_ORACLE_PASS'
    assert payload['gl5_size'] == GL5_SIZE and payload['case_count'] == 4
    assert payload['source_hash'] == digest(HERE / 'rank5_exact.cpp')
    reviewed = []
    for record in payload['records']:
        case = record['case']; oracle = record['oracle']
        assert oracle['status'] == 'EXACT'
        assert oracle['transforms_evaluated'] == GL5_SIZE
        count_stats = replay(case, oracle['count_first'], 'count_first')
        rank_stats = replay(case, oracle['rank_first'], 'rank_first')
        assert count_stats == record['count_first_stats']
        assert rank_stats == record['rank_first_stats']
        native = record['native_tradeoff']
        if case['name'] == 'rank5_tradeoff':
            checked_count = verify_rank_native(tuple(case['rows']), case['n'], native['count_first'])
            checked_rank = verify_rank_native(tuple(case['rows']), case['n'], native['rank_first'])
            assert checked_count['valid'] and checked_rank['valid']
            assert native['count_first_state_count'] == 4
            assert native['rank_first_state_count'] == 2
            assert native['distance'] == 2
        reviewed.append({'name': case['name'], 'count_stats': count_stats,
                         'rank_stats': rank_stats})
    source = {name: digest(HERE / name) for name in
              ('rank5_exact.cpp', 'rank5_driver.py', 'RANK5_REVIEW.py')}
    review = {
        'status': 'VERIFIED_INDEPENDENT_RANK5_REVIEW',
        'group_size': GL5_SIZE,
        'case_count': len(reviewed),
        'rows': reviewed,
        'tradeoff_count_first_state_count': 4,
        'tradeoff_rank_first_state_count': 2,
        'tradeoff_distance': 2,
        'source_hashes': source,
        'scope': 'Independent certificate arithmetic and native replay; finite rank-five evidence only.',
    }
    (HERE / 'RANK5_REVIEW.json').write_text(json.dumps(review, indent=2) + '\n', encoding='utf-8')
    (HERE / 'RANK5_REVIEW.md').write_text(
        '# Independent rank-five review\n\n'
        'The saved four-case run visited all 9,999,360 ordered bases in GL(5,2). '
        'A separate Python replay checked both reported objectives and every '
        'rank-five native certificate. The tradeoff input has native state counts '
        '4 versus 2 at the same distance 2. This remains a finite oracle, not a '
        'universal P-versus-NP result.\n', encoding='utf-8')
    print(json.dumps({'status': review['status'], 'cases': len(reviewed),
                      'group_size': GL5_SIZE, 'tradeoff_states': [4, 2],
                      'tradeoff_distance': 2}))


if __name__ == '__main__':
    run()
