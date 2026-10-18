"""Bounded exact controls for the disjoint-OR affine cover/overlap theorem.

No optimization solver is provided. Affine support enumeration is deliberately
limited to six bits; explicit construction checks are limited to four clauses.
"""
from fractions import Fraction
from itertools import combinations, product
from pathlib import Path
import hashlib
import json
import time

HERE = Path(__file__).resolve().parent


def exact_int(value, name, maximum):
    if type(value) is not int or not 0 <= value <= maximum:
        raise ValueError(name + ' must be an exact nonnegative integer <= ' + str(maximum))
    return value


def counts(m):
    exact_int(m, 'm', 512)
    satisfying, largest = 7 ** m, 4 ** m
    return dict(m=m, variables=3*m, clauses=m, literals=3*m,
                satisfying=satisfying, largest_contained_affine=largest,
                positive_piece_lower=(satisfying+largest-1)//largest,
                partition_piece_upper=3**m, signed_inclusion_piece_upper=2**m,
                squared_normalized_overlap=[7**m, 8**m],
                normalized_l1_squared_lower=[8**m, 7**m],
                unnormalized_K_energy_lower=8**m)


def satisfies(word, m):
    return all((word >> (3*i)) & 7 for i in range(m))


def affine_supports(n):
    """Every nonempty affine subset once, as a bitset of its word indices."""
    exact_int(n, 'n', 6)
    for dimension in range(n+1):
        for pivots in combinations(range(n), dimension):
            free = [j for j in range(n) if j not in pivots]
            positions = [(i,j) for i,pivot in enumerate(pivots) for j in free if j > pivot]
            for choices in range(1 << len(positions)):
                rows = [1 << p for p in pivots]
                for bit,(i,j) in enumerate(positions):
                    if choices >> bit & 1:
                        rows[i] |= 1 << j
                span = [0]
                for row in rows:
                    span += [x ^ row for x in span]
                covered = 0
                for anchor in range(1 << n):
                    if covered >> anchor & 1:
                        continue
                    support = sum(1 << (anchor ^ x) for x in span)
                    covered |= support
                    yield support


def supports_control(m):
    exact_int(m, 'm', 2)
    n=3*m; target=sum(1 << x for x in range(1 << n) if satisfies(x,m))
    number=contained=maximum_size=0; best=Fraction(0); max_union_two=0
    inside=[]
    for support in affine_supports(n):
        number += 1; size=support.bit_count(); intersection=(support & target).bit_count()
        ratio=Fraction(intersection*intersection,size)
        assert ratio <= Fraction(49,8)**m
        best=max(best,ratio)
        if support & ~target == 0:
            contained += 1; maximum_size=max(maximum_size,size);inside.append(support)
            assert size <= 4**m
    if m==1:
        max_union_two=max((a|b).bit_count() for a in inside for b in inside)
        assert max_union_two==6
    assert maximum_size==4**m and best==Fraction(49,8)**m
    return dict(m=m, affine_supports=number, contained_supports=contained,
                maximum_contained_size=maximum_size,
                maximum_intersection_squared_over_size=[best.numerator,best.denominator],
                maximum_two_support_union=max_union_two if m==1 else None)


def positive_partition(m):
    exact_int(m, 'm', 4)
    # Each OR block is partitioned by its first coordinate equal to one.
    answer=[]
    for firsts in product(range(3),repeat=m):
        equations=[]
        for block,first in enumerate(firsts):
            equations += [[1 << (3*block+j),int(j==first)] for j in range(first+1)]
        answer.append(dict(coefficient=1,equations=equations,phase=[]))
    return answer


def signed_inclusion(m):
    exact_int(m, 'm', 4)
    answer=[]
    for subset in range(1 << m):
        equations=[]
        for block in range(m):
            if subset >> block & 1:
                equations += [[1 << (3*block+j),0] for j in range(3)]
        answer.append(dict(coefficient=(-1)**subset.bit_count(),equations=equations,phase=[]))
    return answer


def value(term, word):
    if any((mask & word).bit_count()%2 != rhs for mask,rhs in term['equations']):
        return 0
    sign=sum((mask & word)==mask for mask in term['phase'])%2
    return term['coefficient']*(-1 if sign else 1)


def constructions_control(m):
    positive=positive_partition(m);signed=signed_inclusion(m)
    positive_energy=signed_energy=0
    for word in range(1 << (3*m)):
        wanted=int(satisfies(word,m))
        pv=[value(t,word) for t in positive];sv=[value(t,word) for t in signed]
        assert sum(pv)==sum(sv)==wanted
        assert all(v>=0 for v in pv)
        assert sum(v != 0 for v in pv)==wanted
        positive_energy+=sum(v*v for v in pv);signed_energy+=sum(v*v for v in sv)
    assert positive_energy==7**m and signed_energy==9**m
    assert len(positive)*positive_energy>=8**m and len(signed)*signed_energy>=8**m
    return dict(m=m, original_clauses=[[3*i+1,3*i+2,3*i+3] for i in range(m)],
                original_assignments=1 << (3*m),positive_terms=positive,signed_terms=signed,
                positive_energy=positive_energy,signed_energy=signed_energy)


def signed_controls():
    # Enumerate all ambient degree<=2 phases on every three-bit affine support.
    monomials=[0,1,2,4,3,5,6];checked=0;best=Fraction(0)
    for support in affine_supports(3):
        for coefficients in range(1 << len(monomials)):
            phase=[mask for i,mask in enumerate(monomials) if coefficients >> i & 1]
            correlation=sum((-1)**(sum((mask & word)==mask for mask in phase)%2)
                            for word in range(1,8) if support >> word & 1)
            squared=Fraction(correlation*correlation,7*support.bit_count())
            assert squared<=Fraction(7,8);best=max(best,squared);checked+=1
    assert best==Fraction(7,8)
    # Positive coefficients alone do not make signed atoms nonnegative.
    signed_positive_coefficients=[dict(coefficient=Fraction(1,2),equations=[],phase=[]),
                                  dict(coefficient=Fraction(1,2),equations=[],phase=[1])]
    assert [sum(value(t,x) for t in signed_positive_coefficients) for x in range(2)]==[1,0]
    # Signed local minimum is two: 1-full minus pin000. It is not one atom,
    # because its nonzero support has size seven, not a power of two.
    assert [sum(value(t,x) for t in signed_inclusion(1)) for x in range(8)]==[0]+[1]*7
    return dict(affine_support_phase_pairs=checked,max_squared_normalized_overlap=[7,8],
                local_OR_positive_minimum=3,local_OR_signed_minimum=2,
                positive_coefficients_signed_atoms_counterexample=dict(
                    coefficients=[[1,2],[1,2]],phases=[[],[1]],values=[1,0],
                    individual_support_sizes=[2,2]),
                signed_local_support_leak=dict(full_cube_support_size=8,
                    target_support_size=7,at_zero_contributions=[1,-1]))


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    started=time.perf_counter()
    names=['controls.py','test_controls.py','THEOREM.md']
    before={name:digest(HERE/name) for name in names}
    result=dict(source_sha256=before,source_unchanged_during_run=True,
                symbolic_counts=[counts(m) for m in [0,1,2,3,4,8,16,32,64,128,512]],
                exhaustive_affine_supports=[supports_control(m) for m in range(3)],
                explicit_constructions=[constructions_control(m) for m in range(5)],
                signed_controls=signed_controls(),
                first_block_fiber_multipliers=[[0,1],[1,2],[1,1],[2,1],[9,4],[4,1],[49,8]],
                scope='All-size positive support-cover and coefficient-energy lower bounds; no unrestricted signed rank or SAT lower bound.')
    assert before=={name:digest(HERE/name) for name in names}
    result['seconds']=time.perf_counter()-started
    (HERE/'RESULTS.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(dict(source_unchanged=True,affine_supports=sum(x['affine_supports'] for x in result['exhaustive_affine_supports']),
                         original_assignments=sum(x['original_assignments'] for x in result['explicit_constructions']),
                         signed_pairs=result['signed_controls']['affine_support_phase_pairs'],seconds=result['seconds'])))


if __name__=='__main__':main()
