"""Finite, budgeted plateau/annealing search and expanded native certificate replay.

The saved strict-greedy baseline remains untouched. Annealing starts from the
original parity-check basis, charges all setup/neighbor scores, and records every
attempt. Only a strictly better lexicographic representation replaces a baseline.
There is no global-optimality or general-polynomial-time claim.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
import platform
import random
from time import perf_counter

from row_basis_discovery import (_neighbor_score, _score, _validate, _weights,
                                 verify_row_basis_result)


def anneal_row_basis(check_rows, n, *, max_candidate_evaluations=30000, seed=20261018,
                     cycles=4, perturbation_moves=3, start_temperature=1.1,
                     end_temperature=0.015):
    """Return a verified representation using bounded elementary row-XOR proposals.

    Incumbents minimize the same lexicographic score as the baseline. The scalar
    q + .08*excess + .008*weight controls stochastic acceptance only. Exact-score
    plateaus are traversable. Every evaluated neighbor can improve the incumbent,
    even if its acceptance draw rejects it as the next walk state.
    """
    started = perf_counter()
    original = _validate(check_rows, n)
    for name, value in [('max_candidate_evaluations', max_candidate_evaluations),
                        ('cycles', cycles), ('perturbation_moves', perturbation_moves)]:
        if type(value) is not int or value < (0 if name == 'perturbation_moves' else 1):
            raise ValueError(f'invalid {name}')
    if type(seed) is not int:
        raise ValueError('seed must be an integer')
    for value in [start_temperature, end_temperature]:
        if type(value) not in (int, float) or not math.isfinite(value) or value <= 0:
            raise ValueError('temperatures must be positive finite numbers')
    r = len(original)
    rng = random.Random(seed)
    work = {'candidate_evaluations': 0, 'setup_evaluations': 0, 'neighbor_evaluations': 0,
            'setup_column_bit_visits': 0, 'setup_objective_column_visits': 0,
            'neighbor_column_visits': 0, 'setup_elementary_row_xors': 0,
            'accepted_elementary_row_xors': 0, 'accepted_weight_updates': 0,
            'proposal_random_draws': 0, 'acceptance_random_draws': 0,
            'accepted_plateau_moves': 0, 'accepted_lexicographic_worsenings': 0,
            'accepted_energy_increases': 0}
    rows, transform = list(original), [1 << i for i in range(r)]
    best_rows = best_transform = best_score = original_score = None
    phases, improvements = [], []
    elementary_moves = [(destination, source) for destination in range(r)
                        for source in range(r) if destination != source]
    cycle_count = min(cycles, max_candidate_evaluations)
    for cycle in range(cycle_count):
        if work['candidate_evaluations'] >= max_candidate_evaluations:
            break
        if cycle:
            rows, transform = list(best_rows), list(best_transform)
            for _ in range(perturbation_moves):
                destination, source = elementary_moves[rng.randrange(len(elementary_moves))]
                work['proposal_random_draws'] += 1
                rows[destination] ^= rows[source]
                transform[destination] ^= transform[source]
                work['setup_elementary_row_xors'] += 1
        weights, visits = _weights(rows, n)
        score = _score(weights)
        work['setup_column_bit_visits'] += visits
        work['setup_objective_column_visits'] += 3 * n
        work['candidate_evaluations'] += 1
        work['setup_evaluations'] += 1
        if original_score is None:
            original_score = score
        if best_score is None or score < best_score:
            best_score, best_rows, best_transform = score, tuple(rows), tuple(transform)
            improvements.append({'evaluation': work['candidate_evaluations'], 'objective': list(score),
                                 'kind': 'SETUP', 'cycle': cycle})
        phase = {'cycle': cycle, 'starting_objective': list(score),
                 'setup_evaluation': work['candidate_evaluations'], 'neighbor_evaluations': 0,
                 'accepted_moves': 0, 'temperature_start': start_temperature,
                 'temperature_end': end_temperature}
        phases.append(phase)
        if not elementary_moves:
            phase['ending_objective'] = list(score)
            break
        end_evaluation = max_candidate_evaluations * (cycle + 1) // cycle_count
        proposal_count = max(0, end_evaluation - work['candidate_evaluations'])
        previous_move = None
        for proposal in range(proposal_count):
            choice = rng.randrange(len(elementary_moves))
            work['proposal_random_draws'] += 1
            # Avoid immediately undoing the previous accepted elementary move.
            if choice == previous_move:
                choice = (choice + 1) % len(elementary_moves)
            destination, source = elementary_moves[choice]
            candidate, visits = _neighbor_score(score, weights, rows[source], rows[destination])
            work['candidate_evaluations'] += 1
            work['neighbor_evaluations'] += 1
            work['neighbor_column_visits'] += visits
            phase['neighbor_evaluations'] += 1
            fraction = proposal / max(1, proposal_count - 1)
            temperature = start_temperature * (end_temperature / start_temperature) ** fraction
            energy_delta = (candidate[0] - score[0] + 0.08 * (candidate[1] - score[1])
                            + 0.008 * (candidate[2] - score[2]))
            accepted = energy_delta <= 0
            if not accepted:
                work['acceptance_random_draws'] += 1
                accepted = rng.random() < math.exp(-energy_delta / temperature)
            if candidate < best_score:
                candidate_rows, candidate_transform = list(rows), list(transform)
                candidate_rows[destination] ^= candidate_rows[source]
                candidate_transform[destination] ^= candidate_transform[source]
                best_rows, best_transform, best_score = tuple(candidate_rows), tuple(candidate_transform), candidate
                improvements.append({'evaluation': work['candidate_evaluations'], 'objective': list(candidate),
                                     'kind': 'NEIGHBOR', 'cycle': cycle, 'accepted_into_walk': accepted})
            if accepted:
                work['accepted_plateau_moves'] += candidate == score
                work['accepted_lexicographic_worsenings'] += candidate > score
                work['accepted_energy_increases'] += energy_delta > 0
                changed = rows[source]
                while changed:
                    bit = changed & -changed
                    weights[bit.bit_length() - 1] += -1 if rows[destination] & bit else 1
                    changed ^= bit
                    work['accepted_weight_updates'] += 1
                rows[destination] ^= rows[source]
                transform[destination] ^= transform[source]
                score = candidate
                previous_move = choice
                work['accepted_elementary_row_xors'] += 1
                phase['accepted_moves'] += 1
        phase['ending_objective'] = list(score)
    representation = {'schema': 'row_basis_discovery_v1', 'n': n, 'row_count': r,
                      'row_transform': list(best_transform), 'transformed_check_rows': list(best_rows),
                      'original_objective': list(original_score), 'objective': list(best_score)}
    verification_started = perf_counter()
    verification = verify_row_basis_result(original, n, representation)
    if not verification['valid']:
        raise ArithmeticError(verification)
    verification_seconds = perf_counter() - verification_started
    return {'schema': 'row_basis_annealing_v1', 'representation': representation,
            'verification': verification, 'seed': seed, 'work': work, 'cycles': phases,
            'incumbent_improvements': improvements, 'global_optimum_claimed': False,
            'parameters': {'max_candidate_evaluations': max_candidate_evaluations,
                           'cycles': cycles, 'perturbation_moves': perturbation_moves,
                           'start_temperature': start_temperature, 'end_temperature': end_temperature,
                           'acceptance_energy_weights': [1, 0.08, 0.008]},
            'discovery_seconds': perf_counter() - started - verification_seconds,
            'verification_seconds': verification_seconds}


def _reference(generator):
    if len(generator) > 14:
        raise ValueError('reference enumeration exceeds the archived dimension cap')
    best = None
    word = previous = 0
    for index in range(1, 1 << len(generator)):
        gray = index ^ (index >> 1)
        word ^= generator[(gray ^ previous).bit_length() - 1]
        if word and (best is None or (word.bit_count(), word) < best):
            best = word.bit_count(), word
        previous = gray
    return {'distance': best[0] if best else None, 'word': best[1] if best else None,
            'codewords_visited': 1 << len(generator)}


def _solve_and_replay(checks, n, transform, reference_distance):
    from native_coset_solver import solve_native, verify_native_result
    started = perf_counter()
    result = solve_native(checks, n, row_transform=transform, max_branches=4096)
    replay_started = perf_counter()
    replay = verify_native_result(checks, n, result)
    replay_seconds = perf_counter() - replay_started
    if not replay['valid'] or result['status'] != 'EXACT' or result['distance'] != reference_distance:
        raise ArithmeticError('expanded native solve failed exact reference/replay validation')
    if result['word'] is not None and (not result['word'] or any(
            (result['word'] & row).bit_count() % 2 for row in checks)):
        raise ArithmeticError('expanded native witness violates original parity checks')
    return {'native_result': result, 'independent_replay': replay,
            'independent_replay_seconds': replay_seconds,
            'solve_with_embedded_and_independent_verification_seconds': perf_counter() - started}


def run_experiments():
    root = Path(__file__).resolve().parent
    checkpoint = root
    baseline_path = root / 'ROW_BASIS_RESULTS.json'
    baseline_bytes = baseline_path.read_bytes()
    baseline = json.loads(baseline_bytes)
    paths = [Path(__file__).resolve(), root / 'row_basis_discovery.py', root / 'native_coset_solver.py',
             root / 'matching_certificate.py', baseline_path]
    hashes = {str(path.relative_to(checkpoint)).replace('\\', '/'):
              hashlib.sha256(path.read_bytes()).hexdigest() for path in paths}
    output = {'schema': 'row_basis_escape_experiments_v1', 'python': platform.python_version(),
              'source_sha256': hashes, 'max_native_branches': 4096,
              'heuristic_evaluation_budget': 30000, 'heuristic_seed': 20261018,
              'baseline_artifacts_modified': False, 'global_optimum_claimed': False,
              'baseline_expanded': [], 'escape_attempts': []}
    started = perf_counter()
    # Run discovery first so heuristic outcomes are known before the longer replay.
    for case in baseline['cases']:
        if case['n'] not in (26, 28):
            continue
        attempt = anneal_row_basis(case['original_check_rows'], case['n'],
                                   max_candidate_evaluations=30000, seed=20261018)
        improved = tuple(attempt['representation']['objective']) < tuple(case['discovery']['objective'])
        output['escape_attempts'].append({'n': case['n'], 'attempt': attempt,
                                         'baseline_objective': case['discovery']['objective'],
                                         'strictly_improves_baseline': improved,
                                         'selected_representation': 'ANNEALING' if improved else 'BASELINE'})
        print(f"Annealing n={case['n']}: baseline {case['discovery']['objective']} -> "
              f"{attempt['representation']['objective']}, improved={improved}, "
              f"evaluations={attempt['work']['candidate_evaluations']}, "
              f"search={attempt['discovery_seconds']:.3f}s", flush=True)
    for case in baseline['cases']:
        checks, n, discovery = case['original_check_rows'], case['n'], case['discovery']
        representation_check = verify_row_basis_result(checks, n, discovery)
        if not representation_check['valid']:
            raise ArithmeticError('saved baseline representation failed verification')
        enum_started = perf_counter()
        reference = _reference(case['generator_rows'])
        reference['seconds'] = perf_counter() - enum_started
        if reference['distance'] != case['reference']['distance']:
            raise ArithmeticError('reference distance changed')
        print(f"Expanded baseline n={n}, q={discovery['objective'][0]}: "
              f"solving all {1 << discovery['objective'][0]} branches", flush=True)
        fresh = _solve_and_replay(checks, n, discovery['row_transform'], reference['distance'])
        recorded_discovery_cost = discovery['discovery_seconds'] + discovery['verification_seconds']
        record = {'n': n, 'dimension': case['dimension'], 'original_check_rows': checks,
                  'original_generator_rows': case['generator_rows'], 'row_transform': discovery['row_transform'],
                  'objective': discovery['objective'], 'reference': reference,
                  'representation_verification': representation_check,
                  'recorded_baseline_discovery_and_verification_seconds': recorded_discovery_cost,
                  'recorded_baseline_candidate_evaluations': discovery['work']['candidate_evaluations'],
                  **fresh,
                  'full_cost_using_recorded_discovery_seconds': recorded_discovery_cost
                        + fresh['solve_with_embedded_and_independent_verification_seconds']}
        output['baseline_expanded'].append(record)
        print(f"Expanded baseline n={n}: EXACT distance {fresh['native_result']['distance']}, "
              f"fresh native/replay {fresh['solve_with_embedded_and_independent_verification_seconds']:.3f}s", flush=True)
        attempt_record = next((item for item in output['escape_attempts'] if item['n'] == n), None)
        if attempt_record and attempt_record['strictly_improves_baseline']:
            attempt = attempt_record['attempt']
            representation = attempt['representation']
            # A better lexicographic score cannot increase q beyond the verified baseline's <=12.
            improved = _solve_and_replay(checks, n, representation['row_transform'], reference['distance'])
            attempt_record['native_expanded'] = improved
            attempt_record['reference_distance'] = reference['distance']
            attempt_record['full_discovery_solve_and_verification_seconds'] = (
                attempt['discovery_seconds'] + attempt['verification_seconds']
                + improved['solve_with_embedded_and_independent_verification_seconds'])
            print(f"Selected escape n={n}: EXACT distance {improved['native_result']['distance']}, "
                  f"branches={improved['native_result']['branch_count']}", flush=True)
        # Persist concrete completed cases if the longest baseline is interrupted.
        output['run_complete'] = False
        (root / 'ROW_BASIS_ESCAPE_RESULTS.json').write_text(json.dumps(output, indent=2) + '\n', encoding='utf-8')
    for path in paths:
        key = str(path.relative_to(checkpoint)).replace('\\', '/')
        if hashlib.sha256(path.read_bytes()).hexdigest() != hashes[key]:
            raise RuntimeError(f'source changed during run; rerun for clean provenance: {key}')
    output['run_complete'] = True
    output['total_run_seconds'] = perf_counter() - started
    (root / 'ROW_BASIS_ESCAPE_RESULTS.json').write_text(json.dumps(output, indent=2) + '\n', encoding='utf-8')
    lines = ['# Expanded native certificates and bounded basis escape', '',
             'Date: 2026-10-18. Finite exact instances and bounded heuristic search only. '
             'No global-optimum or general polynomial-time solver claim.', '',
             'The earlier strict-greedy baseline remains unchanged. Its saved, independently verified transforms '
             'are replayed below with an explicit limit of 4,096 branches. Reference enumeration is bounded '
             'to the six archived generator dimensions 9 through 14.', '',
             '| n | Baseline q | Complete branches | Exact distance | Recorded discovery + verification s | Fresh solve + embedded verification + independent replay s | Total using recorded discovery s |',
             '| --- | --- | --- | --- | --- | --- | --- |']
    for case in output['baseline_expanded']:
        lines.append(f"| {case['n']} | {case['objective'][0]} | {case['native_result']['branch_count']} | "
                     f"{case['native_result']['distance']} | {case['recorded_baseline_discovery_and_verification_seconds']:.4f} | "
                     f"{case['solve_with_embedded_and_independent_verification_seconds']:.4f} | "
                     f"{case['full_cost_using_recorded_discovery_seconds']:.4f} |")
    lines += ['', 'The discovery timings above are the saved timings of the prior run, explicitly reused rather '
              'than presented as newly measured. The JSON separates fresh solving, its embedded certificate '
              'verification, and a second independent replay. Reference enumeration timings are separate.', '',
              '## Equal-budget escape attempts', '',
              'One deterministic annealing schedule, seed 20261018, starts afresh from the ORIGINAL parity-check '
              'basis on each of n=26 and n=28. Each attempt has the same 30,000 scored-evaluation cap as the prior '
              'baseline, including initial/restart setup scores. There is no free initialization from the earlier '
              '30,000-evaluation transform and no hidden seed selection.', '',
              'Four cycles cool from temperature 1.1 to 0.015. Between cycles, three elementary row XORs perturb '
              'the current incumbent. Acceptance uses energy q + 0.08 excess + 0.008 total column weight; exact-score '
              'plateaus and some worsening moves are allowed. Incumbents and final selection still use the original '
              'lexicographic tuple. Every evaluated neighbor may improve the incumbent, even if rejected as the walk state.', '',
              '| n | Baseline objective | Escape objective | Scored evaluations | Discovery s | Selected | Native branches | Exact distance | Full new discovery/solve/verification s |',
              '| --- | --- | --- | --- | --- | --- | --- | --- | --- |']
    for item in output['escape_attempts']:
        a = item['attempt']
        native = item.get('native_expanded', {}).get('native_result', {})
        total = item.get('full_discovery_solve_and_verification_seconds')
        lines.append(f"| {item['n']} | {item['baseline_objective']} | {a['representation']['objective']} | "
                     f"{a['work']['candidate_evaluations']} | {a['discovery_seconds']:.4f} | "
                     f"{item['selected_representation']} | {native.get('branch_count', '')} | "
                     f"{native.get('distance', '')} | {f'{total:.4f}' if total is not None else ''} |")
    lines += ['', 'All attempts, including any failures to improve, are retained. Each selected transform is checked '
              'for invertibility and exact equality to P H. Full native branch certificates, original matrices, '
              'reference witnesses, all source/baseline hashes, and detailed work counts are preserved in the JSON. '
              'A smaller finite exception count does not establish a bound on arbitrary inputs.', '',
              'Reproduce with `python row_basis_escape.py`; run independent tests with '
              '`python -m unittest -v test_row_basis_escape`. The production search never enumerates GL(r,2).', '']
    (root / 'ROW_BASIS_ESCAPE_RESULTS.md').write_text('\n'.join(lines), encoding='utf-8')
    return output


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.parse_args()
    run_experiments()
