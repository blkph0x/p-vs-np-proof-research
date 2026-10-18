"""Compare certified compression on the same frozen original requests and caps."""
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys
import time

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE/'compressed_affine_dag_lab'))
from dag import solve_formula, verify_formula

SOURCES = ['run_affine_compression_crosscheck.py', 'compressed_affine_dag_lab/dag.py',
           'affine_sum_compression_lab/compression.py', 'affine_boundary_lab/boundary.py',
           'WEIGHTED_AFFINE_CROSSCHECK.json', 'original_count_reference_lab/RESULTS.json']


def hashes():
    return {name: hashlib.sha256((HERE/name).read_bytes()).hexdigest() for name in SOURCES}


def main():
    before = hashes()
    baseline = json.loads((HERE/'WEIGHTED_AFFINE_CROSSCHECK.json').read_text(encoding='utf-8'))
    reference = json.loads((HERE/'original_count_reference_lab/RESULTS.json').read_text(encoding='utf-8'))
    originals = {r['name']: r for r in reference['cases']}
    rows, summary = [], Counter()
    newly_exact, regressions = [], []
    for old in baseline['cases']:
        n, clauses, caps = old['n'], old['clauses'], old['caps']
        original = originals[old['name']]
        assert n == original['n'] and clauses == original['clauses']
        expected = original['result']['count']
        assert expected == old['expected_count'] == original['independent_control_count']
        started = time.perf_counter()
        result = solve_formula(n, clauses, **caps)
        solve_seconds = time.perf_counter()-started
        check = None
        verify_seconds = None
        if result['status'] == 'EXACT':
            assert result['count'] == expected, (old['name'], result['count'], expected)
            started = time.perf_counter()
            check = verify_formula(n, clauses, result, **caps)
            verify_seconds = time.perf_counter()-started
            assert check['valid'], (old['name'], check)
            summary['exact_original_counts_matched'] += 1
        else:
            assert result['status'] == 'UNKNOWN' and result['count'] is None and result['certificate'] is None
        summary[result['status']] += 1
        if old['result']['status'] == 'UNKNOWN' and result['status'] == 'EXACT':
            newly_exact.append(old['name'])
        if old['result']['status'] == 'EXACT' and result['status'] == 'UNKNOWN':
            regressions.append(old['name'])
        rows.append(dict(name=old['name'], n=n, clauses=clauses, expected_count=expected,
                         original_input_sha256=original['input_sha256'], caps=caps,
                         compression_caps='documented defaults, aggregated over all structural nodes',
                         factor_order='original clause occurrence order', result=result, verification=check,
                         solve_seconds=solve_seconds, verify_seconds=verify_seconds,
                         previous_status=old['result']['status'], previous_stats=old['result']['stats'],
                         previous_solve_seconds=old['elapsed_seconds']))
        print(old['name'], result['status'], result.get('reason', result.get('count')),
              result['stats'], flush=True)
    assert before == hashes(), 'sources changed during comparison; freeze and rerun'
    out = dict(format='compressed-affine-same-original-comparison-v1',
               created_utc=datetime.now(timezone.utc).isoformat(), source_sha256=before,
               sources_unchanged_during_run=True, summary=dict(summary),
               newly_exact=newly_exact, regressions=regressions, cases=rows,
               cap_interpretation='Original work/products/structural-and-marginal-node caps retained. Compression adds charged work and aggregate input/generated/pair/step caps. Retained-piece caps do not assert peak-memory equality; actual live and pending peaks are separate.',
               conclusion='Finite fixed-request comparison; every UNKNOWN and regression retained. No general polynomial decomposition bound.')
    (HERE/'AFFINE_COMPRESSION_CROSSCHECK.json').write_text(json.dumps(out, indent=2)+'\n', encoding='utf-8')
    print(json.dumps({k: out[k] for k in ('summary', 'newly_exact', 'regressions')}, indent=2))


if __name__ == '__main__':
    main()
