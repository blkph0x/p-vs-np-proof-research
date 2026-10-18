from datetime import datetime, timezone
from fractions import Fraction as F
import hashlib
import json
from pathlib import Path
import random

from crossing import (crossover_graph, deletion_signature, enc, encode_matrix,
                      four_port_identity, matchgate_violations, ordinary_crossing,
                      pairing_expansion, q, signed_crossing, solve_pfaffian, verify_pfaffian)

HERE = Path(__file__).resolve().parent


def source_hashes():
    return {p.name: hashlib.sha256(p.read_bytes()).hexdigest()
            for p in [HERE/'crossing.py', HERE/'test_crossing.py',
                      HERE/'run_experiments.py', HERE/'THEOREM.md']}


def main():
    before = source_hashes()
    rng = random.Random(17761018)
    cases = []

    def add(name, a, expected=None, expand=True, caps=None):
        proof = solve_pfaffian(a, **(caps or {}))
        verified = verify_pfaffian(a, proof)
        terms = pairing_expansion(a) if expand else None
        if terms is not None:
            direct = sum((q(r['signed_product']) for r in terms), F(0))
            if expected is not None:
                assert direct == expected
            expected = direct
        if proof['status'] == 'EXACT':
            assert verified['status'] == 'VERIFIED'
            assert q(proof['value']) == expected
        else:
            assert verified['status'] == 'UNKNOWN' and 'value' not in proof
        cases.append({'name': name, 'original_matrix': encode_matrix(a), 'caps': caps or {},
                      'expected_value': enc(expected) if expected is not None else None,
                      'pairing_terms': terms, 'proof': proof, 'verification': verified})

    add('empty', [])
    add('odd_three', [[0, 2, 3], [-2, 0, 4], [-3, -4, 0]])
    add('two_existing_matchings_cancel', [[0, 1, 1, 0], [-1, 0, 0, 1], [-1, 0, 0, 1], [0, -1, -1, 0]])
    add('requires_sign_changing_pivot_swap', [[0, 0, 2, 0], [0, 0, 0, 3], [-2, 0, 0, 0], [0, -3, 0, 0]])
    for n in (2, 4, 6, 8, 10):
        for trial in range(6):
            a = [[F(0) for _ in range(n)] for _ in range(n)]
            for i in range(n):
                for j in range(i+1, n):
                    a[i][j] = F(rng.randint(-3, 3), rng.randint(1, 4))
                    a[j][i] = -a[i][j]
            add(f'rational_random_{n}_{trial}', a)
    for n in (16, 24, 40):
        a = [[int(i < j)-int(i > j) for j in range(n)] for i in range(n)]
        add(f'complete_ordered_graph_{n}', a, F(1), expand=False)
    a = [[0, 2**160], [-2**160, 0]]
    add('large_exact_integer', a)
    add('entry_bit_cap', a, caps={'max_entry_bits': 64})
    add('vertex_cap', [[0, 1], [-1, 0]], caps={'max_vertices': 1})
    n, edges = crossover_graph()
    graph_rows = deletion_signature(n, edges, [0, 1, 2, 3])
    assert [q(row['value']) for row in graph_rows] == signed_crossing()
    ordinary_bad = matchgate_violations(ordinary_crossing())
    assert ordinary_bad and not matchgate_violations(signed_crossing())
    report = {
        'scope': 'Exact ordered rational Pfaffians and crossing-sign controls; no SAT algorithm claim.',
        'created_utc': datetime.now(timezone.utc).isoformat(),
        'source_sha256': before, 'sources_unchanged': before == source_hashes(),
        'ordinary_crossing': list(map(enc, ordinary_crossing())),
        'signed_crossing': list(map(enc, signed_crossing())),
        'ordinary_four_port_residual': enc(four_port_identity(ordinary_crossing())),
        'ordinary_matchgate_violations': ordinary_bad,
        'signed_matchgate_violations': matchgate_violations(signed_crossing()),
        'crossover_graph': {'n': n, 'edges': edges, 'ports': [0, 1, 2, 3], 'deletion_rows': graph_rows},
        'equality4_environment': {'support_masks': [0, 15], 'ordinary_contraction': 2, 'signed_contraction': 0},
        'pfaffian_cases': cases,
        'summary': {'cases': len(cases), 'exact': sum(r['proof']['status'] == 'EXACT' for r in cases),
                    'unknown': sum(r['proof']['status'] == 'UNKNOWN' for r in cases),
                    'saved_pairing_terms': sum(len(r['pairing_terms'] or []) for r in cases),
                    'all_exact_certificates_verified': all(r['verification']['status'] == 'VERIFIED'
                                                        for r in cases if r['proof']['status'] == 'EXACT')},
    }
    assert report['sources_unchanged']
    (HERE/'RESULTS.json').write_text(json.dumps(report, indent=2)+'\n', encoding='utf-8')
    print(json.dumps(report['summary']))


if __name__ == '__main__':
    main()
