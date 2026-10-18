"""Exact graph layout controls for order-discovery cost."""

from __future__ import annotations

from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path

import vertex_separation as vs

HERE = Path(__file__).resolve().parent


def cases():
    return [
        {'name': 'path_8', 'n': 8, 'edges': [(i, i + 1) for i in range(7)],
         'bad_order': list(range(8)), 'expected_width': 1, 'expected_bad_width': 1},
        {'name': 'star_8', 'n': 8, 'edges': [(0, i) for i in range(1, 8)],
         'bad_order': list(range(1, 8)) + [0], 'expected_width': 1, 'expected_bad_width': 7},
        {'name': 'cycle_8', 'n': 8, 'edges': [(i, (i + 1) % 8) for i in range(8)],
         'bad_order': list(range(8)), 'expected_width': 2, 'expected_bad_width': 2},
        {'name': 'complete_6', 'n': 6, 'edges': [(u, v) for u in range(6) for v in range(u + 1, 6)],
         'bad_order': list(range(6)), 'expected_width': 5, 'expected_bad_width': 5},
        {'name': 'complete_bipartite_4_2', 'n': 6,
         'edges': [(i, 4 + j) for i in range(4) for j in range(2)],
         'bad_order': list(range(6)), 'expected_width': 2, 'expected_bad_width': 4},
    ]


def digest(path):
    return sha256(path.read_bytes()).hexdigest()


def run():
    before = {p.name: digest(p) for p in (HERE / 'vertex_separation.py', HERE / 'run_experiments.py')}
    rows = []
    for case in cases():
        result = vs.optimal_order(case['n'], case['edges'])
        checked = vs.verify_certificate(case['n'], case['edges'], result)
        _, bad_width = vs.order_records(case['n'], case['edges'], case['bad_order'])
        assert checked['valid'] and result['status'] == 'EXACT'
        assert result['width'] == case['expected_width'] and bad_width == case['expected_bad_width']
        greedy = vs.greedy_order(case['n'], case['edges'])
        _, greedy_width = vs.order_records(case['n'], case['edges'], greedy)
        rows.append({'case': case, 'bad_width': bad_width, 'greedy_order': greedy,
                     'greedy_width': greedy_width,
                     'optimal': result, 'verification': checked,
                     'clauses': vs.monotone_two_cnf(case['n'], case['edges'])})
    after = {p.name: digest(p) for p in (HERE / 'vertex_separation.py', HERE / 'run_experiments.py')}
    assert before == after
    payload = {'format': 'vertex-separation-order-v1',
               'timestamp_utc': datetime.now(timezone.utc).isoformat(),
               'source_hashes_before': before, 'source_hashes_after': after,
               'source_unchanged_during_run': True, 'rows': rows,
               'case_count': len(rows), 'star_bad_width': rows[1]['bad_width'],
               'star_optimal_width': rows[1]['optimal']['width'],
               'bipartite_greedy_width': rows[4]['greedy_width'],
               'bipartite_optimal_width': rows[4]['optimal']['width']}
    (HERE / 'RESULTS.json').write_text(json.dumps(payload, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'status': 'VERTEX_SEPARATION_RESULTS_WRITTEN', 'cases': len(rows),
                      'star_bad_width': payload['star_bad_width'],
                      'star_optimal_width': payload['star_optimal_width']}))


if __name__ == '__main__':
    run()
