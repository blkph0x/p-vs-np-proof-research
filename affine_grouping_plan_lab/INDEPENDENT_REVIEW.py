"""Independent original-occurrence and saved-gzip proof replay.

Only INDEPENDENT_REVIEW.json is written. No planner/solver search result is
regenerated; the small deterministic planner is replayed for policy consistency.
"""
from collections import Counter
import copy
import gzip
from hashlib import sha256
import importlib.util
import json
from pathlib import Path
import sys
import time

HERE = Path(__file__).resolve().parent


def require(condition, why):
    if not condition: raise RuntimeError(why)


def digest(path):
    h=sha256()
    with path.open('rb') as stream:
        for part in iter(lambda:stream.read(1<<20),b''): h.update(part)
    return h.hexdigest()


def load(name,path):
    spec=importlib.util.spec_from_file_location('grouping_independent_'+name,HERE/path)
    module=importlib.util.module_from_spec(spec);sys.modules[spec.name]=module;spec.loader.exec_module(module)
    return module


def request_hash(n,clauses):
    h=sha256(b'xor3-occurrence-grouping-v1\0')
    for value in [n,len(clauses),*(v for clause in clauses for v in (len(clause),*clause))]:
        raw=abs(value).to_bytes(max(1,(abs(value).bit_length()+7)//8),'big')
        h.update(bytes([value<0])+len(raw).to_bytes(8,'big')+raw)
    return h.hexdigest()


def independently_check_order(n,clauses,proposal):
    certificate=proposal['certificate'];groups=certificate['groups'];used=set();order=[];truth_patterns=0
    require(proposal['input_sha256']==certificate['input_sha256']==request_hash(n,clauses),'original input binding mismatch')
    supports=[]
    for block in groups:
        support=block['support'];ids=block['occurrence_ids']
        require(len(support)==3 and support==sorted(set(support)),'block support mismatch')
        require(len(ids)==4 and len(set(ids))==4 and not used.intersection(ids),'duplicate original occurrence ownership')
        all_eligible={i for i,clause in enumerate(clauses) if len(clause)==3 and {abs(v)-1 for v in clause}==set(support)}
        require(set(ids)==all_eligible,'block omits or invents an eligible same-support occurrence')
        forbidden=[]
        for index in ids:
            require(type(index) is int and 0<=index<len(clauses),'invalid occurrence ID')
            clause=clauses[index]
            require(len(clause)==3 and len({abs(lit) for lit in clause})==3,'repeated variable in block')
            fails=[]
            for local_word in range(8):
                assignment={variable:(local_word>>j&1) for j,variable in enumerate(support)}
                if not any(assignment[abs(lit)-1]==int(lit>0) for lit in clause): fails.append(local_word)
            require(len(fails)==1,'clause does not exclude exactly one full-support assignment')
            forbidden.append(fails[0])
        require(forbidden==sorted(set(forbidden)) and len(forbidden)==4,'forbidden assignments incomplete, repeated or unordered')
        for word in range(8):
            assignment={variable:(word>>j&1) for j,variable in enumerate(support)}
            conjunction=all(any(assignment[abs(lit)-1]==int(lit>0) for lit in clauses[index]) for index in ids)
            require(conjunction==(word.bit_count()%2==block['rhs']),'original block truth table is not stated parity')
            truth_patterns+=1
        require({word.bit_count()%2 for word in forbidden}=={block['forbidden_parity']} and block['rhs']==1-block['forbidden_parity'],'parity metadata mismatch')
        supports.append(tuple(support));used.update(ids);order.extend(ids)
    require(supports==sorted(set(supports)),'block ordering is not canonical by original support')
    complement=[i for i in range(len(clauses)) if i not in used]
    require(certificate['ungrouped_ids']==complement,'ungrouped complement does not cover originals')
    order+=complement
    require(order==certificate['order']==proposal['order'] and sorted(order)==list(range(len(clauses))),'not an exact full original occurrence permutation')
    return dict(blocks=len(groups),truth_patterns=truth_patterns,grouped_occurrences=len(used),
                canonical_ordered_original_clauses=[clauses[i] for i in order])


def mutation_checks(planner):
    clauses=[[1,2,3],[1,-2,-3],[-1,2,-3],[-1,-2,3],[4]]
    plan=planner.plan(4,clauses);require(planner.verify_plan(4,clauses,plan)['valid'],'mutation base proposal invalid')
    changes=[lambda p:p['order'].pop(),lambda p:p['certificate']['order'].pop(),
             lambda p:p['certificate']['ungrouped_ids'].clear(),
             lambda p:p['certificate']['groups'][0]['occurrence_ids'].__setitem__(0,True),
             lambda p:p['certificate']['groups'][0]['occurrence_ids'].__setitem__(0,1),
             lambda p:p['certificate']['groups'][0]['support'].__setitem__(0,True),
             lambda p:p['certificate']['groups'][0].__setitem__('rhs',0),
             lambda p:p['certificate']['groups'][0].__setitem__('forbidden_parity',1),
             lambda p:p.__setitem__('input_sha256','0'*64)]
    rejected=0
    for edit in changes:
        altered=copy.deepcopy(plan);edit(altered)
        require(not planner.verify_plan(4,clauses,altered)['valid'],'corrupted planner claim accepted');rejected+=1
    # Even refreshing the digest cannot excuse omitting a new original clause.
    for extra in [[],clauses[0]]:
        original=clauses+[extra];altered=copy.deepcopy(plan)
        altered['input_sha256']=altered['certificate']['input_sha256']=request_hash(4,original)
        if extra:
            altered['certificate']['ungrouped_ids'].append(5)
            altered['certificate']['order'].append(5);altered['order'].append(5)
        require(not planner.verify_plan(4,original,altered)['valid'],'rehashed incomplete/duplicate bucket accepted');rejected+=1
    cap_count=0
    for caps in [{'max_variables':3},{'max_clauses':4},{'max_literals':12},{'max_blocks':0},{'max_work':0}]:
        answer=planner.plan(4,clauses,**caps)
        require(answer['status']=='UNKNOWN' and answer['order'] is None and answer['certificate'] is None,'planner cap exposed partial order')
        checked=planner.verify_plan(4,clauses,plan,**caps)
        require(checked['status']=='UNKNOWN' and not checked['valid'] and checked['order'] is None,'verifier cap exposed accepted order')
        cap_count+=1
    old=planner._discovery_buckets
    def forbidden(*args,**kwargs): raise RuntimeError('verifier invoked discovery')
    try:
        planner._discovery_buckets=forbidden
        require(planner.verify_plan(4,clauses,plan)['valid'],'independent checker depends on discovery')
    finally: planner._discovery_buckets=old
    return dict(rejected_mutations=rejected,producer_and_checker_unknown_caps=cap_count,checker_discovery_disabled=True)


def main():
    started=time.perf_counter();summary=json.loads((HERE/'RESULTS.json').read_text())
    require(summary['source_hashes_before']==summary['source_hashes_after'] and summary['sources_unchanged_during_run'] is True,'source run not frozen')
    files={name:digest(HERE/name) for name in summary['source_hashes_before']}
    require(files==summary['source_hashes_before'],'recorded source hashes are stale')
    for name in ['RESULTS.json','INDEPENDENT_REVIEW.py','INDEPENDENT_REVIEW.md']:files[name]=digest(HERE/name)
    planner=load('planner','planner.py');engine=load('solver','../compressed_affine_dag_lab/dag.py');controls=load('controls','../affine_compression_stress_lab/controls.py')
    references={'stress22':json.loads((HERE/'../affine_compression_stress_lab/RESULTS.json').read_text())['cases'],
                'original58':json.loads((HERE/'../AFFINE_COMPRESSION_CROSSCHECK.json').read_text())['cases']}
    outcomes={'stress22':Counter(),'original58':Counter()};records=[];new=[];regressions=[];seen=set();paired={};pairs=[]
    blocks=truth_patterns=permutation_entries=0;artifacts={}
    for index,row in enumerate(summary['cases']):
        path=(HERE/row['artifact']).resolve();require(path.is_relative_to(HERE/'certificates'),'artifact path escapes certificate directory')
        require(digest(path)==row['artifact_sha256'],'gzip artifact hash mismatch')
        artifacts[row['artifact']]=row['artifact_sha256']
        with gzip.open(path,'rt',encoding='utf-8') as stream:full=json.load(stream)
        original=full['original_request'];dataset=original['dataset'];name=original['name'];n=original['n'];clauses=original['clauses']
        require((dataset,name) not in seen,'duplicate original request');seen.add((dataset,name))
        require(row['dataset']==dataset and row['name']==name and row['n']==n and row['clauses']==len(clauses),'summary original input mismatch')
        require(original['reference_case_index']==row['reference_case_index'] and original['reference_artifact']==row['reference_artifact'],'reference metadata mismatch')
        source=references[dataset][original['reference_case_index']]
        if dataset=='stress22':
            source_original=source['original_request'];prior=source['compressed'];expected=controls.verify_control(source_original)
            require(original['original_reference']==source_original and original['reference_verification']==expected,'stress source-based original proof mismatch')
            source_count=expected['count'];prior_certified=prior['certified_exact']
        else:
            source_original=source;prior=source;source_count=source['expected_count'];prior_certified=bool(source['verification'] and source['verification']['valid'])
        require(n==source_original['n'] and clauses==source_original['clauses'] and original['caps']==source['caps'],'planner changed original source/caps')
        require(source_count==original['expected_count']==row['expected_count'],'reference original count mismatch')
        require(original['previous_status']==row['previous_status']==prior['result']['status'] and original['previous_certified']==row['previous_certified']==prior_certified and original['previous_stats']==prior['result']['stats'],'baseline status/statistics mismatch')
        proposal=full['proposal'];caps=full['planner_caps']
        require(caps==planner.LIMITS and planner.plan(n,clauses,**caps)==proposal,'deterministic planner replay changed')
        checked_plan=planner.verify_plan(n,clauses,proposal,**caps)
        require(checked_plan==full['plan_verification'] and checked_plan['valid'],'saved planner proof did not replay')
        independent=independently_check_order(n,clauses,proposal)
        blocks+=independent['blocks'];truth_patterns+=independent['truth_patterns'];permutation_entries+=len(clauses)
        require(request_hash(n,clauses)==row['original_input_sha256'],'summary input hash mismatch')
        result=full['result'];checked=None
        if result['status']=='EXACT':
            checked=engine.verify_formula(n,clauses,result,order=checked_plan['order'],**original['caps'])
            require(checked['status'] in ('VERIFIED','UNKNOWN') and checked==full['verification'],'saved solver proof replay changed')
            require(result['count']==source_count,'completed original count differs')
            certified=checked['valid']
            if certified:require(checked['value']==[source_count,1],'verified count mismatch')
            status='VERIFIED_EXACT' if certified else 'VERIFICATION_UNKNOWN'
            ownerships={frozenset(node['factor_ids']) for node in result['certificate']['nodes']}
            hits=sum(frozenset(group['occurrence_ids']) in ownerships for group in checked_plan['groups'])
            alignment=dict(groups=len(checked_plan['groups']),exact_factor_subtrees=hits,not_exact_factor_subtrees=len(checked_plan['groups'])-hits)
        else:
            require(result['status']=='UNKNOWN' and result['certificate'] is None and result['count'] is None and result['value'] is None and full['verification'] is None,'UNKNOWN exposed a count/proof')
            certified=False;status='UNKNOWN';alignment=None
        require(certified==full['certified_exact'] and status==row['status'],'summary certification status mismatch')
        require(alignment==full['completed_tree_alignment']==row['completed_tree_alignment'],'measured group/tree alignment mismatch')
        planning=proposal['stats']['work']+checked_plan['stats']['work'];solving=result['stats']['work'];verification=checked['stats']['work'] if checked else 0
        for key,value in [('planning_work',planning),('planner_plus_solver_work',planning+solving),('total_work_including_solver_replay',planning+solving+verification)]:
            require(full[key]==row[key]==value,'pipeline work omitted a stage: '+key)
        for key,value in [('planner_stats',proposal['stats']),('planner_verification_stats',checked_plan['stats']),('solver_stats',result['stats']),('verification_stats',checked['stats'] if checked else None)]:
            require(row[key]==value,'summary operation counters differ from full artifact')
        newly=certified and not prior_certified;regressed=prior_certified and not certified
        require(row['newly_certified']==newly and row['certification_regression']==regressed,'status comparison flag mismatch')
        if newly:new.append(name)
        if regressed:regressions.append(name)
        outcomes[dataset][status]+=1
        if dataset=='stress22' and source_original['kind']=='cubic_parity':
            key=(source_original['vertices'],tuple(source_original['charges']))
            ordered=independent['canonical_ordered_original_clauses']
            if key in paired:
                previous=paired[key]
                require(previous['ordered']==ordered and previous['status']==status and previous['count']==result.get('count'),'grouped/shuffled canonical original outputs disagree')
                pairs.append(dict(first=previous['name'],second=name,status=status,clauses=len(ordered),count=result.get('count')))
            else:paired[key]=dict(name=name,ordered=ordered,status=status,count=result.get('count'))
        records.append(dict(dataset=dataset,name=name,status=status,blocks=independent['blocks'],expected_count=source_count,
                            independently_verified_original_occurrences=len(clauses),completed_tree_alignment=alignment,
                            fresh_planner_verifier_stats=checked_plan['stats'],fresh_solver_verifier_stats=checked['stats'] if checked else None))
        if (index+1)%20==0:print('replayed '+str(index+1)+' original gzip artifacts',flush=True)
    require(len(records)==80 and len(pairs)==8,'incomplete original/pair coverage')
    require({key:dict(value) for key,value in outcomes.items()}==summary['summary'],'dataset summary mismatch')
    require(new==summary['newly_certified'] and regressions==summary['certification_regressions'],'saved improvements/regressions mismatch')
    require({key:sum(value.values()) for key,value in outcomes.items()}=={'stress22':22,'original58':58},'original dataset size mismatch')
    mutations=mutation_checks(planner)
    require(all(digest(HERE/name)==expected for name,expected in files.items()),'source changed during independent review')
    require(all(digest(HERE/name)==expected for name,expected in artifacts.items()),'gzip artifact changed during independent review')
    out=dict(verdict='CLEAN: original occurrences preserved and every saved stopping status replayed',source_sha256=files,
             recorded_source_references=len(summary['source_hashes_before']),source_unchanged_during_run=True,
             artifact_sha256=artifacts,gzip_original_artifacts=80,summary={k:dict(v) for k,v in outcomes.items()},
             complete_blocks_checked=blocks,local_original_truth_patterns_checked=truth_patterns,
             original_occurrence_permutation_entries=permutation_entries,canonical_grouped_shuffled_pairs=pairs,
             newly_certified=new,certification_regressions=regressions,adversarial_checks=mutations,cases=records,
             seconds=time.perf_counter()-started,
             scope='Planning is an occurrence-preserving order only. Frozen solver certificates are replayed with unchanged original caps; planning and replay work are additional. UNKNOWN is retained. No optimized-plan or general complexity claim.')
    (HERE/'INDEPENDENT_REVIEW.json').write_text(json.dumps(out,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({k:out[k] for k in ('verdict','gzip_original_artifacts','summary','complete_blocks_checked','local_original_truth_patterns_checked','original_occurrence_permutation_entries','newly_certified','certification_regressions','source_unchanged_during_run')}))


if __name__=='__main__':main()
