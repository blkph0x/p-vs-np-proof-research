"""Explicitly bounded truth-table review, not a production recognizer.

All review dimensions are <=5. Pair norms and query-guided support hulls are
checked against separate direct support/Boolean-Mobius calculations.
"""
from collections import Counter
from fractions import Fraction
from hashlib import sha256
from itertools import product
import json
from pathlib import Path
import random

HERE = Path(__file__).resolve().parent
DESIGN_HASH = '157107c1edb28d7f5f312b1b1580cfcacde9f654c6df59b5b970b26ec8b36b3a'
SOURCES = ['AFFINE_ONE_PIECE_RECOGNITION_DESIGN.md', 'AFFINE_ONE_PIECE_RECOGNITION_REVIEW.py',
           'AFFINE_ONE_PIECE_RECOGNITION_REVIEW.md']


def require(condition, why):
    if not condition: raise RuntimeError(why)


def hashes():
    return {name:sha256((HERE/name).read_bytes()).hexdigest() for name in SOURCES}


def atom(n, rows=(), phase=(), coefficient=1):
    c = Fraction(coefficient)
    return dict(rows=[list(r) for r in rows], phase=list(phase), scalar=[c.numerator,c.denominator])


def pin(n, word, coefficient=1):
    return atom(n, [(1<<i,word>>i&1) for i in range(n)], coefficient=coefficient)


def values_of(n, piece):
    return [Fraction(0) if any((x&mask).bit_count()%2 != rhs for mask,rhs in piece['rows'])
            else Fraction(*piece['scalar'])*(-1)**(sum(x&term == term for term in piece['phase'])%2)
            for x in range(1<<n)]


def affine_closure(points):
    anchor = points[0]; directions = {0}
    for x in points:
        delta = x ^ anchor
        directions |= {v ^ delta for v in list(directions)}
    return {anchor ^ d for d in directions}


def independent_rows(vectors):
    pivots = {}; selected = []
    for original in vectors:
        x = original
        while x:
            bit = x.bit_length()-1
            if bit in pivots: x ^= pivots[bit]
            else:
                pivots[bit] = x; selected.append(original); break
    return selected


def hull_equations(n, points):
    anchor = points[0]
    normals = [a for a in range(1,1<<n) if all((a&(x^anchor)).bit_count()%2 == 0 for x in points)]
    return [[a,(a&anchor).bit_count()%2] for a in independent_rows(normals)]


def parametrization(hull):
    anchor = min(hull); image = [0]
    for x in sorted(hull):
        delta = x ^ anchor
        if delta not in image: image += [y ^ delta for y in image]
    return [anchor ^ x for x in image]


def direct_classification(values):
    support = [i for i,value in enumerate(values) if value]
    if not support: return 'ZERO'
    hull = affine_closure(support)
    if len(hull) != len(support): return 'NOT_ONE_PIECE'
    coordinates = parametrization(hull); c = values[coordinates[0]]
    if any(abs(values[x]) != abs(c) for x in coordinates): return 'NOT_ONE_PIECE'
    # Independently recover every coefficient of the full sign truth table.
    coefficients = [int(values[x] != c) for x in coordinates]
    d = len(coordinates).bit_length()-1
    for i in range(d):
        for mask in range(1<<d):
            if mask>>i&1: coefficients[mask] ^= coefficients[mask^(1<<i)]
    return 'ONE_PIECE' if all(not bit or mask.bit_count() <= 2 for mask,bit in enumerate(coefficients)) else 'NOT_ONE_PIECE'


def bounded_norm_hull_review(n, pieces):
    require(type(n) is int and 0 <= n <= 5 and len(pieces) <= 10,'finite review cap')
    tables = [values_of(n,p) for p in pieces]
    values = [sum((t[x] for t in tables),Fraction(0)) for x in range(1<<n)]
    queries = []; pair_contractions = 0
    def norm(rows, extra_table=None):
        nonlocal pair_contractions
        selected = [x for x in range(1<<n) if all((mask&x).bit_count()%2==rhs for mask,rhs in rows)]
        terms = tables+([extra_table] if extra_table is not None else [])
        expanded = Fraction(0)
        for i in range(len(terms)):
            for j in range(i,len(terms)):
                expanded += (1 if i==j else 2)*sum((terms[i][x]*terms[j][x] for x in selected),Fraction(0))
                pair_contractions += 1
        direct = sum((sum((table[x] for table in terms),Fraction(0))**2 for x in selected),Fraction(0))
        require(expanded == direct and expanded >= 0,'incorrect exact restricted pair norm')
        queries.append(dict(rows=rows,value=[expanded.numerator,expanded.denominator]))
        return expanded
    def nonzero_point(restriction):
        rows = [r[:] for r in restriction]; word = 0
        for i in range(n):
            bit = 0 if norm(rows+[[1<<i,0]]) else 1
            rows.append([1<<i,bit]); word |= bit<<i
        require(values[word] != 0 and all((mask&word).bit_count()%2==rhs for mask,rhs in restriction),'prefix norm search found no support')
        return word
    if norm([])==0:
        require(not any(values),'zero norm without zero function')
        return dict(status='ZERO',values=[[v.numerator,v.denominator] for v in values],queries=len(queries),pair_contractions=pair_contractions,hull=[])
    points = [nonzero_point([])]; growths = 0
    while True:
        rows = hull_equations(n,points)
        outside = next(([[mask,rhs^1]] for mask,rhs in rows if norm([[mask,rhs^1]]) > 0),None)
        if outside is None: break
        new = nonzero_point(outside)
        require(new not in affine_closure(points),'hull dimension did not grow')
        points.append(new); growths += 1
        require(growths <= n,'more than n strict dimension increases')
    hull = affine_closure(points)
    direct_hull = affine_closure([x for x,value in enumerate(values) if value])
    require(hull == direct_hull,'query hull differs from direct nonzero-support hull')
    coordinates = parametrization(hull); d = len(coordinates).bit_length()-1
    c = values[coordinates[0]]; final_norm = None
    if c == 0:
        status,reason='NOT_ONE_PIECE','zero canonical anchor'
    else:
        samples=[1<<i for i in range(d)]+[(1<<i)|(1<<j) for i in range(d) for j in range(i+1,d)]
        if any(abs(values[coordinates[u]]) != abs(c) for u in samples):
            status,reason='NOT_ONE_PIECE','sample magnitude mismatch'
        else:
            linear=[int(values[coordinates[1<<i]] != c) for i in range(d)]
            quadratic=[((1<<i)|(1<<j),int(values[coordinates[(1<<i)|(1<<j)]] != c)^linear[i]^linear[j]) for i in range(d) for j in range(i+1,d)]
            candidate=[Fraction(0)]*(1<<n)
            for u,x in enumerate(coordinates):
                parity=sum(linear[i]*(u>>i&1) for i in range(d))+sum(bit for mask,bit in quadratic if u&mask==mask)
                candidate[x]=c*(-1)**(parity%2)
            final_norm=norm([],[-v for v in candidate])
            status='ONE_PIECE' if final_norm==0 else 'NOT_ONE_PIECE'
            reason='final equality norm zero' if final_norm==0 else 'positive final difference norm'
    require(status==direct_classification(values),'sample/norm classification differs from full support/Mobius oracle')
    return dict(status=status,reason=reason,values=[[v.numerator,v.denominator] for v in values],
                hull=sorted(hull),witnessed_support_points=points,rank_increases=growths,
                canonical_anchor=coordinates[0],canonical_anchor_value=[c.numerator,c.denominator],
                final_difference_norm=None if final_norm is None else [final_norm.numerator,final_norm.denominator],
                queries=len(queries),pair_contractions=pair_contractions)


def main():
    before=hashes();require(before[SOURCES[0]]==DESIGN_HASH,'design changed after mathematical review')
    records=[];counts=Counter();queries=pairs=words=0
    def add(name,n,pieces,expected=None):
        nonlocal queries,pairs,words
        result=bounded_norm_hull_review(n,pieces)
        if expected is not None: require(result['status']==expected,'named control classification changed')
        counts[result['status']]+=1;queries+=result['queries'];pairs+=result['pair_contractions'];words+=1<<n
        records.append(dict(name=name,n=n,original_pieces=pieces,review=result))
    add('gapped_support_zero_canonical_anchor',2,[pin(2,x) for x in (1,2,3)],'NOT_ONE_PIECE')
    add('full_support_cubic_sign',3,[pin(3,x,-1 if x==7 else 1) for x in range(8)],'NOT_ONE_PIECE')
    require(records[-1]['review']['final_difference_norm']==[4,1],'cubic countercontrol norm must be four')
    add('overlap_cancellation_to_halfspace',3,[atom(3),atom(3,[(1,0)],coefficient=-1)],'ONE_PIECE')
    add('zero_cancellation',4,[atom(4,phase=[3],coefficient=Fraction(2,7)),atom(4,phase=[3],coefficient=Fraction(-2,7))],'ZERO')
    for i,table in enumerate(product((-1,0,1),repeat=4)):
        add('all_ternary_two_bit_'+str(i),2,[pin(2,x,value) for x,value in enumerate(table) if value])
    for pattern in range(256):
        add('all_three_bit_signs_'+str(pattern),3,[pin(3,x,-1 if pattern>>x&1 else 1) for x in range(8)])
    rng=random.Random(2026101919)
    for i in range(200):
        n=rng.randrange(6);monomials=[0]+[1<<j for j in range(n)]+[(1<<j)|(1<<k) for j in range(n) for k in range(j+1,n)]
        pieces=[atom(n,[(rng.randrange(1<<n),rng.randrange(2)) for _ in range(rng.randrange(4))],
                     rng.sample(monomials,rng.randrange(len(monomials)+1)),Fraction(rng.randrange(-3,4),rng.randrange(1,5)))
                for _ in range(rng.randrange(8))]
        add('seeded_'+str(i),n,pieces)
    require(hashes()==before,'review sources changed')
    out=dict(verdict='SOUND in the exact rational explicit-sum model; finite controls agree',source_sha256=before,
             source_unchanged_during_run=True,seed=2026101919,requests=len(records),statuses=dict(counts),
             original_truth_words=words,restricted_and_final_norm_queries=queries,explicit_pair_contractions=pairs,
             named_controls=records[:4],cases=records[4:],
             scope='This bounded review enumerates at most32 assignments and supplies no production recognizer. The all-size polynomial theorem is reviewed mathematically in the adjacent document, not inferred from these finite tests.')
    (HERE/'AFFINE_ONE_PIECE_RECOGNITION_REVIEW.json').write_text(json.dumps(out,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({k:out[k] for k in ('requests','statuses','original_truth_words','restricted_and_final_norm_queries','explicit_pair_contractions','source_unchanged_during_run')}))


if __name__=='__main__': main()
