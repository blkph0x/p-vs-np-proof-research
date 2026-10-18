"""Compare bounded row-basis descent with an exact GL(r,2) oracle."""

from __future__ import annotations

from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path
import random
import sys

HERE = Path(__file__).resolve().parent
PARENT = HERE.parent
if str(PARENT) not in sys.path:
    sys.path.insert(0, str(PARENT))
from row_basis_discovery import discover_row_basis
from exact_oracle import exact_optimum, exact_parameter_optimum, exceptional_stats
from rank_native_solver import solve_rank_native
from rank_aware_discovery import discover as discover_rank_aware


def rows_from_columns(columns, r):
    return tuple(sum(1 << j for j, column in enumerate(columns) if column >> i & 1)
                 for i in range(r))


def cases():
    counts = {1: 1, 2: 4, 3: 3, 4: 4, 5: 3, 6: 3, 7: 2}
    trap_columns = [value for value, count in counts.items() for _ in range(count)]
    rng = random.Random(20261018)
    random_cases = []
    for case_id in range(8):
        columns = [rng.randrange(1, 16) for _ in range(18 + case_id)]
        random_cases.append({'name': f'random_gl4_{case_id}', 'rows': rows_from_columns(columns, 4),
                             'n': len(columns), 'expected': 'EXACT'})
    return [
        {'name': 'gl3_trap', 'rows': rows_from_columns(trap_columns, 3),
         'n': len(trap_columns), 'expected': 'EXACT'},
        *random_cases,
        {'name': 'rank_tradeoff', 'rows': (17719, 49139, 75762, 15854),
         'n': 17, 'expected': 'EXACT'},
        {'name': 'gl5_capped', 'rows': (1, 2, 4, 8, 16),
         'n': 10, 'expected': 'UNKNOWN', 'max_transforms': 1000},
    ]


def digest(path):
    return sha256(path.read_bytes()).hexdigest()


def run():
    before = {name: digest(HERE / name) for name in ('exact_oracle.py', 'run_experiments.py')}
    before.update({name: digest(PARENT / name) for name in
                   ('rank_native_solver.py', 'native_coset_solver.py', 'matching_certificate.py')})
    rows = []
    for case in cases():
        oracle = exact_optimum(case['rows'], case['n'], max_transforms=case.get('max_transforms'))
        if case['expected'] == 'UNKNOWN':
            assert oracle['status'] == 'UNKNOWN'
            rows.append({'case': case, 'oracle': oracle})
            continue
        assert oracle['status'] == 'EXACT'
        heuristic = discover_row_basis(case['rows'], case['n'],
                                       max_candidate_evaluations=30000 if case['name'] == 'rank_tradeoff' else 3000,
                                       max_restarts=(0 if case['name'] == 'gl3_trap' else
                                                     31 if case['name'] == 'rank_tradeoff' else 8),
                                       restart_moves=4, seed=20261018)
        assert heuristic['verification']['valid']
        assert tuple(heuristic['objective']) >= tuple(oracle['objective'])
        if case['name'] == 'gl3_trap':
            assert tuple(oracle['objective']) == (1, 1, 31)
            assert tuple(heuristic['objective']) == (2, 2, 33)
        if case['name'] == 'rank_tradeoff':
            parameter = exact_parameter_optimum(case['rows'], case['n'])
            heuristic_stats = exceptional_stats(tuple(heuristic['transformed_check_rows']), case['n'])
            assert parameter['status'] == 'EXACT'
            assert parameter['objective'] == [1, 4, 4, 31]
            assert oracle['objective'] == [2, 2, 28]
            assert heuristic_stats == (2, 2, 2, 28)
            native_q = solve_rank_native(case['rows'], case['n'],
                                         row_transform=oracle['row_transform'],
                                         max_states=256, max_dp_transitions=1_000_000,
                                         max_graph_calls=257)
            native_p = solve_rank_native(case['rows'], case['n'],
                                         row_transform=parameter['row_transform'],
                                         max_states=256, max_dp_transitions=1_000_000,
                                         max_graph_calls=257)
            assert native_q['status'] == native_p['status'] == 'EXACT'
            assert native_q['exception_rank'] == 2 and native_q['state_count'] == 4
            assert native_p['exception_rank'] == 1 and native_p['state_count'] == 2
            assert native_q['distance'] == native_p['distance'] == 2
            rank_aware = discover_rank_aware(case['rows'], case['n'],
                                             max_candidate_evaluations=30000,
                                             max_restarts=31, restart_moves=8, seed=20261018)
            assert rank_aware['objective'] == [1, 4, 4, 31]
            native_rank_aware = solve_rank_native(case['rows'], case['n'],
                                                  row_transform=rank_aware['row_transform'],
                                                  max_states=256, max_dp_transitions=1_000_000,
                                                  max_graph_calls=257)
            assert native_rank_aware['status'] == 'EXACT'
            assert native_rank_aware['exception_rank'] == 1
            assert native_rank_aware['state_count'] == 2
            assert native_rank_aware['distance'] == 2
        else:
            parameter = None
            native_q = native_p = rank_aware = native_rank_aware = None
        rows.append({'case': case, 'oracle': oracle,
                     'parameter_oracle': parameter,
                     'native_q': native_q, 'native_p': native_p,
                     'rank_aware': rank_aware, 'native_rank_aware': native_rank_aware,
                     'heuristic_objective': heuristic['objective'],
                     'heuristic_exceptional_stats': list(exceptional_stats(tuple(heuristic['transformed_check_rows']), case['n'])),
                     'heuristic_termination': heuristic['termination'],
                     'heuristic_evaluations': heuristic['work']['candidate_evaluations']})
    after = {name: digest(HERE / name) for name in ('exact_oracle.py', 'run_experiments.py')}
    after.update({name: digest(PARENT / name) for name in
                  ('rank_native_solver.py', 'native_coset_solver.py', 'matching_certificate.py')})
    assert before == after
    payload = {'status': 'ROW_BASIS_EXACT_ORACLE_RESULTS_WRITTEN',
               'timestamp_utc': datetime.now(timezone.utc).isoformat(),
               'source_hashes_before': before, 'source_hashes_after': after,
               'source_unchanged_during_run': True, 'rows': rows,
               'case_count': len(rows),
               'exact_count': sum(row['oracle']['status'] == 'EXACT' for row in rows),
               'unknown_count': sum(row['oracle']['status'] == 'UNKNOWN' for row in rows),
               'gl3_trap_exact': [1, 1, 31], 'gl3_trap_heuristic': [2, 2, 33],
               'rank_tradeoff_q_objective': [2, 2, 28],
               'rank_tradeoff_p_objective': [1, 4, 4, 31],
               'rank_tradeoff_heuristic_stats': [2, 2, 2, 28],
               'rank_tradeoff_native_q_state_count': 4,
               'rank_tradeoff_native_p_state_count': 2,
               'rank_tradeoff_native_distance': 2,
               'rank_tradeoff_rank_aware_objective': [1, 4, 4, 31],
               'rank_tradeoff_rank_aware_state_count': 2}
    (HERE / 'RESULTS.json').write_text(json.dumps(payload, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'status': payload['status'], 'cases': len(rows),
                      'exact': payload['exact_count'], 'unknown': payload['unknown_count'],
                      'gl3_trap_exact': payload['gl3_trap_exact'],
                      'gl3_trap_heuristic': payload['gl3_trap_heuristic'],
                      'rank_tradeoff_q': payload['rank_tradeoff_q_objective'],
                      'rank_tradeoff_p': payload['rank_tradeoff_p_objective'],
                      'rank_tradeoff_native_states': [payload['rank_tradeoff_native_q_state_count'],
                                                      payload['rank_tradeoff_native_p_state_count']],
                      'rank_tradeoff_rank_aware': payload['rank_tradeoff_rank_aware_objective']}))


if __name__ == '__main__':
    run()
