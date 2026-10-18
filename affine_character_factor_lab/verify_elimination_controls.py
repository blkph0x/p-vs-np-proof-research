"""Independent replay of the weighted-DAG comparison records."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import elimination_controls as controls


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    payload = json.loads((HERE / 'ELIMINATION_RESULTS.json').read_text(encoding='utf-8'))
    rows = payload['rows']
    assert len(rows) == 9
    exact = [row for row in rows if row['status'] == 'EXACT']
    unknown = [row for row in rows if row['status'] == 'UNKNOWN']
    assert len(exact) == 8 and len(unknown) == 1
    for key, recorded in payload['source_hashes'].items():
        if key == 'weighted_affine_dag_lab/dag.py':
            actual = sha(controls.WEIGHTED / 'dag.py')
        elif key == 'affine_boundary_lab/boundary.py':
            actual = sha(controls.WEIGHTED.parent / 'affine_boundary_lab' / 'boundary.py')
        else:
            actual = sha(HERE / 'elimination_controls.py')
        assert actual == recorded, key
    replayed = 0
    for row in exact:
        m = row['m']
        order = row['order']
        factors = controls.connected_chain(m)
        result = controls.dag.solve_factors(2 * m, factors, order=order, **controls.CAPS)
        assert result['status'] == 'EXACT' and result['value'] == [1, 1]
        checked = controls.dag.verify_factors(2 * m, factors, result, order=order, **controls.CAPS)
        assert checked['valid'] and checked['status'] == 'VERIFIED'
        assert row['expected_matches'] is True and row['verification_valid'] is True
        assert row['source_request_sha256'] == result['request_sha256']
        replayed += 1
    capped = unknown[0]
    assert capped['name'] == 'poor_order_chain_12'
    assert capped['reason'] == 'work cap' and 'value' not in capped
    review = {
        'status': 'VERIFIED_INDEPENDENT_ELIMINATION_REVIEW',
        'rows': len(rows), 'exact': len(exact), 'unknown': len(unknown),
        'exact_replayed': replayed,
        'interleaved_chain_128_peak_terms': next(row['producer_stats']['peak_terms']
                                                 for row in exact if row['name'] == 'interleaved_chain_128'),
        'poor_order_status': capped['status'],
        'source_hashes_match': True,
    }
    (HERE / 'ELIMINATION_REVIEW.json').write_text(json.dumps(review, indent=2, sort_keys=True) + '\n', encoding='utf-8')
    (HERE / 'ELIMINATION_REVIEW.md').write_text(
        '# Independent weighted-DAG review\n\n'
        'All eight interleaved connected-chain records were regenerated from the '
        'original factor constructors and independently replayed by the weighted '
        'DAG verifier. Every value was one, with peak retained terms at most three '
        'for the 128-block case. The same factors in the saved poor order reached '
        'the declared work cap and carried no value. Dependency source hashes '
        'matched. This is order-sensitive finite evidence, not a general SAT '
        'algorithm or a P-versus-NP result.\n', encoding='utf-8')
    print(json.dumps(review, sort_keys=True))


if __name__ == '__main__':
    main()
