"""Reproduce certified incidence-plus-exception minimum-weight experiments.

Large explicit families use native certificates only. Independent codeword
enumeration is bounded to small seeded controls and the six archived k<=14 codes.
Writes NATIVE_RESULTS.json/csv beside this file; never reruns cut enumeration.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
from importlib.util import module_from_spec, spec_from_file_location
from itertools import combinations
import json
from pathlib import Path
import platform
import random
from time import perf_counter

from native_coset_solver import solve_native, verify_native_result


ROOT = Path(__file__).resolve().parent
CHECKPOINT = ROOT.parent


def load_sibling(name):
    path = CHECKPOINT / 'non_graphic_core_lab' / f'{name}.py'
    spec = spec_from_file_location(f'_native_experiment_{name}', path)
    module = module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


DELETION = load_sibling('deletion_solver')
FANO = load_sibling('fano_certificate')


def digest(values):
    """SHA256 of compact UTF-8 JSON, in stored integer-array order."""
    return hashlib.sha256(json.dumps(values, separators=(',', ':')).encode('utf-8')).hexdigest()


def rank_binary(values):
    pivots = {}
    for value in values:
        while value:
            bit = value & -value
            if bit not in pivots:
                pivots[bit] = value
                break
            value ^= pivots[bit]
    return len(pivots)


def rows_from_columns(columns, row_count):
    return tuple(sum(1 << j for j, column in enumerate(columns) if column >> bit & 1)
                 for bit in range(row_count))


def enumeration_reference(generator, n, max_dimension=18):
    """Independent Gray-code enumeration with an explicit size guard."""
    generator = tuple(generator)
    if len(generator) > max_dimension or n > 28:
        raise ValueError('independent enumeration is restricted to bounded small instances')
    started = perf_counter()
    best = None
    current = previous_gray = 0
    for index in range(1, 1 << len(generator)):
        gray = index ^ (index >> 1)
        changed = gray ^ previous_gray
        current ^= generator[changed.bit_length() - 1]
        if current:
            candidate = current.bit_count(), current
            if best is None or candidate < best:
                best = candidate
        previous_gray = gray
    return {'distance': best[0] if best else None, 'word': best[1] if best else None,
            'codewords_visited': 1 << len(generator), 'generator_rows': list(generator),
            'max_dimension': max_dimension, 'seconds': perf_counter() - started}


def checked_native(checks, n, *, max_branches, expected_distance, row_transform=None):
    started = perf_counter()
    result = solve_native(checks, n, max_branches=max_branches, row_transform=row_transform)
    checked = verify_native_result(checks, n, result)
    if not checked['valid']:
        raise ArithmeticError(f'independent native replay failed: {checked}')
    if result['status'] == 'EXACT' and result['distance'] != expected_distance:
        raise ArithmeticError('native exact distance disagrees with independent reference')
    if result['status'] == 'UNKNOWN' and result['distance'] is not None:
        raise ArithmeticError('incomplete search claimed an exact distance')
    if result['word'] is not None:
        word = result['word']
        if not word or word.bit_length() > n or word.bit_count() != result['upper_bound']:
            raise ArithmeticError('invalid original-coordinate witness')
        if any((row & word).bit_count() % 2 for row in checks):
            raise ArithmeticError('native witness violates original parity checks')
        if expected_distance is None or result['upper_bound'] < expected_distance:
            raise ArithmeticError('native upper bound contradicts the reference optimum')
    return {'native_result': result, 'independent_replay': checked,
            'reference_agreement': True, 'original_witness_valid': result['word'] is not None,
            'solve_and_two_verifications_seconds': perf_counter() - started}


def input_record(checks, columns):
    rank = rank_binary(checks)
    return {'n': len(columns), 'parity_check_rank': rank, 'dimension': len(columns) - rank,
            'original_check_rows': list(checks), 'original_columns': list(columns),
            'original_check_rows_sha256': digest(checks), 'original_columns_sha256': digest(columns),
            'matrix_hash_encoding': 'SHA256(compact UTF-8 JSON integer array)'}


def family_case(t):
    started = perf_counter()
    columns = []
    for u, v in combinations(range(t), 2):
        columns.append((1 << u if u < t - 1 else 0) ^ (1 << v if v < t - 1 else 0))
    columns.append(7)
    checks = rows_from_columns(columns, t - 1)
    n = len(columns)
    # Retain the SEVEN COLUMN VALUES 1..7, not coordinates numbered 1..7.
    retained = [columns.index(value) for value in range(1, 8)]
    certificate = {'schema': FANO.SCHEMA, 'n': n, 'matroid_rank': t - 1,
                   'contraction_indices': [], 'retained_indices': retained,
                   'quotient_basis_indices': [columns.index(value) for value in (1, 2, 4)],
                   'quotient_vectors': list(range(1, 8))}
    fano_started = perf_counter()
    fano_check = FANO.verify_fano_certificate(columns, certificate)
    fano_seconds = perf_counter() - fano_started
    if not fano_check['valid']:
        raise ArithmeticError(f'direct F7 restriction certificate failed: {fano_check}')
    native = checked_native(checks, n, max_branches=2, expected_distance=3,
                            row_transform=tuple(1 << j for j in range(t - 1)))
    result = native['native_result']
    if result['exceptional_coordinates'] != [n - 1] or result['branch_count'] != 2:
        raise ArithmeticError('the constructed family must have exactly one exceptional column')
    if result['status'] != 'EXACT':
        raise ArithmeticError('two family branches did not complete')
    return {'kind': 'complete_graph_plus_fano_column', 't': t, **input_record(checks, columns),
            'construction': 'Reduced incidence of K_t, followed by column 7 (binary 111).',
            'native': native, 'fano_certificate': certificate, 'fano_verification': fano_check,
            'fano_verification_seconds': fano_seconds,
            'trellis_bound': {'type': 'THEOREM_DERIVED_LOWER_BOUND', 'width_at_least': t - 2,
                              'states_at_least': 1 << (t - 2), 'states_power_of_two': f'2^{t - 2}',
                              'enumerated': False,
                              'reason': 'Deleting column 7 recovers M(K_t), whose pathwidth is t-2; '
                                        'matroid pathwidth is minor-monotone and invariant under duality.'},
            'codewords_enumerated': False,
            'distance_reference': 'All columns are nonzero and distinct; a K_t triangle has weight 3.',
            'total_seconds': perf_counter() - started}


def archived_cases(branch_cap):
    source_path = CHECKPOINT / 'high_width_core_stress_lab' / 'random_code_audits.json'
    saved_path = CHECKPOINT / 'high_width_core_stress_lab' / 'random_code_results.json'
    source = json.loads(source_path.read_text(encoding='utf-8'))
    saved = {item['n']: item for item in json.loads(saved_path.read_text(encoding='utf-8'))}
    records = []
    for item in source:
        started = perf_counter()
        n, k = item['n'], item['k']
        generator = rows_from_columns(item['columns'], k)
        reference = enumeration_reference(generator, n, max_dimension=14)
        if reference['distance'] != saved[n]['min_distance']:
            raise ArithmeticError('archived distance differs from fresh bounded enumeration')
        checks = DELETION.parity_check(generator, n)
        columns = DELETION.columns_from_rows(checks, n)
        native = checked_native(checks, n, max_branches=branch_cap,
                                expected_distance=reference['distance'])
        records.append({'kind': 'archived_random_code', 'seed': item['seed'],
                        **input_record(checks, columns), 'generator_rows': list(generator),
                        'generator_rows_sha256': digest(generator),
                        'source_generator_columns_sha256': digest(item['columns']),
                        'enumeration': reference, 'prior_distance': saved[n]['min_distance'],
                        'native': native, 'total_seconds': perf_counter() - started})
        result = native['native_result']
        print(f"Archived n={n}, q={len(result['exceptional_coordinates'])}: {result['status']}, "
              f"{len(result['branches'])}/{result['branch_count']} branches, "
              f"distance={result['distance']}, upper_bound={result['upper_bound']}", flush=True)
    return records


def seeded_cases(per_q, seed):
    rng = random.Random(seed)
    records = []
    for q in range(5):
        for repeat in range(per_q):
            started = perf_counter()
            row_count = rng.randrange(3, 6)
            all_graph_columns = [(1 << u if u < row_count else 0) ^
                                 (1 << v if v < row_count else 0)
                                 for u, v in combinations(range(row_count + 1), 2)]
            rng.shuffle(all_graph_columns)
            graph_count = rng.randrange(row_count, min(len(all_graph_columns), 18 - q) + 1)
            columns = all_graph_columns[:graph_count]
            exceptional_values = [value for value in range(1 << row_count) if value.bit_count() > 2]
            columns += [rng.choice(exceptional_values) for _ in range(q)]
            # Shuffle all coordinates so exceptions are not always a terminal block.
            rng.shuffle(columns)
            n = len(columns)
            checks = rows_from_columns(columns, row_count)
            generator = DELETION.parity_check(checks, n)
            reference = enumeration_reference(generator, n)
            native = checked_native(checks, n, max_branches=1 << q,
                                    expected_distance=reference['distance'])
            result = native['native_result']
            if result['status'] != 'EXACT' or len(result['exceptional_coordinates']) != q:
                raise ArithmeticError('small seeded control did not solve all expected exception branches')
            records.append({'kind': 'seeded_mostly_incidence', 'seed': seed, 'q_requested': q,
                            'repeat': repeat, **input_record(checks, columns),
                            'enumeration': reference, 'native': native,
                            'total_seconds': perf_counter() - started})
        print(f'Seeded q={q}: {per_q} exact comparisons passed', flush=True)
    return records


def csv_record(record):
    result = record['native']['native_result']
    bound = record.get('trellis_bound', {})
    return {'kind': record['kind'], 't': record.get('t'), 'seeded_repeat': record.get('repeat'),
            'n': record['n'], 'rank': record['parity_check_rank'], 'dimension': record['dimension'],
            'exceptional_columns': len(result['exceptional_coordinates']),
            'branch_count': result['branch_count'], 'branches_completed': len(result['branches']),
            'status': result['status'], 'distance': result['distance'], 'upper_bound': result['upper_bound'],
            'certificate_verified': record['native']['independent_replay']['valid'],
            'fano_verified': record.get('fano_verification', {}).get('valid'),
            'trellis_bound_type': bound.get('type'), 'trellis_states_at_least': bound.get('states_at_least'),
            'reference_distance': record.get('enumeration', {}).get('distance', 3),
            'enumerated_codewords': record.get('enumeration', {}).get('codewords_visited', 0),
            'solve_seconds': result['solve_seconds'], 'verify_seconds': result['verification_seconds'],
            'total_seconds': record['total_seconds'], 'check_rows_sha256': record['original_check_rows_sha256'],
            'columns_sha256': record['original_columns_sha256']}


def run(args):
    started = perf_counter()
    implementation = [ROOT / name for name in ('run_native_experiments.py', 'native_coset_solver.py',
                                               'matching_certificate.py')]
    implementation += [CHECKPOINT / 'non_graphic_core_lab' / name
                       for name in ('deletion_solver.py', 'fano_certificate.py')]
    archives = [CHECKPOINT / 'high_width_core_stress_lab' / name
                for name in ('random_code_audits.json', 'random_code_results.json')]
    output = {'schema': 'certified_native_coset_experiments_v1', 'python': platform.python_version(),
              'implementation_sha256': {str(path.relative_to(CHECKPOINT)).replace('\\', '/'):
                                        hashlib.sha256(path.read_bytes()).hexdigest() for path in implementation},
              'archived_input_sha256': {str(path.relative_to(CHECKPOINT)).replace('\\', '/'):
                                       hashlib.sha256(path.read_bytes()).hexdigest() for path in archives},
              'parameters': {'family_t': args.family_t, 'random_branch_cap': args.random_branch_cap,
                             'seeded_per_q': args.seeded_per_q, 'seed': args.seed},
              'interpretation': 'Exact claims require replayed complete native certificates. UNKNOWN remains '
                                'UNKNOWN even when its witness reaches the independent optimum. Large-family '
                                'trellis bounds are theorem-derived lower bounds, not enumerated widths.',
              'family': [], 'archived_random': [], 'seeded_small': []}
    for t in args.family_t:
        case = family_case(t)
        output['family'].append(case)
        print(f"Family t={t}, n={case['n']}: EXACT distance 3, two branches, F7 verified, "
              f"trellis states >=2^{t - 2}, {case['total_seconds']:.3f}s", flush=True)
    output['archived_random'] = archived_cases(args.random_branch_cap)
    output['seeded_small'] = seeded_cases(args.seeded_per_q, args.seed)
    records = output['family'] + output['archived_random'] + output['seeded_small']
    output['total_seconds'] = perf_counter() - started
    output['case_count'] = len(records)
    output['exact_count'] = sum(record['native']['native_result']['status'] == 'EXACT' for record in records)
    output['unknown_count'] = len(records) - output['exact_count']
    (ROOT / 'NATIVE_RESULTS.json').write_text(json.dumps(output, indent=2) + '\n', encoding='utf-8')
    with (ROOT / 'NATIVE_RESULTS.csv').open('w', encoding='utf-8', newline='') as handle:
        rows = [csv_record(record) for record in records]
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    print(f"Saved {len(records)} cases: {output['exact_count']} EXACT, {output['unknown_count']} UNKNOWN "
          f"in {output['total_seconds']:.3f}s", flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--family-t', type=int, nargs='+', default=[5, 8, 16, 32, 64, 128])
    parser.add_argument('--random-branch-cap', type=int, default=64)
    parser.add_argument('--seeded-per-q', type=int, default=6)
    parser.add_argument('--seed', type=int, default=20261018)
    args = parser.parse_args()
    if any(t < 5 or t > 128 for t in args.family_t):
        parser.error('family sizes must be between 5 and 128; no large enumeration is permitted')
    if not 0 <= args.random_branch_cap <= 64 or not 1 <= args.seeded_per_q <= 20:
        parser.error('require branch cap 0..64 and seeded repetitions 1..20')
    run(args)
