"""Replay frozen compact-boundary results against their external original inputs."""
from collections import Counter
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent


def load(name, relative):
    spec = importlib.util.spec_from_file_location(name, HERE/relative)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def read(relative):
    return json.loads((HERE/relative).read_text(encoding='utf-8'))


def main():
    bound, summary = {}, {}
    def bind(folder, mapping):
        for name, expected in mapping.items():
            path = (HERE/folder/name).resolve()
            actual = hashlib.sha256(path.read_bytes()).hexdigest()
            assert actual == expected, ('stale source', str(path))
            key = str(path.relative_to(HERE.parent)).replace('\\', '/')
            assert key not in bound or bound[key] == expected
            bound[key] = expected

    b = load('artifact_boundary', 'affine_boundary_lab/boundary.py')
    r = load('artifact_block_reference', 'affine_boundary_reference/reference.py')
    d = load('artifact_weighted_dag', 'weighted_affine_dag_lab/dag.py')
    c = load('artifact_original_count', 'original_count_reference_lab/reference.py')
    data = read('affine_boundary_lab/RESULTS.json')
    bind('affine_boundary_lab', data['source_sha256'])
    assert data['source_unchanged_during_run']
    counts = Counter()
    for row in data['cases']:
        req, result = row['request'], row['result']
        if result['status'] == 'EXACT':
            assert b.verify_marginal(**req, result=result, **row['caps'])['valid']
            other_req = {k: v for k, v in req.items() if k != 'order'}
            independent = r.marginalize_reference(**other_req)
            assert independent['status'] == 'EXACT'
            assert r.verify_reference(**other_req, result=independent)['valid']
            assert r.equivalent_messages(req['n'], req['retained'], result['message'], independent['message'])['equivalent']
        else:
            assert result['status'] == 'UNKNOWN' and result['message'] is None and result['certificate'] is None
        counts[result['status']] += 1
    summary['one_bit_boundaries_with_independent_block_comparison'] = dict(counts)

    data = read('affine_boundary_reference/RESULTS.json')
    bind('affine_boundary_reference', data['source_sha256'])
    assert data['source_unchanged_during_run']
    counts = Counter()
    for row in data['cases']:
        if row['result']['status'] == 'EXACT':
            assert r.verify_reference(**row['request'], result=row['result'], **row['caps'])['valid']
        else:
            assert row['result']['status'] == 'UNKNOWN' and row['result']['message'] is None
        counts[row['result']['status']] += 1
    summary['block_reference'] = dict(counts)

    data = read('weighted_affine_dag_lab/RESULTS.json')
    assert data['source_hashes_before'] == data['source_hashes_after'] and data['source_unchanged_during_run']
    bind('', data['source_hashes_before'])
    counts = Counter()
    for row in data['cases']:
        req, result = row['original_request'], row['result']
        if result['status'] == 'EXACT':
            if 'clauses' in req:
                check = d.verify_formula(req['n'], req['clauses'], result, **req.get('caps', {}))
            else:
                check = d.verify_factors(req['n'], req['factors'], result, **req.get('caps', {}))
            assert check['valid'] and result['value'] == req['expected']
        else:
            assert result['status'] == 'UNKNOWN' and result['certificate'] is None and result['value'] is None
        counts[result['status']] += 1
    summary['native_and_structured_weighted_dag'] = dict(counts)

    data = read('original_count_reference_lab/RESULTS.json')
    bind('original_count_reference_lab', data['source_sha256'])
    assert data['sources_unchanged_during_run']
    originals = {}
    for row in data['cases']:
        assert c.verify(row['n'], row['clauses'], row['result'], **row['caps'])['valid']
        assert row['result']['count'] == row['independent_control_count']
        assert row['input_sha256'] == c.request_hash(row['n'], row['clauses'])
        originals[row['name']] = row
    summary['original_count_reference_exact'] = len(originals)

    data = read('WEIGHTED_AFFINE_CROSSCHECK.json')
    bind('', data['source_sha256'])
    assert data['sources_unchanged_during_run'] and len(data['cases']) == len(originals)
    counts = Counter()
    names = set()
    for row in data['cases']:
        original = originals[row['name']]
        assert row['name'] not in names
        names.add(row['name'])
        assert row['n'] == original['n'] and row['clauses'] == original['clauses']
        assert row['expected_count'] == original['result']['count']
        result = row['result']
        if result['status'] == 'EXACT':
            assert d.verify_formula(row['n'], row['clauses'], result, **row['caps'])['valid']
            assert result['count'] == row['expected_count']
        else:
            assert result['status'] == 'UNKNOWN' and result['count'] is None and result['certificate'] is None
        counts[result['status']] += 1
    summary['same_original_weighted_dag'] = dict(counts)
    tests = read('AFFINE_BOUNDARY_TEST_SUMMARY.json')
    assert tests['all_tests_passed'] and tests['source_unchanged_during_tests']
    bind('', tests['implementation_sha256'])
    summary['tests_passed'] = tests['test_count']
    reviews = [
        ('affine_boundary_reference/BOUNDARY_CROSSCHECK.json', 'source_unchanged_during_run'),
        ('affine_boundary_reference/INDEPENDENT_REVIEW.json', 'sources_unchanged_during_review'),
        ('original_count_reference_lab/INDEPENDENT_REVIEW.json', 'source_unchanged_during_run'),
        ('weighted_affine_dag_lab/INDEPENDENT_REVIEW.json', 'source_unchanged_during_run')]
    for path, stable_field in reviews:
        reviewed = read(path)
        assert reviewed[stable_field]
        if 'status' in reviewed:
            assert reviewed['status'] == 'PASS'
        if 'verdict' in reviewed:
            assert reviewed['verdict'] == 'PASS'
        bind(str(Path(path).parent), reviewed['source_sha256'])
        bind('', {path: hashlib.sha256((HERE/path).read_bytes()).hexdigest()})
    summary['independent_review_records_with_current_sources'] = len(reviews)
    bind('', {Path(__file__).name: hashlib.sha256(Path(__file__).read_bytes()).hexdigest()})
    for name, expected in bound.items():
        assert hashlib.sha256((HERE.parent/name).read_bytes()).hexdigest() == expected
    out = dict(all_checks_passed=True, created_utc=datetime.now(timezone.utc).isoformat(),
               source_reference_count=len(bound), source_paths_relative_to='checkpoint root',
               source_sha256=bound, summary=summary)
    (HERE/'AFFINE_BOUNDARY_ARTIFACT_AUDIT.json').write_text(json.dumps(out, indent=2)+'\n', encoding='utf-8')
    print(json.dumps(out['summary'], indent=2))
    print('Checked source references:', len(bound))


if __name__ == '__main__':
    main()
