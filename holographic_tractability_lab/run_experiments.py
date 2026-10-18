"""Save original requests, independently checkable exact certificates and scope controls."""
from collections import Counter
from fractions import Fraction
from hashlib import sha256
from itertools import product
import json
from pathlib import Path
import random

from affine_holant import (formula_network, pack, ratio, solve_affine, solve_formula,
                           transformed_network, verify_affine, verify_formula)
from test_affine_holant import I, H, S, brute, equality_graph, formula_oracle, inverse, random_affine_network

HERE = Path(__file__).resolve().parent


def run():
    cases = []
    def network_case(name, network, matrix, reference, caps=None):
        caps = caps or {}
        result = solve_affine(network, matrix, **caps)
        verification = verify_affine(network, matrix, result, **caps) if result['status'] == 'EXACT' else None
        if verification is not None:
            assert verification['valid']
            assert ratio(result['value']) == ratio(reference['value'])
        cases.append(dict(name=name, request=dict(kind='network', network=network, basis=matrix),
                          caps=caps, reference=reference, result=result, verification=verification))

    def formula_case(name, n, clauses, mode, matrix, caps=None, planted=None):
        caps = caps or {}
        reference = {'value': pack(Fraction(formula_oracle(n, clauses, mode)))} if n <= 12 else {'known_satisfiable': True, 'planted_assignment': planted}
        if planted is not None:
            assert all(any(bool(planted >> (abs(lit)-1) & 1) == (lit > 0) for lit in clause) for clause in clauses)
        result = solve_formula(n, clauses, matrix, mode=mode, **caps)
        verification = verify_formula(n, clauses, matrix, result, mode=mode, **caps) if result['status'] == 'EXACT' else None
        if verification is not None:
            assert verification['valid']
            if 'value' in reference:
                assert result['value'] == reference['value']
        cases.append(dict(name=name, request=dict(kind='formula', n=n, clauses=clauses, mode=mode, basis=matrix),
                          caps=caps, reference=reference, result=result, verification=verification))

    network_case('empty_product', {'edges': 0, 'rows': [], 'columns': []}, I,
                 {'value': [1, 1], 'proof': 'empty sum/product convention'})
    network_case('signed_zero_with_two_supported_assignments',
                 {'edges': 1, 'rows': [{'ports': [0], 'values': [1, -1]}], 'columns': [{'ports': [0], 'values': [1, 1]}]},
                 I, {'value': [0, 1], 'supported_assignments': 2})
    phase = [(-1)**(((x & 3) == 3) + ((x & 12) == 12)) for x in range(16)]
    network_case('two_nondegenerate_quadratic_pairs',
                 {'edges': 4, 'rows': [{'ports': [0, 1, 2, 3], 'values': phase}],
                  'columns': [{'ports': [i], 'values': [1, 1]} for i in range(4)]},
                 I, {'value': [4, 1], 'proof': 'two independent four-term signed sums of value 2'})
    for size, shifts, name in ((3, [0, 1, 2], 'K3_3'), (40, [0, 1, 7], 'cubic_120_edges')):
        target = equality_graph(size, shifts)
        original = transformed_network(target, inverse(S))
        reference = {'value': [2, 1], 'proof': 'connected equality target, inverse common basis', 'target': target}
        network_case('inverse_shear_' + name, original, S, reference)
        network_case('identity_rejects_' + name, original, I, reference)
        if size == 40:
            network_case('edge_budget_interrupted_' + name, original, S, reference, {'max_edges': 119})
    rng = random.Random(831026)
    for case in range(6):
        target = random_affine_network(rng, 7)
        original = transformed_network(target, inverse(S))
        expected = brute(original)
        assert expected == brute(target)
        network_case('seeded_signed_affine_' + str(case), original, S,
                     {'value': pack(expected), 'proof': 'all 128 original edge assignments enumerated'})
    formula_case('unused_200_variables', 200, [], 'sat', I, planted=0)
    # This is a separate exact count theorem, not a 2^200 enumeration.
    cases[-1]['reference'] = {'value': [1 << 200, 1], 'proof': '200 independent unused variables'}
    assert cases[-1]['result']['value'] == cases[-1]['reference']['value']
    formula_case('shared_repeated_units', 4, [[1], [-2], [1], [3]], 'sat', H)
    formula_case('contradictory_units', 3, [[1], [-1]], 'slack', H)
    formula_case('empty_clause', 2, [[]], 'sat', S)
    all_polarities = [list(c) for c in product(*[(i, -i) for i in (1, 2, 3)])]
    originals = [('one_ternary', [[1, 2, 3]]),
                 ('duplicated_ternary', [[1, 2, 3]]*2),
                 ('all_eight_ternary_polarities_unsat', all_polarities)]
    for name, clauses in originals:
        for mode in ('sat', 'slack'):
            for basis_name, matrix in [('identity', I), ('Hadamard', H), ('shear', S)]:
                formula_case(name+'_'+mode+'_'+basis_name, 3, clauses, mode, matrix)
    rng = random.Random(24181026)
    n, planted, clauses = 24, rng.randrange(1 << 24), []
    for _ in range(12):
        variables = list(range(1, n+1))
        rng.shuffle(variables)
        for start in range(0, n, 3):
            clause = [v*rng.choice([-1, 1]) for v in variables[start:start+3]]
            if not any(bool(planted >> (abs(lit)-1) & 1) == (lit > 0) for lit in clause):
                clause[0] *= -1
            clauses.append(clause)
    assert len(clauses) == 96
    for mode in ('sat', 'slack'):
        for basis_name, matrix in [('identity', I), ('Hadamard', H), ('shear', S)]:
            formula_case('balanced_planted_24_96_'+mode+'_'+basis_name,
                         n, clauses, mode, matrix, {'max_work': 12000000}, planted)
    source_names = ['affine_holant.py', 'test_affine_holant.py', 'run_experiments.py', 'THEOREM.md']
    results = dict(format='real-affine-holant-experiments-v1',
                   source_sha256={name: sha256((HERE/name).read_bytes()).hexdigest() for name in source_names},
                   primary_source='https://homepages.inf.ed.ac.uk/hguo/papers/HA-general.pdf',
                   primary_scope='Definitions 2.4/2.5 and Theorem 2.2; rational real subclass only, supplied basis only',
                   summary=dict(cases=len(cases), statuses=dict(Counter(c['result']['status'] for c in cases)),
                                test_quadratic_signatures=1099, test_seeded_affine_networks=240,
                                explicitly_enumerated_saved_network_assignments=6*128),
                   cases=cases)
    (HERE/'RESULTS.json').write_text(json.dumps(results, indent=2)+'\n', encoding='utf-8')
    summary = results['summary']
    (HERE/'RESULTS.md').write_text(
        '# Saved real-affine evaluation results\n\n'
        f"{summary['cases']} saved original requests: {summary['statuses']}.\n\n"
        'Every EXACT result has been checked from its external original network or formula. '
        'The transformed K3,3 and 120-edge equality-family controls both evaluate to 2. '
        'The latter avoids enumeration of 2^120 assignments.\n\n'
        'Single/repeated ternary Boolean counts are 7/7; the corresponding slack counts are 10/16. '
        'The all-eight-polarity formula is independently UNSAT. The 24-variable/96-clause controls '
        'retain a satisfying original assignment, but their tested local tensors remain unsupported. '
        'Neither unsupported cases nor the interrupted case contain a value claim.\n\n'
        'The test suite covers all 1,099 quadratic phases through four variables, 240 seeded '
        'full-contraction comparisons, inverse nonsymmetric rational bases, external request '
        'mutations, malformed proofs, signed cancellation, exact rational/big-integer arithmetic, '
        'and budget interruptions. Source hashes and complete replay inputs are in RESULTS.json.\n', encoding='utf-8')
    print(json.dumps(results['summary'], sort_keys=True))


if __name__ == '__main__':
    run()
