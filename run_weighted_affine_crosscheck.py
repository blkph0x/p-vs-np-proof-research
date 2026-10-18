"""Measure the weighted affine DAG on the frozen, complete original CNFs."""
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys
import time

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE/'weighted_affine_dag_lab'))
from dag import solve_formula, verify_formula

CAPS = dict(max_terms=256, max_products=100000, max_nodes=4096,
            max_work=3000000, max_variables=1024, max_factors=4096,
            max_integer_bits=100000)
SOURCES = ['run_weighted_affine_crosscheck.py', 'weighted_affine_dag_lab/dag.py',
           'affine_boundary_lab/boundary.py', 'original_count_reference_lab/RESULTS.json',
           'original_count_reference_lab/reference.py', 'original_count_reference_lab/independent_oracles.py']


def hashes():
    return {name: hashlib.sha256((HERE/name).read_bytes()).hexdigest() for name in SOURCES}


def main():
    before = hashes()
    frozen = json.loads((HERE/'original_count_reference_lab/RESULTS.json').read_text(encoding='utf-8'))
    rows, summary = [], Counter()
    for case in frozen['cases']:
        n, clauses = case['n'], case['clauses']
        assert case['result']['status'] == 'EXACT' and case['verification']['valid']
        expected = case['result']['count']
        assert expected == case['independent_control_count']
        start = time.perf_counter()
        result = solve_formula(n, clauses, **CAPS)
        seconds = time.perf_counter()-start
        check = None
        if result['status'] == 'EXACT':
            assert result['count'] == expected, (case['name'], result['count'], expected)
            check = verify_formula(n, clauses, result, **CAPS)
            assert check['valid'], (case['name'], check)
            summary['exact_original_counts_matched'] += 1
        else:
            assert result['status'] == 'UNKNOWN' and result['count'] is None and result['certificate'] is None
        summary[result['status']] += 1
        rows.append(dict(name=case['name'], n=n, clauses=clauses, original_input_sha256=case['input_sha256'],
                         count_mode='original logical #SAT', caps=CAPS, factor_order='original clause occurrence order',
                         expected_count=expected, result=result, verification=check, elapsed_seconds=seconds,
                         previous_slack_status=case.get('previous_slack_status'),
                         comparison_note='Earlier slack status has a different counted quantity; used only as provenance.'))
        print(case['name'], result['status'], result.get('count'), result['stats'], flush=True)
    after = hashes()
    assert before == after, 'sources changed during benchmark; rerun after freeze'
    out = dict(format='weighted-affine-original-crosscheck-v1', created_utc=datetime.now(timezone.utc).isoformat(),
               source_sha256=before, sources_unchanged_during_run=True, summary=dict(summary), cases=rows,
               conclusion='Finite original-input controls only. Caps are UNKNOWN; no bound on general affine-term growth.')
    (HERE/'WEIGHTED_AFFINE_CROSSCHECK.json').write_text(json.dumps(out, indent=2)+'\n', encoding='utf-8')
    print(json.dumps(out['summary']))


if __name__ == '__main__':
    main()
