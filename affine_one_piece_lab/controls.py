"""Original explicit sums and independent bounded truth-table classification."""
from copy import deepcopy
from fractions import Fraction
from itertools import product
from pathlib import Path
import importlib.util
import random
import sys

NIGHT=Path(__file__).resolve().parent.parent
spec=importlib.util.spec_from_file_location('_one_piece_review_oracles',NIGHT/'affine_compression_review'/'review_oracles.py')
oracle=importlib.util.module_from_spec(spec);sys.modules[spec.name]=oracle;spec.loader.exec_module(oracle)


def pins(n,values):
    ids=list(range(n))
    return [oracle.canonical(n,ids,[[1<<i,(word>>i)&1] for i in ids],scalar=value)
            for word,value in enumerate(values)]


def classify_values(values):
    support=[i for i,v in enumerate(values) if v]
    if not support:return True
    anchor=support[0];c=values[anchor]
    if any(abs(values[x])!=abs(c) for x in support):return False
    translated={x^anchor for x in support}
    if any(x^y not in translated for x in translated for y in translated):return False
    span={0};basis=[]
    for x in sorted(translated):
        if x not in span:
            basis.append(x);span|={s^x for s in tuple(span)}
    truth=[]
    for word in range(1<<len(basis)):
        point=anchor
        for i,b in enumerate(basis):
            if word>>i&1:point^=b
        truth.append(int(values[point]!=c))
    # Complete Boolean Mobius transform, intentionally exponential and small.
    for i in range(len(basis)):
        for word in range(len(truth)):
            if word>>i&1:truth[word]^=truth[word^(1<<i)]
    return all(not coefficient or monomial.bit_count()<=2 for monomial,coefficient in enumerate(truth))


def direct_values(n,retained,messages):
    values=[]
    for word in range(1<<len(retained)):
        original=sum(((word>>i)&1)<<v for i,v in enumerate(retained))
        values.append(sum((oracle.point(m,original) for m in messages),Fraction(0)))
    return values


def named_controls():
    c=lambda n,eq=(),q=(),s=1:oracle.canonical(n,list(range(n)),eq,q,s)
    lines=oracle.nonconfluence_schedules()['four_lines']['outputs']
    cases=[
      dict(name='empty_sum',n=0,retained=[],messages=[],expected='EXACT'),
      dict(name='overlap_zero_cancellation',n=3,retained=list(range(3)),messages=[c(3,q=[3],s=[3,7]),c(3,q=[3],s=[-3,7])],expected='EXACT',zero=True),
      dict(name='one_minus_pin_fallback',n=2,retained=[0,1],messages=[c(2),c(2,[[1,0]],s=-1)],expected='EXACT',fallback=True),
      dict(name='unequal_overlap_coefficients',n=2,retained=[0,1],messages=[c(2,s=2),c(2,s=-1)],expected='EXACT'),
      dict(name='zero_canonical_anchor',n=2,retained=[0,1],messages=pins(2,[0,1,1,1]),expected='UNSUPPORTED',kind='anchor_zero'),
      dict(name='shifted_zero_anchor_with_outside',n=3,retained=[0,1,2],messages=pins(3,[0,1,1,1,0,0,0,0]),expected='UNSUPPORTED',kind='anchor_zero'),
      dict(name='nonuniform_magnitude',n=1,retained=[0],messages=[c(1),c(1,[[1,1]])],expected='UNSUPPORTED',kind='magnitude'),
      dict(name='cubic_final_norm_four',n=3,retained=[0,1,2],messages=pins(3,[1]*7+[-1]),expected='UNSUPPORTED',kind='phase',difference=[4,1]),
      dict(name='failed_fast_norm_gap',n=3,retained=[0,1,2],messages=[c(3),c(3,[[1,1],[2,1],[4,1]],s=-1)],expected='UNSUPPORTED',kind='phase',difference=[1,1]),
      dict(name='four_nonparallel_lines',n=3,retained=[0,1,2],messages=lines,expected='EXACT'),
      dict(name='four_lines_plus_extra_point',n=3,retained=[0,1,2],messages=lines+[c(3,[[1,0],[2,0],[4,0]])],expected='UNSUPPORTED',kind='magnitude'),
      dict(name='actual_hull_smaller_than_union',n=3,retained=[0,1,2],messages=[c(3,[[1,1],[2,0],[4,1]],s=[5,7]),c(3,q=[3]),c(3,q=[3],s=-1)],expected='EXACT',fallback=True),
    ]
    for n in (32,128):
        q=[1,3]+[(1<<i)|(1<<(i+1)) for i in range(2,n-1)]
        messages=[c(n,m['equations'],q,[3,7]) for m in lines]
        cases.append(dict(name=f'wide_signed_partition_{n}',n=n,retained=list(range(n)),messages=messages,expected='EXACT'))
        cases.append(dict(name=f'wide_overlap_cancellation_{n}',n=n,retained=list(range(n)),
           messages=[c(n,q=q,s=[-2,5]),c(n,[[1,0]],q,[7,3]),c(n,[[1,0]],q,[-7,3])],expected='EXACT'))
    ids=[8,2,5,0];n=10
    messages=[oracle.canonical(n,ids,[[(1<<8)|(1<<2),1],[1<<5,b]],[(1<<2)|1],[5,13]) for b in (0,1)]
    cases.append(dict(name='sparse_permuted_original_universe',n=n,retained=ids,messages=messages,expected='EXACT'))
    for cap,value in [('max_work',0),('max_norm_queries',0),('max_pair_contractions',0),('max_point_evaluations',0),('max_certificate_products',0),('max_variables',2),('max_pieces',3),('max_scalar_bits',0)]:
        cases.append(dict(name='budget_'+cap,n=3,retained=[0,1,2],messages=lines,expected='UNKNOWN',caps={cap:value}))
    return cases


def small_complete_requests():
    for n in range(3):
        for values in product((-1,0,1),repeat=1<<n):
            yield dict(n=n,retained=list(range(n)),messages=pins(n,values),values=list(values),
                       expected='EXACT' if classify_values(values) else 'UNSUPPORTED')


def signed_three_requests():
    for truth in range(256):
        values=[-1 if truth>>i&1 else 1 for i in range(8)]
        yield dict(n=3,retained=[0,1,2],messages=pins(3,values),truth=truth,
                   expected='EXACT' if truth.bit_count()%2==0 else 'UNSUPPORTED')


def seeded_requests(seed=1910261701,count=120):
    rng=random.Random(seed)
    for index in range(count):
        n=rng.randrange(5);ids=list(range(n));rng.shuffle(ids);messages=[]
        for _ in range(rng.randrange(7)):
            if messages and rng.randrange(4)==0:
                m=deepcopy(rng.choice(messages));m['scalar'][0]*=-1
                if m['zero']:m['scalar']=[0,1]
            else:
                eq=[[rng.randrange(1<<n),rng.randrange(2)] for _ in range(rng.randrange(3))]
                q=[t for t in range(1<<n) if t.bit_count()<=2 and rng.randrange(4)==0]
                m=oracle.canonical(n,ids,eq,q,Fraction(rng.randrange(-3,4),rng.choice([1,3,5])))
            messages.append(m)
        values=direct_values(n,ids,messages)
        yield dict(index=index,n=n,retained=ids,messages=messages,
                    expected='EXACT' if classify_values(values) else 'UNSUPPORTED')


def mutations(result):
    answer=[]
    def change(name,fn):
        r=deepcopy(result);fn(r);answer.append((name,r))
    change('wrong_external_binding',lambda r:r['certificate'].__setitem__('input_sha256','0'*64))
    change('wrong_root_norm',lambda r:r['certificate']['root_norm'].__setitem__('value',[-1,1]))
    if result['certificate']['root_norm']['products']:
        change('omitted_norm_pair',lambda r:r['certificate']['root_norm']['products'].pop())
        change('wrong_norm_pair',lambda r:r['certificate']['root_norm']['products'][0].__setitem__('pair',[0,999]))
        change('boolean_pair_index',lambda r:r['certificate']['root_norm']['products'][0]['pair'].__setitem__(0,False))
        change('wrong_block_scalar',lambda r:r['certificate']['root_norm']['products'][0]['result']['message'].__setitem__('scalar',[123,1]))
    cert=result['certificate']
    if cert['kind']=='equality':
        change('wrong_candidate_sign',lambda r:r['certificate']['candidate']['scalar'].__setitem__(0,-r['certificate']['candidate']['scalar'][0]))
        change('false_final_norm',lambda r:r['certificate']['difference_norm'].__setitem__('value',[1,1]))
    if 'points' in cert:
        change('zero_support_point',lambda r:r['certificate']['points'].__setitem__(0,0))
        change('duplicate_support_point',lambda r:r['certificate']['points'].append(r['certificate']['points'][0]))
        change('wrong_sample_value',lambda r:r['certificate']['samples'][0].__setitem__('value',[99,1]))
        change('wrong_sample_word',lambda r:r['certificate']['samples'][0].__setitem__('word',999))
        if cert['outside_norms']:
            change('missing_outside_half',lambda r:r['certificate']['outside_norms'].pop())
            change('wrong_outside_restriction',lambda r:r['certificate']['outside_norms'][0].__setitem__('restriction',[]))
        if cert['kind']=='phase':
            change('incomplete_quadratic_samples',lambda r:r['certificate']['samples'].pop())
            change('false_positive_difference',lambda r:r['certificate']['difference_norm'].__setitem__('value',[0,1]))
    return answer
