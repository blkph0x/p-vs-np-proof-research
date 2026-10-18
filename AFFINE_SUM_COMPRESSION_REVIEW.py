"""Reproduce the bounded algebraic controls for the reviewed merge design.

No production module is imported or modified. This writes only the sibling
AFFINE_SUM_COMPRESSION_REVIEW.json, and refuses an unreviewed draft revision.
"""
from hashlib import sha256
import json
from pathlib import Path
import random

HERE = Path(__file__).resolve().parent
DRAFT = 'AFFINE_SUM_COMPRESSION_NEXT.md'
REVIEWED_DRAFT_SHA256 = '6a271b4597991f07ff6ee6813ac6b55deaefb663857832e32cd631ccbb01fa40'
SEED = 2026101903


def phase_criterion_checks():
    cases = accepted = 0
    by_dimension = []
    for r in range(4):
        terms = [0] + [1 << i for i in range(r)]
        terms += [(1 << i) | (1 << j) for i in range(r) for j in range(i+1, r)]
        phases = []
        for coefficients in range(1 << len(terms)):
            chosen = [term for j, term in enumerate(terms) if coefficients >> j & 1]
            values = [sum((x & term) == term for term in chosen) & 1
                      for x in range(1 << r)]
            phases.append((chosen, values))
        dimension_cases = dimension_accepted = 0
        for q0, values0 in phases:
            for q1, values1 in phases:
                difference = set(q0) ^ set(q1)
                expected_quadratic = all(term.bit_count() <= 1 for term in difference)
                for sigma in (0, 1):
                    # Build the two-coset sign truth table independently, then
                    # recover its unique Boolean polynomial by Mobius transform.
                    anf = values0 + [bit ^ sigma for bit in values1]
                    for axis in range(r+1):
                        for mask in range(1 << (r+1)):
                            if mask >> axis & 1:
                                anf[mask] ^= anf[mask ^ (1 << axis)]
                    degree = max((mask.bit_count() for mask, coefficient in enumerate(anf)
                                  if coefficient), default=0)
                    assert (degree <= 2) == expected_quadratic
                    dimension_cases += 1
                    dimension_accepted += expected_quadratic
        cases += dimension_cases
        accepted += dimension_accepted
        by_dimension.append(dict(common_free_coordinates=r, cases=dimension_cases,
                                 quadratic_unions=dimension_accepted,
                                 cubic_obstructions=dimension_cases-dimension_accepted))
    assert cases == 33320
    return dict(cases=cases, quadratic_unions=accepted, cubic_obstructions=cases-accepted,
                by_dimension=by_dimension,
                oracle='complete two-coset sign table followed by Boolean Mobius transform')


def binary_rank(rows):
    pivots = {}
    for row in rows:
        while row:
            pivot = row.bit_length()-1
            if pivot in pivots:
                row ^= pivots[pivot]
            else:
                pivots[pivot] = row
                break
    return len(pivots)


def union_support_checks():
    rng = random.Random(SEED)
    cases = assignments = 0
    for _ in range(1000):
        n = rng.randrange(1, 8)
        rank = rng.randrange(1, n+1)
        rows, basis = [], {}
        while len(rows) < rank:
            original = rng.randrange(1, 1 << n)
            vector = original
            while vector:
                pivot = vector.bit_length()-1
                if pivot in basis:
                    vector ^= basis[pivot]
                else:
                    basis[pivot] = vector
                    rows.append(original)
                    break
        b0, b1 = rng.randrange(1 << rank), rng.randrange(1 << rank)
        while b1 == b0:
            b1 = rng.randrange(1 << rank)
        difference = b0 ^ b1
        j = next(i for i in range(rank) if difference >> i & 1)
        merged = [(rows[i] ^ (rows[j] if difference >> i & 1 else 0),
                   ((b0 >> i) & 1) ^ (((difference >> i) & 1) * ((b0 >> j) & 1)))
                  for i in range(rank) if i != j]
        assert binary_rank(rows) == rank
        assert binary_rank([row for row, rhs in merged]) == rank-1
        supported = 0
        for x in range(1 << n):
            syndrome = sum(((row & x).bit_count() & 1) << i for i, row in enumerate(rows))
            on_union = all(((row & x).bit_count() & 1) == rhs for row, rhs in merged)
            assert (syndrome in (b0, b1)) == on_union
            if on_union:
                selector = ((rows[j] & x).bit_count() & 1) ^ ((b0 >> j) & 1)
                assert syndrome == (b1 if selector else b0)
                supported += 1
            assignments += 1
        assert supported == 1 << (n-rank+1)
        cases += 1
    assert cases == 1000 and assignments == 35126
    return dict(cases=cases, assignment_checks=assignments, seed=SEED,
                dimensions_min=1, dimensions_max=7,
                rank_drop_checks=cases, selector_checks='every supported enumerated assignment',
                oracle='direct original syndromes versus merged-row satisfaction')


def main():
    sources = [DRAFT, Path(__file__).name, 'AFFINE_SUM_COMPRESSION_REVIEW.md']
    before = {name: sha256((HERE/name).read_bytes()).hexdigest() for name in sources}
    if before[DRAFT] != REVIEWED_DRAFT_SHA256:
        raise RuntimeError('Draft changed; independent mathematical review is required before rebinding this audit.')
    phase = phase_criterion_checks()
    union = union_support_checks()
    after = {name: sha256((HERE/name).read_bytes()).hexdigest() for name in sources}
    assert before == after
    result = dict(format='affine-sum-compression-design-review-v1',
                  reviewed_draft=DRAFT, reviewed_draft_sha256=REVIEWED_DRAFT_SHA256,
                  source_sha256=before, source_unchanged_during_run=True,
                  phase_criterion=phase, union_support=union,
                  scope='Bounded independent identity controls plus the accompanying mathematical review; no production merge or SAT speedup claim.')
    (HERE/'AFFINE_SUM_COMPRESSION_REVIEW.json').write_text(json.dumps(result, indent=2)+'\n', encoding='utf-8')
    print(json.dumps(dict(phase_sign_cases=phase['cases'], union_systems=union['cases'],
                         union_assignment_checks=union['assignment_checks'],
                         reviewed_draft_sha256=REVIEWED_DRAFT_SHA256), sort_keys=True))


if __name__ == '__main__':
    main()
