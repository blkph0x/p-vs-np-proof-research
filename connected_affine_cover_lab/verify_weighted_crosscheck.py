"""Independent replay of the connected-path weighted-DAG crosscheck."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import weighted_crosscheck as wc

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent


def hashes():
    paths = [ROOT / 'weighted_affine_dag_lab' / 'dag.py',
             ROOT / 'affine_boundary_lab' / 'boundary.py', HERE / 'weighted_crosscheck.py',
             HERE / 'verify_weighted_crosscheck.py']
    return {str(p.relative_to(ROOT)).replace('\\', '/'): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in paths}


def run():
    payload = json.loads((HERE / 'WEIGHTED_RESULTS.json').read_text(encoding='utf-8'))
    rows = payload['rows']
    assert len(rows) == 5 and payload['exact_count'] == 5
    replay = []
    for row in rows:
        n = row['n']
        factors = wc.path_factors(n)
        order = list(range(n - 1))
        result = wc.dag.solve_factors(n, factors, order=order, **wc.CAPS)
        checked = wc.dag.verify_factors(n, factors, result, order=order, **wc.CAPS)
        expected = [wc.cover.fib_count(n), 1]
        assert result['status'] == 'EXACT' and result['value'] == expected
        assert checked['valid'] and checked['value'] == expected
        assert result['stats']['peak_terms'] <= 4
        replay.append({'n': n, 'value': result['value'], 'verified': checked['valid'],
                       'peak_terms': result['stats']['peak_terms']})
    source = hashes()
    assert payload['source_hashes_before'] == payload['source_hashes_after']
    review = {'status': 'VERIFIED_INDEPENDENT_WEIGHTED_CROSSCHECK', 'rows': replay,
              'row_count': len(replay), 'exact_count': sum(x['verified'] for x in replay),
              'max_peak_terms': max(x['peak_terms'] for x in replay),
              'replay_source_hashes': source}
    (HERE / 'WEIGHTED_REVIEW.json').write_text(json.dumps(review, indent=2) + '\n', encoding='utf-8')
    (HERE / 'WEIGHTED_REVIEW.md').write_text(
        '# Independent weighted-DAG review\n\n'
        'The path CNFs for n = 8, 16, 32, 64, and 128 were reconstructed from n, '
        'solved again, and replay-verified against the Fibonacci count. All five are '
        'EXACT; the largest retained message has four terms. This is an escape route '
        'from the nonnegative affine-support cover lower bound, not a P=NP result.\n',
        encoding='utf-8')
    print(json.dumps({'status': review['status'], 'rows': len(replay),
                      'exact': review['exact_count'], 'max_peak_terms': review['max_peak_terms']}))


if __name__ == '__main__':
    run()
