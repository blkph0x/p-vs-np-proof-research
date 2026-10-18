"""Budgeted row-basis discovery for the incidence-plus-exceptions native route.

Production search uses only elementary row XORs, strict lexicographic descent,
and explicitly counted seeded perturbations. It never asserts a global optimum.
The evaluation budget includes the initial and restart setup scores. Running this
file benchmarks the six archived codes and writes ROW_BASIS_RESULTS.json/md.
"""
from __future__ import annotations

import argparse
import hashlib
from importlib.util import module_from_spec, spec_from_file_location
import json
from pathlib import Path
import platform
import random
from time import perf_counter


def _nonnegative(value, name):
    if type(value) is not int or value < 0:
        raise ValueError(f'{name} must be a nonnegative integer')


def _validate(check_rows, n):
    _nonnegative(n, 'n')
    rows = tuple(check_rows)
    if any(type(row) is not int or row < 0 or row.bit_length() > n for row in rows):
        raise ValueError('checks must be nonnegative n-bit integers')
    return rows


def _weights(rows, n):
    weights = [0] * n
    visits = 0
    for row in rows:
        while row:
            bit = row & -row
            weights[bit.bit_length() - 1] += 1
            visits += 1
            row ^= bit
    return weights, visits


def objective(check_rows, n):
    """(exception count, total excess above weight two, total column weight)."""
    weights, _ = _weights(_validate(check_rows, n), n)
    return _score(weights)


def _score(weights):
    return (sum(weight > 2 for weight in weights),
            sum(max(0, weight - 2) for weight in weights), sum(weights))


def _neighbor_score(score, weights, source_row, destination_row):
    q, excess, total = score
    visits = 0
    while source_row:
        bit = source_row & -source_row
        old = weights[bit.bit_length() - 1]
        new = old + (-1 if destination_row & bit else 1)
        q += int(new > 2) - int(old > 2)
        excess += max(0, new - 2) - max(0, old - 2)
        total += new - old
        source_row ^= bit
        visits += 1
    return (q, excess, total), visits


def _rank_for_verification(values):
    pivots = {}
    xors = 0
    for value in values:
        while value:
            low = value & -value
            if low not in pivots:
                pivots[low] = value
                break
            value ^= pivots[low]
            xors += 1
    return len(pivots), xors


def verify_row_basis_result(check_rows, n, result):
    """Check P invertible, PH equality, and both scores, independently of moves.

    Products are recomputed from original column parities, rather than trusting
    the search's row-XOR trace. This validates the representation, not optimality.
    """
    try:
        original = _validate(check_rows, n)
        r = len(original)
        if not isinstance(result, dict) or result.get('schema') != 'row_basis_discovery_v1':
            raise ValueError('invalid row-basis result schema')
        if type(result.get('n')) is not int or result['n'] != n:
            raise ValueError('coordinate count mismatch')
        if type(result.get('row_count')) is not int or result['row_count'] != r:
            raise ValueError('row count mismatch')
        transform = tuple(result['row_transform'])
        if len(transform) != r or any(type(row) is not int or row < 0 or row.bit_length() > r
                                     for row in transform):
            raise ValueError('transform must be an r-by-r binary matrix')
        rank, xors = _rank_for_verification(transform)
        if rank != r:
            raise ValueError('transform is singular')
        columns = [sum(1 << i for i, row in enumerate(original) if row >> j & 1) for j in range(n)]
        expected = tuple(sum(1 << j for j, column in enumerate(columns)
                             if (combination & column).bit_count() % 2)
                         for combination in transform)
        supplied = _validate(result['transformed_check_rows'], n)
        if supplied != expected:
            raise ValueError('transformed parity checks differ from P times H')
        original_weights = [column.bit_count() for column in columns]
        transformed_weights = [sum((row >> j) & 1 for row in expected) for j in range(n)]
        original_score = [sum(w > 2 for w in original_weights),
                          sum(w - 2 for w in original_weights if w > 2), sum(original_weights)]
        transformed_score = [sum(w > 2 for w in transformed_weights),
                             sum(w - 2 for w in transformed_weights if w > 2), sum(transformed_weights)]
        for key, expected_score in [('original_objective', original_score), ('objective', transformed_score)]:
            supplied_score = result[key]
            if (not isinstance(supplied_score, (list, tuple)) or len(supplied_score) != 3
                    or any(type(value) is not int for value in supplied_score)
                    or list(supplied_score) != expected_score):
                raise ValueError(f'{key} mismatch')
        return {'valid': True, 'errors': [], 'transform_rank': rank,
                'equivalent_original_problem': True, 'rank_xor_reductions': xors,
                'matrix_entry_parity_checks': r * n, 'global_optimality_checked': False}
    except (KeyError, TypeError, ValueError) as exc:
        return {'valid': False, 'errors': [str(exc)]}


def discover_row_basis(check_rows, n, *, max_candidate_evaluations=30000,
                       max_restarts=31, restart_moves=8, seed=20261018):
    """Find a verified equivalent representation within a deterministic budget.

    Every scored transform, including identity and each restart setup, consumes
    one candidate evaluation. Each neighborhood scans ordered row-XOR moves.
    Only strict improvements are accepted within a descent. Restarts perturb the
    incumbent by restart_moves elementary operations and are separately counted.
    """
    started = perf_counter()
    original = _validate(check_rows, n)
    for name, value in [('max_candidate_evaluations', max_candidate_evaluations),
                        ('max_restarts', max_restarts), ('restart_moves', restart_moves)]:
        _nonnegative(value, name)
    if max_candidate_evaluations < 1:
        raise ValueError('at least one evaluation is required to score the initial basis')
    if type(seed) is not int:
        raise ValueError('seed must be an integer')
    r = len(original)
    rng = random.Random(seed)
    work = {'candidate_evaluations': 0, 'neighbor_evaluations': 0,
            'setup_evaluations': 0, 'setup_column_bit_visits': 0,
            'setup_objective_column_visits': 0, 'neighbor_column_visits': 0,
            'restart_elementary_row_xors': 0, 'descent_elementary_row_xors': 0,
            'descent_weight_updates': 0, 'restarts_started': 0,
            'neighborhoods_started': 0, 'neighborhoods_completed': 0,
            'local_minima_reached': 0}
    rows = list(original)
    transform = [1 << i for i in range(r)]
    best_score = original_score = None
    best_rows = best_transform = None
    best_is_local = False
    improvements = []
    descents = []
    termination = None

    def remember(score, local=False):
        nonlocal best_score, best_rows, best_transform, best_is_local
        if best_score is None or score < best_score:
            best_score, best_rows, best_transform = score, tuple(rows), tuple(transform)
            best_is_local = local
            improvements.append({'evaluation': work['candidate_evaluations'], 'objective': list(score),
                                 'restart': work['restarts_started']})
        elif tuple(transform) == best_transform and local:
            best_is_local = True

    for restart in range(max_restarts + 1):
        if work['candidate_evaluations'] == max_candidate_evaluations:
            termination = 'EVALUATION_LIMIT'
            break
        if restart:
            rows, transform = list(best_rows), list(best_transform)
            work['restarts_started'] += 1
            for _ in range(restart_moves):
                destination = rng.randrange(r)
                source = rng.randrange(r - 1)
                if source >= destination:
                    source += 1
                rows[destination] ^= rows[source]
                transform[destination] ^= transform[source]
                work['restart_elementary_row_xors'] += 1
        weights, visits = _weights(rows, n)
        work['setup_column_bit_visits'] += visits
        work['setup_objective_column_visits'] += 3 * n
        score = _score(weights)
        work['setup_evaluations'] += 1
        work['candidate_evaluations'] += 1
        if original_score is None:
            original_score = score
        remember(score)
        descent = {'restart': restart, 'starting_objective': list(score), 'accepted_moves': [],
                   'local_minimum_certified': False}
        descents.append(descent)
        while True:
            work['neighborhoods_started'] += 1
            chosen = None
            complete_scan = True
            for destination in range(r):
                for source in range(r):
                    if source == destination:
                        continue
                    if work['candidate_evaluations'] == max_candidate_evaluations:
                        complete_scan = False
                        break
                    candidate, visits = _neighbor_score(score, weights, rows[source], rows[destination])
                    work['candidate_evaluations'] += 1
                    work['neighbor_evaluations'] += 1
                    work['neighbor_column_visits'] += visits
                    if candidate < score and (chosen is None or (candidate, destination, source) < chosen):
                        chosen = candidate, destination, source
                if not complete_scan:
                    break
            if complete_scan:
                work['neighborhoods_completed'] += 1
            if chosen is not None:
                next_score, destination, source = chosen
                changed = rows[source]
                while changed:
                    bit = changed & -changed
                    weights[bit.bit_length() - 1] += -1 if rows[destination] & bit else 1
                    changed ^= bit
                    work['descent_weight_updates'] += 1
                rows[destination] ^= rows[source]
                transform[destination] ^= transform[source]
                work['descent_elementary_row_xors'] += 1
                descent['accepted_moves'].append({'destination': destination, 'source': source,
                                                  'before': list(score), 'after': list(next_score)})
                score = next_score
                remember(score)
            elif complete_scan:
                work['local_minima_reached'] += 1
                descent['local_minimum_certified'] = True
                remember(score, local=True)
            if not complete_scan:
                termination = 'EVALUATION_LIMIT'
                break
            if chosen is None:
                break
        descent['ending_objective'] = list(score)
        if termination:
            break
        if r < 2:
            termination = 'NO_ROW_XOR_MOVES'
            break
    if termination is None:
        termination = 'RESTART_LIMIT'
    work['row_integer_xors'] = 2 * (work['restart_elementary_row_xors'] + work['descent_elementary_row_xors'])
    result = {'schema': 'row_basis_discovery_v1', 'n': n, 'row_count': r,
              'row_transform': list(best_transform), 'transformed_check_rows': list(best_rows),
              'original_objective': list(original_score), 'objective': list(best_score),
              'termination': termination, 'global_optimum_claimed': False,
              'best_is_row_xor_local_minimum': best_is_local, 'seed': seed,
              'limits': {'max_candidate_evaluations': max_candidate_evaluations,
                         'max_restarts': max_restarts, 'restart_moves': restart_moves},
              'work': work, 'incumbent_improvements': improvements, 'descents': descents,
              'discovery_seconds': perf_counter() - started}
    verification_started = perf_counter()
    result['verification'] = verify_row_basis_result(original, n, result)
    result['verification_seconds'] = perf_counter() - verification_started
    if not result['verification']['valid']:
        raise ArithmeticError(result['verification'])
    return result


def _enumerate(generator):
    if len(generator) > 14:
        raise ValueError('archived reference enumeration is bounded to dimension 14')
    best = None
    word = last = 0
    for index in range(1, 1 << len(generator)):
        gray = index ^ (index >> 1)
        word ^= generator[(gray ^ last).bit_length() - 1]
        if word and (best is None or (word.bit_count(), word) < best):
            best = word.bit_count(), word
        last = gray
    return {'distance': best[0] if best else None, 'word': best[1] if best else None,
            'codewords_visited': 1 << len(generator)}


def run_stored_experiments(max_candidate_evaluations=30000, seed=20261018):
    from native_coset_solver import solve_native, verify_native_result
    root = Path(__file__).resolve().parent
    checkpoint = root
    helper_path = checkpoint / 'charged_work_core_lab' / 'deletion_solver.py'
    spec = spec_from_file_location('_row_basis_helpers', helper_path)
    helper = module_from_spec(spec)
    spec.loader.exec_module(helper)
    input_path = checkpoint / 'high_width_core_stress_lab' / 'random_code_audits.json'
    reference_path = checkpoint / 'high_width_core_stress_lab' / 'random_code_results.json'
    references = {row['n']: row for row in json.loads(reference_path.read_text())}
    paths = [Path(__file__).resolve(), root / 'native_coset_solver.py', root / 'matching_certificate.py',
             helper_path, input_path, reference_path]
    hashes = {str(path.relative_to(checkpoint)).replace('\\', '/'):
              hashlib.sha256(path.read_bytes()).hexdigest() for path in paths}
    started = perf_counter()
    output = {'schema': 'row_basis_discovery_experiments_v1', 'python': platform.python_version(),
              'source_sha256': hashes, 'seed': seed, 'max_candidate_evaluations': max_candidate_evaluations,
              'native_branch_cap': 256, 'global_optimum_claimed': False, 'cases': []}
    for sample in json.loads(input_path.read_text()):
        n, k = sample['n'], sample['k']
        generator = tuple(sum(1 << j for j, column in enumerate(sample['columns']) if column >> i & 1)
                          for i in range(k))
        checks = helper.parity_check(generator, n)
        discovery = discover_row_basis(checks, n, max_candidate_evaluations=max_candidate_evaluations,
                                       max_restarts=31, restart_moves=8, seed=seed)
        reference = _enumerate(generator)
        if reference['distance'] != references[n]['min_distance']:
            raise ArithmeticError('fresh and stored reference distances disagree')
        native = solve_native(checks, n, row_transform=discovery['row_transform'], max_branches=256)
        verified = verify_native_result(checks, n, native)
        if not verified['valid'] or len(native['exceptional_coordinates']) != discovery['objective'][0]:
            raise ArithmeticError('native replay or exception count failed')
        if native['status'] == 'EXACT' and native['distance'] != reference['distance']:
            raise ArithmeticError('native exact answer differs from reference')
        if native['word'] is not None:
            word = native['word']
            if (not word or word.bit_count() != native['upper_bound']
                    or any((word & row).bit_count() % 2 for row in checks)
                    or native['upper_bound'] < reference['distance']):
                raise ArithmeticError('native witness failed original problem validation')
        case = {'n': n, 'dimension': k, 'generator_rows': list(generator),
                'original_check_rows': list(checks),
                'original_check_rows_sha256': hashlib.sha256(json.dumps(checks, separators=(',', ':')).encode()).hexdigest(),
                'discovery': discovery, 'native_result': native, 'native_independent_replay': verified,
                'reference': reference}
        output['cases'].append(case)
        print(f"n={n}: q {discovery['original_objective'][0]} -> {discovery['objective'][0]}, "
              f"evaluations {discovery['work']['candidate_evaluations']}, "
              f"search {discovery['discovery_seconds']:.3f}s; native {native['status']} "
              f"{len(native['branches'])}/{native['branch_count']} branches, "
              f"distance {native['distance']}, upper bound {native['upper_bound']}", flush=True)
    for path in paths:
        key = str(path.relative_to(checkpoint)).replace('\\', '/')
        if hashlib.sha256(path.read_bytes()).hexdigest() != hashes[key]:
            raise RuntimeError(f'source changed during run; rerun for consistent provenance: {key}')
    output['total_seconds'] = perf_counter() - started
    (root / 'ROW_BASIS_RESULTS.json').write_text(json.dumps(output, indent=2) + '\n', encoding='utf-8')
    lines = ['# Bounded automatic row-basis discovery', '',
             'Date: 2026-10-18. These are finite search results, not global optima or a P-versus-NP conclusion.', '',
             'Each search starts from the stored generator-derived parity-check basis. The lexicographic objective is '
             '(number of columns of weight >2, total excess above weight 2, total column weight). '
             'A descent scans elementary destination-row XOR source-row moves and accepts only strict improvement. '
             'Seeded restarts apply eight elementary moves to the incumbent; at most 31 restarts are allowed.', '',
             'The evaluation cap includes the identity score, every scored neighbor, and every restart setup score. '
             'Setup bit visits, scored-column visits, accepted moves, perturbation moves, and completed neighborhoods '
             'are separately counted in the JSON. Counters describe integer operations, not bit complexity.', '',
             '| n | q before | q after | Evaluations | Setups | Restarts | Discovery seconds | Native branches completed/total | Status | Exact distance | Upper bound |',
             '| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |']
    for case in output['cases']:
        d, s = case['discovery'], case['native_result']
        lines.append(f"| {case['n']} | {d['original_objective'][0]} | {d['objective'][0]} | "
                     f"{d['work']['candidate_evaluations']} | {d['work']['setup_evaluations']} | "
                     f"{d['work']['restarts_started']} | {d['discovery_seconds']:.4f} | "
                     f"{len(s['branches'])}/{s['branch_count']} | {s['status']} | "
                     f"{s['distance'] if s['distance'] is not None else ''} | "
                     f"{s['upper_bound'] if s['upper_bound'] is not None else ''} |")
    lines += ['', 'Every saved transform P is independently checked to be square and invertible. '
              'The verifier reconstructs P H from original column parities, checks equality with the emitted matrix, '
              'and independently recomputes the objective. The native solver then receives the ORIGINAL H and P, '
              'and its full certificate is replayed against that original problem. Small reference enumeration '
              '(dimension at most 14) checks exact answers and upper-bound witnesses.', '',
              'Search exhaustion is not a nonexistence result. A completed neighborhood only proves local optimality '
              'under a single row XOR. No exhaustive general-linear-group search occurs in production. '
              'The separate tests use GL(3,2) as a tiny independent audit oracle.', '',
              'Reproduce with `python row_basis_discovery.py`; run tests with '
              '`python -m unittest -v test_row_basis_discovery`. Full matrices, invertible transforms, '
              'descent traces, source hashes, native certificates, and reference witnesses are in '
              '`ROW_BASIS_RESULTS.json`.', '']
    (root / 'ROW_BASIS_RESULTS.md').write_text('\n'.join(lines), encoding='utf-8')
    return output


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--max-candidate-evaluations', type=int, default=30000)
    parser.add_argument('--seed', type=int, default=20261018)
    options = parser.parse_args()
    if not 1 <= options.max_candidate_evaluations <= 30000:
        parser.error('candidate evaluation cap must lie in 1..30000')
    run_stored_experiments(options.max_candidate_evaluations, options.seed)
