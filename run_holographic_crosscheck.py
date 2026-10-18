"""Compare tensor methods on the same original formulas, with honest cap results."""
from collections import Counter
from datetime import datetime, timezone
from fractions import Fraction
import hashlib
import json
from math import comb
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE/'tensor_basis_lab'))
sys.path.insert(0, str(HERE/'holographic_tractability_lab'))
from tensor_basis import solve_basis, verify_basis
from affine_holant import solve_formula, verify_formula

BASES = {'identity': [[1, 0], [0, 1]], 'Hadamard': [[1, 1], [1, -1]],
         'nonsymmetric': [[1, 2], [1, 3]]}
TENSOR_CAPS = {'max_edge_assignments': 1024, 'max_local_states': 4096,
               'max_arithmetic': 1000000}
AFFINE_CAPS = {'max_entries': 16384, 'max_work': 1000000}


def hashes():
    names = ['run_holographic_crosscheck.py', 'ALGEBRAIC_CROSSCHECK.json',
             'tensor_basis_lab/tensor_basis.py', 'holographic_tractability_lab/affine_holant.py']
    return {name: hashlib.sha256((HERE/name).read_bytes()).hexdigest() for name in names}


def original_count(n, clauses, mode):
    if n <= 8:
        total = 0
        for assignment in range(1 << n):
            term = 1
            for clause in clauses:
                true = sum(((assignment >> (abs(lit)-1)) & 1) == (lit > 0) for lit in clause)
                term *= int(true > 0) if mode == 'sat' else (comb(len(clause)-1, true-1) if true else 0)
            total += term
        return total, 'original variable assignment enumeration'
    # Exact closed form only after checking that these really are disjoint positive triples.
    assert all(len(c) == 3 and all(type(lit) is int and lit > 0 for lit in c) for c in clauses)
    literals = [lit for clause in clauses for lit in clause]
    assert len(literals) == len(set(literals)) == n and set(literals) == set(range(1, n+1))
    return (7 if mode == 'sat' else 10)**len(clauses), 'verified disjoint positive ternary product'


def main():
    before = hashes()
    previous = json.loads((HERE/'ALGEBRAIC_CROSSCHECK.json').read_text(encoding='utf-8'))
    originals = [{'name': r['name'], 'n': r['n'], 'clauses': r['clauses'],
                  'previous_slack_count': r['original_reference_count']} for r in previous['cases']]
    originals += [{'name': name, 'n': n, 'clauses': cs} for name, n, cs in (
        ('empty_zero_variables', 0, []), ('unused_variables', 3, []),
        ('contradictory_units', 1, [[1], [-1]]), ('empty_clause', 2, [[]]),
        ('repeated_literal', 1, [[1, 1, 1]]), ('tautological_clause', 1, [[1, -1]]))]
    rows, stats = [], {'tensor': Counter(), 'affine': Counter()}
    for case in originals:
        n, clauses = case['n'], case['clauses']
        for mode in ('sat', 'slack'):
            expected, reference = original_count(n, clauses, mode)
            if mode == 'slack' and 'previous_slack_count' in case:
                assert expected == case['previous_slack_count']
            for basis_name, matrix in BASES.items():
                tensor = solve_basis(n, clauses, matrix, mode=mode, **TENSOR_CAPS)
                affine = solve_formula(n, clauses, matrix, mode=mode, **AFFINE_CAPS)
                tv = av = None
                if tensor['status'] == 'EXACT':
                    assert Fraction(*tensor['count']) == expected
                    tv = verify_basis(n, clauses, matrix, tensor['certificate'], mode=mode, **TENSOR_CAPS)
                    assert tv['valid']
                else:
                    assert tensor['status'] == 'UNKNOWN' and tensor.get('count') is None
                if affine['status'] == 'EXACT':
                    assert Fraction(*affine['value']) == expected
                    av = verify_formula(n, clauses, matrix, affine, mode=mode, **AFFINE_CAPS)
                    assert av['valid']
                else:
                    assert affine['status'] in ('UNKNOWN', 'UNSUPPORTED') and affine.get('value') is None
                stats['tensor'][tensor['status']] += 1
                stats['affine'][affine['status']] += 1
                rows.append({'name': case['name'], 'n': n, 'clauses': clauses, 'mode': mode,
                             'basis_name': basis_name, 'basis': matrix, 'expected_original_count': expected,
                             'reference_method': reference, 'tensor': tensor, 'tensor_verification': tv,
                             'affine': affine, 'affine_verification': av})
        print(case['name'], flush=True)
    assert before == hashes()
    summary = {'original_formulas': len(originals), 'inherited_original_formulas': len(previous['cases']),
               'original_mode_basis_requests': len(rows), 'statuses': stats,
               'all_exact_counts_match_originals': True,
               'affine_exact_where_full_edge_enumeration_capped': sum(r['affine']['status'] == 'EXACT'
                                                                    and r['tensor']['status'] == 'UNKNOWN' for r in rows)}
    report = {'created_utc': datetime.now(timezone.utc).isoformat(), 'source_sha256': before,
              'scope': 'Same-original finite comparison. Unsupported bases and exhausted caps make no SAT decision.',
              'tensor_caps': TENSOR_CAPS, 'affine_caps': AFFINE_CAPS, 'summary': summary, 'cases': rows}
    (HERE/'HOLOGRAPHIC_CROSSCHECK.json').write_text(json.dumps(report, indent=2)+'\n', encoding='utf-8')
    print(json.dumps(summary))


if __name__ == '__main__':
    main()
