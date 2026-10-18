"""Run pinned-output circuit CNF controls through the frontier SAT solver."""

from __future__ import annotations

from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
VARIABLE_LAB = HERE.parent / 'variable_boundary_sat_lab'
if str(VARIABLE_LAB) not in sys.path:
    sys.path.insert(0, str(VARIABLE_LAB))
import boundary_dp  # noqa: E402
ORDER_LAB = HERE.parent / 'primal_order_sat_lab'
if str(ORDER_LAB) not in sys.path:
    sys.path.insert(0, str(ORDER_LAB))
import primal_order  # noqa: E402

from circuit_cnf import build_circuit, build_threshold_circuit, pin_integer, pin_variables  # noqa: E402


def digest(path):
    return sha256(path.read_bytes()).hexdigest()


def source_weight(forms, assignment):
    return sum((form & assignment).bit_count() & 1 for form in forms)


def run():
    forms = (1, 2, 3, 5, 9, 17, 7)
    dimension = 5
    circuit = build_circuit(forms, dimension)
    base_clauses = circuit['clauses']
    rows = []
    for assignment in range(1 << dimension):
        target = source_weight(forms, assignment)
        clauses = pin_variables(base_clauses, range(1, dimension + 1),
                                [(assignment >> bit) & 1 for bit in range(dimension)])
        clauses = pin_integer(clauses, circuit['output_bits'], target)
        exact = boundary_dp.solve(circuit['variables'], clauses, circuit['order'],
                                  max_states=1_000_000, max_transitions=4_000_000)
        assert exact['status'] == 'EXACT' and exact['sat']
        wrong = target + 1 if target < len(forms) else target - 1
        wrong_clauses = pin_variables(base_clauses, range(1, dimension + 1),
                                      [(assignment >> bit) & 1 for bit in range(dimension)])
        wrong_clauses = pin_integer(wrong_clauses, circuit['output_bits'], wrong)
        rejected = boundary_dp.solve(circuit['variables'], wrong_clauses, circuit['order'],
                                     max_states=1_000_000, max_transitions=4_000_000)
        assert rejected['status'] == 'EXACT' and not rejected['sat']
        rows.append({'assignment': assignment, 'target': target,
                     'wrong_target': wrong,
                     'exact_states': exact['stats']['states'],
                     'exact_transitions': exact['stats']['transitions'],
                     'wrong_states': rejected['stats']['states'],
                     'wrong_transitions': rejected['stats']['transitions'],
                     'max_width': exact['stats']['max_width']})
    tiny = build_circuit((1, 2, 3), 3)
    tiny_boundaries = boundary_dp.boundaries(tiny['variables'], tiny['clauses'], tiny['order'])
    optimum = primal_order.optimal_order(tiny['variables'], tiny['clauses'],
                                         max_subsets=500_000)
    assert optimum['status'] == 'EXACT'
    order_control = {
        'forms': [1, 2, 3], 'dimension': 3,
        'variables': tiny['variables'], 'clauses': len(tiny['clauses']),
        'topological_width': max(map(len, tiny_boundaries)),
        'optimal_width': optimum['width'],
        'subset_state_count': optimum['state_count'],
        'optimal_order': optimum['order'],
    }
    distance_forms = (1, 2, 3, 4, 5, 6, 7)
    distance_circuit = build_circuit(distance_forms, 3)
    distance_queries = []
    compact_circuits = []
    for threshold in range(5):
        compact = build_threshold_circuit(distance_forms, 3, threshold)
        compact_circuits.append(compact)
        threshold_clauses = list(compact['clauses'])
        threshold_clauses.append([1, 2, 3])
        result = boundary_dp.solve(compact['variables'], threshold_clauses,
                                   compact['order'], max_states=1_000_000,
                                   max_transitions=4_000_000)
        assert result['status'] == 'EXACT'
        distance_queries.append({'threshold': threshold, 'sat': result['sat'],
                                 'states': result['stats']['states'],
                                 'transitions': result['stats']['transitions'],
                                 'max_width': result['stats']['max_width']})
    before = {name: digest(HERE / name) for name in
              ('circuit_cnf.py', 'run_experiments.py', 'THEOREM.md')}
    payload = {
        'status': 'CIRCUIT_BOUNDARY_CHECK_PASS',
        'timestamp_utc': datetime.now(timezone.utc).isoformat(),
        'forms': list(forms), 'dimension': dimension,
        'circuit': circuit,
        'queries': rows,
        'order_control': order_control,
        'distance_control': {
            'forms': list(distance_forms), 'dimension': 3,
            'minimum_nonzero_weight': 4,
            'queries': distance_queries,
            'compact_circuits': compact_circuits,
        },
        'summary': {
            'assignments': len(rows),
            'all_exact_sat': all(row['exact_states'] > 0 for row in rows),
            'all_wrong_rejected': all(row['wrong_states'] > 0 for row in rows),
            'max_width': max(row['max_width'] for row in rows),
            'max_exact_states': max(row['exact_states'] for row in rows),
            'max_wrong_states': max(row['wrong_states'] for row in rows),
        },
        'source_hashes_before': before,
    }
    after = {name: digest(HERE / name) for name in before}
    assert before == after
    payload['source_hashes_after'] = after
    (HERE / 'RESULTS.json').write_text(json.dumps(payload, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'status': payload['status'], **payload['summary']}))


if __name__ == '__main__':
    run()
