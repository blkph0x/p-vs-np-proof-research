"""Exhaustive three-variable cross-check against brute force and replay."""

from __future__ import annotations

from hashlib import sha256
from itertools import combinations, permutations, product
import json
from pathlib import Path

import boundary_dp as dp

HERE = Path(__file__).resolve().parent


def digest(path):
    return sha256(path.read_bytes()).hexdigest()


def run():
    n = 3
    clauses = []
    for choices in product((0, 1, -1), repeat=n):
        if all(choice == 0 for choice in choices):
            continue
        clauses.append([((index + 1) * choice) for index, choice in enumerate(choices) if choice])
    orders = list(permutations(range(n)))
    source_names = ('boundary_dp.py', 'EXHAUSTIVE_SMALL_CHECK.py')
    before = {name: digest(HERE / name) for name in source_names}
    certificates = 0
    cnf_count = 0
    for size in range(4):
        for selected in combinations(clauses, size):
            cnf = [list(clause) for clause in selected]
            expected = dp.brute_sat(n, cnf)
            cnf_count += 1
            for order in orders:
                result = dp.solve(n, cnf, order)
                assert result['status'] == 'EXACT'
                assert result['sat'] == expected
                assert dp.verify(n, cnf, result)['valid']
                certificates += 1
    after = {name: digest(HERE / name) for name in source_names}
    assert before == after
    review = {'status': 'EXHAUSTIVE_SMALL_BOUNDARY_CROSSCHECK_PASS',
              'variables': n, 'max_clauses': 3, 'cnfs': cnf_count,
              'orders': len(orders), 'certificates': certificates,
              'source_hashes_before': before, 'source_hashes_after': after,
              'source_unchanged_during_run': True}
    (HERE / 'EXHAUSTIVE_SMALL_CHECK.json').write_text(json.dumps(review, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(review))


if __name__ == '__main__':
    run()
