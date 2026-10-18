"""Read-only replay of frozen affine-compression artifacts and original inputs.

Writes only AFFINE_COMPRESSION_ARTIFACT_AUDIT.json. This audit does not rerun
search, infer a solution from an UNKNOWN, or make comparative timing claims.
"""
from collections import Counter
from datetime import datetime, timezone
from fractions import Fraction
from hashlib import sha256
import importlib.util
from itertools import combinations, product
import json
from pathlib import Path
import sys
import time

HERE = Path(__file__).resolve().parent
ARTIFACTS = {
    'compression': ('affine_sum_compression_lab/RESULTS.json', 'affine_sum_compression_lab'),
    'adapter': ('compressed_affine_dag_lab/RESULTS.json', '.'),
    'review': ('affine_compression_review/RESULTS.json', '.'),
    'capacity': ('affine_sum_capacity_lab/RESULTS.json', 'affine_sum_capacity_lab'),
    'crosscheck': ('AFFINE_COMPRESSION_CROSSCHECK.json', '.'),
    'stress': ('affine_compression_stress_lab/RESULTS.json', 'affine_compression_stress_lab'),
    'stress_review': ('affine_compression_stress_lab/INDEPENDENT_REVIEW.json', 'affine_compression_stress_lab'),
    'old_adapter': ('weighted_affine_dag_lab/RESULTS.json', '.'),
    'old_crosscheck': ('WEIGHTED_AFFINE_CROSSCHECK.json', '.'),
    'original_reference': ('original_count_reference_lab/RESULTS.json', 'original_count_reference_lab'),
    'tests': ('AFFINE_COMPRESSION_TEST_SUMMARY.json', '.'),
}


class AuditFailure(Exception):
    pass


def require(condition, explanation):
    if not condition:
        raise AuditFailure(explanation)


def digest(path):
    h = sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda: stream.read(1 << 20), b''):
            h.update(chunk)
    return h.hexdigest()


def load_module(name, filename):
    spec = importlib.util.spec_from_file_location('compression_artifact_audit_'+name, HERE/filename)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def unique(rows, key):
    answer = {key(row): row for row in rows}
    require(len(answer) == len(rows), 'duplicate original request names')
    return answer


def no_claim(result):
    require(result['status'] == 'UNKNOWN', 'unexpected nonexact result status')
    require(result.get('certificate') is None, 'UNKNOWN contains a certificate')
    for key in ('messages', 'value', 'count'):
        require(result.get(key) is None, 'UNKNOWN contains a claimed '+key)


def canonical_value(message, word):
    if message['zero'] or any((mask & word).bit_count() % 2 != rhs for mask, rhs in message['equations']):
        return Fraction(0)
    parity = sum((word & term) == term for term in message['phase']) % 2
    return Fraction(*message['scalar']) * (-1 if parity else 1)


def original_hash(n, clauses):
    # Independently encode the exact original reference protocol, including
    # every clause occurrence/order and all declared original variables.
    h = sha256(b'original-count-reference-v1\0')
    for value in [n, len(clauses), *(v for clause in clauses for v in (len(clause), *clause))]:
        raw = abs(value).to_bytes(max(1, (abs(value).bit_length()+7)//8), 'big')
        h.update(bytes([value < 0])); h.update(len(raw).to_bytes(8, 'big')); h.update(raw)
    return h.hexdigest()


def audit_provenance(data):
    files, records = {}, []
    for label, (filename, base) in ARTIFACTS.items():
        payload = data[label]
        paths = payload.get('source_sha256', payload.get('source_hashes_before', payload.get('implementation_sha256')))
        require(type(paths) is dict and paths, 'missing source map: '+filename)
        if 'source_hashes_after' in payload:
            require(paths == payload['source_hashes_after'], 'recorded before/after source mismatch: '+filename)
        flags = [payload[key] for key in ('source_unchanged_during_run', 'sources_unchanged_during_run', 'source_unchanged_during_tests') if key in payload]
        require(flags and all(value is True for value in flags), 'missing unchanged-source claim: '+filename)
        for relative, expected in paths.items():
            resolved = (HERE/base/relative).resolve()
            require(resolved.is_relative_to(HERE.parent), 'source path escapes checkpoint: '+relative)
            actual = digest(resolved)
            require(actual == expected, 'stale source hash: '+filename+' -> '+relative)
            normalized = str(resolved.relative_to(HERE.parent)).replace('\\', '/')
            require(normalized not in files or files[normalized] == actual, 'conflicting current source hashes')
            files[normalized] = actual
        records.append(dict(artifact=filename, source_references=len(paths), artifact_sha256=digest(HERE/filename)))
    return dict(recorded_source_references=sum(row['source_references'] for row in records),
                unique_recorded_sources=len(files), sources_relative_to_checkpoint=files, artifacts=records)


def audit_compression(payload, engine):
    counts = Counter(); rows = []; assignment_checks = symbolic = 0
    for row in payload['controls']:
        result = row['result']; counts[result['status']] += 1
        if result['status'] == 'UNKNOWN':
            no_claim(result); rows.append(dict(name=row['name'], status='UNKNOWN', reason=result['reason'])); continue
        checked = engine.verify_compression(row['n'], row['retained'], row['originals'], result)
        require(checked['valid'], 'compression replay failed: '+row['name']+' '+str(checked))
        if len(row['retained']) <= 8:
            for bits in range(1 << len(row['retained'])):
                word = sum(((bits >> j) & 1) << i for j, i in enumerate(row['retained']))
                require(sum(canonical_value(p, word) for p in row['originals']) == sum(canonical_value(p, word) for p in checked['messages']),
                        'original compact sum mismatch: '+row['name'])
            assignment_checks += 1 << len(row['retained'])
            require(row['independent_assignment_checks'] == 1 << len(row['retained']), 'saved direct-check count mismatch')
        if 'algebraic_expected_messages' in row:
            require(checked['messages'] == row['algebraic_expected_messages'], 'wide expected-message mismatch')
            symbolic += 1
        rows.append(dict(name=row['name'], status='VERIFIED', fresh_verifier_stats=checked['stats']))
    require(dict(counts) == {'EXACT': 102, 'UNKNOWN': 7}, 'compression result counts changed')
    require(payload['totals'] == dict(EXACT=102, UNKNOWN=7, assignment_checks=assignment_checks, explicit_symbolic_controls=symbolic), 'compression saved totals mismatch')
    return dict(**counts, original_assignment_checks=assignment_checks, wide_expected_message_checks=symbolic, cases=rows)


def verify_dag_case(engine, request, result, caps):
    if 'clauses' in request:
        checked = engine.verify_formula(request['n'], request['clauses'], result, **caps)
    else:
        checked = engine.verify_factors(request['n'], request['factors'], result, **caps)
    require(checked['valid'], 'DAG replay failed: '+request['name']+' '+str(checked))
    return checked


def audit_adapter(payload, baseline, engine):
    previous = unique(baseline['cases'], lambda row: row['original_request']['name'])
    counts = Counter(); compared = new = regressed = 0; rows = []
    for row in payload['cases']:
        request, result = row['original_request'], row['result']; name = request['name']
        counts[result['status']] += 1
        if result['status'] == 'UNKNOWN':
            no_claim(result); checked = None
        else:
            checked = verify_dag_case(engine, request, result, request.get('caps', {}))
            require(result['value'] == request['expected'] == checked['value'], 'adapter original analytic count mismatch')
        if name in previous:
            old = previous[name]; compared += 1
            require(request == old['original_request'], 'adapter comparison changed original input')
            expected = {key: old['result'].get(key) for key in ('status', 'value', 'stats', 'reason')}
            require(row['frozen_baseline_comparison'] == expected, 'adapter saved baseline mismatch')
            new += old['result']['status'] != 'EXACT' and result['status'] == 'EXACT'
            regressed += old['result']['status'] == 'EXACT' and result['status'] != 'EXACT'
        else:
            require(row['frozen_baseline_comparison'] is None, 'invented baseline comparison')
        rows.append(dict(name=name, status=result['status'], fresh_verifier_stats=checked['stats'] if checked else None))
    require(dict(counts) == {'EXACT': 19, 'UNKNOWN': 3}, 'adapter exact/unknown counts changed')
    comparison = dict(compared_cases=compared, newly_exact=new, regressed_to_unknown=regressed)
    require(comparison == payload['shared_request_status_comparison'], 'adapter comparison summary mismatch')
    return dict(**counts, comparison=comparison, cases=rows)


def audit_crosscheck(payload, old_payload, references, engine, old_engine, reference_engine):
    originals = unique(references['cases'], lambda row: row['name'])
    old = unique(old_payload['cases'], lambda row: row['name'])
    require(set(old) == set(originals) == {row['name'] for row in payload['cases']} and len(payload['cases']) == 58,
            'same-original comparison coverage mismatch')
    counts = Counter(); both = []; rows = []; newly = []; regressions = []
    metrics = {key: Counter(lower=0, equal=0, higher=0) for key in ('work', 'products', 'nodes', 'peak_terms')}
    reference_proofs = old_proofs = 0
    for row in payload['cases']:
        name = row['name']; previous = old[name]; original = originals[name]
        for other in (previous, original):
            require(row['n'] == other['n'] and row['clauses'] == other['clauses'], 'original formula changed: '+name)
        hash_value = original_hash(row['n'], row['clauses'])
        require(hash_value == row['original_input_sha256'] == previous['original_input_sha256'] == original['input_sha256'], 'original request hash mismatch')
        require(row['expected_count'] == previous['expected_count'] == original['result']['count'] == original['independent_control_count'], 'reference count mismatch')
        checked_reference = reference_engine.verify(original['n'], original['clauses'], original['result'], **original['caps'])
        require(checked_reference['valid'] and checked_reference['count'] == row['expected_count'], 'original count certificate failed: '+name)
        reference_proofs += 1
        require(row['caps'] == previous['caps'], 'original DAG caps changed')
        require(row['previous_status'] == previous['result']['status'] and row['previous_stats'] == previous['result']['stats'], 'stored old status/counters mismatch')
        require(row['factor_order'] == previous['factor_order'] == 'original clause occurrence order', 'original factor order changed')
        result = row['result']; counts[result['status']] += 1
        checked = None
        if result['status'] == 'UNKNOWN':
            no_claim(result)
        else:
            checked = engine.verify_formula(row['n'], row['clauses'], result, **row['caps'])
            require(checked['valid'] and checked['value'] == [row['expected_count'], 1], 'new original count proof failed: '+name)
        prior_result = previous['result']
        if prior_result['status'] == 'EXACT':
            prior_check = old_engine.verify_formula(row['n'], row['clauses'], prior_result, **previous['caps'])
            require(prior_check['valid'] and prior_check['value'] == [row['expected_count'], 1], 'old original count proof failed: '+name)
            old_proofs += 1
        else:
            no_claim(prior_result)
        if result['status'] == prior_result['status'] == 'EXACT':
            values = {}
            for key, distribution in metrics.items():
                a, b = prior_result['stats'][key], result['stats'][key]
                relation = 'lower' if b < a else 'higher' if b > a else 'equal'
                distribution[relation] += 1
                values[key] = dict(old=a, new=b, relation=relation)
            both.append(dict(name=name, recorded_producer_counters=values))
        if result['status'] == 'EXACT' and prior_result['status'] != 'EXACT': newly.append(name)
        if result['status'] != 'EXACT' and prior_result['status'] == 'EXACT': regressions.append(name)
        rows.append(dict(name=name, status=result['status'], expected_count=row['expected_count'], fresh_verifier_stats=checked['stats'] if checked else None))
    require(dict(counts) == {'EXACT':54, 'UNKNOWN':4} and len(both) == 54, 'same-original exact/unknown comparison changed')
    require(newly == payload['newly_exact'] and regressions == payload['regressions'], 'status comparison summary mismatch')
    require(payload['summary'] == dict(exact_original_counts_matched=54, EXACT=54, UNKNOWN=4), 'crosscheck summary mismatch')
    return dict(**counts, original_reference_certificates=reference_proofs, baseline_certificates=old_proofs,
                newly_exact=newly, regressions=regressions, both_exact=len(both), recorded_counter_comparison={k:dict(v) for k,v in metrics.items()},
                counter_scope='Saved producer counters, checked against frozen baseline records; not separately certified CPU, peak bytes or comparative runtime.',
                peak_terms_scope='Old transient dictionary peak and new settled retained-piece peak have different meanings; new actual-live/pending counts remain separate.',
                per_case_counter_comparison=both, cases=rows)


def audit_stress(payload, review, engine, old_engine, controls):
    source_cases = controls.fixed_controls(); records = payload['cases']
    require(len(records) == len(source_cases) == 22, 'stress source coverage mismatch')
    summaries = {'baseline':Counter(), 'compressed':Counter()}; rows = []; newly = []; regressions = []
    independent_counts = {}; clause_omissions = 0; grouped = {}; paired = 0
    for saved, original in zip(records, source_cases):
        require(saved['original_request'] == original, 'stress original request differs from source constructor')
        proof = controls.verify_control(original)
        require(proof == saved['original_count_proof'], 'stress analytic proof differs from fresh source replay')
        require(saved['caps'] == payload['caps'], 'stress caps mismatch')
        clause_omissions += len(original['clauses'])
        if original['kind'] == 'pigeonhole':
            p, h = original['pigeons'], original['holes']
            count = sum(set(range(p)).issubset(word) for word in product(range(-1,p), repeat=h))
            require(count == proof['count'], 'independent hole-owner count mismatch')
            independent_counts[original['name']] = count
        else:
            key = (original['vertices'], tuple(original['charges']))
            if key in grouped:
                previous = grouped[key]
                require(previous['edges'] == original['edges'] and sorted(map(tuple,previous['clauses'])) == sorted(map(tuple,original['clauses'])), 'grouped/shuffled inputs differ')
                paired += 1
            else:
                grouped[key] = original
        checked_row = dict(name=original['name'], original_count=proof['count'], engines={})
        certified = {}
        for name, implementation in [('baseline',old_engine), ('compressed',engine)]:
            record = saved[name]; result = record['result']; summary = summaries[name]
            summary[result['status']] += 1
            if result['status'] == 'UNKNOWN':
                no_claim(result); require(record['certified_exact'] is False and record['verification'] is None, 'UNKNOWN was certified')
                checked = None; certified[name] = False
            else:
                require(result['count'] == proof['count'], 'stress original count mismatch')
                checked = implementation.verify_formula(original['n'], original['clauses'], result, **saved['caps'])
                require(checked['status'] in ('VERIFIED','UNKNOWN'), 'stress proof rejected')
                certified[name] = checked['valid']
                require(certified[name] == record['certified_exact'], 'stress saved certification status differs')
                if certified[name]:
                    require(checked['value'] == [proof['count'],1], 'stress fresh verified value mismatch')
                summary['verified_exact' if certified[name] else 'verification_unknown'] += 1
            checked_row['engines'][name] = dict(status=result['status'], certified_exact=certified[name], fresh_verifier_stats=checked['stats'] if checked else None)
        if certified['compressed'] and not certified['baseline']: newly.append(original['name'])
        if certified['baseline'] and not certified['compressed']: regressions.append(original['name'])
        rows.append(checked_row)
    normalized = {k:dict(v) for k,v in summaries.items()}
    require(normalized == payload['summary'], 'stress saved summaries mismatch')
    require(summaries['baseline']['verified_exact'] == 2 and summaries['compressed']['verified_exact'] == 11, 'stress exact proof totals changed')
    require(newly == payload['newly_certified_exact'] and len(newly) == 9 and regressions == payload['certification_regressions'], 'stress improvement/regression mismatch')
    require(review['source_controls'] == 22 and review['single_clause_omissions_rejected'] == clause_omissions == 2611 and len(review['grouped_shuffled_pairs']) == paired == 8, 'independent stress review coverage mismatch')
    indexed_review = unique(review['controls'], lambda row:row['name'])
    for original in source_cases:
        r = indexed_review[original['name']]
        require(r['n'] == original['n'] and r['clauses'] == len(original['clauses']) and r['structural_count'] == original['expected_count'], 'stress independent review original mismatch')
    return dict(source_analytic_proofs=22, summaries=normalized, newly_certified_exact=newly, certification_regressions=regressions,
                grouped_shuffled_pairs=paired, independently_recounted_pigeonhole_cases=independent_counts,
                prior_mutation_evidence='2,611 omissions remain source-hash bound to the frozen independent review; this auditor checks its complete coverage counts but does not rerun those mutations.', cases=rows)


def small_dictionary(n):
    """Independent construction via all linear spans, cosets and intrinsic phases."""
    universe = range(1 << n); spaces = {frozenset([0])}; queue = list(spaces)
    for space in queue:
        for vector in universe:
            bigger = space | frozenset(x ^ vector for x in space)
            if bigger not in spaces:
                spaces.add(bigger); queue.append(bigger)
    directions = set(); support_count = 0
    for space in spaces:
        coordinates = [0]
        for vector in sorted(space):
            if vector not in coordinates:
                coordinates += [x ^ vector for x in coordinates]
        d = len(coordinates).bit_length()-1
        require(len(coordinates) == 1 << d, 'nonlinear constructed span')
        monomials = [1 << i for i in range(d)] + [(1 << i)|(1 << j) for i in range(d) for j in range(i+1,d)]
        cosets = {frozenset(anchor ^ x for x in space) for anchor in universe}
        support_count += len(cosets)
        for coset in cosets:
            anchor = min(coset); ordered = [anchor ^ x for x in coordinates]
            support = sum(1 << x for x in ordered)
            for coefficients in range(1 << len(monomials)):
                negative = 0
                for x, physical in enumerate(ordered):
                    parity = sum((coefficients >> i & 1) and (x & term == term) for i,term in enumerate(monomials)) % 2
                    negative |= parity << physical
                directions.add((support,negative))
    return sorted(directions), support_count


def pair_coverage(n, directions):
    vectors = [tuple(0 if not support >> i & 1 else -1 if negative >> i & 1 else 1 for i in range(1<<n)) for support,negative in directions]
    single = {0} | {support for support,negative in directions if negative == 0}
    covered = set(single); peak = pairs = 0
    for u,v in combinations(vectors,2):
        i,j = next((i,j) for i in range(len(u)) for j in range(i+1,len(u)) if u[i]*v[j] != u[j]*v[i])
        det = u[i]*v[j]-u[j]*v[i]; points = set()
        for a,b in product((0,1),repeat=2):
            alpha,beta = a*v[j]-b*v[i], b*u[i]-a*u[j]
            word = 0
            for k,(x,y) in enumerate(zip(u,v)):
                value = alpha*x+beta*y
                if value not in (0,det): break
                if value == det: word |= 1 << k
            else:
                points.add(word)
        covered |= points; peak = max(peak,len(points)); pairs += 1
    return dict(n=n,directions=len(directions),one_piece_boolean_functions=len(single),two_piece_boolean_functions=len(covered),
                total_boolean_functions=1 << (1<<n),independent_pair_spans=pairs,max_boolean_points_in_pair_span=peak)


def audit_capacity(payload, implementation):
    small = []; pairs = []
    for saved in payload['exact_dictionary_controls']:
        n = saved['n']; require(0 <= n <= 4, 'unexpected small capacity dimension')
        directions,supports = small_dictionary(n)
        require(len(directions) == saved['dictionary_count'] and supports == saved['affine_supports'], 'independent small dictionary count mismatch')
        require(saved['tested_nonempty_subsets'] == (1 << (1 << n))-1 and saved['ambient_phases'] == 1 << (n*(n+1)//2), 'small capacity work metadata mismatch')
        small.append(dict(n=n,dictionary_count=len(directions),affine_supports=supports))
        if n <= 3:
            result = pair_coverage(n,directions)
            require(result == payload['exact_small_pair_span_controls'][n], 'small exact pair-span count mismatch')
            pairs.append(result)
    # Alternative Gaussian recurrence G(n,d)=2^d G(n-1,d)+G(n-1,d-1).
    row = [1]; values = {}; recurrence_checks = 0
    for n in range(129):
        if n:
            row = [((1 << d)*row[d] if d < n else 0) + (row[d-1] if d else 0) for d in range(n+1)]
        count = sum(g << (n-d+d*(d+1)//2) for d,g in enumerate(row))
        product_count = 1 << n
        for i in range(n): product_count *= (1 << i)+1
        require(count == product_count == implementation.dictionary_count(n) == implementation.dictionary_product(n), 'Gaussian recurrence/product mismatch')
        values[n] = count; recurrence_checks += 1
    for saved in payload['arbitrary_truth_function_existence_bounds']:
        n = saved['n']; d = values[n]; bits = 1+d.bit_length(); lower = ((1<<n)-1)//bits+1
        require(saved['dictionary_directions'] == d and saved['per_piece_exponent_bound'] == bits and
                saved['some_boolean_function_requires_at_least'] == lower and saved['all_boolean_functions_representable_with'] == 1<<n,
                'capacity existence-bound formula mismatch')
        require((lower-1)*bits < 1<<n, 'capacity strict exponent inequality failed')
    return dict(independently_constructed_small_dictionaries=small,independent_pair_span_counts=pairs,
                alternative_gaussian_recurrence_and_product_checks=recurrence_checks,existence_bounds_checked=len(payload['arbitrary_truth_function_existence_bounds']),
                scope='Representation counting for arbitrary truth functions only; no succinct-CNF or general algorithmic lower bound.')


def audit_review(payload, data):
    for key,label,expected in [('saved_compression_replay','compression',(102,7)), ('saved_dag_replay','adapter',(19,3))]:
        r = payload[key]
        require(r['source'] == ARTIFACTS[label][0] and r['sha256'] == digest(HERE/r['source']), 'independent review result binding mismatch')
        require((r['exact'],r['unknown']) == expected, 'independent review replay counts mismatch')
    require(payload['original_compact_sums']['requests'] == len(payload['original_compact_sums']['cases']) == 200, 'review compact-request coverage mismatch')
    require(payload['original_factor_requests']['requests'] == len(payload['original_factor_requests']['cases']) == 200, 'review factor-request coverage mismatch')
    require(payload['semantic_and_source_mutations']['rejected'] == 92, 'review mutation count mismatch')
    return dict(source_bound_review_compact_requests=200,source_bound_review_factor_requests=200,source_bound_compression_mutations=92,
                recorded_saved_compression_replay={k:v for k,v in payload['saved_compression_replay'].items() if k!='cases'},
                recorded_saved_adapter_replay={k:v for k,v in payload['saved_dag_replay'].items() if k!='cases'},
                scope='Review source/result hashes and coverage totals checked. Its random mutation suites and block-norm proofs are recorded evidence, not rerun by this auditor.')


def audit_tests(payload):
    require(payload['all_tests_passed'] is True and payload['source_unchanged_during_tests'] is True, 'phase tests were not a stable pass')
    require(payload['test_count'] == sum(r['test_count'] for r in payload['suites']) == 54 and payload['suite_count'] == len(payload['suites']) == 5, 'phase test totals mismatch')
    require(all(r['passed'] is True and r['returncode'] == 0 for r in payload['suites']), 'phase suite failed')
    output = (HERE/'AFFINE_COMPRESSION_TEST_OUTPUT.txt').read_text(encoding='utf-8')
    require('FAILED' not in output and output.count('\nOK') == 5, 'phase saved test output does not show five passing suites')
    return dict(test_count=54,suite_count=5,all_tests_passed=True,source_hashes_checked=len(payload['implementation_sha256']),
                output_sha256=digest(HERE/'AFFINE_COMPRESSION_TEST_OUTPUT.txt'),scope='Recorded new-phase tests only; no old-suite rerun asserted.')


def main():
    started = time.perf_counter(); failures = []; sections = {}; data = {}
    paths = [HERE/name for name,_ in ARTIFACTS.values()] + [Path(__file__).resolve(), HERE/'AFFINE_COMPRESSION_TEST_OUTPUT.txt']
    initial = {str(path.relative_to(HERE)).replace('\\','/'):digest(path) for path in paths}
    try:
        for label,(filename,_) in ARTIFACTS.items():
            data[label] = json.loads((HERE/filename).read_text(encoding='utf-8'))
        sections['provenance'] = audit_provenance(data)
    except Exception as exc:
        failures.append(dict(stage='provenance',error=type(exc).__name__+': '+str(exc)))
    if not failures:
        engines = dict(compression=load_module('compression','affine_sum_compression_lab/compression.py'),
                       adapter=load_module('adapter','compressed_affine_dag_lab/dag.py'),
                       old=load_module('old','weighted_affine_dag_lab/dag.py'),
                       reference=load_module('reference','original_count_reference_lab/reference.py'),
                       controls=load_module('controls','affine_compression_stress_lab/controls.py'),
                       capacity=load_module('capacity','affine_sum_capacity_lab/capacity.py'))
        stages = [
            ('compression',lambda:audit_compression(data['compression'],engines['compression'])),
            ('adapter',lambda:audit_adapter(data['adapter'],data['old_adapter'],engines['adapter'])),
            ('same_58_originals',lambda:audit_crosscheck(data['crosscheck'],data['old_crosscheck'],data['original_reference'],engines['adapter'],engines['old'],engines['reference'])),
            ('stress_22_originals',lambda:audit_stress(data['stress'],data['stress_review'],engines['adapter'],engines['old'],engines['controls'])),
            ('capacity',lambda:audit_capacity(data['capacity'],engines['capacity'])),
            ('independent_review_binding',lambda:audit_review(data['review'],data)),
            ('recorded_phase_tests',lambda:audit_tests(data['tests'])),
        ]
        for name,operation in stages:
            try:
                sections[name] = operation(); print(name+' PASS',flush=True)
            except Exception as exc:
                failures.append(dict(stage=name,error=type(exc).__name__+': '+str(exc))); print(name+' FAIL '+str(exc),flush=True)
        try:
            require(audit_provenance(data) == sections['provenance'], 'recorded sources changed during audit')
        except Exception as exc:
            failures.append(dict(stage='final_provenance',error=type(exc).__name__+': '+str(exc)))
    final = {name:digest(HERE/name) for name in initial}
    if initial != final:
        failures.append(dict(stage='artifact_stability',error='input artifact or auditor source changed during audit'))
    output = dict(status='FAIL' if failures else 'PASS',timestamp_utc=datetime.now(timezone.utc).isoformat(),
                  input_artifact_and_auditor_sha256=initial,input_artifacts_unchanged_during_audit=initial==final,
                  failures=failures,sections=sections,seconds=time.perf_counter()-started,
                  scope='Current recorded source binding, saved exact certificate replay, original-input/count consistency and finite capacity controls. UNKNOWN claims remain unresolved. Recorded counters are not runtime or byte-memory proofs; no comparative timing claim.')
    (HERE/'AFFINE_COMPRESSION_ARTIFACT_AUDIT.json').write_text(json.dumps(output,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(dict(status=output['status'],failures=failures,seconds=output['seconds'])),flush=True)
    return 1 if failures else 0


if __name__ == '__main__':
    raise SystemExit(main())
