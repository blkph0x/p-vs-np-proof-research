"""Independent replay of the quadratic-length trace-code family."""
from __future__ import annotations
from hashlib import sha256
import copy
import json
import random
from pathlib import Path

ROOT=Path(__file__).resolve().parent


def poly_mul(a,b):
    result=0
    while b:
        if b&1: result^=a
        b>>=1; a<<=1
    return result


def poly_mod(value,modulus):
    degree=modulus.bit_length()-1
    while value and value.bit_length()-1>=degree:
        value^=modulus<<(value.bit_length()-1-degree)
    return value


def gcd(a,b):
    while b: a,b=b,poly_mod(a,b)
    return a


def irreducible(modulus,degree):
    x=2; value=x
    for step in range(1,degree+1):
        value=poly_mod(poly_mul(value,value),modulus)
        if step<=degree//2 and gcd(value^x,modulus)!=1: return False
    return value==x


def field_modulus(degree):
    for lower in range(1,1<<degree,2):
        candidate=(1<<degree)|lower
        if irreducible(candidate,degree): return candidate
    raise ArithmeticError('no modulus')


def gf_mul(a,b,modulus,degree):
    result=0; mask=(1<<degree)-1
    while b:
        if b&1: result^=a
        b>>=1; a<<=1
        if a&(1<<degree): a^=modulus
    return result&mask


def trace(value,modulus,degree):
    result=0; power=value
    for _ in range(degree):
        result^=power; power=gf_mul(power,power,modulus,degree)
    if result not in (0,1): raise ArithmeticError('trace')
    return result


def rank(values):
    pivots={}
    for value in values:
        while value:
            pivot=value.bit_length()-1
            if pivot in pivots: value^=pivots[pivot]
            else: pivots[pivot]=value; break
    return len(pivots)


def parameters(degree):
    k=int(degree); q=1<<k; t=q//(2*k); r=k*t; budget=1+r+r*(r-1)//2; distance=(q-t+1)*(q//2)
    if k<4 or t<2 or distance<=budget or not(q//4<=r<=q//2): raise AssertionError('formula')
    return {'field_degree':k,'field_size':q,'polynomial_degree':t,'binary_rank':r,'columns':q*(q-1),'minimum_code_distance':distance,'low_weight_budget':budget,'state_lower_bound':1<<r,'rank_lower_bound_n_quarter':q//4,'rank_upper_bound_n_half':q//2}


def columns(degree):
    spec=parameters(degree); k=spec['field_degree']; q=spec['field_size']; t=spec['polynomial_degree']; modulus=field_modulus(k)
    dual=tuple(sum(trace(gf_mul(value,1<<bit,modulus,k),modulus,k)<<bit for bit in range(k)) for value in range(q))
    out=[]
    for evaluation in range(q):
        powers=[1]
        for _ in range(1,t): powers.append(gf_mul(powers[-1],evaluation,modulus,k))
        for beta in range(1,q):
            out.append(sum(dual[gf_mul(beta,power,modulus,k)]<<(coefficient*k) for coefficient,power in enumerate(powers)))
    if len(out)!=spec['columns'] or len(set(out))!=len(out): raise AssertionError('columns')
    return modulus,tuple(out)


def transform(values,rows):
    return tuple(sum(((mask&value).bit_count()&1)<<row for row,mask in enumerate(rows)) for value in values)


def stats(values):
    exceptional=[value for value in values if value.bit_count()>2]
    return [len(exceptional),rank(exceptional),sum(max(0,value.bit_count()-2) for value in values),sum(value.bit_count() for value in values)]


def upper(r):
    return tuple((1<<row)|((1<<(row+1)) if row+1<r else 0) for row in range(r))


def random_transforms(r, count, seed):
    rng=random.Random(seed); transforms=[]
    for _ in range(count):
        current=[1<<row for row in range(r)]
        for _ in range(3*r):
            destination=rng.randrange(r); source=rng.randrange(r-1)
            if source>=destination: source+=1
            current[destination]^=current[source]
        if rank(current)!=r: raise AssertionError('singular transform')
        transforms.append(tuple(current))
    return tuple(transforms)


def digest(values,r):
    h=sha256(); width=(r+7)//8
    for value in values: h.update(value.to_bytes(width,'little'))
    return h.hexdigest()


def verify_record(record):
    try:
        degree=int(record['parameters']['field_degree']); spec=parameters(degree)
        if record['parameters']!=spec: return False
        modulus,values=columns(degree)
        if record['field_modulus']!=modulus or record['distinct_columns']!=len(values): return False
        if record['column_digest']!=digest(values,spec['binary_rank']): return False
        if record['transform_count']!=len(record['sampled_stats']): return False
        transforms=(tuple(1<<row for row in range(spec['binary_rank'])),upper(spec['binary_rank']),*random_transforms(spec['binary_rank'],record['transform_count']-2,20261018+degree))
        if len(transforms)!=record['transform_count']:
            return False
        for rows,saved in zip(transforms,record['sampled_stats']):
            observed=stats(transform(values,rows))
            if saved!={'exceptional_count':observed[0],'exceptional_rank':observed[1],'excess':observed[2],'total':observed[3]}: return False
        return all(saved['exceptional_rank']==spec['binary_rank'] for saved in record['sampled_stats'])
    except (KeyError,TypeError,ValueError,IndexError,AssertionError,ArithmeticError): return False


def main():
    artifact=json.loads((ROOT/'QUADRATIC_CODE_FAMILY_RESULTS.json').read_text(encoding='utf-8'))
    assert artifact['all_checks_passed'] and artifact['degrees_checked']==[4,5,6,7]
    assert all(verify_record(record) for record in artifact['records'])
    assert [spec['field_degree'] for spec in artifact['formula_sweep']]==list(range(4,13))
    assert all(spec==parameters(spec['field_degree']) for spec in artifact['formula_sweep'])
    for spec in artifact['formula_sweep']:
        q=spec['field_size']; r=spec['binary_rank']; n=spec['columns']
        assert q//4<=r<=q//2 and n<16*r*r and spec['state_lower_bound']==1<<r
    forged=copy.deepcopy(artifact['records'][0]); forged['field_modulus']^=1
    assert not verify_record(forged)
    assert artifact['adversarial']=={'forged_record_rejected':True}
    print(json.dumps({'independent_checks_passed':True,'degrees':artifact['degrees_checked'],'formula_sweep':len(artifact['formula_sweep']),'state_bounds':[row['parameters']['state_lower_bound'] for row in artifact['records']]}))


if __name__=='__main__': main()
