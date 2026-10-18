"""Independent input truth checks and affine-fiber controls, no solver claims."""
from fractions import Fraction
from hashlib import sha256
from pathlib import Path
import json
import random

HERE = Path(__file__).resolve().parent


def h(path):
    return sha256(path.read_bytes()).hexdigest()


def sat(clauses, word):
    return all(any(bool(word & (1 << (abs(lit)-1))) == (lit > 0)
                   for lit in clause) for clause in clauses)


def term_value(term, word):
    for row, rhs in term['equations']:
        parity = 0
        for bit in range(row.bit_length()):
            if (row >> bit) & 1:
                parity ^= (word >> bit) & 1
        if parity != rhs:
            return 0
    sign = 1
    for monomial in term['phase']:
        active = all((word >> bit) & 1 for bit in range(monomial.bit_length())
                     if (monomial >> bit) & 1)
        if active:
            sign = -sign
    return term['coefficient']*sign


def main():
    data = json.loads((HERE/'RESULTS.json').read_text())
    names = ['RESULTS.json','THEOREM.md','controls.py','test_controls.py','INDEPENDENT_REVIEW.py']
    before = {name:h(HERE/name) for name in names}
    for name, expected in data['source_sha256'].items():
        assert h(HERE/name) == expected
    truth_words = 0
    for case in data['explicit_constructions']:
        m = case['m']
        assert case['original_clauses'] == [[3*j+1,3*j+2,3*j+3] for j in range(m)]
        assert len(case['positive_terms']) == 3**m
        assert len(case['signed_terms']) == 2**m
        totals = dict(positive_terms=0,signed_terms=0)
        sat_count = 0
        for word in range(1 << (3*m)):
            wanted = sat(case['original_clauses'],word)
            sat_count += wanted
            for kind in totals:
                values = [term_value(term,word) for term in case[kind]]
                assert sum(values) == wanted
                totals[kind] += sum(v*v for v in values)
                if kind == 'positive_terms':
                    assert all(v >= 0 for v in values)
                    assert sum(bool(v) for v in values) == wanted
            truth_words += 1
        assert sat_count == 7**m
        assert totals['positive_terms'] == case['positive_energy'] == 7**m
        assert totals['signed_terms'] == case['signed_energy'] == 9**m
    # Enumerate affine subsets by closure, without the producer's RREF enumeration.
    local = []
    for mask in range(1,256):
        points = {x for x in range(8) if (mask >> x) & 1}
        anchor = min(points)
        differences = {x ^ anchor for x in points}
        if all(a ^ b in differences for a in differences for b in differences):
            local.append(points)
    multipliers = sorted({Fraction(len(p-{0})**2,len(p)) for p in local})
    assert [[x.numerator,x.denominator] for x in multipliers] == data['first_block_fiber_multipliers']
    assert len(local) == data['exhaustive_affine_supports'][1]['affine_supports'] == 51
    assert max(multipliers) == Fraction(49,8)
    contained = [p for p in local if 0 not in p]
    assert max(len(a | b) for a in contained for b in contained) == 6
    # Independent held-out random affine images with cross-block dependencies.
    rng = random.Random(10182026)
    random_cases = random_points = 0
    for m in range(1,13):
        n = 3*m
        for _ in range(50):
            points = {rng.getrandbits(n)}
            for _ in range(rng.randrange(min(n,8)+1)):
                direction = rng.getrandbits(n)
                points |= {x ^ direction for x in points}
            hits = sum(all((x >> (3*j)) & 7 for j in range(m)) for x in points)
            assert hits*hits*8**m <= len(points)*49**m
            if hits == len(points):
                assert len(points) <= 4**m
            random_cases += 1
            random_points += len(points)
    for case in data['symbolic_counts']:
        m = case['m']
        assert case['positive_piece_lower'] == -(-(7**m)//(4**m))
        assert case['largest_contained_affine'] == 4**m
        assert case['squared_normalized_overlap'] == [7**m,8**m]
        assert case['unnormalized_K_energy_lower'] == 8**m
    after = {name:h(HERE/name) for name in names}
    assert before == after
    result = dict(status='VERIFIED_INDEPENDENT_CONTROLS', source_hashes_before=before,
                  source_hashes_after=after, source_unchanged_during_review=True,
                  original_truth_words=truth_words, independently_enumerated_local_affine_sets=len(local),
                  random_affine_cases=random_cases, random_affine_points=random_points,
                  fiber_multipliers=[[x.numerator,x.denominator] for x in multipliers],
                  mathematical_review='Support-containment, projection dimension, equal-size fibers, triangle inequality, coefficient-energy and Gram consequences reviewed. Finite controls supplement the all-size proofs.',
                  scope='No unrestricted signed piece lower bound; the original disjoint-clause SAT and count are easy.')
    (HERE/'INDEPENDENT_REVIEW.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({key:result[key] for key in ['status','original_truth_words','random_affine_cases','random_affine_points']}))


if __name__ == '__main__':
    main()
