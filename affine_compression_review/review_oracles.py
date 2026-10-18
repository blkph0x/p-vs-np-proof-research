"""Independent, bounded review oracles; no compressor discovery is imported.

The point oracle evaluates original equations/monomials directly.  The wide
oracle expands a squared norm into closed affine quadratic sums and calls the
separately implemented block-support reference (not the one-bit producer).
"""
from fractions import Fraction
from pathlib import Path
import importlib.util

NIGHT = Path(__file__).resolve().parent.parent
spec = importlib.util.spec_from_file_location('compression_review_block_reference',
                                             NIGHT/'affine_boundary_reference'/'reference.py')
reference = importlib.util.module_from_spec(spec)
spec.loader.exec_module(reference)


def canonical(n, retained, equations=(), phase=(), scalar=1):
    result = reference.marginalize_reference(n, retained, list(equations),
                  list(phase), scalar, active=retained, max_work=20000000)
    assert result['status'] == 'EXACT', result
    return result['message']


def point(message, word):
    """Direct original-coordinate evaluation, with no row normalization."""
    if message['zero']:
        return Fraction(0)
    if any(((mask & word).bit_count() & 1) != rhs
           for mask, rhs in message['equations']):
        return Fraction(0)
    phase = sum((word & monomial) == monomial
                for monomial in message['phase']) & 1
    return Fraction(*message['scalar']) * (-1 if phase else 1)


def exhaustive_equal(n, retained, left, right):
    checks = 0
    for assignment in range(1 << len(retained)):
        word = sum(((assignment >> i) & 1) << v
                   for i, v in enumerate(retained))
        lhs = sum((point(m, word) for m in left), Fraction(0))
        rhs = sum((point(m, word) for m in right), Fraction(0))
        checks += 1
        if lhs != rhs:
            return {'equal': False, 'checks': checks, 'word': word,
                    'left': [lhs.numerator, lhs.denominator],
                    'right': [rhs.numerator, rhs.denominator]}
    return {'equal': True, 'checks': checks, 'word': None}


def norm_identity(n, retained, left, right, *, save_proofs=False):
    """Prove equality iff exact sum_y (sum(left)-sum(right))**2 = 0.

    Assumes valid compact input descriptors. Every closed marginal result is
    independently certificate-checked by the block reference.  No truth-table
    is used, and no producer compression function is called.
    """
    for message in left+right:
        check=reference.equivalent_messages(n,retained,message,message,max_work=20000000)
        assert check['status']=='EXACT' and check['equivalent'], check
    terms = [(m, 1) for m in left if not m['zero']]
    terms += [(m, -1) for m in right if not m['zero']]
    total = Fraction(0)
    records = []
    arithmetic_work=0
    scalar_bits=0
    for i, (a, sa) in enumerate(terms):
        for j in range(i, len(terms)):
            b, sb = terms[j]
            coefficient = Fraction(*a['scalar']) * Fraction(*b['scalar']) * sa * sb
            if i != j:
                coefficient *= 2
            request = dict(n=n, retained=[], active=list(retained),
                           equations=a['equations']+b['equations'],
                           phase=a['phase']+b['phase'],
                           scalar=[coefficient.numerator, coefficient.denominator])
            result = reference.marginalize_reference(**request, max_work=20000000)
            assert result['status'] == 'EXACT', result
            checked = reference.verify_reference(**request, result=result,
                                                 max_work=20000000)
            assert checked['valid'], checked
            value = point(result['message'],0)
            total += value
            arithmetic_work+=result['stats']['work']+checked['stats']['work']
            scalar_bits=max(scalar_bits,abs(coefficient.numerator).bit_length(),
                            coefficient.denominator.bit_length(),
                            abs(value.numerator).bit_length(),value.denominator.bit_length(),
                            abs(total.numerator).bit_length(),total.denominator.bit_length())
            record = dict(pair=[i,j], request=request,
                          value=[value.numerator,value.denominator])
            if save_proofs:
                record['result'] = result
            records.append(record)
    assert total >= 0, 'a squared norm cannot be negative'
    return dict(equal=(total == 0), squared_norm=[total.numerator,total.denominator],
                block_checks=len(records), products=records,
                stats=dict(block_producer_and_checker_work=arithmetic_work,
                           observed_scalar_bits=scalar_bits))


def verify_norm_identity(n, retained, left, right, proof, *, max_products=4096,
                         max_work=20000000, max_scalar_bits=65536):
    """Check an external-input-bound squared-norm certificate, not discovery.

    A valid positive norm proves inequality; only valid zero proves equality.
    Caps bound pair count, aggregated reference-checker work and rational bits.
    The block checker is separately capped at the same work limit per call.
    """
    work=0
    try:
        if type(n) is not int or n<0 or type(retained) not in (list,tuple) or any(type(v) is not int or not 0<=v<n for v in retained) or len(set(retained))!=len(retained):
            raise ValueError('invalid external coordinate header')
        if n>4096:
            return dict(valid=False,status='UNKNOWN',equal=None,work=work)
        if any(type(v) is not int or v<0 for v in (max_products,max_work,max_scalar_bits)):
            raise ValueError('invalid resource cap')
        if type(left) is not list or type(right) is not list:
            raise ValueError('explicit input lists required')
        for message in left+right:
            check=reference.equivalent_messages(n,retained,message,message,
                         max_work=max_work,max_scalar_bits=max_scalar_bits)
            work+=check['stats']['work']
            if check['status']=='UNKNOWN' or work>max_work:
                return dict(valid=False,status='UNKNOWN',equal=None,work=work)
            if check['status']!='EXACT' or not check['equivalent']:
                raise ValueError('invalid external message')
        terms=[(m,1) for m in left if not m['zero']]
        terms += [(m,-1) for m in right if not m['zero']]
        count=len(terms)*(len(terms)+1)//2
        if count>max_products:
            return dict(valid=False,status='UNKNOWN',equal=None,work=work)
        if type(proof) is not dict or type(proof.get('equal')) is not bool or type(proof.get('block_checks')) is not int or proof['block_checks']!=count or type(proof.get('products')) is not list or len(proof['products'])!=count:
            raise ValueError('malformed product coverage')
        total=Fraction(0)
        position=0
        for i,(a,sa) in enumerate(terms):
            for j in range(i,len(terms)):
                b,sb=terms[j]
                coefficient=Fraction(*a['scalar'])*Fraction(*b['scalar'])*sa*sb*(1 if i==j else 2)
                request=dict(n=n,retained=[],active=list(retained),
                  equations=a['equations']+b['equations'],phase=a['phase']+b['phase'],
                  scalar=[coefficient.numerator,coefficient.denominator])
                record=proof['products'][position];position+=1
                if type(record) is not dict or record.get('pair')!=[i,j] or any(type(x) is not int for x in record['pair']) or record.get('request')!=request:
                    raise ValueError('external product binding mismatch')
                checked=reference.verify_reference(**request,result=record.get('result'),
                             max_work=max_work,max_scalar_bits=max_scalar_bits)
                work+=checked['stats']['work']
                if checked['status']=='UNKNOWN' or work>max_work:
                    return dict(valid=False,status='UNKNOWN',equal=None,work=work)
                if not checked['valid']:
                    raise ValueError('invalid block product proof')
                value=point(record['result']['message'],0)
                if type(record.get('value')) is not list or any(type(x) is not int for x in record['value']) or record['value']!=[value.numerator,value.denominator]:
                    raise ValueError('wrong closed-product value')
                total+=value
                if max(abs(total.numerator).bit_length(),total.denominator.bit_length(),abs(coefficient.numerator).bit_length(),coefficient.denominator.bit_length())>max_scalar_bits:
                    return dict(valid=False,status='UNKNOWN',equal=None,work=work)
        if total<0 or type(proof.get('squared_norm')) is not list or any(type(x) is not int for x in proof['squared_norm']) or proof['squared_norm']!=[total.numerator,total.denominator] or proof['equal']!=(total==0):
            raise ValueError('wrong exact squared norm')
        return dict(valid=True,status='VERIFIED',equal=(total==0),
                    squared_norm=[total.numerator,total.denominator],work=work)
    except (ValueError,TypeError,KeyError,IndexError,OverflowError) as error:
        return dict(valid=False,status='INVALID',equal=None,reason=str(error),work=work)


def direct_norm(n,retained,left,right):
    total=Fraction(0)
    for assignment in range(1<<len(retained)):
        word=sum(((assignment>>i)&1)<<v for i,v in enumerate(retained))
        difference=sum((point(m,word) for m in left),Fraction(0))-sum((point(m,word) for m in right),Fraction(0))
        total+=difference*difference
    return dict(squared_norm=[total.numerator,total.denominator],assignments=1<<len(retained))


def controls(width=3):
    assert width >= 3
    ids = list(range(width))
    def m(eq=(), q=(), c=1):
        return canonical(width, ids, eq, q, c)
    # Each entry supplies its own intended output: rejected identities are
    # deliberately false, independently of whether discovery attempts them.
    return [
      dict(name='parallel_union', valid=True,
           left=[m([[1,0]], [6]),m([[1,1]], [6])], right=[m(q=[6])]),
      dict(name='parallel_opposite_sign', valid=True,
           left=[m([[1,0]], [6], [3,7]),m([[1,1]], [6], [-3,7])],
           right=[m(q=[6,1],c=[3,7])]),
      dict(name='phase_split', valid=True,
           left=[m(q=[6],c=[3,7]),m(q=[6,1],c=[3,7])],
           right=[m([[1,0]], [6], [6,7])]),
      dict(name='nested_agrees_only_on_subspace', valid=True,
           left=[m(q=[3]),m([[1,0]],c=-1)],right=[m([[1,1]],q=[2])]),
      dict(name='nested_effective_sign', valid=True,
           left=[m(q=[3]),m([[1,1]],q=[2,0],c=1)],
           right=[m([[1,0]])]),
      dict(name='nonparallel_supports', valid=False,
           left=[m([[1,0]]),m([[2,0]])],right=[m()]),
      dict(name='unequal_magnitudes', valid=False,
           left=[m([[1,0]],c=1),m([[1,1]],c=2)],right=[m()]),
      dict(name='incompatible_quadratic_phase', valid=False,
           left=[m([[1,0]],q=[6]),m([[1,1]])],right=[m(q=[6])]),
      dict(name='nonaffine_phase_split', valid=False,
           left=[m(),m(q=[3])],right=[m([[1,0]],c=2)]),
      dict(name='nested_wrong_codimension', valid=False,
           left=[m(),m([[1,0],[2,0]],c=-1)],right=[m([[1,1]])]),
      dict(name='nested_nonconstant_restricted_phase', valid=False,
           left=[m(q=[3]),m([[1,0]],q=[2],c=-1)],right=[m([[1,1]],q=[2])]),
      dict(name='nested_wrong_effective_sign', valid=False,
           left=[m(q=[3]),m([[1,1]],q=[2],c=1)],right=[m([[1,0]])]),
    ]


def affine_span_message(points):
    """Three-variable independent geometric support constructor for schedules."""
    rows=[]
    for mask in range(1,8):
        values={(mask & x).bit_count() & 1 for x in points}
        if len(values)==1:
            rows.append([mask,values.pop()])
    result=canonical(3,[0,1,2],rows)
    actual={x for x in range(8) if point(result,x)}
    assert actual==set(points), ('points must be exactly an affine space',points)
    return result


def nonconfluence_schedules():
    singles=[affine_span_message([x]) for x in range(8)]
    schedules={
      'four_lines': [[0,1],[4,6],[3,7],[2,5]],
      'one_space': [[0,1],[2,3],[4,5],[6,7],[8,9],[10,11],[12,13]],
    }
    answer={}
    for name, pairs in schedules.items():
        live={i:([i],message) for i,message in enumerate(singles)}
        proofs=[]
        for new_id,(i,j) in enumerate(pairs,start=8):
            a,ma=live.pop(i);b,mb=live.pop(j)
            points=a+b
            out=affine_span_message(points)
            proof=norm_identity(3,[0,1,2],[ma,mb],[out])
            assert proof['equal']
            proofs.append(dict(consumed=[i,j],fresh=new_id,output=out,
                               squared_norm=proof['squared_norm']))
            live[new_id]=(points,out)
        outputs=[m for _,m in live.values()]
        assert exhaustive_equal(3,[0,1,2],singles,outputs)['equal']
        answer[name]=dict(inputs=singles,steps=proofs,live_ids=list(live),outputs=outputs,
                          final_count=len(outputs))
    bad=answer['four_lines']['outputs']
    supports=[{x for x in range(8) if point(m,x)} for m in bad]
    directions=[]
    for support in supports:
        a,b=sorted(support);directions.append(a^b)
    assert len(set(directions))==4
    assert all(not (a&b) for i,a in enumerate(supports) for b in supports[i+1:])
    answer['four_lines']['directions']=directions
    answer['four_lines']['stream_order']=[0,1,4,6,3,7,2,5]
    answer['one_space']['stream_order']=list(range(8))
    return answer
