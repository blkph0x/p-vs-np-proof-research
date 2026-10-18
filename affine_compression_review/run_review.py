"""Reproduce all independently owned compression evidence and source hashes."""
from copy import deepcopy
from datetime import datetime,timezone
from fractions import Fraction
from hashlib import sha256
import json
from pathlib import Path
from review_oracles import (canonical,controls,direct_norm,norm_identity,
                    verify_norm_identity,nonconfluence_schedules)
from production_review import (compression,seeded_requests,certificate_mutations,
                    forged_invalid_identity,actual_nonconfluence,load,NIGHT)
from dag_review import (dag,requests,direct_audit,audit_all_node_rewrites,
                       block_marginal_audit,mutations,symbolic_rewrite_audit)

HERE=Path(__file__).resolve().parent


def hashes():
    paths=list(HERE.glob('*.py'))+list(HERE.glob('*.md'))
    for directory in ('affine_sum_compression_lab','compressed_affine_dag_lab','affine_sum_capacity_lab'):
        paths+=list((NIGHT/directory).glob('*.py'))+list((NIGHT/directory).glob('THEOREM.md'))+list((NIGHT/directory).glob('RESULTS.json'))
    paths += [NIGHT/'affine_boundary_lab'/'boundary.py',NIGHT/'affine_boundary_reference'/'reference.py']
    return {str(p.relative_to(NIGHT)).replace('\\','/'):sha256(p.read_bytes()).hexdigest()
            for p in sorted(set(paths))}


def rule_controls():
    answer=[]
    for width in (3,128,512):
        for control in controls(width):
            ids=list(range(width))
            proof=norm_identity(width,ids,control['left'],control['right'],save_proofs=True)
            verification=verify_norm_identity(width,ids,control['left'],control['right'],proof)
            assert verification['valid'] and verification['equal']==control['valid']
            if width==3:
                direct=direct_norm(width,ids,control['left'],control['right'])
                assert direct['squared_norm']==proof['squared_norm']
            else:
                small=next(c for c in controls(3) if c['name']==control['name'])
                scaled=Fraction(*direct_norm(3,[0,1,2],small['left'],small['right'])['squared_norm'])*(1<<(width-3))
                assert proof['squared_norm']==[scaled.numerator,scaled.denominator]
                direct=dict(independent_free_coordinate_scaling=True)
            produced=compression.compress(width,ids,control['left'])
            checked=compression.verify_compression(width,ids,control['left'],produced)
            assert checked['valid']
            assert len(produced['messages'])==(1 if control['valid'] else 2)
            answer.append(dict(n=width,retained=ids,control=control,proof=proof,
                  verification=verification,direct_oracle=direct,production=produced,
                  production_verification=checked))
    return answer


def sum_requests():
    answer=[];assignments=0
    for request in seeded_requests():
        n,ids,originals=request['n'],request['retained'],request['messages']
        result=compression.compress(n,ids,originals)
        assert result['status']=='EXACT'
        checked=compression.verify_compression(n,ids,originals,result);assert checked['valid']
        direct=direct_norm(n,ids,originals,result['messages']);assert direct['squared_norm']==[0,1]
        assignments+=direct['assignments']
        answer.append(dict(original_request=request,result=result,verification=checked,direct_oracle=direct))
    return dict(seed=1910261401,requests=len(answer),original_assignments=assignments,cases=answer)


def mutation_controls():
    answer=[]
    for control in controls(3)[:5]:
        original=control['left'];result=compression.compress(3,[0,1,2],original)
        for name,changed in certificate_mutations(result):
            checked=compression.verify_compression(3,[0,1,2],original,changed)
            assert checked['status']=='INVALID', (name,checked)
            answer.append(dict(control=control['name'],mutation=name,verification=checked))
        changed=deepcopy(original);changed[0]['scalar'][0]*=2
        for name,external in [('changed_external_coefficient',changed),('extra_external_input',original+[original[0]])]:
            checked=compression.verify_compression(3,[0,1,2],external,result)
            assert checked['status']=='INVALID'
            answer.append(dict(control=control['name'],mutation=name,verification=checked))
    for control in controls(3)[5:]:
        forged=forged_invalid_identity(control)
        checked=compression.verify_compression(3,[0,1,2],control['left'],forged)
        assert checked['status']=='INVALID'
        answer.append(dict(control=control['name'],mutation='forged_semantic_identity',
                           forged_result=forged,verification=checked))
    return dict(rejected=len(answer),cases=answer)


def dag_requests():
    answer=[];assignment_count=boundary_count=rewrite_count=block_count=0
    for request in requests():
        result=dag.solve_factors(request['n'],request['factors'],order=request['order'])
        assert result['status']=='EXACT'
        checked=dag.verify_factors(request['n'],request['factors'],result,order=request['order'])
        assert checked['valid']
        direct=direct_audit(request,result)
        rewrites=audit_all_node_rewrites(result)
        assignment_count+=direct['original_assignments'];boundary_count+=direct['boundary_values']
        rewrite_count+=sum(len(n['rewrites']) for n in rewrites)
        block_count+=sum(c['block_checks'] for n in rewrites for c in n['rewrites'])
        answer.append(dict(original_request=request,result=result,verification=checked,
                           direct_oracle=direct,independent_rewrites=rewrites))
    n=5;clauses=[[1],[-1,2],[2,3],[-3,4],[4,5]]
    exact=dag.solve_formula(n,clauses);adversaries=[]
    for name,changed in mutations(exact):
        checked=dag.verify_formula(n,clauses,changed);assert checked['status']=='INVALID'
        adversaries.append(dict(name=name,verification=checked))
    return dict(seed=1910261501,requests=len(answer),original_assignments=assignment_count,
         intermediate_boundary_values=boundary_count,independent_rewrite_norms=rewrite_count,
         closed_block_checks=block_count,cases=answer,
         mutation_request=dict(n=n,clauses=clauses),mutations=adversaries)


def replay_saved_dag():
    path=NIGHT/'compressed_affine_dag_lab'/'RESULTS.json'
    saved=json.loads(path.read_text(encoding='utf-8'));answer=[]
    exact=unknown=blocks=rewrites=norm_pairs=0
    for index,case in enumerate(saved['cases']):
        request=case['original_request'];result=case['result'];caps=request.get('caps',{})
        if result['status']=='UNKNOWN':
            assert result['value'] is None and result['certificate'] is None and result['count'] is None
            unknown+=1;answer.append(dict(index=index,original_request=request,status='UNKNOWN',claim_is_null=True));continue
        if 'clauses' in request:
            check=dag.verify_formula(request['n'],request['clauses'],result,**caps)
        else:check=dag.verify_factors(request['n'],request['factors'],result,**caps)
        assert check['valid'],(request['name'],check)
        marginal_checks=[block_marginal_audit(r) for r in result['certificate']['marginals']]
        rewrite_checks=audit_all_node_rewrites(result)
        blocks+=len(marginal_checks)
        rewrites+=sum(len(n['rewrites']) for n in rewrite_checks)
        norm_pairs+=sum(r['block_checks'] for n in rewrite_checks for r in n['rewrites'])
        exact+=1;answer.append(dict(index=index,original_request=request,status='EXACT',
                verification=check,independent_marginals=marginal_checks,
                independent_rewrites=rewrite_checks))
    return dict(source=str(path.relative_to(NIGHT)).replace('\\','/'),sha256=sha256(path.read_bytes()).hexdigest(),
       exact=exact,unknown=unknown,independent_marginals=blocks,
       independent_rewrite_norms=rewrites,closed_norm_block_checks=norm_pairs,cases=answer)


def replay_saved_compression():
    path=NIGHT/'affine_sum_compression_lab'/'RESULTS.json'
    saved=json.loads(path.read_text(encoding='utf-8'));answer=[]
    exact=unknown=assignments=rewrites=norm_pairs=wide=0
    for index,case in enumerate(saved['controls']):
        result=case['result'];n=case['n'];ids=case['retained'];originals=case['originals']
        if result['status']=='UNKNOWN':
            assert result['messages'] is None and result['certificate'] is None
            unknown+=1;answer.append(dict(index=index,name=case['name'],status='UNKNOWN',claim_is_null=True));continue
        checked=compression.verify_compression(n,ids,originals,result,**case['caps']);assert checked['valid']
        checks=symbolic_rewrite_audit(n,ids,originals,result)
        rewrites+=len(checks);norm_pairs+=sum(c['block_checks'] for c in checks)
        if len(ids)<=8:
            direct=direct_norm(n,ids,originals,result['messages'])
            assert direct['squared_norm']==[0,1];assignments+=direct['assignments']
        else:
            direct=norm_identity(n,ids,originals,result['messages'],save_proofs=True)
            check_norm=verify_norm_identity(n,ids,originals,result['messages'],direct)
            assert check_norm['valid'] and check_norm['equal'];wide+=1
        exact+=1;answer.append(dict(index=index,name=case['name'],status='EXACT',
                     verification=checked,independent_rewrites=checks,independent_oracle=direct))
    return dict(source=str(path.relative_to(NIGHT)).replace('\\','/'),sha256=sha256(path.read_bytes()).hexdigest(),
       exact=exact,unknown=unknown,direct_assignments=assignments,wide_whole_sum_norms=wide,
       independent_rewrite_norms=rewrites,closed_norm_block_checks=norm_pairs,cases=answer)


def capacity_review():
    module=load('reviewed_capacity',NIGHT/'affine_sum_capacity_lab'/'capacity.py')
    rows=[]
    for n in range(65):
        product=(1<<n)
        for i in range(n):product*=1+(1<<i)
        observed=module.dictionary_count(n)
        assert observed==product==module.dictionary_product(n)
        result=module.existence_bound(n)
        k=result['some_boolean_function_requires_at_least']-1
        assert k*result['per_piece_exponent_bound']<(1<<n)
        rows.append(result)
    return dict(verdict='no defect found',exact_product_checks=len(rows),rows=rows)


def run():
    before=hashes()
    report=dict(format='independent-affine-compression-review-v1',
                timestamp_utc=datetime.now(timezone.utc).isoformat(),
                source_hashes_before=before)
    report['rule_controls']=rule_controls()
    report['original_compact_sums']=sum_requests()
    report['semantic_and_source_mutations']=mutation_controls()
    report['explicit_nonconfluence_schedules']=nonconfluence_schedules()
    report['actual_streaming_nonconfluence']=actual_nonconfluence()
    report['original_factor_requests']=dag_requests()
    report['saved_compression_replay']=replay_saved_compression()
    report['saved_dag_replay']=replay_saved_dag()
    report['capacity_review']=capacity_review()
    after=hashes();assert before==after,'a reviewed source changed during the run'
    report['source_hashes_after']=after;report['source_unchanged_during_run']=True
    (HERE/'RESULTS.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    summary={key:{k:v for k,v in report[key].items() if k not in ('cases','rows','mutations')}
             for key in ('original_compact_sums','semantic_and_source_mutations','original_factor_requests','saved_compression_replay','saved_dag_replay','capacity_review')}
    print(json.dumps(summary,indent=2))


if __name__=='__main__':run()
