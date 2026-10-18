"""Run exact primal-order search followed by SAT certificate generation."""

from __future__ import annotations

from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path

import primal_order as po

HERE = Path(__file__).resolve().parent


def cases():
    chain = [[-(i + 1), i + 2] for i in range(7)]
    unsat = [[1]] + [[-(i + 1), i + 2] for i in range(7)] + [[-8]]
    star = [[i + 1, 8] for i in range(7)]
    complete = [[i + 1, j + 1] for i in range(6) for j in range(i + 1, 6)]
    dense = [[-(a + 1), -(b + 1), -(c + 1)]
             for a in range(6) for b in range(a + 1, 6) for c in range(b + 1, 6)]
    return [
        {'name': 'chain_8_sat', 'n': 8, 'clauses': chain, 'expected_status': 'EXACT', 'expected_sat': True, 'expected_width': 1},
        {'name': 'chain_8_unsat', 'n': 8, 'clauses': unsat, 'expected_status': 'EXACT', 'expected_sat': False, 'expected_width': 1},
        {'name': 'star_8', 'n': 8, 'clauses': star, 'expected_status': 'EXACT', 'expected_sat': True, 'expected_width': 1},
        {'name': 'complete_6', 'n': 6, 'clauses': complete, 'expected_status': 'EXACT', 'expected_sat': True, 'expected_width': 5},
        {'name': 'dense_negative_3cnf_6', 'n': 6, 'clauses': dense, 'expected_status': 'EXACT', 'expected_sat': True, 'expected_width': 5},
        {'name': 'complete_12_search_cap', 'n': 12,
         'clauses': [[i + 1, j + 1] for i in range(12) for j in range(i + 1, 12)],
         'expected_status': 'UNKNOWN', 'expected_reason': 'subset cap', 'max_subsets': 100},
    ]


def digest(path):
    return sha256(path.read_bytes()).hexdigest()


def run():
    source = ('primal_order.py', 'run_experiments.py')
    before = {name: digest(HERE / name) for name in source}
    rows = []
    for case in cases():
        kwargs = {'max_subsets': case.get('max_subsets', 1_000_000)}
        result = po.solve(case['n'], case['clauses'], **kwargs)
        assert result['status'] == case['expected_status']
        if result['status'] == 'EXACT':
            assert result['sat'] == case['expected_sat']
            assert result['width'] == case['expected_width']
            assert po.verify(case['n'], case['clauses'], result)['valid']
        else:
            assert result['reason'] == case['expected_reason']
        rows.append({'case': case, 'result': result})
    after = {name: digest(HERE / name) for name in source}
    assert before == after
    payload = {'format': 'primal-order-sat-v1',
               'timestamp_utc': datetime.now(timezone.utc).isoformat(),
               'source_hashes_before': before, 'source_hashes_after': after,
               'source_unchanged_during_run': True, 'rows': rows,
               'case_count': len(rows), 'exact_count': sum(r['result']['status'] == 'EXACT' for r in rows),
               'unknown_count': sum(r['result']['status'] == 'UNKNOWN' for r in rows)}
    (HERE / 'RESULTS.json').write_text(json.dumps(payload, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'status': 'PRIMAL_ORDER_RESULTS_WRITTEN', 'cases': len(rows),
                      'exact': payload['exact_count'], 'unknown': payload['unknown_count'],
                      'chain_width': rows[0]['result']['width'],
                      'complete_width': rows[3]['result']['width']}))


if __name__ == '__main__':
    run()
