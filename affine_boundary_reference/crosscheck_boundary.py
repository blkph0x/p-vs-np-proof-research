"""Replay every frozen production boundary output with the independent block oracle."""
from hashlib import sha256
import json
from pathlib import Path

from reference import equivalent_messages, marginalize_reference, verify_reference

HERE = Path(__file__).resolve().parent
PRODUCTION = HERE.parent/'affine_boundary_lab'


def hashes():
    source = json.loads((PRODUCTION/'RESULTS.json').read_text(encoding='utf-8'))
    out = {'reference.py': sha256((HERE/'reference.py').read_bytes()).hexdigest(),
           'crosscheck_boundary.py': sha256(Path(__file__).read_bytes()).hexdigest(),
           '../affine_boundary_lab/RESULTS.json': sha256((PRODUCTION/'RESULTS.json').read_bytes()).hexdigest()}
    for name, expected in source['source_sha256'].items():
        actual = sha256((PRODUCTION/name).read_bytes()).hexdigest()
        assert actual == expected
        out['../affine_boundary_lab/'+name] = actual
    return out


def run():
    before = hashes()
    source = json.loads((PRODUCTION/'RESULTS.json').read_text(encoding='utf-8'))
    records = []
    summary = dict(production_exact=0, production_unknown=0, reference_verified=0,
                   symbolically_equal=0, largest_retained=0)
    for index, case in enumerate(source['cases']):
        request = dict(case['request'])
        request.pop('order', None)  # Block elimination has its own independent order.
        result = case['result']
        if result['status'] != 'EXACT':
            assert result['message'] is None and result['certificate'] is None
            summary['production_unknown'] += 1
            records.append(dict(index=index, name=case['name'], status='UNKNOWN', claim=None))
            continue
        summary['production_exact'] += 1
        summary['largest_retained'] = max(summary['largest_retained'], len(request['retained']))
        reference = marginalize_reference(**request, max_work=20000000)
        assert reference['status'] == 'EXACT', case['name']
        verified = verify_reference(request['n'], request['retained'], request['equations'], request['phase'],
                                    request.get('scalar', 1), reference, active=request.get('active'), max_work=20000000)
        assert verified['valid'], (case['name'], verified)
        comparison = equivalent_messages(request['n'], request['retained'], reference['message'], result['message'], max_work=20000000)
        assert comparison['status'] == 'EXACT' and comparison['equivalent'], (case['name'], comparison)
        summary['reference_verified'] += 1
        summary['symbolically_equal'] += 1
        records.append(dict(index=index, name=case['name'], status='EXACT',
                            reference_request_sha256=reference['certificate']['input_sha256'],
                            reference_message=reference['message'], reference_stats=reference['stats'],
                            reference_verification=verified, comparison=comparison))
    after = hashes()
    assert before == after
    report = dict(schema='independent-boundary-block-crosscheck-v1', source_sha256=after,
                  source_unchanged_during_run=True, original_requests='../affine_boundary_lab/RESULTS.json',
                  reference_work_cap=20000000, summary=summary, cases=records)
    (HERE/'BOUNDARY_CROSSCHECK.json').write_text(json.dumps(report, indent=2)+'\n', encoding='utf-8')
    (HERE/'BOUNDARY_CROSSCHECK.md').write_text(
        '# Independent frozen-boundary artifact cross-check\n\n'
        'All 96 saved EXACT production messages were independently recomputed by the block '
        'support-parametrization/internal-pair algorithm, checked by its left-nullspace and '
        'pair-identity verifier, and compared symbolically with the production messages. '
        'All agree, including a 512-coordinate retained boundary. No boundary truth table '
        'was expanded for those wide cases.\n\n'
        'The six production UNKNOWN records contain no message or certificate. Each exact '
        'case used a separate reference work cap of 20,000,000; this validates the function '
        'and does not assert identical cost or success under the production caps.\n\n'
        'BOUNDARY_CROSSCHECK.json records the source/result hashes, original-case indices, '
        'reference input bindings, recomputed messages and verification outcomes. The original '
        'requests remain in the hash-bound production RESULTS.json. The replay script is '
        'crosscheck_boundary.py. All hashed inputs were unchanged during the run. This is '
        'a reproducible validation report, not a proof-assistant formalization.\n', encoding='utf-8')
    print(json.dumps(summary, sort_keys=True))


if __name__ == '__main__':
    run()
