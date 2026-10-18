"""Independently replay the exact arithmetic records for the rank bound."""

from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path

from exception_rank_bound import theorem_parameters, verify_bound

HERE = Path(__file__).resolve().parent


def digest(path):
    return sha256(path.read_bytes()).hexdigest()


def run():
    payload = json.loads((HERE / 'EXCEPTION_RANK_BOUND_RESULTS.json').read_text(encoding='utf-8'))
    assert payload['status'] == 'EXCEPTION_RANK_BOUND_CHECK_PASS'
    assert payload['ranks_checked'] == [6, 7, 8, 16, 32]
    assert payload['source_hash'] == digest(HERE / 'exception_rank_bound.py')
    for record in payload['records']:
        r = record['rank']
        assert record == dict(verify_bound(r), **theorem_parameters(r))
        assert record['union_bound_lt_one']
    source = {name: digest(HERE / name) for name in
              ('exception_rank_bound.py', 'run_exception_rank_bound.py',
               'EXCEPTION_RANK_BOUND_REVIEW.py')}
    review = {
        'status': 'VERIFIED_INDEPENDENT_EXCEPTION_RANK_BOUND',
        'ranks_checked': payload['ranks_checked'],
        'minimum_rank6_states': 64,
        'rank32_columns': 16 * 32 * 32 + 32,
        'rank32_states': 2 ** 32,
        'source_hashes': source,
        'scope': 'Exact replay of the probabilistic existence inequalities; no explicit hard matrix is claimed.',
    }
    (HERE / 'EXCEPTION_RANK_BOUND_REVIEW.json').write_text(
        json.dumps(review, indent=2) + '\n', encoding='utf-8')
    (HERE / 'EXCEPTION_RANK_BOUND_REVIEW.md').write_text(
        '# Independent exceptional-rank bound review\n\n'
        'Exact rational replay confirms the union-bound construction for ranks '
        '6, 7, 8, 16 and 32. At rank 32 it gives 16,416 columns and a forced '
        'minimum exceptional-state count of 2^32 for this route. The result is '
        'probabilistic existence, not an explicit hard instance or a P-versus-NP '
        'separation.\n', encoding='utf-8')
    print(json.dumps({'status': review['status'], 'ranks': review['ranks_checked'],
                      'rank32_columns': review['rank32_columns'],
                      'rank32_states': review['rank32_states']}))


if __name__ == '__main__':
    run()
