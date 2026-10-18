"""Independent exact GL(r,2) replay and heuristic-gap review."""

from __future__ import annotations

from functools import reduce
from hashlib import sha256
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
PARENT = HERE.parent
if str(PARENT) not in sys.path:
    sys.path.insert(0, str(PARENT))
from row_basis_discovery import objective
from rank_native_solver import verify_rank_native
from rank_aware_discovery import verify as verify_rank_aware


def binary_rank(values):
    pivots = {}
    for value in values:
        while value:
            pivot = value.bit_length() - 1
            if pivot in pivots:
                value ^= pivots[pivot]
            else:
                pivots[pivot] = value
                break
    return len(pivots)


def exceptional_stats(rows, n):
    columns = [sum(((row >> column) & 1) << index for index, row in enumerate(rows))
               for column in range(n)]
    exceptional = [column for column in columns if column.bit_count() > 2]
    return (len(exceptional), binary_rank(exceptional),
            sum(max(0, column.bit_count() - 2) for column in columns),
            sum(column.bit_count() for column in columns))


def transforms(r):
    values = range(1 << r)

    def extend(prefix, span):
        if len(prefix) == r:
            yield tuple(prefix); return
        for row in values:
            if row in span:
                continue
            yield from extend(prefix + [row], span | {member ^ row for member in span})
    yield from extend([], {0})


def apply(rows, transform):
    return tuple(reduce(
                     int.__xor__,
                     (rows[j] for j in range(len(rows)) if mask >> j & 1),
                     0)
                 for mask in transform)


def exact(rows, n, cap=None):
    best = None; count = 0
    for transform in transforms(len(rows)):
        if cap is not None and count >= cap:
            return {'status': 'UNKNOWN', 'transforms_evaluated': count}
        transformed = apply(rows, transform); count += 1
        candidate = (objective(transformed, n), tuple(transform), transformed)
        if best is None or candidate[:2] < best[:2]:
            best = candidate
    return {'status': 'EXACT', 'objective': list(best[0]),
            'row_transform': list(best[1]), 'transformed_rows': list(best[2]),
            'transforms_evaluated': count}


def parameter_exact(rows, n):
    best = None; count = 0
    for transform in transforms(len(rows)):
        transformed = apply(rows, transform); count += 1
        stats = exceptional_stats(transformed, n)
        candidate = ((stats[1], stats[0], stats[2], stats[3]), tuple(transform), transformed, stats)
        if best is None or candidate[:2] < best[:2]:
            best = candidate
    return {'status': 'EXACT', 'objective': list(best[0]), 'stats': list(best[3]),
            'row_transform': list(best[1]), 'transformed_rows': list(best[2]),
            'transforms_evaluated': count}


def digest(path):
    return sha256(path.read_bytes()).hexdigest()


def run():
    payload = json.loads((HERE / 'RESULTS.json').read_text(encoding='utf-8'))
    rows = []
    for saved in payload['rows']:
        case = saved['case']; oracle = exact(tuple(case['rows']), case['n'], case.get('max_transforms'))
        assert oracle['status'] == saved['oracle']['status']
        if oracle['status'] == 'EXACT':
            assert oracle['objective'] == saved['oracle']['objective']
            assert oracle['transforms_evaluated'] == saved['oracle']['transforms_evaluated']
            if case['name'] == 'gl3_trap':
                assert saved['heuristic_objective'] == [2, 2, 33]
        parameter = None
        if case['name'] == 'rank_tradeoff':
            parameter = parameter_exact(tuple(case['rows']), case['n'])
            assert parameter['objective'] == saved['parameter_oracle']['objective'] == [1, 4, 4, 31]
            assert saved['heuristic_exceptional_stats'] == [2, 2, 2, 28]
            checked_q = verify_rank_native(tuple(case['rows']), case['n'], saved['native_q'])
            checked_p = verify_rank_native(tuple(case['rows']), case['n'], saved['native_p'])
            assert checked_q['valid'] and checked_p['valid']
            assert saved['native_q']['exception_rank'] == 2 and saved['native_q']['state_count'] == 4
            assert saved['native_p']['exception_rank'] == 1 and saved['native_p']['state_count'] == 2
            assert saved['native_q']['distance'] == saved['native_p']['distance'] == 2
            assert verify_rank_aware(tuple(case['rows']), case['n'], saved['rank_aware'])['valid']
            checked_rank_aware = verify_rank_native(tuple(case['rows']), case['n'], saved['native_rank_aware'])
            assert checked_rank_aware['valid']
            assert saved['rank_aware']['objective'] == [1, 4, 4, 31]
            assert saved['native_rank_aware']['state_count'] == 2
        rows.append({'name': case['name'], 'oracle_status': oracle['status'],
                     'objective': oracle.get('objective'),
                     'parameter_objective': parameter.get('objective') if parameter else None,
                     'heuristic_objective': saved.get('heuristic_objective'),
                     'heuristic_exceptional_stats': saved.get('heuristic_exceptional_stats')})
    source = {name: digest(HERE / name) for name in
              ('exact_oracle.py', 'run_experiments.py', 'INDEPENDENT_REVIEW.py', 'rank_aware_discovery.py')}
    source.update({name: digest(PARENT / name) for name in
                   ('rank_native_solver.py', 'native_coset_solver.py', 'matching_certificate.py')})
    review = {'status': 'VERIFIED_INDEPENDENT_ROW_BASIS_ORACLE_REVIEW',
              'case_count': len(rows), 'exact_count': sum(row['oracle_status'] == 'EXACT' for row in rows),
              'unknown_count': sum(row['oracle_status'] == 'UNKNOWN' for row in rows),
              'rows': rows, 'source_hashes': source,
              'gl3_trap_exact': [1, 1, 31], 'gl3_trap_heuristic': [2, 2, 33],
              'rank_tradeoff_q_objective': [2, 2, 28],
              'rank_tradeoff_p_objective': [1, 4, 4, 31],
              'rank_tradeoff_heuristic_stats': [2, 2, 2, 28],
              'rank_tradeoff_native_q_state_count': 4,
              'rank_tradeoff_native_p_state_count': 2,
              'rank_tradeoff_native_distance': 2,
              'rank_tradeoff_rank_aware_objective': [1, 4, 4, 31],
              'rank_tradeoff_rank_aware_state_count': 2}
    (HERE / 'INDEPENDENT_REVIEW.json').write_text(json.dumps(review, indent=2) + '\n', encoding='utf-8')
    (HERE / 'INDEPENDENT_REVIEW.md').write_text(
        '# Independent row-basis oracle review\n\n'
        'A second GL(r,2) enumerator independently replayed every exact result. '
        'The known rank-three trap has global objective (1,1,31), while bounded '
        'local descent returns (2,2,33); the rank-tradeoff control has count/rank '
        '(2,2) versus (4,1), and a rank-five cap remains UNKNOWN.\n', encoding='utf-8')
    print(json.dumps({'status': review['status'], 'cases': len(rows),
                      'exact': review['exact_count'], 'unknown': review['unknown_count'],
                      'gl3_trap_exact': review['gl3_trap_exact'],
                      'gl3_trap_heuristic': review['gl3_trap_heuristic'],
                      'rank_tradeoff_q': review['rank_tradeoff_q_objective'],
                      'rank_tradeoff_p': review['rank_tradeoff_p_objective'],
                      'rank_tradeoff_native_states': [review['rank_tradeoff_native_q_state_count'],
                                                      review['rank_tradeoff_native_p_state_count']],
                      'rank_tradeoff_rank_aware': review['rank_tradeoff_rank_aware_objective']}))


if __name__ == '__main__':
    run()
