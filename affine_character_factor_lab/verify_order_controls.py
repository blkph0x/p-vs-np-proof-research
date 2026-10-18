"""Independent replay of bounded order-discovery controls."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import elimination_controls as elimination
import order_discovery as discovery
import run_order_controls as runner


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    payload = json.loads((HERE / 'ORDER_DISCOVERY_RESULTS.json').read_text(encoding='utf-8'))
    rows = payload['rows']
    assert len(rows) == 7
    for key, recorded in payload['source_hashes'].items():
        if key == 'weighted_affine_dag_lab/dag.py':
            actual = sha(HERE.parent / 'weighted_affine_dag_lab' / 'dag.py')
        else:
            actual = sha(HERE / key)
        assert actual == recorded, key
    chain_replayed = 0
    for row in rows[:3]:
        m = row['variables'] // 2
        factors = elimination.connected_chain(m)
        scopes = runner.scopes_for(factors)
        found = discovery.find_order(2 * m, scopes, 3, max_states=100_000)
        assert found['status'] == 'EXACT' and found['width'] <= 3
        factor_order = discovery.factor_order_from_variable_order(scopes, found['order'])
        result = elimination.dag.solve_factors(2 * m, factors, order=factor_order, **elimination.CAPS)
        checked = elimination.dag.verify_factors(2 * m, factors, result, order=factor_order, **elimination.CAPS)
        assert result['status'] == 'EXACT' and result['value'] == [1, 1]
        assert checked['valid'] and checked['status'] == 'VERIFIED'
        assert row['solve_status'] == 'EXACT' and row['verification_valid'] is True
        chain_replayed += 1
    star = discovery.find_order(32, [[0, i] for i in range(1, 32)], 1)
    assert star['status'] == 'EXACT' and star['width'] == 1
    complete = discovery.find_order(8, [[i, j] for i in range(8) for j in range(i + 1, 8)], 2)
    assert complete['status'] == 'NO'
    cycle = discovery.find_order(16, [[i, (i + 1) % 16] for i in range(16)], 1)
    assert cycle['status'] == 'NO'
    capped = discovery.find_order(32, [[i, i + 1] for i in range(31)], 1, max_states=1)
    assert capped['status'] == 'UNKNOWN' and 'order' not in capped
    review = {
        'status': 'VERIFIED_INDEPENDENT_ORDER_REVIEW',
        'rows': len(rows), 'chain_exact_replayed': chain_replayed,
        'star_width': star['width'], 'complete_status': complete['status'],
        'cycle_status': cycle['status'], 'budget_status': capped['status'],
        'source_hashes_match': True,
    }
    (HERE / 'ORDER_DISCOVERY_REVIEW.json').write_text(json.dumps(review, indent=2, sort_keys=True) + '\n', encoding='utf-8')
    (HERE / 'ORDER_DISCOVERY_REVIEW.md').write_text(
        '# Independent order-discovery review\n\n'
        'The bounded filled-graph search was replayed from the original scopes. '
        'It found width-three orders for the cumulative-parity chains and those '
        'orders drove independently verified exact weighted-DAG certificates '
        'through 128 blocks. It returned NO for the complete graph at width two '
        'and the cycle at width one, and UNKNOWN for the explicitly capped path '
        'search. A NO result is used only after all legal branches under the cap '
        'are exhausted; a state-cap stop carries no order or value.\n', encoding='utf-8')
    print(json.dumps(review, sort_keys=True))


if __name__ == '__main__':
    main()
