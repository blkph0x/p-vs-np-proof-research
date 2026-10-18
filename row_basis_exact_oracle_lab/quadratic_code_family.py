"""Quadratic-length trace-code family forcing full exceptional rank.

This is a separate strengthening of the older explicit family.  Over GF(2^k)
set q=2^k, t=floor(q/(2k)), and r=k*t.  Trace coordinates for every
(evaluation, nonzero beta) give n=q(q-1) binary columns.  The distance lower
bound beats the 1+r+binom(r,2) low-weight budget for every k>=4, while
q/4 <= r <= q/2, so n=O(r^2) and the route-specific syndrome count is 2^r.
"""
from __future__ import annotations
from hashlib import sha256
import json
from pathlib import Path
import random

from exact_oracle import rank
from explicit_code_family import field_modulus, gf_mul, gf_trace

ROOT=Path(__file__).resolve().parent


def parameters(degree):
    k=int(degree)
    if type(degree) is not int or k<4:
        raise ValueError('degree must be an integer >= 4')
    q=1<<k; t=q//(2*k)
    if t<2:
        raise ValueError('degree too small')
    r=k*t; budget=1+r+r*(r-1)//2; distance=(q-t+1)*(q//2)
    if distance<=budget:
        raise ArithmeticError('distance does not beat low-weight budget')
    if r<q//4 or r>q//2:
        raise ArithmeticError('rank scaling bound failed')
    return {'field_degree':k,'field_size':q,'polynomial_degree':t,'binary_rank':r,'columns':q*(q-1),'minimum_code_distance':distance,'low_weight_budget':budget,'state_lower_bound':1<<r,'rank_lower_bound_n_quarter':q//4,'rank_upper_bound_n_half':q//2}


def generate_columns(degree):
    spec=parameters(degree); k=spec['field_degree']; q=spec['field_size']; t=spec['polynomial_degree']; modulus=field_modulus(k)
    dual=tuple(sum(gf_trace(gf_mul(value,1<<bit,modulus,k),modulus,k)<<bit for bit in range(k)) for value in range(q))
    columns=[]
    for evaluation in range(q):
        powers=[1]
        for _ in range(1,t):
            powers.append(gf_mul(powers[-1],evaluation,modulus,k))
        for beta in range(1,q):
            column=0
            for coefficient,power in enumerate(powers):
                column |= dual[gf_mul(beta,power,modulus,k)] << (coefficient*k)
            columns.append(column)
    if len(columns)!=spec['columns'] or len(set(columns))!=len(columns):
        raise ArithmeticError('columns are not distinct')
    return modulus,tuple(columns)


def transform_columns(columns,transform):
    return tuple(sum(((mask&column).bit_count()&1)<<row for row,mask in enumerate(transform)) for column in columns)


def column_stats(columns):
    exceptional=[column for column in columns if column.bit_count()>2]
    return (len(exceptional),rank(exceptional),sum(max(0,column.bit_count()-2) for column in columns),sum(column.bit_count() for column in columns))


def upper_transform(rank_value):
    return tuple((1<<row)|((1<<(row+1)) if row+1<rank_value else 0) for row in range(rank_value))


def random_transforms(rank_value,count,seed):
    rng=random.Random(seed); transforms=[]
    for _ in range(count):
        current=[1<<row for row in range(rank_value)]
        for _ in range(3*rank_value):
            destination=rng.randrange(rank_value); source=rng.randrange(rank_value-1)
            if source>=destination: source+=1
            current[destination]^=current[source]
        if rank(current)!=rank_value: raise ArithmeticError('singular transform')
        transforms.append(tuple(current))
    return tuple(transforms)


def digest_columns(columns,rank_value):
    width=(rank_value+7)//8; digest=sha256()
    for column in columns: digest.update(column.to_bytes(width,'little'))
    return digest.hexdigest()


def verify_sampled_transforms(degree,transform_count=2):
    spec=parameters(degree); modulus,columns=generate_columns(degree)
    transforms=(tuple(1<<row for row in range(spec['binary_rank'])),upper_transform(spec['binary_rank']),*random_transforms(spec['binary_rank'],transform_count,20261018+degree))
    stats=[]
    for transform in transforms:
        if rank(transform)!=spec['binary_rank']: raise ArithmeticError('singular sampled transform')
        observed=column_stats(transform_columns(columns,transform))
        if observed[1]!=spec['binary_rank']: raise AssertionError('exceptional rank lost')
        stats.append({'exceptional_count':observed[0],'exceptional_rank':observed[1],'excess':observed[2],'total':observed[3]})
    return {'parameters':spec,'field_modulus':modulus,'column_digest':digest_columns(columns,spec['binary_rank']),'distinct_columns':len(columns),'transform_count':len(transforms),'sampled_stats':stats}


def verify_record(record):
    try:
        degree=int(record['parameters']['field_degree']); expected=parameters(degree)
        if record['parameters']!=expected: return False
        modulus,columns=generate_columns(degree)
        if int(record['field_modulus'])!=modulus or int(record['distinct_columns'])!=len(columns): return False
        if record['column_digest']!=digest_columns(columns,expected['binary_rank']): return False
        if int(record['transform_count'])!=len(record['sampled_stats']): return False
        checked=verify_sampled_transforms(degree,transform_count=int(record['transform_count'])-2)
        return checked['sampled_stats']==record['sampled_stats']
    except (KeyError,TypeError,ValueError,IndexError,ArithmeticError):
        return False


def build_artifact():
    degrees=[4,5,6,7]; records=[verify_sampled_transforms(degree,transform_count=2) for degree in degrees]
    assert all(verify_record(record) for record in records)
    formulas=[parameters(degree) for degree in range(4,13)]
    forged=json.loads(json.dumps(records[0])); forged['parameters']['state_lower_bound']=0
    return {'all_checks_passed':True,'degrees_checked':degrees,'records':records,'formula_sweep':formulas,'adversarial':{'forged_record_rejected':not verify_record(forged)},'scope':'Quadratic-length explicit trace family; lower bound is for the exceptional-syndrome row-basis route only.'}


def write_artifact():
    artifact=build_artifact(); (ROOT/'QUADRATIC_CODE_FAMILY_RESULTS.json').write_text(json.dumps(artifact,indent=2)+'\n',encoding='utf-8'); return artifact

if __name__=='__main__': print(json.dumps(write_artifact(),indent=2))
