"""Original partition fixtures, independent of the recognition implementation."""
from copy import deepcopy
from fractions import Fraction
from itertools import combinations
from pathlib import Path
import importlib.util
import random
import sys

NIGHT=Path(__file__).resolve().parent.parent
spec=importlib.util.spec_from_file_location('partition_review_oracles',NIGHT/'affine_compression_review'/'review_oracles.py')
oracle=importlib.util.module_from_spec(spec);sys.modules[spec.name]=oracle;spec.loader.exec_module(oracle)


def named_controls():
    schedules=oracle.nonconfluence_schedules()
    lines=schedules['four_lines']['outputs'];singletons=schedules['four_lines']['inputs']
    cases=[dict(name='four_nonparallel_lines',n=3,retained=[0,1,2],messages=lines,expected_status='EXACT'),
           dict(name='eight_singletons',n=3,retained=[0,1,2],messages=singletons,expected_status='EXACT')]
    for n in (16,64,128):
        retained=list(range(n))
        phase=[1,3]+[(1<<i)|(1<<(i+1)) for i in range(2,n-1)]
        messages=[oracle.canonical(n,retained,m['equations'],phase,[3,7]) for m in lines]
        cases.append(dict(name=f'wide_signed_quadratic_lines_{n}',n=n,retained=retained,
              messages=messages,expected_status='EXACT',expected_message=oracle.canonical(n,retained,phase=phase,scalar=[3,7]),
              caps={'max_work':20000000}))
    n=32;ids=list(range(n));phase=[3,6,12,24]
    cases.append(dict(name='mixed_support_dimensions',n=n,retained=ids,
       messages=[oracle.canonical(n,ids,rows,phase,[-5,11]) for rows in ([[1,0]],[[1,1],[2,0]],[[1,1],[2,1]])],
       expected_status='EXACT',expected_message=oracle.canonical(n,ids,phase=phase,scalar=[-5,11])))
    ids=[8,2,5,0];n=10
    cases.append(dict(name='shifted_hull_sparse_permuted',n=n,retained=ids,
       messages=[oracle.canonical(n,ids,[[(1<<8)|(1<<2),1],[1<<5,b]],[(1<<2)|1],[5,13]) for b in (0,1)],
       expected_status='EXACT',expected_message=oracle.canonical(n,ids,[[(1<<8)|(1<<2),1]],[(1<<2)|1],[5,13])))
    unequal=deepcopy(lines);unequal[0]['scalar']=[2,1]
    cubic=[oracle.canonical(3,[0,1,2],m['equations'],scalar=-1 if v==7 else 1) for v,m in enumerate(singletons)]
    cases += [
      dict(name='overlap',n=3,retained=[0,1,2],messages=lines+[lines[0]],expected_status='UNSUPPORTED'),
      dict(name='gap',n=3,retained=[0,1,2],messages=lines[:-1],expected_status='UNSUPPORTED'),
      dict(name='unequal_magnitudes',n=3,retained=[0,1,2],messages=unequal,expected_status='UNSUPPORTED'),
      dict(name='incompatible_cubic_signs',n=3,retained=[0,1,2],messages=cubic,expected_status='UNSUPPORTED'),
      dict(name='empty_sum',n=4,retained=[3,1],messages=[],expected_status='EXACT'),
      dict(name='zero_only',n=4,retained=[3,1],messages=[oracle.canonical(4,[3,1],scalar=0)],expected_status='EXACT'),
      dict(name='explicit_zero_plus_partition',n=3,retained=[0,1,2],messages=[oracle.canonical(3,[0,1,2],scalar=0)]+lines,expected_status='EXACT'),
    ]
    for cap,value in [('max_work',0),('max_pieces',3),('max_pairs',5),('max_unknowns',6),('max_rows',1),('max_variables',2),('max_scalar_bits',0)]:
        cases.append(dict(name='budget_'+cap,n=3,retained=[0,1,2],messages=lines,
                          caps={cap:value},expected_status='UNKNOWN'))
    return cases


def affine_supports(n=3):
    result={}
    for mask in range(1,1<<(1<<n)):
        points=[v for v in range(1<<n) if mask>>v&1]
        translated={v^points[0] for v in points}
        if any(a^b not in translated for a in translated for b in translated):continue
        equations=[]
        for row in range(1,1<<n):
            values={(row&v).bit_count()%2 for v in points}
            if len(values)==1:equations.append([row,values.pop()])
        result[mask]=oracle.canonical(n,list(range(n)),equations)
    return result


def all_affine_partitions_three():
    supports=affine_supports()
    def visit(remaining,chosen):
        if not remaining:
            yield [supports[m] for m in chosen];return
        first=remaining&-remaining
        for mask in supports:
            if mask&first and mask&remaining==mask:
                yield from visit(remaining^mask,chosen+[mask])
    yield from visit(255,[])


def seeded_partitions(seed=1910261601,count=160):
    rng=random.Random(seed)
    for index in range(count):
        n=rng.randrange(1,8);ids=list(range(n));rng.shuffle(ids)
        leaves=[[]]
        # Axis splits have a simple independent disjoint-cover construction;
        # the exhaustive three-bit suite also includes nonparallel partitions.
        for _ in range(rng.randrange(8)):
            available=[i for i,rows in enumerate(leaves) if len(rows)<n]
            if not available:break
            i=rng.choice(available);rows=leaves.pop(i)
            used={mask.bit_length()-1 for mask,_ in rows}
            bit=1<<rng.choice([v for v in range(n) if v not in used])
            leaves.extend([rows+[[bit,0]],rows+[[bit,1]]])
        rng.shuffle(leaves)
        phase=[t for t in range(1<<n) if t.bit_count()<=2 and rng.randrange(3)==0]
        scale=Fraction(rng.choice([-3,-1,1,5]),rng.choice([1,3,7]))
        messages=[oracle.canonical(n,ids,rows,phase,scale) for rows in leaves]
        yield dict(index=index,n=n,retained=ids,messages=messages,
                   expected_message=oracle.canonical(n,ids,phase=phase,scalar=scale))


def mutations(result):
    answer=[]
    def change(name,fn):
        r=deepcopy(result);fn(r);answer.append((name,r))
    change('wrong_input_hash',lambda r:r['certificate'].__setitem__('input_sha256','0'*64))
    change('omitted_input_index',lambda r:r['certificate']['active_indices'].pop())
    change('boolean_active_id',lambda r:r['certificate']['active_indices'].__setitem__(0,False))
    change('missing_pair',lambda r:r['certificate']['intersections'].pop())
    change('wrong_pair',lambda r:r['certificate']['intersections'][0].__setitem__('pair',[0,0]))
    change('zero_contradiction',lambda r:r['certificate']['intersections'][0].__setitem__('contradiction',0))
    change('out_of_range_contradiction',lambda r:r['certificate']['intersections'][0].__setitem__('contradiction',1<<100))
    change('boolean_contradiction',lambda r:r['certificate']['intersections'][0].__setitem__('contradiction',True))
    change('wrong_dimension',lambda r:r['certificate'].__setitem__('hull_dimension',2))
    change('wrong_cardinality',lambda r:r['certificate'].__setitem__('coverage_cardinality',7))
    change('wrong_support_dimension',lambda r:r['certificate']['support_dimensions'].__setitem__(0,0))
    change('wrong_output_phase',lambda r:r['message'].__setitem__('phase',[1]))
    change('wrong_output_sign',lambda r:r['message'].__setitem__('scalar',[-1,1]))
    change('wrong_output_magnitude',lambda r:r['message'].__setitem__('scalar',[2,1]))
    change('wrong_output_free_ids',lambda r:r['message'].__setitem__('free_ids',[0,1]))
    return answer
