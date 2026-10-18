"""Cross-check the connected parity family with the audited weighted DAG."""

from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import time

HERE = Path(__file__).resolve().parent
WEIGHTED = HERE.parent / "weighted_affine_dag_lab"
spec = importlib.util.spec_from_file_location("_weighted_affine_dag_for_character_crosscheck",
                                               WEIGHTED / "dag.py")
dag = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = dag
spec.loader.exec_module(dag)


CAPS = dict(max_terms=4096, max_products=1_000_000, max_nodes=200_000,
            max_work=10_000_000, max_variables=256, max_factors=4096,
            max_integer_bits=100_000)


def source_hash(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def connected_chain(m):
    """OR pairs plus independent cumulative parity rows, all original IDs kept."""
    factors = [{'kind': 'or', 'literals': [2 * i + 1, 2 * i + 2]}
               for i in range(m)]
    for i in range(m):
        row = 3 if i == 0 else (3 << (2 * i)) | (3 << (2 * (i - 1)))
        scope = [v for v in range(2 * m) if (row >> v) & 1]
        factors.append({'kind': 'affine', 'scope': scope,
                        'equations': [[row, 0]], 'phase': [], 'scalar': 1})
    return factors


def interleaved_order(m):
    return [j for i in range(m) for j in (i, m + i)]


def run_case(name, m, order, caps=None):
    factors = connected_chain(m)
    selected_caps = dict(CAPS)
    if caps:
        selected_caps.update(caps)
    started = time.perf_counter()
    result = dag.solve_factors(2 * m, factors, order=order, **selected_caps)
    elapsed = time.perf_counter() - started
    row = {'name': name, 'm': m, 'factor_count': len(factors),
           'order': list(order), 'status': result['status'],
           'elapsed_seconds': elapsed,
           'source_request_sha256': result.get('request_sha256'),
           'producer_stats': result.get('stats', {})}
    if result['status'] == 'EXACT':
        checked = dag.verify_factors(2 * m, factors, result, order=order, **selected_caps)
        row.update({'value': result['value'], 'expected': [1, 1],
                    'expected_matches': result['value'] == [1, 1],
                    'verification': checked['status'],
                    'verification_valid': checked.get('valid', False),
                    'verifier_stats': checked.get('stats', {})})
    else:
        row['reason'] = result.get('reason')
    return row


def main():
    rows = []
    for m in [1, 2, 4, 8, 16, 32, 64, 128]:
        rows.append(run_case(f'interleaved_chain_{m}', m, interleaved_order(m)))
    # The same original factors and a deliberately poor factor order. This is
    # a resource control, not a value claim when the cap is reached.
    rows.append(run_case('poor_order_chain_12', 12, list(range(24)),
                         {'max_terms': 64, 'max_nodes': 4096, 'max_work': 1_000_000}))
    payload = {
        'schema': 'affine_character_weighted_dag_crosscheck_v1',
        'interpretation': 'Audited weighted affine DAG replay on a connected cumulative-parity family; order-sensitive finite evidence, not a general SAT claim.',
        'rows': rows,
        'source_hashes': {
            'weighted_affine_dag_lab/dag.py': source_hash(WEIGHTED / 'dag.py'),
            'affine_boundary_lab/boundary.py': source_hash(WEIGHTED.parent / 'affine_boundary_lab' / 'boundary.py'),
            'elimination_controls.py': source_hash(HERE / 'elimination_controls.py'),
        },
    }
    (HERE / 'ELIMINATION_RESULTS.json').write_text(json.dumps(payload, indent=2, sort_keys=True) + '\n', encoding='utf-8')
    print(json.dumps({'status': 'ELIMINATION_CONTROLS_WRITTEN',
                      'rows': len(rows),
                      'exact': sum(row['status'] == 'EXACT' for row in rows),
                      'unknown': sum(row['status'] == 'UNKNOWN' for row in rows)}, sort_keys=True))


if __name__ == '__main__':
    main()
