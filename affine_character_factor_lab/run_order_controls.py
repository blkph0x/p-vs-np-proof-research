"""Run bounded order discovery and feed certified orders to the DAG control."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import elimination_controls as elimination
import order_discovery as discovery


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def scopes_for(factors):
    return [([abs(v) - 1 for v in f['literals']] if f['kind'] == 'or' else list(f['scope']))
            for f in factors]


def chain_case(m):
    factors = elimination.connected_chain(m)
    scopes = scopes_for(factors)
    found = discovery.find_order(2 * m, scopes, 3, max_states=100_000)
    assert found['status'] == 'EXACT'
    factor_order = discovery.factor_order_from_variable_order(scopes, found['order'])
    result = elimination.dag.solve_factors(2 * m, factors, order=factor_order, **elimination.CAPS)
    checked = elimination.dag.verify_factors(2 * m, factors, result, order=factor_order, **elimination.CAPS)
    return {'name': f'chain_{m}', 'variables': 2 * m,
            'discovery': found, 'factor_order': factor_order,
            'solve_status': result['status'], 'value': result.get('value'),
            'verification': checked['status'], 'verification_valid': checked.get('valid', False),
            'peak_terms': result.get('stats', {}).get('peak_terms'),
            'solve_work': result.get('stats', {}).get('work')}


def graph_case(name, n, scopes, width, max_states=100_000):
    found = discovery.find_order(n, scopes, width, max_states=max_states)
    valid = found['status'] == 'EXACT' and discovery.verify_order(n, scopes, found['order'], width)['valid']
    return {'name': name, 'n': n, 'scope_count': len(scopes), 'width_cap': width,
            'status': found['status'], 'states': found.get('states'),
            'width': found.get('width'), 'order': found.get('order'),
            'certificate_valid': valid, 'reason': found.get('reason')}


def main():
    rows = [chain_case(m) for m in [8, 32, 128]]
    rows.append(graph_case('star_width_1', 32, [[0, i] for i in range(1, 32)], 1))
    rows.append(graph_case('complete_width_2_no', 8,
                           [[i, j] for i in range(8) for j in range(i + 1, 8)], 2))
    rows.append(graph_case('cycle_width_1_no', 16,
                           [[i, (i + 1) % 16] for i in range(16)], 1))
    rows.append(graph_case('path_budget_unknown', 32, [[i, i + 1] for i in range(31)], 1,
                           max_states=1))
    payload = {
        'schema': 'bounded_order_discovery_controls_v1',
        'interpretation': 'Exact capped discovery of filled-primal-graph orders; UNKNOWN means the search cap, not NO.',
        'rows': rows,
        'source_hashes': {
            'order_discovery.py': sha(HERE / 'order_discovery.py'),
            'run_order_controls.py': sha(HERE / 'run_order_controls.py'),
            'elimination_controls.py': sha(HERE / 'elimination_controls.py'),
            'weighted_affine_dag_lab/dag.py': sha(HERE.parent / 'weighted_affine_dag_lab' / 'dag.py'),
        },
    }
    (HERE / 'ORDER_DISCOVERY_RESULTS.json').write_text(json.dumps(payload, indent=2, sort_keys=True) + '\n', encoding='utf-8')
    print(json.dumps({'status': 'ORDER_CONTROLS_WRITTEN', 'rows': len(rows),
                      'exact': sum(r['status'] == 'EXACT' for r in rows if 'status' in r),
                      'chain_exact': sum(r['solve_status'] == 'EXACT' for r in rows if 'solve_status' in r)}, sort_keys=True))


if __name__ == '__main__':
    main()
