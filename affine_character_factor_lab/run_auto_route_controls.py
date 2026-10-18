"""Saved end-to-end discovery-to-solver controls."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import auto_route
import elimination_controls


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def record(name, n, factors, width_cap, max_states=100_000):
    result = auto_route.solve_auto(n, factors, width_cap=width_cap,
                                  max_states=max_states)
    row = {'name': name, 'n': n, 'factor_count': len(factors),
           'width_cap': width_cap, 'max_states': max_states,
           'status': result['status'], 'reason': result.get('reason'),
           'discovery_status': result.get('discovery', {}).get('status'),
           'discovery_states': result.get('discovery', {}).get('states')}
    if result['status'] == 'EXACT':
        row.update({'value': result['value'],
                    'verification_valid': result['weighted_verification']['valid'],
                    'discovered_width': result['discovery']['width'],
                    'factor_order': result['factor_order'],
                    'peak_terms': result['weighted_result']['stats']['peak_terms'],
                    'producer_work': result['weighted_result']['stats']['work']})
    return row


def main():
    rows = []
    for m in [8, 32, 128]:
        rows.append(record(f'chain_{m}', 2 * m,
                           elimination_controls.connected_chain(m), 3))
    rows.append(record('chain_width_two_no', 16,
                       elimination_controls.connected_chain(8), 2))
    complete = [{'kind': 'or', 'literals': [i + 1, j + 1]}
                for i in range(8) for j in range(i + 1, 8)]
    rows.append(record('complete_width_two_no', 8, complete, 2))
    path = [{'kind': 'or', 'literals': [i + 1, i + 2]} for i in range(31)]
    rows.append(record('path_discovery_capped', 32, path, 1, max_states=1))
    payload = {
        'schema': 'automatic_width_route_controls_v1',
        'interpretation': 'Discovery, weighted solve and independent replay are one bounded route; NO/UNKNOWN are never converted to SAT values.',
        'rows': rows,
        'source_hashes': {name: sha(HERE / name) for name in
                          ['auto_route.py', 'run_auto_route_controls.py',
                           'elimination_controls.py', 'order_discovery.py']},
    }
    (HERE / 'AUTO_ROUTE_RESULTS.json').write_text(json.dumps(payload, indent=2, sort_keys=True) + '\n', encoding='utf-8')
    print(json.dumps({'status': 'AUTO_ROUTE_CONTROLS_WRITTEN', 'rows': len(rows),
                      'exact': sum(r['status'] == 'EXACT' for r in rows),
                      'no': sum(r['status'] == 'NO' for r in rows),
                      'unknown': sum(r['status'] == 'UNKNOWN' for r in rows)}, sort_keys=True))


if __name__ == '__main__':
    main()
