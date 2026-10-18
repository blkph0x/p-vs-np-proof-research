"""Dense redundant syntax control for the supplied-order frontier DP."""

from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path

import boundary_dp as dp

HERE = Path(__file__).resolve().parent


def formula(pairs):
    n = 2 * pairs
    clauses = []
    for pair in range(pairs):
        left, right = 2 * pair, 2 * pair + 1
        clauses.extend([[-(left + 1), right + 1], [left + 1, -(right + 1)]])
    # Each added clause is a tautology, but it makes every variable pair
    # adjacent in the syntactic primal graph.
    for left in range(n):
        for right in range(left + 1, n):
            clauses.append([left + 1, -(left + 1), right + 1])
    return n, clauses


def strip_tautologies(clauses):
    return [clause for clause in clauses
            if not any(literal > 0 and -literal in clause for literal in clause)]


def digest(path):
    return sha256(path.read_bytes()).hexdigest()


def run():
    before = {name: digest(HERE / name) for name in ('boundary_dp.py', 'REDUNDANCY_ADVERSARY.py')}
    rows = []
    for pairs in range(3, 9):
        n, dense = formula(pairs)
        clean = strip_tautologies(dense)
        order = list(range(n))
        raw = dp.solve(n, dense, order)
        normalized = dp.solve(n, clean, order)
        assert raw['status'] == normalized['status'] == 'EXACT'
        assert raw['sat'] == normalized['sat'] is True
        assert raw['stats']['max_width'] == n - 1
        assert normalized['stats']['max_width'] == 1
        # After the first 2k variables, each of the k independent equalities
        # still contributes a distinct assignment while tautologies keep all
        # processed variables on the frontier. Thus at least 2^k states occur.
        assert raw['stats']['states'] >= 1 << pairs
        assert dp.verify(n, dense, raw)['valid']
        assert dp.verify(n, clean, normalized)['valid']
        rows.append({'pairs': pairs, 'variables': n, 'raw_clauses': len(dense),
                     'clean_clauses': len(clean), 'raw': raw['stats'],
                     'normalized': normalized['stats'], 'sat': raw['sat']})
    after = {name: digest(HERE / name) for name in ('boundary_dp.py', 'REDUNDANCY_ADVERSARY.py')}
    assert before == after
    payload = {'status': 'REDUNDANCY_ADVERSARY_PASS', 'rows': rows,
               'source_hashes_before': before, 'source_hashes_after': after,
               'source_unchanged_during_run': True,
               'interpretation': 'syntactic frontier blow-up; no SAT hardness claim'}
    (HERE / 'REDUNDANCY_ADVERSARY.json').write_text(json.dumps(payload, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'status': payload['status'], 'cases': len(rows),
                      'largest_raw_states': rows[-1]['raw']['states'],
                      'largest_normalized_states': rows[-1]['normalized']['states']}))


if __name__ == '__main__':
    run()
