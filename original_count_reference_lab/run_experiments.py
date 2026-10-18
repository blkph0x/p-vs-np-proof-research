"""Freeze original inputs and independent #SAT references before the new benchmark."""
from collections import Counter
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import time

from reference import solve, verify, request_hash, legacy
from test_reference import truth_count
from independent_oracles import bitset_truth_count, sliding_count

HERE = Path(__file__).resolve().parent
NIGHT = HERE.parent
CHECKPOINT = NIGHT.parent
CAPS = dict(max_states=100000, max_work=10000000, max_depth=400)
SOURCES = ['reference.py', 'test_reference.py', 'independent_oracles.py', 'THEOREM.md', 'run_experiments.py',
           '../ALGEBRAIC_CROSSCHECK.json', '../coefficient_structure_lab/RESULTS.json',
           '../../automatic_parameter_discovery_lab/engine.py',
           '../../automatic_parameter_discovery_lab/parameter_routes.py',
           '../../semantic_branch_dp_lab/engine.py']


def hashes():
    return {name: hashlib.sha256((HERE/name).read_bytes()).hexdigest() for name in SOURCES}


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


def cases():
    old = json.loads((NIGHT/'ALGEBRAIC_CROSSCHECK.json').read_text(encoding='utf-8'))
    rows = [dict(name='earlier_'+r['name'], n=r['n'], clauses=r['clauses'],
                 provenance='ALGEBRAIC_CROSSCHECK.json original formula') for r in old['cases']]
    rows += [dict(name=name, n=n, clauses=c, provenance='original-input edge control')
             for name, n, c in [('empty_zero_variables', 0, []), ('unused_variables', 3, []),
                                ('contradictory_units', 1, [[1], [-1]]), ('empty_clause', 2, [[]]),
                                ('repeated_literal', 1, [[1, 1, 1]]), ('tautological_clause', 1, [[1, -1]])]]
    old = json.loads((NIGHT/'coefficient_structure_lab/RESULTS.json').read_text(encoding='utf-8'))
    for row in old['controls']:
        enc = row['original_encoding']
        rows.append(dict(name='structure_'+row['name'], n=enc['n'], clauses=enc['clauses'],
                         provenance='coefficient_structure_lab/RESULTS.json original formula',
                         previous_slack_status=row['result']['status'],
                         previous_slack_order=row['external_order']))
    semantic = load('count_benchmark_semantic', CHECKPOINT/'semantic_branch_dp_lab/engine.py')
    for connected in (False, True):
        rows.append(dict(name=f'legacy_mixed_12_connected_{connected}', n=72,
                         clauses=[list(c) for c in legacy.mixed_family(12, connect=connected)],
                         provenance='automatic_parameter_discovery_lab.engine.mixed_family',
                         expected_count=0))
    rows.append(dict(name='legacy_sliding_64_radius2_seed17', n=66,
                     clauses=[list(c) for c in semantic.sliding_cnf(64, radius=2, seed=17)],
                     provenance='semantic_branch_dp_lab.engine.sliding_cnf'))
    return rows


def control_reference(case):
    n, clauses = case['n'], case['clauses']
    if n <= 8:
        return truth_count(n, clauses), 'complete original logical assignment enumeration'
    if 'expected_count' in case:
        return case['expected_count'], 'legacy mixed family contradiction from its unit implications'
    if not clauses:
        return 1 << n, 'all original variables are free'
    flat = [v for c in clauses for v in c]
    if all(len(c) == 3 and all(v > 0 for v in c) for c in clauses) and len(set(flat)) == len(flat) == n:
        return 7**len(clauses), 'checked variable-disjoint positive ternary clauses'
    if clauses == [[2*j+1, 2*j+2, 2*j+3] for j in range(len(clauses))] and n == 2*len(clauses)+1:
        a, b = 2, 7
        for _ in range(2, len(clauses)+1):
            a, b = b, 3*b+2*a
        return b, 'checked ternary chain transfer recurrence'
    if clauses == [[1, v] for v in range(2, n+1)]:
        return (1 << (n-1))+1, 'checked positive binary star'
    if clauses == [[u, v] for u in range(1, n+1) for v in range(u+1, n+1)]:
        return n+1, 'checked complete positive binary interaction'
    return None, None


def main():
    before = hashes()
    rows, summary = [], Counter()
    for case in cases():
        n, clauses = case['n'], case['clauses']
        start = time.perf_counter()
        result = solve(n, clauses, **CAPS)
        seconds = time.perf_counter()-start
        expected, evidence = control_reference(case)
        oracle = None
        if expected is None and n <= 32:
            oracle = bitset_truth_count(n, clauses)
        elif expected is None and case['name'] == 'legacy_sliding_64_radius2_seed17':
            oracle = sliding_count(n, clauses)
        if oracle:
            expected, evidence = oracle['count'], oracle['method']
        check = None
        if result['status'] == 'EXACT':
            check = verify(n, clauses, result, **CAPS)
            assert check['valid'], (case['name'], check)
            if expected is not None:
                assert result['count'] == expected, (case['name'], result['count'], expected)
            summary['verified_exact'] += 1
        if expected is not None:
            summary['independent_control_counts'] += 1
        summary[result['status']] += 1
        rows.append({**case, 'input_sha256': request_hash(n, clauses), 'caps': CAPS,
                     'result': result, 'verification': check, 'elapsed_seconds': seconds,
                     'independent_control_count': expected, 'independent_control_method': evidence,
                     'independent_oracle_statistics': oracle})
        print(case['name'], result['status'], result['count'], flush=True)
    after = hashes()
    assert before == after
    out = dict(format='frozen-original-cnf-count-benchmarks-v1', created_utc=datetime.now(timezone.utc).isoformat(),
               source_sha256=before, sources_unchanged_during_run=True,
               interpretation='Counts are original logical #SAT counts, not earlier slack coefficients. Reference is exponential.',
               summary=dict(summary), cases=rows)
    (HERE/'RESULTS.json').write_text(json.dumps(out, indent=2)+'\n', encoding='utf-8')
    print(json.dumps(out['summary']))


if __name__ == '__main__':
    main()
