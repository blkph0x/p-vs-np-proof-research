"""Independently replay the saved small-terminal perturbation controls."""
from copy import deepcopy
from hashlib import sha256
import json
from pathlib import Path

import small_terminal_perturbation as solver


HERE = Path(__file__).resolve().parent


def direct(columns, u_columns, labels, weights, target, row_count, nonempty):
    best = None
    for word in range(1 << len(columns)):
        if nonempty and word == 0:
            continue
        z = 0
        for j, label in enumerate(labels):
            if word >> j & 1:
                z ^= label
        rhs = sum((((sum((word >> j) & 1 for j, col in enumerate(columns)
                          if col >> i & 1)) & 1) << i) for i in range(row_count))
        for i, col in enumerate(u_columns):
            if z >> i & 1:
                rhs ^= col
        if rhs != target:
            continue
        cost = sum(weight for j, weight in enumerate(weights) if word >> j & 1)
        candidate = (cost, word)
        if best is None or candidate < best:
            best = candidate
    return best


def direct_original(rows, weights, target, nonempty):
    best = None
    for word in range(1 << len(weights)):
        if nonempty and word == 0:
            continue
        if any(((row & word).bit_count() & 1) != ((target >> i) & 1)
               for i, row in enumerate(rows)):
            continue
        candidate = (sum(weight for j, weight in enumerate(weights) if word >> j & 1), word)
        if best is None or candidate < best:
            best = candidate
    return best


def main():
    artifact = json.loads((HERE/'PERTURBATION_SMALL_RESULTS.json').read_text(encoding='utf-8'))
    source_files = ('small_terminal_perturbation.py', 'test_small_terminal_perturbation.py',
                    'run_small_terminal_experiments.py', 'verify_small_terminal_results.py',
                    'PERTURBATION_SMALL_TERMINAL_THEOREM.md', 'labelled_tjoin.py', 'labelled_tables.py')
    current = {name: sha256((HERE/name).read_bytes()).hexdigest() for name in source_files}
    checks = 0
    for saved in artifact['controls']:
        columns = saved['columns']; u = saved['u_columns']; labels = saved['labels']
        weights = saved['weights']; target = saved['target']; row_count = saved['row_count']
        p = saved['p']; nonempty = saved['require_nonzero']
        if saved.get('adapter'):
            expected = direct_original(saved['original_rows'], weights, target, nonempty)
            result = solver.solve_original(saved['original_rows'], columns, u, labels, target,
                                           weights=weights, row_count=row_count, p=p,
                                           require_nonzero=nonempty, limits=saved.get('limits'))
        else:
            expected = direct(columns, u, labels, weights, target, row_count, nonempty)
            result = solver.solve_perturbation(columns, u, labels, target, weights=weights,
                                               row_count=row_count, p=p, require_nonzero=nonempty,
                                               limits=saved.get('limits'))
        if saved['status'] == 'UNKNOWN':
            if result['status'] != 'UNKNOWN':
                raise AssertionError((saved['name'], 'saved UNKNOWN changed status'))
        else:
            if result['status'] != 'EXACT':
                raise AssertionError((saved['name'], result))
            if saved.get('adapter'):
                checked = solver.verify_original(saved['original_rows'], columns, u, labels,
                                                target, result, weights=weights,
                                                row_count=row_count, p=p,
                                                require_nonzero=nonempty)
            else:
                checked = solver.verify_perturbation(columns, u, labels, target, result,
                                                     weights=weights, row_count=row_count, p=p,
                                                     require_nonzero=nonempty)
            if not checked['valid']:
                raise AssertionError((saved['name'], checked))
            if expected is None:
                if result['weight'] is not None:
                    raise AssertionError((saved['name'], 'false feasible result'))
            elif result['weight'] != expected[0]:
                raise AssertionError((saved['name'], result['weight'], expected))
            checks += 1
    # Rebuild a certificate and reject independent metadata and nested-proof edits.
    exact = solver.solve_perturbation([3, 5], [1], [1, 0], 0, weights=[2, 1], p=1)
    changed = deepcopy(exact)
    changed['certificate']['branches'][0]['rhs'] ^= 1
    if solver.verify_perturbation([3, 5], [1], [1, 0], 0, changed,
                                  weights=[2, 1], p=1)['valid']:
        raise AssertionError('branch metadata mutation accepted')
    changed = deepcopy(exact)
    changed['certificate']['branches'][0]['result']['weight'] = 99
    if solver.verify_perturbation([3, 5], [1], [1, 0], 0, changed,
                                  weights=[2, 1], p=1)['valid']:
        raise AssertionError('nested proof mutation accepted')
    output = {'status': 'PASS', 'saved_controls': len(artifact['controls']),
              'exact_controls_replayed': checks,
              'saved_status_counts': {'VERIFIED_EXACT': artifact['verified_exact'],
                                      'UNKNOWN': artifact['unknown']},
              'source_hashes_current': current,
              'source_hashes_saved': artifact['source_sha256'],
              'source_unchanged': current == artifact['source_sha256'],
              'mutation_controls': 2}
    (HERE/'PERTURBATION_SMALL_AUDIT.json').write_text(json.dumps(output, indent=2)+'\n', encoding='utf-8')
    print(json.dumps(output, indent=2))


if __name__ == '__main__':
    main()
