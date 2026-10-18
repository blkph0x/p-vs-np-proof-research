"""Run the predeclared optional recognizer on the frozen original formulas.

This runner reads the 22 stress and 58 earlier requests from their existing
hash-bound records, uses original clause occurrence order, and compares only
after each fresh run. It does not supply expected answers to the solver.
"""
from collections import Counter
from datetime import datetime, timezone
from hashlib import sha256
import gzip
import importlib.util
import json
from pathlib import Path
import sys
import time

HERE = Path(__file__).resolve().parent
NIGHT = HERE.parent


def digest(path):
    return sha256(path.read_bytes()).hexdigest()


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def requests():
    grouped = json.loads((NIGHT/'affine_grouping_plan_lab'/'RESULTS.json').read_text())
    rows = []
    for row in grouped['cases']:
        if row['dataset'] != 'stress22':
            continue
        with gzip.open(NIGHT/'affine_grouping_plan_lab'/row['artifact'], 'rt', encoding='utf-8') as stream:
            artifact = json.load(stream)
        original = artifact['original_request']
        rows.append(dict(dataset='stress22', name=row['name'], n=original['n'],
                         clauses=original['clauses'], caps=original['caps'],
                         expected_count=row['expected_count'], previous_status=row['previous_status'],
                         previous_certified=row['previous_certified'],
                         grouped_status=row['status'], grouped_certified=row['status']=='VERIFIED_EXACT',
                         source_artifact=row['artifact'], source_artifact_sha256=row['artifact_sha256']))
    earlier = json.loads((NIGHT/'AFFINE_COMPRESSION_CROSSCHECK.json').read_text())
    for row in earlier['cases']:
        rows.append(dict(dataset='original58', name=row['name'], n=row['n'], clauses=row['clauses'],
                         caps=row['caps'], expected_count=row['expected_count'],
                         previous_status=row['result']['status'],
                         previous_certified=bool(row['verification'] and row['verification']['valid']),
                         grouped_status=None, grouped_certified=None,
                         source_artifact='AFFINE_COMPRESSION_CROSSCHECK.json',
                         source_artifact_sha256=digest(NIGHT/'AFFINE_COMPRESSION_CROSSCHECK.json')))
    assert len(rows) == 80 and Counter(row['dataset'] for row in rows) == {'stress22': 22, 'original58': 58}
    return rows


def main():
    engine = load('global_comparison_engine', HERE/'dag.py')
    before = {
        'dag.py': digest(HERE/'dag.py'),
        'POLICY.md': digest(HERE/'POLICY.md'),
        'fast_recognition.py': digest(NIGHT/'affine_fast_recognition_lab'/'fast_recognition.py'),
        'one_piece.py': digest(NIGHT/'affine_one_piece_lab'/'one_piece.py'),
        'grouping_RESULTS.json': digest(NIGHT/'affine_grouping_plan_lab'/'RESULTS.json'),
        'compression_CROSSCHECK.json': digest(NIGHT/'AFFINE_COMPRESSION_CROSSCHECK.json'),
    }
    policy = dict(engine.RECOGNITION_POLICY)
    caps = dict(engine.RECOGNITION_LIMITS)
    aggregate = dict(engine.RECOGNITION_AGGREGATE_LIMITS)
    started = datetime.now(timezone.utc).isoformat()
    rows = []
    summary = {dataset: Counter() for dataset in ('stress22', 'original58')}
    for request in requests():
        tick = time.perf_counter()
        result = engine.solve_formula(request['n'], request['clauses'],
                                      recognition_policy=policy,
                                      recognition_caps=caps,
                                      recognition_aggregate_caps=aggregate,
                                      **request['caps'])
        elapsed = time.perf_counter()-tick
        status = ('VERIFIED_EXACT' if result['status']=='EXACT' and result.get('certificate') is not None
                  else ('UNKNOWN' if result['status']=='UNKNOWN' else result['status']))
        # The expected count is checked only after the solver's exact result is produced.
        if result['status'] == 'EXACT':
            assert result['count'] == request['expected_count'], (request['name'], result['count'], request['expected_count'])
            checked = engine.verify_formula(request['n'], request['clauses'], result,
                                            recognition_policy=policy,
                                            recognition_caps=caps,
                                            recognition_aggregate_caps=aggregate,
                                            **request['caps'])
            assert checked['valid'], (request['name'], checked)
            verification_status = 'VERIFIED'
        else:
            assert result['status']=='UNKNOWN' and result.get('certificate') is None and result.get('count') is None
            checked = None
            verification_status = None
        summary[request['dataset']][status] += 1
        recognition = {key:value for key,value in result['stats'].items() if key.startswith('recognition_')}
        rows.append(dict(dataset=request['dataset'], name=request['name'], n=request['n'],
                         clauses=len(request['clauses']), expected_count=request['expected_count'],
                         previous_status=request['previous_status'], previous_certified=request['previous_certified'],
                         grouped_status=request['grouped_status'], grouped_certified=request['grouped_certified'],
                         status=status, result_status=result['status'], count=result.get('count'),
                         verification_status=verification_status, elapsed_seconds=elapsed,
                         solver_stats=result['stats'], recognition_stats=recognition,
                         source_artifact=request['source_artifact'], source_artifact_sha256=request['source_artifact_sha256']))
        print(request['dataset'], request['name'], status,
              'recognition_attempts='+str(recognition['recognition_attempts']),
              'recognition_exact='+str(recognition['recognition_exact']),
              'recognition_rejected='+str(recognition['recognition_rejected']),
              'work='+str(result['stats']['work']), flush=True)
    after = {
        'dag.py': digest(HERE/'dag.py'),
        'POLICY.md': digest(HERE/'POLICY.md'),
        'fast_recognition.py': digest(NIGHT/'affine_fast_recognition_lab'/'fast_recognition.py'),
        'one_piece.py': digest(NIGHT/'affine_one_piece_lab'/'one_piece.py'),
        'grouping_RESULTS.json': digest(NIGHT/'affine_grouping_plan_lab'/'RESULTS.json'),
        'compression_CROSSCHECK.json': digest(NIGHT/'AFFINE_COMPRESSION_CROSSCHECK.json'),
    }
    assert before == after
    output = dict(format='global-recognition-original-comparison-v1',
                  timestamp_utc=started, finished_utc=datetime.now(timezone.utc).isoformat(),
                  source_hashes_before=before, source_hashes_after=after,
                  sources_unchanged_during_run=True, clause_order='original occurrence order',
                  recognition_policy=policy, recognition_caps=caps,
                  recognition_aggregate_caps=aggregate, summary={k:dict(v) for k,v in summary.items()},
                  cases=rows,
                  interpretation='Optional recognizer is attempted only after mandatory greedy output. Existing solver limits and original factors are retained. Counts are comparisons after fresh exact results; UNKNOWN remains UNKNOWN. This finite benchmark is not a polynomial-time claim.')
    (HERE/'COMPARISON_RESULTS.json').write_text(json.dumps(output, indent=2)+'\n')
    print(json.dumps(output['summary'], indent=2))


if __name__ == '__main__':
    main()
