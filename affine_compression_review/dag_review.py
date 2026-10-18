"""Independent original-factor and pointwise-node audit of compressed DAGs."""
from copy import deepcopy
from fractions import Fraction
import random
from review_oracles import point,norm_identity,reference
from production_review import load,NIGHT

dag=load('reviewed_compressed_dag',NIGHT/'compressed_affine_dag_lab'/'dag.py')


def factor_value(factor,word):
    if factor['kind']=='or':
        return Fraction(any(bool(word>>(abs(x)-1)&1)==(x>0) for x in factor['literals']))
    if any((word&mask).bit_count()%2!=rhs for mask,rhs in factor['equations']):
        return Fraction(0)
    sign=(-1)**sum(word&mask==mask for mask in factor['phase'])
    return Fraction(*factor['scalar'])*sign


def scope(factor):
    if factor['kind']=='affine':return set(factor['scope'])
    literals=set(factor['literals'])
    return set() if any(-x in literals for x in literals) else {abs(x)-1 for x in literals}


def words(ids):
    ids=list(ids)
    for v in range(1<<len(ids)):
        yield sum(((v>>i)&1)<<bit for i,bit in enumerate(ids))


def requests(seed=1910261501,count=200):
    rng=random.Random(seed)
    for index in range(count):
        n=rng.randrange(7);factors=[]
        for _ in range(rng.randrange(8)):
            if rng.randrange(2):
                factors.append(dict(kind='or',literals=[] if not n else
                      [rng.choice([-1,1])*rng.randrange(1,n+1) for _ in range(rng.randrange(5))]))
            else:
                ids=[v for v in range(n) if rng.randrange(2)]
                mask=sum(1<<v for v in ids)
                equations=[[rng.randrange(1<<n)&mask,rng.randrange(2)] for _ in range(rng.randrange(3))]
                phase=[t for t in range(1<<n) if t&~mask==0 and t.bit_count()<=2 and rng.randrange(3)==0]
                factors.append(dict(kind='affine',scope=ids,equations=equations,phase=phase,
                                    scalar=[rng.randrange(-3,4),rng.choice([1,3,5])]))
        order=list(range(len(factors)));rng.shuffle(order)
        yield dict(index=index,n=n,factors=factors,order=order)


def direct_audit(request,result):
    n,factors=request['n'],request['factors']
    expected=Fraction(0)
    for word in range(1<<n):
        product=Fraction(1)
        for factor in factors:product*=factor_value(factor,word)
        expected+=product
    assert result['value']==[expected.numerator,expected.denominator]
    scopes=[scope(f) for f in factors];checks=0
    for node in result['certificate']['nodes']:
        ids=node['factor_ids']
        inside=set().union(*(scopes[i] for i in ids))
        outside=set().union(*(scopes[i] for i in range(len(factors)) if i not in ids))
        boundary=inside&outside
        assert node['boundary']==sorted(boundary)
        for y in words(sorted(boundary)):
            marginal=Fraction(0)
            for z in words(sorted(inside-boundary)):
                product=Fraction(1)
                for i in ids:product*=factor_value(factors[i],y|z)
                marginal+=product
            observed=sum((point(m,y) for m in node['messages']),Fraction(0))
            assert observed==marginal,(node,y,observed,marginal)
            checks+=1
    return dict(original_assignments=1<<n,boundary_values=checks,
                expected=[expected.numerator,expected.denominator])


def symbolic_rewrite_audit(n,retained,originals,result):
    """Check all trace rewrites through block norms, independently of grammar."""
    live={};records=[];arrivals=0
    for step in result['certificate']['events']:
        if step['kind']=='input':
            live[step['id']]=originals[arrivals];arrivals+=1
        elif step['kind']=='rewrite':
            first=live.pop(step['left']);second=live.pop(step['right'])
            output=step['normalization']['message']
            norm=norm_identity(n,retained,[first,second],[output])
            assert norm['equal'],(step,norm)
            records.append(dict(rule=step['rule'],consumed=[step['left'],step['right']],
                                block_checks=norm['block_checks'],squared_norm=norm['squared_norm']))
            live[step['id']]=output
        elif step['kind']=='drop_zero':
            assert live.pop(step['id'])['zero']
        elif step['kind']!='failed_pair':raise AssertionError('unknown event')
    assert arrivals==len(originals)
    assert sorted(live)==result['certificate']['final_ids']
    return records


def block_marginal_audit(record):
    request=record['request']
    result=reference.marginalize_reference(**request,max_work=20000000)
    assert result['status']=='EXACT'
    check=reference.verify_reference(**request,result=result,max_work=20000000)
    assert check['valid']
    same=reference.equivalent_messages(request['n'],request['retained'],
                              result['message'],record['result']['message'],max_work=20000000)
    assert same['status']=='EXACT' and same['equivalent']
    return dict(input_sha256=result['certificate']['input_sha256'],equal=True)


def audit_all_node_rewrites(result):
    cert=result['certificate'];records=cert['marginals'];answer=[]
    for index,node in enumerate(cert['nodes']):
        originals=[records[ref]['result']['message'] for ref in node['requests']]
        # An empty input stream has no rewrite; its n is immaterial here.
        dimension=originals[0]['n'] if originals else 0
        checks=symbolic_rewrite_audit(dimension,node['boundary'],originals,node['compression'])
        answer.append(dict(node=index,rewrites=checks))
    return answer


def mutations(result):
    answer=[]
    def change(name,fn):
        r=deepcopy(result);fn(r);answer.append((name,r))
    def product(r):return next(x for x in r['certificate']['nodes'] if x['kind']=='product')
    change('missing_compression',lambda r:r['certificate']['nodes'][0].pop('compression'))
    change('null_compression',lambda r:r['certificate']['nodes'][0].__setitem__('compression',None))
    change('omitted_original_factor',lambda r:r['certificate']['nodes'][-1]['factor_ids'].pop())
    change('omitted_pair_reference',lambda r:product(r)['requests'].pop())
    change('duplicate_child',lambda r:product(r)['children'].__setitem__(1,product(r)['children'][0]))
    change('wrong_active_universe',lambda r:r['certificate']['nodes'][0].__setitem__('active',[]))
    change('wrong_original_free_variables',lambda r:r['certificate']['free_variables'].append(0))
    change('missing_stream_arrival',lambda r:r['certificate']['nodes'][0]['compression']['certificate']['events'].pop(0))
    change('false_value',lambda r:r.__setitem__('value',[123,1]))
    return answer
