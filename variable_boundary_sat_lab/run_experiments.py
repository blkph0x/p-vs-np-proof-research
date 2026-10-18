"""Run supplied-order boundary SAT DP controls."""

from __future__ import annotations

from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path

import boundary_dp as dp

HERE = Path(__file__).resolve().parent


def cases():
    chain = [[-(i + 1), i + 2] for i in range(63)]
    unsat = [[1]] + [[-(i + 1), i + 2] for i in range(63)] + [[-64]]
    star = [[i + 1, 12] for i in range(11)]
    dense = [[-(a + 1), -(b + 1), -(c + 1)]
             for a in range(6) for b in range(a + 1, 6) for c in range(b + 1, 6)]
    return [
        {'name': 'chain_64_sat', 'n': 64, 'clauses': chain, 'order': list(range(64)), 'expected_sat': True},
        {'name': 'chain_64_unsat', 'n': 64, 'clauses': unsat, 'order': list(range(64)), 'expected_sat': False},
        {'name': 'star_bad_order', 'n': 12, 'clauses': star, 'order': list(range(12)), 'expected_sat': True},
        {'name': 'star_good_order', 'n': 12, 'clauses': star, 'order': [11] + list(range(11)), 'expected_sat': True},
        {'name': 'dense_3cnf_6', 'n': 6, 'clauses': dense, 'order': list(range(6)), 'expected_sat': True},
    ]


def digest(path):
    return sha256(path.read_bytes()).hexdigest()


def run():
    before = {p.name: digest(p) for p in (HERE / 'boundary_dp.py', HERE / 'run_experiments.py')}
    rows = []
    for case in cases():
        result = dp.solve(case['n'], case['clauses'], case['order'])
        checked = dp.verify(case['n'], case['clauses'], result)
        assert result['status'] == 'EXACT' and result['sat'] == case['expected_sat']
        assert checked['valid']
        rows.append({'case': case, 'result': result, 'verification': checked})
    after = {p.name: digest(p) for p in (HERE / 'boundary_dp.py', HERE / 'run_experiments.py')}
    assert before == after
    payload = {'format': 'variable-boundary-sat-v1',
               'timestamp_utc': datetime.now(timezone.utc).isoformat(),
               'source_hashes_before': before, 'source_hashes_after': after,
               'source_unchanged_during_run': True, 'rows': rows,
               'case_count': len(rows),
               'chain_64_width': rows[0]['result']['stats']['max_width'],
               'chain_64_unsat_width': rows[1]['result']['stats']['max_width'],
               'star_bad_width': rows[2]['result']['stats']['max_width'],
               'star_good_width': rows[3]['result']['stats']['max_width']}
    (HERE / 'RESULTS.json').write_text(json.dumps(payload, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'status': 'VARIABLE_BOUNDARY_RESULTS_WRITTEN', 'cases': len(rows),
                      'chain_width': payload['chain_64_width'],
                      'star_bad_width': payload['star_bad_width'],
                      'star_good_width': payload['star_good_width']}))


if __name__ == '__main__':
    run()
