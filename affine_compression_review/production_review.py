"""Reproducible production adversaries; never edits the reviewed implementation."""
from copy import deepcopy
from fractions import Fraction
from pathlib import Path
import importlib.util
import random
import sys
from review_oracles import canonical,controls,point,direct_norm,nonconfluence_schedules

NIGHT=Path(__file__).resolve().parent.parent


def load(name,path):
    spec=importlib.util.spec_from_file_location(name,path)
    module=importlib.util.module_from_spec(spec);sys.modules[name]=module
    spec.loader.exec_module(module)
    return module


compression=load('reviewed_compression',NIGHT/'affine_sum_compression_lab'/'compression.py')


def seeded_requests(seed=1910261401,count=200):
    rng=random.Random(seed)
    answer=[]
    for index in range(count):
        n=rng.randrange(7);retained=list(range(n));rng.shuffle(retained)
        messages=[]
        for _ in range(rng.randrange(9)):
            if messages and rng.randrange(4)==0:
                m=deepcopy(rng.choice(messages));m['scalar'][0]*=rng.choice([-1,1])
                if m['zero']:m['scalar']=[0,1]
            else:
                eq=[[rng.randrange(1<<n),rng.randrange(2)] for _ in range(rng.randrange(4))]
                q=[mask for mask in range(1<<n) if mask.bit_count()<=2 and rng.randrange(5)==0]
                m=canonical(n,retained,eq,q,Fraction(rng.randrange(-4,5),rng.randrange(1,5)))
            messages.append(m)
        answer.append(dict(index=index,n=n,retained=retained,messages=messages))
    return answer


def certificate_mutations(result):
    mutations=[]
    def change(name,fn):
        r=deepcopy(result);fn(r);mutations.append((name,r))
    def rewrite(r):
        return next(e for e in r['certificate']['events'] if e['kind']=='rewrite')
    change('wrong_external_hash',lambda r:r['certificate'].__setitem__('input_sha256','0'*64))
    change('omitted_input',lambda r:r['certificate']['events'].pop(0))
    change('wrong_input_index',lambda r:r['certificate']['events'][0].__setitem__('index',1))
    change('boolean_input_id',lambda r:r['certificate']['events'][0].__setitem__('id',False))
    change('same_consumed_id',lambda r:rewrite(r).__setitem__('right',rewrite(r)['left']))
    change('future_consumed_id',lambda r:rewrite(r).__setitem__('left',100000))
    change('reused_output_id',lambda r:rewrite(r).__setitem__('id',rewrite(r)['left']))
    change('boolean_consumed_id',lambda r:rewrite(r).__setitem__('left',False))
    change('wrong_rule',lambda r:rewrite(r).__setitem__('rule','unknown'))
    change('wrong_row_type',lambda r:rewrite(r).__setitem__('parameters',{'row':False}))
    change('omitted_final_id',lambda r:r['certificate']['final_ids'].clear())
    change('wrong_final_scalar',lambda r:r['messages'][0].__setitem__('scalar',[42,1]))
    change('wrong_normalization_scalar',lambda r:rewrite(r)['normalization']['message'].__setitem__('scalar',[42,1]))
    change('drop_nonzero',lambda r:r['certificate']['events'].append({'kind':'drop_zero','id':r['certificate']['final_ids'][0]}))
    change('duplicate_consumption',lambda r:r['certificate']['events'].append(deepcopy(rewrite(r))))
    return mutations


def forged_invalid_identity(control):
    result=compression.compress(3,[0,1,2],control['left'])
    assert len(result['messages'])==2
    result=deepcopy(result)
    rules={
      'nonparallel_supports':('parallel',{'row':0}),
      'unequal_magnitudes':('parallel',{'row':0}),
      'incompatible_quadratic_phase':('parallel',{'row':0}),
      'nonaffine_phase_split':('same_support',{}),
      'nested_wrong_codimension':('nested',{'outer':'left','row':0}),
      'nested_nonconstant_restricted_phase':('nested',{'outer':'left','row':0}),
      'nested_wrong_effective_sign':('nested',{'outer':'left','row':0}),
    }
    rule,parameters=rules[control['name']]
    out=control['right'][0]
    normalization=compression.boundary.normalize_message(3,[0,1,2],out['equations'],out['phase'],out['scalar'])
    result['certificate']['events']=[e for e in result['certificate']['events'] if e['kind']=='input']
    result['certificate']['events'].append(dict(kind='rewrite',left=0,right=1,id=2,
                                rule=rule,parameters=parameters,normalization=normalization))
    result['certificate']['final_ids']=[2];result['messages']=[out]
    return result


def actual_nonconfluence():
    result={}
    for name,data in nonconfluence_schedules().items():
        originals=[data['inputs'][i] for i in data['stream_order']]
        produced=compression.compress(3,[0,1,2],originals)
        checked=compression.verify_compression(3,[0,1,2],originals,produced)
        assert checked['valid'] and len(produced['messages'])==data['final_count']
        assert direct_norm(3,[0,1,2],originals,produced['messages'])['squared_norm']==[0,1]
        result[name]=dict(originals=originals,result=produced,verification=checked)
    return result
