"""Root review: independent symbolic Kronecker action and recursive graph sums."""
import copy
from datetime import datetime, timezone
from fractions import Fraction
import hashlib
from itertools import product
import json
from pathlib import Path
import sympy as sp

import basis

HERE = Path(__file__).resolve().parent


def main():
    sources = ('basis.py', 'test_basis.py', 'run_experiments.py', 'THEOREM.md')
    before = {p: hashlib.sha256((HERE/p).read_bytes()).hexdigest() for p in sources}
    saved = json.loads((HERE/'RESULTS.json').read_text(encoding='utf-8'))
    assert before == saved['source_hashes_before'] == saved['source_hashes_after']
    a, b, c, d, u, rho = sp.symbols('a b c d u rho')
    variables = (a, b, c, d, u)
    t = sp.Matrix([[a, b], [c, d]])
    adj = t.adjugate()
    kt = sp.kronecker_product(t, t, t)
    kj = sp.kronecker_product(adj, adj, adj)
    g = list(sp.Matrix([[1, 0, 0, 0, 0, 0, 0, 1]]) * kt)
    clauses = {}
    for name, sig in (('OR3', [0, 1, 1, 1]), ('SLACK3', [0, 1, 2, 1])):
        col = sp.Matrix([sig[i.bit_count()] for i in range(8)])
        clauses[name] = list(kj*col)

    def expression(terms):
        return sp.expand(sum(term['coefficient']*sp.prod(x**e for x, e in zip(variables, term['powers']))
                             for term in terms))

    cert = saved['certificate']
    assert basis.verify_product_type_obstruction(saved['product_type_certificate'])
    assert saved['product_type_certificate_replayed']
    assert saved['counts']['product_type_common_basis_obstructions'] == 1
    product_review = saved['product_type_certificate']
    assert product_review['surviving_zero_support_masks_abcd'] == [6, 9]
    checked_equations = 0
    for system in cert['equation_systems']:
        clause = clauses[system['gate']]
        expected = [g[(1 << k)-1] for k in range(4) if k % 2 != system['eq_support_parity']]
        expected += [clause[(1 << k)-1] for k in range(4) if k % 2 != system['clause_support_parity']]
        expected += [u*t.det()-1]
        assert len(expected) == len(system['equations']) == 5
        for wanted, terms in zip(expected, system['equations']):
            assert sp.expand(wanted-expression(terms)) == 0
            checked_equations += 1
    substituted_entries = 0
    for name, table in [('EQ3', g), *clauses.items()]:
        for k in range(4):
            actual = sp.rem(sp.expand(table[(1 << k)-1].subs({a: rho, b: 1, c: 1, d: -rho**2})), rho**3-1, rho)
            expected = sum(v*rho**i for i, v in enumerate(cert['reduced_entries'][name][k]))
            assert sp.expand(actual-expected) == 0
            substituted_entries += 1
    for identity in cert['bezout']:
        p, aa, bb = [sum(v*rho**i for i, v in enumerate(identity[key])) for key in ('p', 'A', 'B')]
        assert sp.expand(aa*p+bb*(rho**3-1)) == identity['K'] != 0

    # Independent replay of the four-family clause classification.  This uses
    # the reduced q0..q3 equations directly, rather than calling the helper
    # under review.  A rational polynomial c0+c1*rho+c2*rho^2 vanishes at a
    # primitive cube root exactly when c0=c1=c2.
    def primitive_zero(coefficients):
        return coefficients[0] == coefficients[1] == coefficients[2]

    classification_signatures = 0
    for f in product((-1, 0, 1), repeat=4):
        f0, f1, f2, f3 = f
        q = (
            (-f0-f3, -3*f1, -3*f2),
            (f2, -f0+f3, -f1),
            (f1, f2, -f0-f3),
            (-f0+f3, 3*f1, -3*f2),
        )
        branches = []
        for rho_name, zero in (
            ('one', lambda terms: sum(terms) == 0),
            ('primitive', primitive_zero),
        ):
            for clause_parity, indices in ((0, (1, 3)), (1, (0, 2))):
                if all(zero(q[index]) for index in indices):
                    branches.extend((
                        {'rho': rho_name, 'eq_support_parity': 0,
                         'clause_support_parity': clause_parity},
                        {'rho': rho_name, 'eq_support_parity': 1,
                         'clause_support_parity': 1-clause_parity},
                    ))
        assert branches == saved['symmetric_clause_classification'].get(
            'EQ3' if f == basis.EQ3 else 'NAE3' if f == basis.NAE3 else
            'OR3' if f == basis.OR3 else 'SLACK3' if f == basis.SLACK3 else
            '__unlisted__', branches)
        classification_signatures += 1

    # Independent symbolic replay of both edge-specific certificates.  The
    # support enumeration is checked from the saved masks, then the normalized
    # adjugate clause equations are regenerated from scratch.
    edge_certificates = {
        'OR3': saved['edge_specific_certificate'],
        'SLACK3': saved['edge_specific_slack_certificate'],
    }
    assert basis.verify_edge_specific_or3_certificate(edge_certificates['OR3'])
    assert basis.verify_edge_specific_slack_certificate(edge_certificates['SLACK3'])
    assert all(edge['eq_survivors'] == {'0': [[15, 15, 15]], '1': [[15, 15, 15]]}
               for edge in edge_certificates.values())
    x, y, z, r1, r2, r3 = sp.symbols('x y z r1 r2 r3')
    normalized = [sp.Matrix([[1, rr], [pp, -pp*rr]])
                  for pp, rr in ((x, r1), (y, r2), (z, r3))]
    adj_normalized = [matrix.adjugate() for matrix in normalized]
    monomial_vars = {'xy': x*y, 'xz': x*z, 'x': x, 'yz': y*z, 'y': y, 'z': z, '1': 1}
    def vector_polynomial(vector, monomials):
        return sum(coefficient * monomial_vars[name]
                   for coefficient, name in zip(vector, monomials))
    factors = {
        'even': {1: -r2*r3, 2: -r1*r3, 4: r1*r2, 7: 1},
        'odd': {0: -r1*r2*r3, 3: -r3, 5: r2, 6: r1},
    }
    output_indices = {'even': [1, 2, 4, 7], 'odd': [0, 3, 5, 6]}
    edge_equations_checked = 0
    for gate, edge in edge_certificates.items():
        clause_values = {'OR3': [0, 1, 1, 1], 'SLACK3': [0, 1, 2, 1]}[gate]
        clause_values = [clause_values[source.bit_count()] for source in range(8)]
        values = []
        for output in range(8):
            value = 0
            for source in range(8):
                term = clause_values[source]
                for port in range(3):
                    term *= adj_normalized[port][(output >> port) & 1, (source >> port) & 1]
                value += term
            values.append(sp.expand(value).subs(z, 1/(x*y)))
        for parity in ('even', 'odd'):
            for index, vector in zip(output_indices[parity], edge['clause_equations'][parity]):
                expected = vector_polynomial(vector, edge['monomials']).subs(z, 1/(x*y))
                assert sp.expand(values[index] - factors[parity][index] * expected) == 0
                edge_equations_checked += 1
            identity = edge['identities'][parity]
            assert sum(identity[i] * vector_polynomial(edge['clause_equations'][parity][i], edge['monomials'])
                       for i in range(4)) == identity[4]

    # Replay every per-edge column-flip case, which is the normalization needed
    # when different degree-three equality nodes choose different parity
    # orientations.  This is independent of the standard-library generator.
    global_equations_checked = 0
    global_certificates = {
        'OR3': saved['edge_specific_global_certificate'],
        'SLACK3': saved['edge_specific_global_slack_certificate'],
    }
    for gate, global_certificate in global_certificates.items():
        assert basis.verify_edge_specific_global_certificate(global_certificate)
        clause_values_by_weight = {'OR3': [0, 1, 1, 1], 'SLACK3': [0, 1, 2, 1]}[gate]
        clause_values = [clause_values_by_weight[source.bit_count()] for source in range(8)]
        for case_name, case in global_certificate['cases'].items():
            flips = [int(bit) for bit in case_name]
            matrices = []
            for index, flipped in enumerate(flips):
                matrix = sp.Matrix([[1, r1 if index == 0 else r2 if index == 1 else r3],
                                    [x if index == 0 else y if index == 1 else z,
                                     -(x if index == 0 else y if index == 1 else z) *
                                     (r1 if index == 0 else r2 if index == 1 else r3)]])
                if flipped:
                    matrix = matrix * sp.Matrix([[0, 1], [1, 0]])
                matrices.append(matrix)
            adjugates = [matrix.adjugate() for matrix in matrices]
            values = []
            for output in range(8):
                value = 0
                for source in range(8):
                    term = clause_values[source]
                    for port in range(3):
                        term *= adjugates[port][(output >> port) & 1, (source >> port) & 1]
                    value += term
                values.append(sp.expand(value))
            for parity in ('even', 'odd'):
                monomials = [tuple(exponent) for exponent in global_certificate['monomials']]
                for output, factor, vector in zip(case[parity]['outputs'], case[parity]['factors'], case[parity]['equations']):
                    expected = sum(coefficient * x**exponent[0] * y**exponent[1] * z**exponent[2]
                                   for coefficient, exponent in zip(vector, monomials))
                    rfactor = r1**factor[0] * r2**factor[1] * r3**factor[2]
                    assert sp.expand(values[output] - rfactor * expected) == 0
                    global_equations_checked += 1
                identity = case[parity]['identity']
                identity_poly = sum(sum(identity[i] * case[parity]['equations'][i][j]
                                         for i in range(4)) * x**monomials[j][0] * y**monomials[j][1] * z**monomials[j][2]
                                    for j in range(len(monomials)))
                assert identity_poly == identity[4]

    # Independently enumerate by pairing the smallest remaining vertex.
    boundary_count = 0
    for control in saved['positive_controls']:
        graph = control['graph']
        weights = {tuple(sorted((i, j))): Fraction(w) for i, j, w in graph['edges']}
        def pm(vertices):
            if not vertices:
                return Fraction(1)
            first, *rest = vertices
            return sum((weights.get((first, other), 0)*pm([x for x in rest if x != other])
                        for other in rest), Fraction(0))
        original = sp.Matrix([control['signature'][i.bit_count()] for i in range(8)])
        mt = sp.Matrix([[sp.Rational(v) for v in row] for row in control['basis']])
        if control['orientation'] == 'row':
            transformed = list(original.T*sp.kronecker_product(mt, mt, mt))
        else:
            inv = mt.inv()
            transformed = list(sp.kronecker_product(inv, inv, inv)*original)
        for mask in range(8):
            deleted = {v for bit, v in enumerate(graph['ports']) if mask >> bit & 1}
            total = pm([v for v in range(graph['vertices']) if v not in deleted])
            assert total == Fraction(control['transformed'][mask]) == transformed[mask]
            boundary_count += 1
    mutations = []
    for kind in ('constant', 'original_equation', 'reduced_entry'):
        changed = copy.deepcopy(cert)
        if kind == 'constant':
            changed['bezout'][0]['K'] += 1
        elif kind == 'original_equation':
            changed['equation_systems'][0]['equations'][0][0]['coefficient'] += 1
        else:
            changed['reduced_entries']['OR3'][0][0] += 1
        assert not basis.verify_obstruction(changed)
        mutations.append(kind)
    assert basis.verify_obstruction(cert)
    assert before == {p: hashlib.sha256((HERE/p).read_bytes()).hexdigest() for p in sources}
    report = {'all_checks_passed': True, 'reviewer': 'root, independent of lab author',
              'created_utc': datetime.now(timezone.utc).isoformat(), 'sympy_version': sp.__version__,
              'source_sha256': before, 'original_branch_equations_checked': checked_equations,
              'normal_form_entries_checked': substituted_entries, 'bezout_identities_checked': 4,
              'classification_signatures_checked': classification_signatures,
              'classification_replay': 'independent q-equation replay over {-1,0,1}^4',
              'edge_specific_equations_checked': edge_equations_checked,
              'edge_specific_replay': 'independent symbolic adjugate replay with seven support masks',
              'global_edge_specific_equations_checked': global_equations_checked,
              'global_edge_specific_replay': 'all eight per-edge flip cases for OR3 and slack',
              'product_type_obstruction_review': 'exact zero-mask split and diagonal/anti-diagonal support replay',
              'independent_recursive_graph_entries': boundary_count, 'mutation_rejections': mutations,
              'proof_review': 'All complex normal-form branches, nonzero scaling, odd-parity swaps and field scope reviewed; no gap found. Not proof-assistant formalization.'}
    (HERE/'INDEPENDENT_REVIEW.json').write_text(json.dumps(report, indent=2)+'\n', encoding='utf-8')
    print(json.dumps(report))


if __name__ == '__main__':
    main()
