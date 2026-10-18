"""Saved original requests, full proofs and exact analytic controls."""
from datetime import datetime, timezone
from fractions import Fraction
from hashlib import sha256
import json
from pathlib import Path
from time import perf_counter

import dag


HERE = Path(__file__).resolve().parent


def affine(scope, equations=(), phase=(), scalar=1):
    return {'kind': 'affine', 'scope': list(scope), 'equations': [list(r) for r in equations],
            'phase': list(phase), 'scalar': dag.pack(scalar)}


def cases():
    out = []
    for m in (1, 4, 16, 64, 128):
        out.append(dict(name=f'shared_pair_private_clause_{m}', n=m+2,
                        clauses=[[1, 2, i+3] for i in range(m)],
                        expected=dag.pack(3*(1 << m)+1),
                        reference='If x or y is true, all private bits are free; otherwise every private bit is forced true.'))
    for width in (1, 3, 32, 128):
        n = width+1
        factors = [affine(range(n), [], [(1 << width) | (1 << i) for i in range(width)]),
                   {'kind': 'or', 'literals': list(range(1, width+1))}]
        out.append(dict(name=f'phase_induced_even_boundary_{width}', n=n, factors=factors,
                        expected=dag.pack((1 << width)-2),
                        reference='Summing the internal phase bit gives twice the even-parity boundary indicator; OR excludes the all-zero boundary.'))
    for width in (4, 32, 128):
        scope = list(range(width))
        rows = [[(1 << width)-1, 0]]
        phase = [(1 << i) | (1 << (i+1)) for i in range(width-1)]
        factors = [affine(scope, rows, phase, Fraction(-3, 5)),
                   affine(scope, rows, phase, Fraction(7, 11))]
        out.append(dict(name=f'wide_signed_phase_product_{width}', n=width, factors=factors,
                        expected=dag.pack(Fraction(-21, 55)*(1 << (width-1))),
                        reference='The two equal phases cancel and duplicate parity supports agree; exactly half of all boundary assignments remain.'))
    out += [dict(name='negative_constant_free_universe', n=9,
                 factors=[affine([], [], [0], Fraction(3, 7))], expected=dag.pack(Fraction(-3, 7)*512),
                 reference='A constant negative phase times all 512 original assignments.'),
            dict(name='signed_phase_zero_sum', n=9, factors=[affine([0], [], [1])],
                 expected=[0, 1], reference='The two values of the phase bit cancel; other original variables are free.')]
    for m, cap in ((2, 256), (6, 256), (12, 16)):
        factors = [{'kind': 'or', 'literals': [2*i+1, 2*i+2]} for i in range(m)]
        factors.append(affine(range(2*m), [[(1 << (2*m))-1, 0]]))
        out.append(dict(name=f'paired_ors_global_even_{m}_cap_{cap}', n=2*m, factors=factors,
                        expected=dag.pack((3**m+(-1)**m)//2), caps={'max_terms': cap},
                        reference='Each accepted pair has one even and two odd assignments; even total parity has (3^m+(-1)^m)/2 assignments.'))
    out.append(dict(name='products_before_merge_cap', n=2, clauses=[[1, 2], [1, 2]],
                    expected=[3, 1], caps={'max_products': 3},
                    reference='The repeated OR has three assignments, but the requested cap excludes the four mandatory pre-merge products.'))
    return out


def source_hashes():
    paths = [HERE/'dag.py', HERE/'test_dag.py', HERE/'run_experiments.py', HERE/'THEOREM.md',
             HERE.parent/'affine_boundary_lab'/'boundary.py']
    return {str(p.relative_to(HERE.parent)).replace('\\', '/'): sha256(p.read_bytes()).hexdigest() for p in paths}


def run():
    before = source_hashes()
    results = []
    for request in cases():
        caps = request.get('caps', {})
        started = perf_counter()
        if 'clauses' in request:
            result = dag.solve_formula(request['n'], request['clauses'], **caps)
            checked = dag.verify_formula(request['n'], request['clauses'], result, **caps)
        else:
            result = dag.solve_factors(request['n'], request['factors'], **caps)
            checked = dag.verify_factors(request['n'], request['factors'], result, **caps)
        elapsed = perf_counter()-started
        if result['status'] == 'EXACT':
            assert result['value'] == request['expected'], request['name']
            assert checked['valid'], (request['name'], checked)
        else:
            assert result['status'] == 'UNKNOWN' and not checked['valid']
            assert result['value'] is None and result['certificate'] is None
        results.append({'original_request': request, 'result': result, 'verification': checked,
                        'produce_and_verify_seconds': elapsed})
    after = source_hashes()
    assert before == after
    exact = sum(row['result']['status'] == 'EXACT' for row in results)
    payload = {'format': 'weighted-affine-dag-experiments-v1',
               'timestamp_utc': datetime.now(timezone.utc).isoformat(),
               'source_hashes_before': before, 'source_hashes_after': after,
               'source_unchanged_during_run': True,
               'case_count': len(results), 'exact_count': exact, 'unknown_count': len(results)-exact,
               'cases': results}
    (HERE/'RESULTS.json').write_text(json.dumps(payload, indent=2)+'\n', encoding='utf-8')
    lines = ['# Weighted affine DAG saved controls', '',
             f'{len(results)} original requests: {exact} EXACT with independently replayed certificates; {len(results)-exact} UNKNOWN.', '',
             'Every exact value agrees with the analytic formula stated with its original input. These are deliberately structured controls, not a general complexity or speed claim. Full inputs, all exact certificates, source hashes, and elapsed wall-clock times are in `RESULTS.json`.', '',
             '| Original request | Status | Exact value or stopping reason | Peak pieces | Pre-merge products |',
             '|---|---|---|---:|---:|']
    for row in results:
        req, result = row['original_request'], row['result']
        value = str(dag.rational(result['value'])) if result['status'] == 'EXACT' else result['reason']
        lines.append(f"| {req['name']} | {result['status']} | {value} | {result['stats']['peak_terms']} | {result['stats']['products']} |")
    lines += ['', 'The 128-bit boundary controls retain compact affine messages instead of constructing a 2^128 table. The global-parity paired-OR failure demonstrates that even a structured, independently solvable input can exceed this planner’s component cap. The product-cap failure is intentional: identical output components do not erase the cost of producing all input pairs.', '',
              'The separate original-CNF benchmark in `../WEIGHTED_AFFINE_CROSSCHECK.json` reports 54/58 EXACT counts with replay and four UNKNOWN requests at the default caps. The complete binary interaction on 16 variables, planted 32-variable/128-clause input, and legacy connected mixed 12 fixture exceed 4,096 combined nodes. The planted 24-variable/96-clause input reaches 257 retained pieces. The 72-variable disjoint, 81-variable chain, and 66-variable sliding fixtures complete exactly. All 58 were also solved by the separate bounded branch/component reference; no general speed or coverage advantage is claimed. These failures are not replaced by the positive controls above.', '',
              'Source hashes were unchanged over this run. Timing includes producing and independently replaying the certificate on this machine; no comparative speed conclusion is drawn.', '']
    (HERE/'RESULTS.md').write_text('\n'.join(lines), encoding='utf-8')
    print(json.dumps({k: payload[k] for k in ('case_count', 'exact_count', 'unknown_count', 'source_unchanged_during_run')}))


if __name__ == '__main__':
    run()
