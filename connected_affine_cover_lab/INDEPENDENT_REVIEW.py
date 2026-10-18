"""Independent arithmetic and exhaustive review of the connected cover bound."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import cover


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def independent_count(n):
    # Count strings with no adjacent zeros by a two-state recurrence.
    ending_one, ending_zero = 1, 0
    for _ in range(n):
        ending_one, ending_zero = ending_one + ending_zero, ending_one
    return ending_one + ending_zero


def independent_affine(support, n):
    support = set(support)
    if not support:
        return None
    base = next(iter(support))
    directions = {x ^ base for x in support}
    if 0 not in directions or len(directions) & (len(directions) - 1):
        return None
    if any((x ^ y) not in directions for x in directions for y in directions):
        return None
    return (len(directions).bit_length() - 1, len(support))


def main():
    payload = json.loads((HERE / 'RESULTS.json').read_text(encoding='utf-8'))
    exhaustive = payload['exhaustive_small']
    all_size = payload['all_size_controls']
    assert len(exhaustive) == 7 and len(all_size) == 8
    for name, recorded in payload['source_hashes'].items():
        assert sha(HERE / name) == recorded, name
    small_replayed = 0
    for row in exhaustive:
        n = row['n']
        target = {x for x in range(1 << n)
                  if all(((x >> i) & 1) or ((x >> (i + 1)) & 1)
                         for i in range(max(0, n - 1)))}
        max_dimension = -1
        contained = 0
        for support in cover.affine_supports(n):
            if support <= target:
                info = independent_affine(support, n)
                assert info is not None
                contained += 1
                max_dimension = max(max_dimension, info[0])
        assert len(target) == independent_count(n) == row['satisfying_count']
        assert max_dimension == (n + 1) // 2 == row['max_contained_dimension']
        assert contained == row['contained_supports']
        small_replayed += 1
    large_replayed = 0
    for row in all_size:
        n = row['n']
        assert row['satisfying_count'] == independent_count(n)
        assert row['explicit_dimension'] == (n + 1) // 2
        expected = (independent_count(n) + (1 << ((n + 1) // 2)) - 1) // (1 << ((n + 1) // 2))
        assert row['lower_bound_pieces'] == expected
        large_replayed += 1
    review = {'status': 'VERIFIED_INDEPENDENT_CONNECTED_AFFINE_REVIEW',
              'small_cases': small_replayed, 'all_size_cases': large_replayed,
              'n256_lower_bound': next(row['lower_bound_pieces'] for row in all_size if row['n'] == 256),
              'source_hashes_match': True}
    (HERE / 'INDEPENDENT_REVIEW.json').write_text(json.dumps(review, indent=2, sort_keys=True) + '\n', encoding='utf-8')
    (HERE / 'INDEPENDENT_REVIEW.md').write_text(
        '# Independent connected affine review\n\n'
        'The seven exhaustive small path instances were regenerated and checked '
        'with an independent affine-coset closure test. Their maximum contained '
        'dimension is exactly ceil(n/2). The Fibonacci recurrence and the all-size '
        'piece lower bound were independently recomputed through n=256; the '
        'n=256 lower bound is 1,090,151,200,392,118. Source hashes match. The '
        'result applies only to nonnegative affine-support decompositions and does '
        'not claim SAT hardness or a P-versus-NP resolution.\n', encoding='utf-8')
    print(json.dumps(review, sort_keys=True))


if __name__ == '__main__':
    main()
