"""Save reproducible small-terminal perturbation controls."""
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path
import random

import small_terminal_perturbation as solver


HERE = Path(__file__).resolve().parent


def oracle(columns, u_columns, labels, target, weights, row_count, require_nonzero):
    best = None
    for word in range(1 << len(columns)):
        if require_nonzero and not word:
            continue
        z = 0
        for j, label in enumerate(labels):
            if word >> j & 1:
                z ^= label
        b = 0
        for i in range(row_count):
            b |= (sum((word >> j) & 1 for j, column in enumerate(columns)
                      if column >> i & 1) & 1) << i
        for i, column in enumerate(u_columns):
            if z >> i & 1:
                b ^= column
        if b != target:
            continue
        cost = sum(weight for j, weight in enumerate(weights) if word >> j & 1)
        candidate = (cost, word)
        if best is None or candidate < best:
            best = candidate
    return best


def matrix_rows(columns, u_columns, labels, row_count):
    rows = []
    for i in range(row_count):
        base = sum(1 << j for j, column in enumerate(columns) if column >> i & 1)
        perturbation = 0
        for a, u_column in enumerate(u_columns):
            if u_column >> i & 1:
                perturbation ^= sum(1 << j for j, label in enumerate(labels) if label >> a & 1)
        rows.append(base ^ perturbation)
    return rows


def original_oracle(rows, target, weights, require_nonzero):
    best = None
    for word in range(1 << len(weights)):
        if require_nonzero and not word:
            continue
        if any(((row & word).bit_count() & 1) != ((target >> i) & 1)
               for i, row in enumerate(rows)):
            continue
        candidate = (sum(weight for j, weight in enumerate(weights) if word >> j & 1), word)
        if best is None or candidate < best:
            best = candidate
    return best


def run_case(name, columns, u_columns, labels, target, weights, *, row_count=None,
             p=None, require_nonzero=True, limits=None):
    if row_count is None:
        row_count = max([0, target.bit_length(), *(x.bit_length() for x in columns),
                         *(x.bit_length() for x in u_columns)])
    expected = oracle(columns, u_columns, labels, target, weights, row_count, require_nonzero)
    result = solver.solve_perturbation(columns, u_columns, labels, target, weights=weights,
                                       row_count=row_count, p=p,
                                       require_nonzero=require_nonzero, limits=limits)
    if result['status'] == 'EXACT':
        checked = solver.verify_perturbation(columns, u_columns, labels, target, result,
                                             weights=weights, row_count=row_count, p=p,
                                             require_nonzero=require_nonzero)
        if not checked['valid']:
            raise AssertionError((name, checked))
        actual = None if result['weight'] is None else (result['weight'], result['word'])
        if (actual is None) != (expected is None) or (actual is not None and actual[0] != expected[0]):
            raise AssertionError((name, actual, expected))
        status = 'VERIFIED_EXACT'
    else:
        if result.get('certificate') is not None or result.get('weight') is not None or result.get('word') is not None:
            raise AssertionError((name, result))
        checked = None
        status = 'UNKNOWN'
    return {'name': name, 'row_count': row_count, 'columns': list(columns),
            'u_columns': list(u_columns), 'labels': list(labels), 'weights': list(weights),
            'target': target, 'p': p, 'require_nonzero': require_nonzero,
            'limits': limits,
            'expected': None if expected is None else list(expected), 'status': status,
            'weight': result.get('weight'), 'word': result.get('word'),
            'stats': result.get('stats'), 'reason': result.get('reason')}


def run_original_case(name, columns, u_columns, labels, target, weights, *, row_count,
                      p, require_nonzero, limits=None):
    original_rows = matrix_rows(columns, u_columns, labels, row_count)
    expected = original_oracle(original_rows, target, weights, require_nonzero)
    result = solver.solve_original(original_rows, columns, u_columns, labels, target,
                                   weights=weights, row_count=row_count, p=p,
                                   require_nonzero=require_nonzero, limits=limits)
    if result['status'] == 'EXACT':
        checked = solver.verify_original(original_rows, columns, u_columns, labels, target,
                                         result, weights=weights, row_count=row_count, p=p,
                                         require_nonzero=require_nonzero)
        if not checked['valid']:
            raise AssertionError((name, checked))
        actual = None if result['weight'] is None else (result['weight'], result['word'])
        if (actual is None) != (expected is None) or (actual is not None and actual[0] != expected[0]):
            raise AssertionError((name, actual, expected))
        status = 'VERIFIED_EXACT'
    else:
        if result.get('certificate') is not None or result.get('weight') is not None or result.get('word') is not None:
            raise AssertionError((name, result))
        status = 'UNKNOWN'
    return {'name': name, 'adapter': True, 'original_rows': original_rows,
            'row_count': row_count, 'columns': list(columns),
            'u_columns': list(u_columns), 'labels': list(labels), 'weights': list(weights),
            'target': target, 'p': p, 'require_nonzero': require_nonzero,
            'limits': limits, 'expected': None if expected is None else list(expected),
            'status': status, 'weight': result.get('weight'), 'word': result.get('word'),
            'stats': result.get('stats'), 'reason': result.get('reason')}


def main():
    rows = []
    rows.append(run_case('one_edge_inconsistent', [3], [3], [1], 1, [1],
                         require_nonzero=False))
    rows.append(run_case('triangle_wrong_label', [3, 5, 6], [1], [1, 0, 0], 3,
                         [1, 1, 1]))
    rows.append(run_case('zero_rank_loop', [0, 1], [], [0, 0], 0, [0, 3], p=0))
    rows.append(run_case('explicit_branch_cap_unknown', [3], [3], [1], 0, [1],
                         limits={'max_branches': 1}))
    rng = random.Random(2026101819)
    exact = 0
    for index in range(160):
        r = rng.randrange(1, 5)
        m = rng.randrange(0, 7)
        p = rng.randrange(0, 3)
        columns = []
        for _ in range(m):
            support = rng.sample(range(r), rng.randrange(min(2, r) + 1))
            columns.append(sum(1 << i for i in support))
        u_columns = [rng.randrange(1 << r) for _ in range(p)]
        labels = [rng.randrange(1 << p) for _ in range(m)]
        weights = [rng.randrange(4) for _ in range(m)]
        target = rng.randrange(1 << r)
        row = run_case(f'random_{index:03d}', columns, u_columns, labels, target, weights,
                       row_count=r, p=p, require_nonzero=bool(index & 1))
        rows.append(row)
        exact += row['status'] == 'VERIFIED_EXACT'
    adapter_exact = 0
    for index in range(80):
        r = rng.randrange(1, 5)
        m = rng.randrange(0, 7)
        p = rng.randrange(0, 3)
        columns = []
        for _ in range(m):
            support = rng.sample(range(r), rng.randrange(min(2, r) + 1))
            columns.append(sum(1 << i for i in support))
        u_columns = [rng.randrange(1 << r) for _ in range(p)]
        labels = [rng.randrange(1 << p) for _ in range(m)]
        weights = [rng.randrange(4) for _ in range(m)]
        target = rng.randrange(1 << r)
        row = run_original_case(f'adapter_{index:03d}', columns, u_columns, labels, target,
                                weights, row_count=r, p=p, require_nonzero=bool(index & 1))
        rows.append(row)
        adapter_exact += row['status'] == 'VERIFIED_EXACT'
    sources = {}
    for path in (HERE/'small_terminal_perturbation.py', HERE/'test_small_terminal_perturbation.py',
                 HERE/'PERTURBATION_SMALL_TERMINAL_THEOREM.md', HERE/'run_small_terminal_experiments.py',
                 HERE/'verify_small_terminal_results.py',
                 HERE/'labelled_tjoin.py', HERE/'labelled_tables.py'):
        sources[path.name] = sha256(path.read_bytes()).hexdigest()
    output = {'format': 'small-terminal-perturbation-controls-v1',
              'timestamp_utc': datetime.now(timezone.utc).isoformat(),
              'seed': 2026101819, 'random_cases': 160, 'adapter_cases': 80,
              'verified_exact': exact + adapter_exact,
              'random_verified_exact': exact, 'adapter_verified_exact': adapter_exact,
              'unknown': sum(row['status'] == 'UNKNOWN' for row in rows),
              'controls': rows, 'source_sha256': sources,
              'interpretation': 'The solver is exact for a supplied graph B+UV representation with explicit 2**p branch enumeration. UNKNOWN records carry no optimum. This is a parameterized class result, not a general SAT algorithm.'}
    (HERE/'PERTURBATION_SMALL_RESULTS.json').write_text(json.dumps(output, indent=2)+'\n', encoding='utf-8')
    print(json.dumps({key: output[key] for key in ('format', 'random_cases', 'verified_exact', 'unknown')}, indent=2))


if __name__ == '__main__':
    main()
