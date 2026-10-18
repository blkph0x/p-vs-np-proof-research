"""Run the separate rank-five exhaustive oracle and replay its certificates.

The C++ program is intentionally separate from the Python GL(5,2) oracle.  This
driver compiles it in a temporary directory, checks that all 9,999,360 elements
of GL(5,2) were visited, and independently recomputes each reported transform
and objective with the existing Python arithmetic.  It does not turn a finite
rank-five search into a general representation-discovery algorithm.
"""

from __future__ import annotations

from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path
import subprocess
import sys
import tempfile

HERE = Path(__file__).resolve().parent
PARENT = HERE.parent
if str(PARENT) not in sys.path:
    sys.path.insert(0, str(PARENT))
from rank_native_solver import solve_rank_native
from exact_oracle import apply, exceptional_stats, score, rank

GL5_SIZE = 9_999_360


def cases():
    return [
        {
            'name': 'rank5_tradeoff',
            'rows': (17719, 49139, 75762, 15854, 131072),
            'n': 18,
            'expected_count_objective': [2, 2, 29],
            'expected_rank_objective': [1, 4, 4, 32],
        },
        {
            'name': 'rank5_mixed',
            'rows': (17719, 49139, 75762, 15854, 3),
            'n': 17,
            'expected_count_objective': [2, 2, 27],
            'expected_rank_objective': [2, 2, 2, 27],
        },
        {
            'name': 'rank5_random_a',
            'rows': (956, 3758, 4805, 2779, 3923),
            'n': 13,
            'expected_count_objective': [1, 1, 20],
            'expected_rank_objective': [1, 1, 1, 20],
        },
        {
            'name': 'rank5_random_b',
            'rows': (8421, 54921, 18196, 19303, 31637),
            'n': 16,
            'expected_count_objective': [1, 1, 28],
            'expected_rank_objective': [1, 1, 1, 28],
        },
    ]


def digest(path):
    return sha256(path.read_bytes()).hexdigest()


def compile_and_run(case, executable):
    source = HERE / 'rank5_exact.cpp'
    compile = subprocess.run(
        ['g++', '-O3', '-std=c++17', str(source), '-o', str(executable)],
        cwd=HERE, capture_output=True, text=True, timeout=180)
    if compile.returncode:
        raise RuntimeError(compile.stdout + compile.stderr)
    command = [str(executable), str(case['n']), *(str(row) for row in case['rows'])]
    run = subprocess.run(command, cwd=HERE, capture_output=True, text=True, timeout=180)
    if run.returncode:
        raise RuntimeError(run.stdout + run.stderr)
    return json.loads(run.stdout)


def replay_candidate(case, candidate, objective_kind):
    rows = tuple(case['rows'])
    transform = tuple(candidate['row_transform'])
    if len(transform) != 5 or rank(transform) != 5:
        raise AssertionError(f"{case['name']}: singular certificate")
    transformed = apply(rows, transform)
    expected_score = score(transformed, case['n'])
    expected_stats = exceptional_stats(transformed, case['n'])
    if objective_kind == 'count_first':
        if list(expected_score) != candidate['objective']:
            raise AssertionError(f"{case['name']}: count arithmetic mismatch")
    else:
        if list((expected_stats[1], *expected_stats[:1], *expected_stats[2:])) != candidate['objective']:
            raise AssertionError(f"{case['name']}: rank arithmetic mismatch")
    if candidate['exceptional_rank'] != expected_stats[1]:
        raise AssertionError(f"{case['name']}: rank metadata mismatch")
    if candidate['exceptional_count'] != expected_stats[0] or candidate['excess'] != expected_stats[2] or candidate['total'] != expected_stats[3]:
        raise AssertionError(f"{case['name']}: scalar metadata mismatch")
    return list(transformed), list(expected_stats)


def run():
    source = HERE / 'rank5_exact.cpp'
    before = digest(source)
    records = []
    with tempfile.TemporaryDirectory(prefix='rank5_oracle_') as temporary:
        executable = Path(temporary) / 'rank5_exact.exe'
        for case in cases():
            saved = compile_and_run(case, executable)
            if saved.get('status') != 'EXACT' or saved.get('transforms_evaluated') != GL5_SIZE:
                raise AssertionError(f"{case['name']}: incomplete exhaustive run")
            count_rows, count_stats = replay_candidate(case, saved['count_first'], 'count_first')
            rank_rows, rank_stats = replay_candidate(case, saved['rank_first'], 'rank_first')
            if saved['count_first']['objective'] != case['expected_count_objective']:
                raise AssertionError(f"{case['name']}: count objective changed")
            if saved['rank_first']['objective'] != case['expected_rank_objective']:
                raise AssertionError(f"{case['name']}: rank objective changed")
            native = {}
            if case['name'] == 'rank5_tradeoff':
                count_native = solve_rank_native(case['rows'], case['n'],
                                                 row_transform=saved['count_first']['row_transform'],
                                                 max_states=512, max_dp_transitions=1_000_000,
                                                 max_graph_calls=513)
                rank_native = solve_rank_native(case['rows'], case['n'],
                                                row_transform=saved['rank_first']['row_transform'],
                                                max_states=512, max_dp_transitions=1_000_000,
                                                max_graph_calls=513)
                if count_native['status'] != rank_native['status']:
                    raise AssertionError('native status mismatch')
                if count_native['status'] != 'EXACT' or rank_native['status'] != 'EXACT':
                    raise AssertionError('native rank-five tradeoff did not certify')
                if count_native['distance'] != rank_native['distance']:
                    raise AssertionError('native distance changed under basis transform')
                native = {
                    'count_first_state_count': count_native['state_count'],
                    'rank_first_state_count': rank_native['state_count'],
                    'distance': count_native['distance'],
                    'count_first': count_native,
                    'rank_first': rank_native,
                }
            records.append({
                'case': case,
                'oracle': saved,
                'count_first_transformed_rows': count_rows,
                'count_first_stats': count_stats,
                'rank_first_transformed_rows': rank_rows,
                'rank_first_stats': rank_stats,
                'native_tradeoff': native,
            })
    after = digest(source)
    if before != after:
        raise AssertionError('source changed during rank-five search')
    payload = {
        'status': 'RANK5_EXHAUSTIVE_ORACLE_PASS',
        'timestamp_utc': datetime.now(timezone.utc).isoformat(),
        'source_hash': before,
        'gl5_size': GL5_SIZE,
        'case_count': len(records),
        'records': records,
        'tradeoff_count_first_state_count': records[0]['native_tradeoff']['count_first_state_count'],
        'tradeoff_rank_first_state_count': records[0]['native_tradeoff']['rank_first_state_count'],
        'tradeoff_distance': records[0]['native_tradeoff']['distance'],
        'scope': 'Exact exhaustive rank-five basis search for four fixed inputs; no universal complexity claim.',
    }
    (HERE / 'RANK5_RESULTS.json').write_text(json.dumps(payload, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({
        'status': payload['status'], 'cases': payload['case_count'],
        'gl5_size': GL5_SIZE,
        'tradeoff_states': [payload['tradeoff_count_first_state_count'], payload['tradeoff_rank_first_state_count']],
        'tradeoff_distance': payload['tradeoff_distance'],
    }))


if __name__ == '__main__':
    run()
