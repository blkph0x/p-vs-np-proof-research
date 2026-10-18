"""Fresh consistency audit for the original-formula integration comparison."""
from collections import Counter
from hashlib import sha256
import json
from pathlib import Path
import importlib.util

HERE = Path(__file__).resolve().parent
NIGHT = HERE.parent


def digest(path): return sha256(path.read_bytes()).hexdigest()


def load_engine():
    spec = importlib.util.spec_from_file_location('_comparison_audit_engine', HERE/'dag.py')
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module); return module


def main():
    data = json.loads((HERE/'COMPARISON_RESULTS.json').read_text())
    engine = load_engine()
    assert data['format'] == 'global-recognition-original-comparison-v1'
    assert data['clause_order'] == 'original occurrence order'
    assert data['recognition_policy'] == engine.RECOGNITION_POLICY
    assert data['recognition_caps'] == engine.RECOGNITION_LIMITS
    assert data['recognition_aggregate_caps'] == engine.RECOGNITION_AGGREGATE_LIMITS
    assert len(data['cases']) == 80
    assert Counter(row['dataset'] for row in data['cases']) == {'stress22':22,'original58':58}
    expected_sources = {
        'dag.py': HERE/'dag.py', 'POLICY.md': HERE/'POLICY.md',
        'fast_recognition.py': NIGHT/'affine_fast_recognition_lab'/'fast_recognition.py',
        'one_piece.py': NIGHT/'affine_one_piece_lab'/'one_piece.py',
        'grouping_RESULTS.json': NIGHT/'affine_grouping_plan_lab'/'RESULTS.json',
        'compression_CROSSCHECK.json': NIGHT/'AFFINE_COMPRESSION_CROSSCHECK.json'}
    current = {name:digest(path) for name,path in expected_sources.items()}
    assert current == data['source_hashes_before'] == data['source_hashes_after']
    counts = {name:Counter() for name in ('stress22','original58')}
    previous = {name:Counter() for name in ('stress22','original58')}
    recognition_attempts=recognition_rejections=recognition_exact=0
    for row in data['cases']:
        assert row['status'] == row['result_status'] if row['result_status'] != 'EXACT' else row['status']=='VERIFIED_EXACT'
        assert row['status'] in ('VERIFIED_EXACT','UNKNOWN')
        stats=row['solver_stats']; rec=row['recognition_stats']
        assert all(type(v) is int and v >= 0 for v in rec.values())
        assert rec['recognition_attempts'] >= rec['recognition_exact']+rec['recognition_rejected']
        assert row['result_status'] == 'EXACT' or row['count'] is None
        if row['result_status']=='EXACT': assert row['count'] == row['expected_count'] and row['verification_status']=='VERIFIED'
        else: assert row['verification_status'] is None
        counts[row['dataset']][row['status']] += 1
        previous[row['dataset']][('VERIFIED_EXACT' if row['previous_certified'] else 'UNKNOWN')] += 1
        recognition_attempts += rec['recognition_attempts']; recognition_rejections += rec['recognition_rejected']; recognition_exact += rec['recognition_exact']
        assert stats['work'] >= 0 and row['elapsed_seconds'] >= 0
    assert {k:dict(v) for k,v in counts.items()} == data['summary']
    # The optional stage must preserve exact/unknown coverage on this original-order run.
    assert counts['stress22']['VERIFIED_EXACT'] == previous['stress22']['VERIFIED_EXACT'] == 11
    assert counts['original58']['VERIFIED_EXACT'] == previous['original58']['VERIFIED_EXACT'] == 54
    assert recognition_exact == 0 and recognition_rejections > 0 and recognition_attempts >= recognition_rejections
    output=dict(status='VERIFIED_COMPARISON_BINDINGS', source_hashes=current,
                cases=len(data['cases']), summary=data['summary'],
                recognition_attempts=recognition_attempts,
                recognition_rejections=recognition_rejections,
                recognition_exact=recognition_exact,
                unchanged_coverage=True,
                scope='Fresh hashes, fixed policy, row arithmetic and post-run exact-count checks. No solver rerun or claim of asymptotic improvement.')
    (HERE/'COMPARISON_AUDIT.json').write_text(json.dumps(output,indent=2)+'\n')
    print(json.dumps(output))


if __name__ == '__main__': main()
