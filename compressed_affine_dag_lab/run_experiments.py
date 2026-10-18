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
    out += [dict(name='unit_streaming_retained_cap_one', n=1, clauses=[[1], [1]],
                 expected=[1, 1], caps={'max_terms': 1},
                 reference='Both original unit occurrences require x=1; two pending pieces reduce to one retained pin.'),
            dict(name='aggregate_compression_inputs_cap', n=1, clauses=[[1], [1]],
                 expected=[1, 1], caps={'compression_caps': {'max_inputs': 3}},
                 reference='The two separate unit leaves require four incoming pieces in total before their parent; the aggregate cap is three.'),
            dict(name='unit_implication_chain_32_with_free_variables', n=34,
                 clauses=[[1]]+[[-i, i+1] for i in range(1, 32)], expected=[4, 1],
                 reference='The unit forces all 32 chain variables true; the two unused original variables contribute four assignments.'),
            dict(name='signed_sparse_unit_context', n=40,
                 factors=[{'kind': 'or', 'literals': [-3]},
                          affine([2, 17, 39], [[(1 << 17) | (1 << 39), 1]],
                                 [(1 << 2) | (1 << 17)], Fraction(-5, 3))],
                 expected=dag.pack(Fraction(-5, 3)*(1 << 38)),
                 reference='The negative unit sets bit2=0, so the phase vanishes; one parity equation leaves two assignments on bits17,39 and all other original positions are free.')]
    return out


def source_hashes():
    paths = [HERE/'dag.py', HERE/'test_dag.py', HERE/'run_experiments.py', HERE/'THEOREM.md',
             HERE.parent/'affine_boundary_lab'/'boundary.py',
             HERE.parent/'affine_sum_compression_lab'/'compression.py',
             HERE.parent/'weighted_affine_dag_lab'/'dag.py',
             HERE.parent/'weighted_affine_dag_lab'/'RESULTS.json']
    return {str(p.relative_to(HERE.parent)).replace('\\', '/'): sha256(p.read_bytes()).hexdigest() for p in paths}


def run():
    before = source_hashes()
    baseline = json.loads((HERE.parent/'weighted_affine_dag_lab'/'RESULTS.json').read_text(encoding='utf-8'))
    baseline_cases = {row['original_request']['name']: row for row in baseline['cases']}
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
        comparison = None
        if request['name'] in baseline_cases:
            prior = baseline_cases[request['name']]
            assert prior['original_request'] == request
            comparison = {key: prior['result'].get(key) for key in ('status', 'value', 'stats', 'reason')}
        results.append({'original_request': request, 'result': result, 'verification': checked,
                        'frozen_baseline_comparison': comparison,
                        'produce_and_verify_seconds': elapsed})
    after = source_hashes()
    assert before == after
    exact = sum(row['result']['status'] == 'EXACT' for row in results)
    compared = [row for row in results if row['frozen_baseline_comparison'] is not None]
    comparison_summary = dict(compared_cases=len(compared),
        newly_exact=sum(row['frozen_baseline_comparison']['status'] != 'EXACT' and row['result']['status'] == 'EXACT' for row in compared),
        regressed_to_unknown=sum(row['frozen_baseline_comparison']['status'] == 'EXACT' and row['result']['status'] != 'EXACT' for row in compared))
    payload = {'format': 'compressed-affine-dag-experiments-v1',
               'timestamp_utc': datetime.now(timezone.utc).isoformat(),
               'source_hashes_before': before, 'source_hashes_after': after,
               'source_unchanged_during_run': True,
               'dag_default_caps': dag.LIMITS, 'compression_default_caps': dag.COMPRESSION_LIMITS,
               'shared_request_status_comparison': comparison_summary,
               'case_count': len(results), 'exact_count': exact, 'unknown_count': len(results)-exact,
               'cases': results}
    (HERE/'RESULTS.json').write_text(json.dumps(payload, indent=2)+'\n', encoding='utf-8')
    lines = ['# Compressed affine DAG saved controls', '',
             f'{len(results)} original requests: {exact} EXACT with independently replayed certificates; {len(results)-exact} UNKNOWN.', '',
             f"Among the {comparison_summary['compared_cases']} unchanged requests from the frozen control set, {comparison_summary['newly_exact']} become newly exact and {comparison_summary['regressed_to_unknown']} regress to UNKNOWN. This status comparison does not equate the different transient-retention semantics or claim a runtime benefit.", '',
             'Every exact value agrees with the analytic formula stated with its original input. These are deliberately structured controls, not a general complexity or speed claim. Full inputs, all exact certificates, source hashes, elapsed times, and the saved external baseline results for the 18 unchanged requests are in `RESULTS.json`.', '',
             '| Original request | Status | Exact value or stopping reason | Input-list peak | Retained peak | Live-ID peak | Products | Pair attempts |',
             '|---|---|---|---:|---:|---:|---:|---:|']
    for row in results:
        req, result = row['original_request'], row['result']
        value = str(dag.rational(result['value'])) if result['status'] == 'EXACT' else result['reason']
        stats = result['stats']
        lines.append(f"| {req['name']} | {result['status']} | {value} | {stats['peak_generated_input_terms']} | {stats['peak_terms']} | {stats['compression_peak_live_pieces']} | {stats['products']} | {stats['compression_attempted_pairs']} |")
    lines += ['', 'The 128-bit boundary controls retain compact affine messages instead of constructing a 2^128 table. Input lists, retained sets, and transient live IDs are different measured objects; the complete input list and all certificates still occupy memory. Pending canonical objects and work counters are separately recorded in JSON.', '',
              'The product-cap and aggregate-input-cap controls deliberately stop even though their logical counts are known. Compression does not refund generated cross-products, and per-node calls do not reset aggregate compressor budgets. The one-piece unit control reports its transient extra piece rather than concealing it.', '',
              'The unchanged external baseline remains in `../weighted_affine_dag_lab/RESULTS.json` and its 58-original-CNF comparison remains in `../WEIGHTED_AFFINE_CROSSCHECK.json`. The parent records the separate new 58-request comparison, including improvements and regressions. These additional native controls do not replace that dataset.', '',
              'Source hashes were unchanged over this run. Timing includes producing and independently replaying the certificate on this machine; no comparative speed conclusion is drawn. The new streaming retained-set cap differs from the baseline transient dictionary cap, and that distinction must be preserved in comparisons.', '']
    (HERE/'RESULTS.md').write_text('\n'.join(lines), encoding='utf-8')
    print(json.dumps({k: payload[k] for k in ('case_count', 'exact_count', 'unknown_count', 'source_unchanged_during_run')}))


if __name__ == '__main__':
    run()
