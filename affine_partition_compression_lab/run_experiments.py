"""Source-hashed original inputs and exact certificate/oracle evidence."""
from copy import deepcopy
from datetime import datetime,timezone
from hashlib import sha256
import json
from pathlib import Path
from partition import recognize,verify_partition,digest
from controls import (NIGHT,oracle,named_controls,all_affine_partitions_three,
                      seeded_partitions,mutations)

HERE=Path(__file__).resolve().parent


def source_hashes():
    paths=list(HERE.glob('*.py'))+[HERE/'THEOREM.md',
          NIGHT/'affine_compression_review'/'review_oracles.py',
          NIGHT/'affine_boundary_reference'/'reference.py']
    return {str(p.relative_to(NIGHT)).replace('\\','/'):sha256(p.read_bytes()).hexdigest() for p in sorted(paths)}


def evaluate(request,norm=False):
    n,ids,messages=request['n'],request['retained'],request['messages']
    caps=request.get('caps',{});result=recognize(n,ids,messages,**caps)
    expected=request.get('expected_status','EXACT');assert result['status']==expected,(request,result)
    record=dict(original_request=request,result=result)
    if expected=='EXACT':
        checked=verify_partition(n,ids,messages,result,**caps);assert checked['valid'],checked
        record['verification']=checked
        if 'expected_message' in request:assert result['message']==request['expected_message']
        if len(ids)<=8:
            direct=oracle.direct_norm(n,ids,messages,[result['message']]);assert direct['squared_norm']==[0,1]
            record['direct_oracle']=direct
        if norm:
            proof=oracle.norm_identity(n,ids,messages,[result['message']],save_proofs=True)
            checked_norm=oracle.verify_norm_identity(n,ids,messages,[result['message']],proof)
            assert checked_norm['valid'] and checked_norm['equal']
            record['norm_certificate']=proof;record['norm_verification']=checked_norm
    else:assert result['message'] is None and result['certificate'] is None
    return record


def run():
    before=source_hashes()
    named=[evaluate(c,norm=True) for c in named_controls()]
    partitions=[]
    for index,messages in enumerate(all_affine_partitions_three()):
        partitions.append(evaluate(dict(index=index,n=3,retained=[0,1,2],messages=messages)))
    assert len(partitions)==912
    singles=next(c['messages'] for c in named_controls() if c['name']=='eight_singletons')
    signs=[]
    for truth in range(256):
        messages=deepcopy(singles)
        for v,m in enumerate(messages):m['scalar']=[-1 if truth>>v&1 else 1,1]
        expected='EXACT' if truth.bit_count()%2==0 else 'UNSUPPORTED'
        signs.append(evaluate(dict(truth=truth,n=3,retained=[0,1,2],messages=messages,
                                   expected_status=expected,independent_cubic_anf=truth.bit_count()%2)))
    seeded=[evaluate(c) for c in seeded_partitions()]
    control=named_controls()[0];base=recognize(3,[0,1,2],control['messages'])
    rejected=[]
    for name,changed in mutations(base):
        checked=verify_partition(3,[0,1,2],control['messages'],changed)
        assert checked['status']=='INVALID';rejected.append(dict(name=name,result=changed,verification=checked))
    for mode in ('phase','overlap','magnitude'):
        changed=deepcopy(control['messages'])
        if mode=='phase':changed[0]['scalar']=[-1,1]
        elif mode=='overlap':changed[0]=deepcopy(changed[1])
        else:changed[0]['scalar']=[2,1]
        forged=deepcopy(base);forged['certificate']['input_sha256']=digest(dict(n=3,retained=[0,1,2],messages=changed))
        checked=verify_partition(3,[0,1,2],changed,forged);assert checked['status']=='INVALID'
        rejected.append(dict(name='rehashed_'+mode,originals=changed,result=forged,verification=checked))
    all_cases=named+partitions+signs+seeded
    totals={status:sum(c['result']['status']==status for c in all_cases) for status in ('EXACT','UNSUPPORTED','UNKNOWN')}
    totals.update(cases=len(all_cases),direct_assignments=sum(c.get('direct_oracle',{}).get('assignments',0) for c in all_cases),
          norm_certificates=sum('norm_certificate' in c for c in all_cases),
          norm_block_checks=sum(c.get('norm_certificate',{}).get('block_checks',0) for c in all_cases),
          rejected_mutations=len(rejected))
    after=source_hashes();assert after==before,'source changed during run'
    report=dict(format='affine-partition-compression-results-v1',timestamp_utc=datetime.now(timezone.utc).isoformat(),
       seed=1910261601,scope='standalone explicit disjoint equal-magnitude affine-partition recognition',
       source_hashes_before=before,source_hashes_after=after,source_unchanged_during_run=True,
       test_command='python -m unittest discover -v',totals=totals,named_controls=named,
       all_three_bit_affine_partitions=partitions,all_three_bit_sign_tables=signs,
       seeded_partitions=seeded,mutation_base=control,mutations=rejected)
    (HERE/'RESULTS.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(totals,indent=2))


if __name__=='__main__':run()
