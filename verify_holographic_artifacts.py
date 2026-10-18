"""Replay saved holographic claims against external original inputs and hashes."""
from datetime import datetime, timezone
from fractions import Fraction as F
import hashlib
import json
from math import comb
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
for name in ('tensor_basis_lab', 'simultaneous_basis_lab', 'holographic_tractability_lab', 'crossing_sign_lab'):
    sys.path.insert(0, str(HERE/name))
import tensor_basis as tensor
import basis
import affine_holant as affine
import crossing


def read(name):
    return json.loads((HERE/name).read_text(encoding='utf-8'))


def logical_count(n, clauses, mode):
    if n > 8:
        if not clauses:
            return 1 << n
        literals = [v for clause in clauses for v in clause]
        assert all(len(clause) == 3 and all(v > 0 for v in clause) for clause in clauses)
        assert len(literals) == len(set(literals)) == n and set(literals) == set(range(1, n+1))
        return (7 if mode == 'sat' else 10)**len(clauses)
    total = 0
    for x in range(1 << n):
        factor = 1
        for clause in clauses:
            truth = [bool(x & (1 << (abs(lit)-1))) == (lit > 0) for lit in clause]
            t = sum(truth)
            factor *= int(any(truth)) if mode == 'sat' else (comb(len(clause)-1, t-1) if t else 0)
        total += factor
    return total


def direct_network(net):
    assert net['edges'] <= 12
    total = F(0)
    for x in range(1 << net['edges']):
        term = F(1)
        for node in net['rows']+net['columns']:
            local = sum(((x >> e) & 1) << i for i, e in enumerate(node['ports']))
            term *= affine.ratio(node['values'][local])
        total += term
    return total


def main():
    bound = {}
    def bind(folder, mappings):
        for name, expected in mappings.items():
            path = (Path(folder)/name).as_posix()
            actual = hashlib.sha256((HERE/path).read_bytes()).hexdigest()
            assert actual == expected, ('stale source', path)
            assert path not in bound or bound[path] == expected, ('conflicting source references', path)
            bound[path] = expected

    tb = read('tensor_basis_lab/RESULTS.json')
    sb = read('simultaneous_basis_lab/RESULTS.json')
    sir = read('simultaneous_basis_lab/INDEPENDENT_REVIEW.json')
    af = read('holographic_tractability_lab/RESULTS.json')
    cr = read('crossing_sign_lab/RESULTS.json')
    cc = read('HOLOGRAPHIC_CROSSCHECK.json')
    ts = read('HOLOGRAPHIC_TEST_SUMMARY.json')
    for folder, data, field in (
        ('tensor_basis_lab', tb, 'source_sha256'),
        ('simultaneous_basis_lab', sb, 'source_hashes_before'),
        ('holographic_tractability_lab', af, 'source_sha256'),
        ('crossing_sign_lab', cr, 'source_sha256'),
        ('', cc, 'source_sha256'), ('', ts, 'implementation_sha256')):
        bind(folder, data[field])
    assert sb['source_hashes_before'] == sb['source_hashes_after']
    assert sir['all_checks_passed'] and sir['classification_signatures_checked'] == 81
    assert tb['source_unchanged_during_run'] and cr['sources_unchanged']
    assert ts['all_tests_passed'] and ts['source_unchanged_during_tests']
    summary = {}

    exact = unknown = 0
    for row in tb['cases']:
        req, result = row['request'], row['result']
        args = (req['n'], req['clauses'], req['basis'])
        if result['status'] == 'EXACT':
            check = tensor.verify_basis(*args, result['certificate'], mode=req['mode'], **tb['limits'])
            assert check['valid']
            assert F(*result['count']) == logical_count(req['n'], req['clauses'], req['mode'])
            exact += 1
        else:
            assert result['status'] == 'UNKNOWN' and result['count'] is None and result['certificate'] is None
            unknown += 1
    for row in tb['local_transform_controls']:
        req = row['request']
        assert tensor.verify_transformation(req['n'], req['clauses'], req['basis'],
                                             row['result']['certificate'], mode=req['mode'], **tb['limits'])['valid']
    for row in tb['wrong_same_basis_controls']:
        req, saved = row['request'], row['control']
        replay = tensor.wrong_same_basis_control(req['n'], req['clauses'], req['basis'], mode=req['mode'], **tb['limits'])
        assert replay['changes_count'] and replay == saved
    summary['tensor'] = {'exact_proofs': exact, 'unknown': unknown,
                         'local_transform_proofs': len(tb['local_transform_controls']),
                         'wrong_action_controls': len(tb['wrong_same_basis_controls'])}

    assert basis.verify_obstruction(sb['certificate'])
    assert basis.verify_product_type_obstruction(sb['product_type_certificate'])
    assert sb['product_type_certificate_replayed']
    assert sb['counts']['product_type_common_basis_obstructions'] == 1
    classification = sb['symmetric_clause_classification']
    assert classification['OR3'] == [] and classification['SLACK3'] == []
    assert classification['NAE3'] == basis.common_eq3_parity_branches(basis.NAE3)
    assert classification['EQ3'] == basis.common_eq3_parity_branches(basis.EQ3)
    assert sb['counts']['symmetric_clause_families'] == 4
    assert basis.verify_edge_specific_or3_certificate(sb['edge_specific_certificate'])
    assert basis.verify_edge_specific_slack_certificate(sb['edge_specific_slack_certificate'])
    assert basis.verify_edge_specific_global_certificate(sb['edge_specific_global_certificate'])
    assert basis.verify_edge_specific_global_certificate(sb['edge_specific_global_slack_certificate'])
    assert sb['counts']['edge_specific_parity_branches'] == 4
    assert sb['counts']['edge_specific_surviving_support_triples'] == 2
    assert sb['counts']['edge_specific_clause_pairs_excluded'] == 2
    assert sb['counts']['edge_specific_flip_cases_checked_per_clause'] == 16
    assert sir['edge_specific_equations_checked'] == 16 and sir['global_edge_specific_equations_checked'] == 128
    entries = 0
    for row in sb['positive_controls']:
        graph = row['graph']
        weights = [(u, v, F(w)) for u, v, w in graph['edges']]
        graph_rows = crossing.deletion_signature(graph['vertices'], weights, graph['ports'])
        values = [crossing.q(x['value']) for x in graph_rows]
        assert values == [F(v) for v in row['transformed']]
        matrix = [[F(v) for v in r] for r in row['basis']]
        assert values == basis.transform(row['signature'], matrix if row['orientation'] == 'row'
                                         else basis.inverse2(matrix), row['orientation'])
        entries += len(values)
    summary['simultaneous_basis'] = {'parity_systems': len(sb['certificate']['equation_systems']),
                                     'bezout_identities': len(sb['certificate']['bezout']),
                                     'positive_graph_entries': entries,
                                     'symmetric_clause_families': sb['counts']['symmetric_clause_families'],
                                     'edge_specific_surviving_support_triples': sb['counts']['edge_specific_surviving_support_triples'],
                                     'edge_specific_clause_pairs_excluded': sb['counts']['edge_specific_clause_pairs_excluded'],
                                     'edge_specific_flip_cases_checked_per_clause': sb['counts']['edge_specific_flip_cases_checked_per_clause'],
                                     'product_type_common_basis_obstructions': sb['counts']['product_type_common_basis_obstructions']}

    exact = unsupported = unknown = planted = brute = 0
    for row in af['cases']:
        req, result, caps = row['request'], row['result'], row['caps']
        if result['status'] == 'EXACT':
            if req['kind'] == 'formula':
                check = affine.verify_formula(req['n'], req['clauses'], req['basis'], result, mode=req['mode'], **caps)
                reference = logical_count(req['n'], req['clauses'], req['mode'])
                assert F(*result['value']) == reference
            else:
                check = affine.verify_affine(req['network'], req['basis'], result, **caps)
                if req['network']['edges'] <= 12:
                    assert F(*result['value']) == direct_network(req['network'])
                    brute += 1
            assert check['valid']
            if 'value' in row['reference']:
                assert F(*result['value']) == F(*row['reference']['value'])
            exact += 1
        else:
            assert result['status'] in ('UNSUPPORTED', 'UNKNOWN')
            assert result['value'] is None and result['certificate'] is None
            unsupported += result['status'] == 'UNSUPPORTED'
            unknown += result['status'] == 'UNKNOWN'
        if 'planted_assignment' in row['reference']:
            x = row['reference']['planted_assignment']
            assert type(x) is int and 0 <= x < 1 << req['n']
            assert all(any(bool(x & (1 << (abs(lit)-1))) == (lit > 0) for lit in clause) for clause in req['clauses'])
            planted += 1
    summary['affine'] = {'exact_proofs': exact, 'unsupported': unsupported, 'unknown': unknown,
                         'original_witnesses': planted, 'small_networks_recounted': brute}

    exact = unknown = terms = 0
    for row in cr['pfaffian_cases']:
        original, proof = row['original_matrix'], row['proof']
        if proof['status'] == 'EXACT':
            assert crossing.verify_pfaffian(original, proof)['status'] == 'VERIFIED'
            assert crossing.q(proof['value']) == crossing.q(row['expected_value'])
            exact += 1
        else:
            assert proof['status'] == 'UNKNOWN' and 'value' not in proof
            unknown += 1
        if row['pairing_terms'] is not None:
            replay = crossing.pairing_expansion(original)
            assert replay == row['pairing_terms']
            assert sum((crossing.q(x['signed_product']) for x in replay), F(0)) == crossing.q(row['expected_value'])
            terms += len(replay)
    graph = cr['crossover_graph']
    assert crossing.deletion_signature(graph['n'], graph['edges'], graph['ports']) == graph['deletion_rows']
    assert [crossing.q(r['value']) for r in graph['deletion_rows']] == crossing.signed_crossing()
    assert crossing.four_port_identity(cr['ordinary_crossing']) == 2
    assert crossing.matchgate_violations(cr['signed_crossing']) == []
    assert sum(crossing.q(cr['ordinary_crossing'][i]) for i in (0, 15)) == 2
    assert sum(crossing.q(cr['signed_crossing'][i]) for i in (0, 15)) == 0
    summary['crossing'] = {'exact_pfaffian_proofs': exact, 'unknown': unknown,
                           'pairing_terms': terms, 'graph_boundary_entries': 16}

    tc = ac = 0
    for row in cc['cases']:
        n, clauses, mode, matrix = row['n'], row['clauses'], row['mode'], row['basis']
        expected = logical_count(n, clauses, mode)
        assert row['expected_original_count'] == expected
        if row['tensor']['status'] == 'EXACT':
            assert tensor.verify_basis(n, clauses, matrix, row['tensor']['certificate'], mode=mode, **cc['tensor_caps'])['valid']
            assert F(*row['tensor']['count']) == expected
            tc += 1
        else:
            assert row['tensor']['status'] == 'UNKNOWN' and row['tensor'].get('count') is None
        if row['affine']['status'] == 'EXACT':
            assert affine.verify_formula(n, clauses, matrix, row['affine'], mode=mode, **cc['affine_caps'])['valid']
            assert F(*row['affine']['value']) == expected
            ac += 1
        else:
            assert row['affine']['status'] in ('UNKNOWN', 'UNSUPPORTED') and row['affine'].get('value') is None
    summary['same_original_crosscheck'] = {'requests': len(cc['cases']), 'tensor_exact': tc, 'affine_exact': ac}
    bind('', {Path(__file__).name: hashlib.sha256(Path(__file__).read_bytes()).hexdigest()})
    for name, value in bound.items():
        assert hashlib.sha256((HERE/name).read_bytes()).hexdigest() == value
    report = {'all_checks_passed': True, 'created_utc': datetime.now(timezone.utc).isoformat(),
              'source_reference_count': len(bound), 'source_sha256': bound, 'summary': summary}
    (HERE/'HOLOGRAPHIC_ARTIFACT_AUDIT.json').write_text(json.dumps(report, indent=2)+'\n', encoding='utf-8')
    print(json.dumps(report['summary']))
    print('Checked source references:', len(bound))


if __name__ == '__main__':
    main()
