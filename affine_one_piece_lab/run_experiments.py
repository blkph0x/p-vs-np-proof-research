"""Persist original explicit sums, complete recognition proofs and provenance."""
from copy import deepcopy
from datetime import datetime,timezone
from hashlib import sha256
import json
from pathlib import Path
from one_piece import recognize,verify_one_piece,partition
from controls import (NIGHT,oracle,named_controls,small_complete_requests,
                       signed_three_requests,seeded_requests,direct_values,
                       classify_values,mutations)

HERE=Path(__file__).resolve().parent


def hashes():
    paths=[HERE/name for name in ('one_piece.py','controls.py','test_one_piece.py','run_experiments.py','THEOREM.md')]
    paths += [NIGHT/'affine_partition_compression_lab'/'partition.py',
              NIGHT/'affine_boundary_reference'/'reference.py',
              NIGHT/'affine_compression_review'/'review_oracles.py']
    return {str(p.relative_to(NIGHT)).replace('\\','/'):sha256(p.read_bytes()).hexdigest() for p in paths}


def evaluate(case):
    n,ids,messages=case['n'],case['retained'],case['messages'];caps=case.get('caps',{})
    result=recognize(n,ids,messages,**caps)
    assert result['status']==case['expected'],(case,result)
    answer=dict(original_request=case,result=result)
    if result['status']=='UNKNOWN':
        assert result['message'] is None and result['certificate'] is None
        return answer
    checked=verify_one_piece(n,ids,messages,result,**caps);assert checked['valid'],checked
    answer['verification']=checked
    if len(ids)<=8:
        values=direct_values(n,ids,messages)
        accepted=classify_values(values)
        assert accepted==(result['status']=='EXACT')
        answer['independent_truth_values']=[[v.numerator,v.denominator] for v in values]
        answer['independent_classification']=accepted
        if accepted:
            direct=oracle.direct_norm(n,ids,messages,[result['message']]);assert direct['squared_norm']==[0,1]
            answer['direct_difference_norm']=direct
    if case.get('fallback'):assert result['stats']['norm_queries']>2
    if 'kind' in case:assert result['certificate']['kind']==case['kind']
    if 'difference' in case:assert result['certificate']['difference_norm']['value']==case['difference']
    return answer


def run():
    before=hashes()
    named=[evaluate(c) for c in named_controls()]
    ternary=[evaluate(c) for c in small_complete_requests()]
    signs=[evaluate(c) for c in signed_three_requests()]
    random_cases=[evaluate(c) for c in seeded_requests()]
    rejected=[]
    names={'four_nonparallel_lines','shifted_zero_anchor_with_outside','cubic_final_norm_four','nonuniform_magnitude'}
    for row in named:
        case=row['original_request']
        if case['name'] not in names:continue
        result=row['result']
        for name,changed in mutations(result):
            if name=='zero_support_point' and result['certificate']['kind']!='anchor_zero':continue
            checked=verify_one_piece(case['n'],case['retained'],case['messages'],changed)
            assert checked['status']=='INVALID',(case['name'],name,checked)
            rejected.append(dict(control=case['name'],mutation=name,verification=checked))
        original=deepcopy(case['messages']);first=next(m for m in original if not m['zero']);first['scalar'][0]*=2
        forged=deepcopy(result)
        forged['certificate']['input_sha256']=partition.digest(dict(format='explicit-one-piece-v1',n=case['n'],retained=case['retained'],messages=original))
        checked=verify_one_piece(case['n'],case['retained'],original,forged);assert checked['status']=='INVALID'
        rejected.append(dict(control=case['name'],mutation='rehashed_changed_coefficient',verification=checked))
    cases=named+ternary+signs+random_cases
    totals={status:sum(c['result']['status']==status for c in cases) for status in ('EXACT','UNSUPPORTED','UNKNOWN')}
    totals.update(cases=len(cases),direct_truth_values=sum(len(c.get('independent_truth_values',[])) for c in cases),
       verified_obstructions=sum(c['result']['status']=='UNSUPPORTED' and c['verification']['valid'] for c in cases),
       rejected_mutations=len(rejected),producer_norm_queries=sum(c['result']['stats']['norm_queries'] for c in cases),
       producer_pair_contractions=sum(c['result']['stats']['pair_contractions'] for c in cases),
       checker_pair_contractions=sum(c.get('verification',{}).get('stats',{}).get('pair_contractions',0) for c in cases))
    after=hashes();assert after==before,'production/dependency changed during run'
    report=dict(format='complete-affine-one-piece-results-v1',timestamp_utc=datetime.now(timezone.utc).isoformat(),
       seed=1910261701,source_hashes_before=before,source_hashes_after=after,source_unchanged_during_run=True,
       test_command='python -m unittest discover -v',totals=totals,named_controls=named,
       all_small_ternary_tables=ternary,all_three_bit_sign_tables=signs,seeded_explicit_sums=random_cases,
       mutation_recipe='controls.mutations plus externally rehashed coefficient change',mutations=rejected)
    (HERE/'RESULTS.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(totals,indent=2))


if __name__=='__main__':run()
