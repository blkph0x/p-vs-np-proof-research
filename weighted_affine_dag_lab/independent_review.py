"""Reproduce the independent mixed-factor, boundary and block-reference audit.

This is validation code only. It changes no production source. All original
held-out requests and exact source/dependency hashes are retained in the
machine-readable report; saved production requests are bound by RESULTS.json.
"""
from fractions import Fraction
from hashlib import sha256
from itertools import combinations
import importlib.util
import json
from pathlib import Path
import random
import sys

HERE = Path(__file__).resolve().parent
NIGHT = HERE.parent
SEED = 191026732
EXPECTED_TOTALS = dict(requests=200, original_words=3591,
                       structural_boundary_values=4306,
                       independent_marginals=1155)
EXPECTED_SAVED = dict(exact=16, unknown=2, independent_marginal_replays=580)


def module_at(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def source_hashes():
    saved = json.loads((HERE/'RESULTS.json').read_text(encoding='utf-8'))
    hashes = {}
    for relative, expected in saved['source_hashes_after'].items():
        actual = sha256((NIGHT/relative).read_bytes()).hexdigest()
        assert actual == expected, ('production source changed', relative)
        hashes['../'+relative] = actual
    for relative in ('independent_review.py', 'RESULTS.json', '../affine_boundary_reference/reference.py'):
        hashes[relative] = sha256((HERE/relative).read_bytes()).hexdigest()
    return hashes


def rational(value):
    return Fraction(*value) if isinstance(value, (list, tuple)) else Fraction(value)


def pack(value):
    return [value.numerator, value.denominator]


def assignments(ids):
    for mask in range(1 << len(ids)):
        yield sum(((mask >> i) & 1) << variable for i, variable in enumerate(ids))


def factor_value(factor, word):
    if factor['kind'] == 'or':
        return Fraction(int(any(bool(word >> (abs(literal)-1) & 1) == (literal > 0)
                                for literal in factor['literals'])))
    if any((word & mask).bit_count() % 2 != rhs for mask, rhs in factor['equations']):
        return Fraction(0)
    return rational(factor['scalar'])*(-1)**sum((word & mask) == mask for mask in factor['phase'])


def normalized_scope(factor):
    # Independent of dag.source_terms: only Boolean OR normalization is used.
    if factor['kind'] == 'affine':
        return set(factor['scope'])
    literals = set(factor['literals'])
    if any(-literal in literals for literal in literals):
        return set()
    return {abs(literal)-1 for literal in literals}


def message_value(message, word):
    if message['zero']:
        return Fraction(0)
    if any((word & mask).bit_count() % 2 != rhs for mask, rhs in message['equations']):
        return Fraction(0)
    return rational(message['scalar'])*(-1)**sum((word & mask) == mask for mask in message['phase'])


def check_marginal(record, reference, work_cap=None):
    request = record['request']
    caps = {} if work_cap is None else {'max_work': work_cap}
    recomputed = reference.marginalize_reference(**request, **caps)
    assert recomputed['status'] == 'EXACT', recomputed
    checked = reference.verify_reference(request['n'], request['retained'], request['equations'],
                                         request['phase'], request['scalar'], recomputed,
                                         active=request['active'], **caps)
    assert checked['valid'], checked
    compared = reference.equivalent_messages(request['n'], request['retained'],
                                             recomputed['message'], record['result']['message'], **caps)
    assert compared['status'] == 'EXACT' and compared['equivalent'], compared
    return dict(request_sha256=recomputed['certificate']['input_sha256'],
                reference_verified=True, symbolically_equal=True,
                retained_coordinates=len(request['retained']))


def heldout_requests():
    rng = random.Random(SEED)
    for case in range(200):
        n = rng.randrange(7)
        factors = []
        for _ in range(rng.randrange(8)):
            if rng.randrange(2):
                literals = [] if not n else [rng.choice([-1, 1])*rng.randrange(1, n+1)
                                             for _ in range(rng.randrange(5))]
                factors.append({'kind': 'or', 'literals': literals})
            else:
                scoped = [v for v in range(n) if rng.randrange(2)]
                equations = [[sum(1 << v for v in scoped if rng.randrange(2)), rng.randrange(2)]
                             for _ in range(rng.randrange(3))]
                terms = ([0]+[1 << v for v in scoped]
                         +[(1 << i) | (1 << j) for i, j in combinations(scoped, 2)])
                phase = [term for term in terms if rng.randrange(2)]
                factors.append(dict(kind='affine', scope=scoped, equations=equations,
                                    phase=phase, scalar=[rng.choice([-3, -1, 0, 1, 2]),
                                                        rng.choice([1, 3, 7])]))
        order = list(range(len(factors)))
        rng.shuffle(order)
        yield case, dict(n=n, factors=factors, order=order)


def run_heldout(dag, reference):
    totals = dict.fromkeys(EXPECTED_TOTALS, 0)
    cases = []
    for case, request in heldout_requests():
        n, factors, order = request['n'], request['factors'], request['order']
        result = dag.solve_factors(n, factors, order=order)
        assert result['status'] == 'EXACT', (case, result)
        verification = dag.verify_factors(n, factors, result, order=order)
        assert verification['valid'], (case, verification)
        expected = Fraction(0)
        for word in range(1 << n):
            product = Fraction(1)
            for factor in factors:
                product *= factor_value(factor, word)
            expected += product
            totals['original_words'] += 1
        assert rational(result['value']) == expected, (case, result['value'], expected)
        scopes = [normalized_scope(factor) for factor in factors]
        boundary_values = 0
        for node in result['certificate']['nodes']:
            ids = node['factor_ids']
            inside = set().union(*(scopes[i] for i in ids)) if ids else set()
            outside = (set().union(*(scopes[i] for i in range(len(factors)) if i not in ids))
                       if len(ids) < len(factors) else set())
            boundary = sorted(inside & outside)
            assert node['boundary'] == boundary
            for y in assignments(boundary):
                expected_node = Fraction(0)
                for z in assignments(sorted(inside-set(boundary))):
                    product = Fraction(1)
                    for i in ids:
                        product *= factor_value(factors[i], y | z)
                    expected_node += product
                observed = sum((message_value(message, y) for message in node['messages']), Fraction(0))
                assert observed == expected_node, (case, node['factor_ids'], y, observed, expected_node)
                boundary_values += 1
        marginals = [check_marginal(record, reference) for record in result['certificate']['marginals']]
        totals['requests'] += 1
        totals['structural_boundary_values'] += boundary_values
        totals['independent_marginals'] += len(marginals)
        cases.append(dict(case=case, original_request=request,
                          original_request_sha256=result['request_sha256'],
                          independently_enumerated_value=pack(expected),
                          production_value=result['value'], production_verified=True,
                          original_words=1 << n, structural_boundary_values=boundary_values,
                          marginal_checks=marginals))
    assert totals == EXPECTED_TOTALS, totals
    return totals, cases


def run_saved(dag, reference):
    saved = json.loads((HERE/'RESULTS.json').read_text(encoding='utf-8'))
    totals = dict.fromkeys(EXPECTED_SAVED, 0)
    cases = []
    for index, case in enumerate(saved['cases']):
        request, result = case['original_request'], case['result']
        caps = request.get('caps', {})
        if result['status'] == 'UNKNOWN':
            assert result['value'] is None and result['count'] is None and result['certificate'] is None
            totals['unknown'] += 1
            cases.append(dict(index=index, name=request['name'], status='UNKNOWN', claim=None))
            continue
        if 'clauses' in request:
            checked = dag.verify_formula(request['n'], request['clauses'], result, **caps)
        else:
            checked = dag.verify_factors(request['n'], request['factors'], result, **caps)
        assert checked['valid'], (request['name'], checked)
        assert rational(result['value']) == rational(request['expected'])
        name = request['name']
        if name.startswith('shared_pair_private_clause_'):
            assert rational(result['value']) == 3*(1 << len(request['clauses']))+1
        if name.startswith('phase_induced_even_boundary_'):
            width = len(next(f['literals'] for f in request['factors'] if f['kind'] == 'or'))
            assert rational(result['value']) == (1 << width)-2
        if name.startswith('wide_signed_phase_product_'):
            assert rational(result['value']) == Fraction(-21, 55)*(1 << (request['n']-1))
        if name.startswith('paired_ors_global_even_'):
            count = sum(f['kind'] == 'or' for f in request['factors'])
            assert rational(result['value']) == (3**count+(-1)**count)//2
        marginal_checks = [check_marginal(record, reference, work_cap=20000000)
                           for record in result['certificate']['marginals']]
        totals['exact'] += 1
        totals['independent_marginal_replays'] += len(marginal_checks)
        cases.append(dict(index=index, name=name, status='EXACT', production_verified=True,
                          original_request_sha256=result['request_sha256'],
                          value=result['value'], marginal_checks=marginal_checks))
    assert totals == EXPECTED_SAVED, totals
    return totals, cases


def run():
    before = source_hashes()
    dag = module_at('_independent_review_production_dag', HERE/'dag.py')
    reference = module_at('_independent_review_block_reference', NIGHT/'affine_boundary_reference/reference.py')
    heldout_summary, heldout_cases = run_heldout(dag, reference)
    saved_summary, saved_cases = run_saved(dag, reference)
    after = source_hashes()
    assert before == after
    report = dict(schema='weighted-affine-dag-independent-review-v1',
                  verdict='PASS', source_sha256=after, source_unchanged_during_run=True,
                  random_seed=SEED, heldout_summary=heldout_summary,
                  saved_summary=saved_summary, saved_original_requests='RESULTS.json',
                  saved_reference_work_cap=20000000,
                  heldout_cases=heldout_cases, saved_cases=saved_cases)
    (HERE/'INDEPENDENT_REVIEW.json').write_text(json.dumps(report, indent=2)+'\n', encoding='utf-8')
    print(json.dumps({'heldout': heldout_summary, 'saved': saved_summary}, sort_keys=True))


if __name__ == '__main__':
    run()
