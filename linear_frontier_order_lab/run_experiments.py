"""Run exact rank-frontier order controls."""

from __future__ import annotations

from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path

import frontier

HERE = Path(__file__).resolve().parent


def crossing_pairs(m):
    return [[int(c == i or c == m + i) for c in range(2 * m)] for i in range(m)]


def cases():
    return [
        {'name': 'crossing_pairs_6', 'matrix': crossing_pairs(6), 'bad_order': list(range(12)),
         'expected_width': 1, 'expected_bad_width': 6},
        {'name': 'repeated_rows_10', 'matrix': [[1] * 10 for _ in range(7)],
         'bad_order': list(range(10)), 'expected_width': 1, 'expected_bad_width': 1},
        {'name': 'identity_10', 'matrix': [[int(r == c) for c in range(10)] for r in range(10)],
         'bad_order': list(range(10)), 'expected_width': 0, 'expected_bad_width': 0},
        {'name': 'dense_4', 'matrix': [[1, 1, 0, 1], [0, 1, 1, 1], [1, 0, 1, 0]],
         'bad_order': list(range(4)), 'expected_width': None, 'expected_bad_width': None},
    ]


def digest(path):
    return sha256(path.read_bytes()).hexdigest()


def run():
    before = {p.name: digest(p) for p in (HERE / 'frontier.py', HERE / 'run_experiments.py')}
    rows = []
    for case in cases():
        result = frontier.optimal_order(case['matrix'])
        checked = frontier.verify_order_certificate(case['matrix'], result)
        bad_records, bad_width = frontier.order_records(case['matrix'], case['bad_order'])
        assert checked['valid'] and result['status'] == 'EXACT'
        if case['expected_width'] is not None:
            assert result['width'] == case['expected_width']
            assert bad_width == case['expected_bad_width']
        rows.append({'name': case['name'], 'matrix': case['matrix'],
                     'bad_order': case['bad_order'], 'bad_width': bad_width,
                     'optimal': result, 'verification': checked})
    after = {p.name: digest(p) for p in (HERE / 'frontier.py', HERE / 'run_experiments.py')}
    assert before == after
    payload = {'format': 'linear-frontier-order-v1',
               'timestamp_utc': datetime.now(timezone.utc).isoformat(),
               'source_hashes_before': before, 'source_hashes_after': after,
               'source_unchanged_during_run': True, 'rows': rows,
               'case_count': len(rows),
               'crossing_bad_width': rows[0]['bad_width'],
               'crossing_optimal_width': rows[0]['optimal']['width']}
    (HERE / 'RESULTS.json').write_text(json.dumps(payload, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'status': 'LINEAR_FRONTIER_RESULTS_WRITTEN', 'cases': len(rows),
                      'crossing_bad_width': payload['crossing_bad_width'],
                      'crossing_optimal_width': payload['crossing_optimal_width']}))


if __name__ == '__main__':
    run()
