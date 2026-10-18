from collections import Counter
from datetime import datetime, timezone
from hashlib import sha256
import importlib.util
import json
from pathlib import Path
import sys
import time

from controls import fixed_controls, verify_control

HERE = Path(__file__).resolve().parent
SOURCES = ['controls.py', 'test_controls.py', 'THEOREM.md', 'run_experiments.py',
           '../weighted_affine_dag_lab/dag.py', '../compressed_affine_dag_lab/dag.py',
           '../affine_sum_compression_lab/compression.py', '../affine_boundary_lab/boundary.py']
CAPS = dict(max_terms=256, max_products=100000, max_nodes=4096,
            max_work=3000000, max_variables=1024, max_factors=4096,
            max_integer_bits=100000)


def load(name, relative):
    spec = importlib.util.spec_from_file_location(name, HERE/relative)
    mod = importlib.util.module_from_spec(spec); sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


def hashes():
    return {name: sha256((HERE/name).read_bytes()).hexdigest() for name in SOURCES}


def main():
    before = hashes()
    engines = {'baseline': load('stress_old_weighted_dag', '../weighted_affine_dag_lab/dag.py'),
               'compressed': load('stress_compressed_dag', '../compressed_affine_dag_lab/dag.py')}
    summaries = {name: Counter() for name in engines}
    rows = []
    for original in fixed_controls():
        ground_truth = verify_control(original)
        row = dict(original_request=original, original_count_proof=ground_truth, caps=CAPS)
        for name, engine in engines.items():
            started = time.perf_counter()
            result = engine.solve_formula(original['n'], original['clauses'], **CAPS)
            solve_seconds = time.perf_counter()-started
            checked = None
            verify_seconds = None
            certified = False
            if result['status'] == 'EXACT':
                assert result['count'] == ground_truth['count'], (original['name'], name, result['count'])
                started = time.perf_counter()
                checked = engine.verify_formula(original['n'], original['clauses'], result, **CAPS)
                verify_seconds = time.perf_counter()-started
                assert checked['status'] in ('VERIFIED', 'UNKNOWN'), (original['name'], name, checked)
                certified = checked['valid']
                summaries[name]['verified_exact' if certified else 'verification_unknown'] += 1
            else:
                assert result['status'] == 'UNKNOWN' and result['count'] is None and result['certificate'] is None
            summaries[name][result['status']] += 1
            row[name] = dict(result=result, verification=checked, certified_exact=certified,
                             solve_seconds=solve_seconds, verify_seconds=verify_seconds)
            print(original['name'], name, result['status'], result.get('reason', result.get('count')),
                  'verified='+str(certified), flush=True)
        rows.append(row)
    assert before == hashes(), 'sources changed during stress run'
    newly_exact = [r['original_request']['name'] for r in rows if r['compressed']['certified_exact'] and not r['baseline']['certified_exact']]
    regressions = [r['original_request']['name'] for r in rows if r['baseline']['certified_exact'] and not r['compressed']['certified_exact']]
    out = dict(format='original-cnf-affine-compression-stress-v1', created_utc=datetime.now(timezone.utc).isoformat(),
               source_sha256=before, sources_unchanged_during_run=True, caps=CAPS,
               summary={name: dict(values) for name, values in summaries.items()},
               newly_certified_exact=newly_exact, certification_regressions=regressions, cases=rows,
               interpretation='Additional independently counted original controls. No expander, generic-hardness or general polynomial-time claim. All cap failures retained.')
    (HERE/'RESULTS.json').write_text(json.dumps(out, indent=2)+'\n', encoding='utf-8')
    print(json.dumps({k: out[k] for k in ('summary', 'newly_certified_exact', 'certification_regressions')}, indent=2))


if __name__ == '__main__':
    main()
