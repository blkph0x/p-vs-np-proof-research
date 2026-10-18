"""Run the same frozen 22 stress and 58 original requests with a checked order."""
from collections import Counter
from datetime import datetime, timezone
import gc
import gzip
from hashlib import sha256
import importlib.util
import json
from pathlib import Path
import sys
from time import perf_counter

import planner


HERE = Path(__file__).resolve().parent
NIGHT = HERE.parent
SOURCE_PATHS = ['planner.py', 'test_planner.py', 'THEOREM.md', 'run_experiments.py',
    '../compressed_affine_dag_lab/dag.py', '../affine_sum_compression_lab/compression.py',
    '../affine_boundary_lab/boundary.py', '../../proof_motif_candidate_lab/miner.py',
    '../affine_compression_stress_lab/controls.py', '../affine_compression_stress_lab/RESULTS.json',
    '../AFFINE_COMPRESSION_CROSSCHECK.json']


def file_hash(path):
    digest = sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1 << 20), b''):
            digest.update(block)
    return digest.hexdigest()


def source_hashes():
    return {name: file_hash(HERE/name) for name in SOURCE_PATHS}


def load(name, relative):
    spec = importlib.util.spec_from_file_location(name, HERE/relative)
    module = importlib.util.module_from_spec(spec); sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def originals():
    path = NIGHT/'affine_compression_stress_lab'/'RESULTS.json'
    data = json.loads(path.read_text(encoding='utf-8'))
    requests = []
    controls = load('grouping_stress_reference', '../affine_compression_stress_lab/controls.py')
    for index, row in enumerate(data['cases']):
        original = row['original_request']
        reference = controls.verify_control(original)
        assert reference['valid'] and reference['count'] == row['original_count_proof']['count']
        prior = row['compressed']
        requests.append(dict(dataset='stress22', name=original['name'], n=original['n'],
            clauses=original['clauses'], caps=row['caps'], expected_count=reference['count'],
            original_reference=original, reference_verification=reference,
            reference_artifact='../affine_compression_stress_lab/RESULTS.json', reference_case_index=index,
            previous_status=prior['result']['status'], previous_certified=prior['certified_exact'],
            previous_stats=prior['result']['stats']))
    del data
    gc.collect()
    path = NIGHT/'AFFINE_COMPRESSION_CROSSCHECK.json'
    data = json.loads(path.read_text(encoding='utf-8'))
    for index, row in enumerate(data['cases']):
        requests.append(dict(dataset='original58', name=row['name'], n=row['n'], clauses=row['clauses'],
            caps=row['caps'], expected_count=row['expected_count'],
            reference_artifact='../AFFINE_COMPRESSION_CROSSCHECK.json', reference_case_index=index,
            previous_status=row['result']['status'],
            previous_certified=bool(row['verification'] and row['verification']['valid']),
            previous_stats=row['result']['stats']))
    assert Counter(row['dataset'] for row in requests) == {'stress22': 22, 'original58': 58}
    return requests


def alignment(result, groups):
    if result is None or result['status'] != 'EXACT':
        return None
    ownerships = {tuple(node['factor_ids']) for node in result['certificate']['nodes']}
    exact = sum(tuple(sorted(block['occurrence_ids'])) in ownerships for block in groups)
    return dict(groups=len(groups), exact_factor_subtrees=exact, not_exact_factor_subtrees=len(groups)-exact)


def save_artifact(path, payload):
    with path.open('wb') as raw:
        with gzip.GzipFile(filename='', mode='wb', fileobj=raw, mtime=0) as compressed:
            for chunk in json.JSONEncoder(separators=(',', ':')).iterencode(payload):
                compressed.write(chunk.encode('utf-8'))
    return file_hash(path)


def run():
    before = source_hashes()
    requests = originals()
    engine = load('grouping_frozen_compressed_dag', '../compressed_affine_dag_lab/dag.py')
    output = HERE/'certificates'; output.mkdir(exist_ok=True)
    summaries = {name: Counter() for name in ('stress22', 'original58')}
    rows = []
    for index, original in enumerate(requests):
        n, clauses, caps = original['n'], original['clauses'], original['caps']
        started = perf_counter()
        proposal = planner.plan(n, clauses)
        plan_check = planner.verify_plan(n, clauses, proposal)
        plan_seconds = perf_counter()-started
        result, verified, solve_seconds, verify_seconds = None, None, None, None
        certified = False
        if plan_check['valid']:
            started = perf_counter()
            result = engine.solve_formula(n, clauses, order=plan_check['order'], **caps)
            solve_seconds = perf_counter()-started
            if result['status'] == 'EXACT':
                assert result['count'] == original['expected_count'], (original['name'], result['count'])
                started = perf_counter()
                verified = engine.verify_formula(n, clauses, result, order=plan_check['order'], **caps)
                verify_seconds = perf_counter()-started
                assert verified['status'] in ('VERIFIED', 'UNKNOWN'), (original['name'], verified)
                certified = verified['valid']
            else:
                assert result['status'] == 'UNKNOWN' and result['count'] is None and result['certificate'] is None
        status = 'VERIFIED_EXACT' if certified else ('VERIFICATION_UNKNOWN' if result and result['status'] == 'EXACT' else 'UNKNOWN')
        summaries[original['dataset']][status] += 1
        planning_work = proposal['stats']['work']+plan_check['stats']['work']
        solving_work = result['stats']['work'] if result else 0
        replay_work = verified['stats']['work'] if verified else 0
        full = dict(original_request=original, planner_caps=planner.LIMITS,
            proposal=proposal, plan_verification=plan_check, result=result, verification=verified,
            certified_exact=certified, planning_work=planning_work,
            planner_plus_solver_work=planning_work+solving_work,
            total_work_including_solver_replay=planning_work+solving_work+replay_work,
            plan_seconds=plan_seconds, solve_seconds=solve_seconds, verify_seconds=verify_seconds,
            completed_tree_alignment=alignment(result, plan_check.get('groups', [])))
        relative = f'certificates/{index:03d}_{original["dataset"]}.json.gz'
        artifact_hash = save_artifact(HERE/relative, full)
        rows.append(dict(dataset=original['dataset'], name=original['name'], n=n, clauses=len(clauses),
            original_input_sha256=planner.input_hash(n, clauses), reference_artifact=original['reference_artifact'],
            reference_case_index=original['reference_case_index'], artifact=relative, artifact_sha256=artifact_hash,
            status=status, expected_count=original['expected_count'], count=result.get('count') if result else None,
            previous_status=original['previous_status'], previous_certified=original['previous_certified'],
            newly_certified=certified and not original['previous_certified'],
            certification_regression=original['previous_certified'] and not certified,
            planner_stats=proposal['stats'], planner_verification_stats=plan_check['stats'],
            solver_stats=result['stats'] if result else None,
            verification_stats=verified['stats'] if verified else None,
            reason=result.get('reason') if result else proposal.get('reason'),
            planning_work=planning_work, planner_plus_solver_work=planning_work+solving_work,
            total_work_including_solver_replay=planning_work+solving_work+replay_work,
            completed_tree_alignment=full['completed_tree_alignment'],
            plan_seconds=plan_seconds, solve_seconds=solve_seconds, verify_seconds=verify_seconds))
        print(original['dataset'], original['name'], status, 'blocks='+str(proposal['stats']['blocks']),
              'work='+str(planning_work+solving_work), flush=True)
    after = source_hashes()
    assert before == after, 'sources changed during run'
    payload = dict(format='complete-xor3-grouping-fixed-originals-v1',
        timestamp_utc=datetime.now(timezone.utc).isoformat(), source_hashes_before=before,
        source_hashes_after=after, sources_unchanged_during_run=True,
        summary={key: dict(value) for key, value in summaries.items()}, cases=rows,
        newly_certified=[row['name'] for row in rows if row['newly_certified']],
        certification_regressions=[row['name'] for row in rows if row['certification_regression']],
        interpretation='Exact original-clause permutation only. Solver caps unchanged; additional planning/replay work is explicit. No general polynomial-time or optimized-planning claim.')
    (HERE/'RESULTS.json').write_text(json.dumps(payload, indent=2)+'\n', encoding='utf-8')
    lines = ['# Checked XOR3 grouping: fixed original requests', '',
        f"Dataset statuses: {payload['summary']}. Newly certified: {len(payload['newly_certified'])}; regressions: {len(payload['certification_regressions'])}.", '',
        'Only the verified clause occurrence order is passed to the unchanged compressed solver. All original inputs and complete proof replays are in hash-bound gzip JSON files under `certificates/`. Planning is additional work; the unchanged solver cap is not presented as a cap on the entire pipeline.', '',
        '| Dataset / original request | Status | Blocks | Planner + solver work | Exact block subtrees |',
        '|---|---|---:|---:|---:|']
    for row in rows:
        matched = row['completed_tree_alignment']
        structural = f"{matched['exact_factor_subtrees']}/{matched['groups']}" if matched is not None else 'unavailable'
        lines.append(f"| {row['dataset']} / {row['name']} | {row['status']} | {row['planner_stats']['blocks']} | {row['planner_plus_solver_work']} | {structural} |")
    lines += ['', 'All cap failures and regressions remain visible. Complete blocks need not be exact balanced-tree subtrees; the table reports the completed certificate structure rather than assuming alignment. Reference counts enter only post-solve comparisons. No general complexity or runtime claim follows from these finite requests.', '']
    (HERE/'RESULTS.md').write_text('\n'.join(lines), encoding='utf-8')
    print(json.dumps({key: payload[key] for key in ('summary', 'newly_certified', 'certification_regressions')}, indent=2))


if __name__ == '__main__':
    run()
