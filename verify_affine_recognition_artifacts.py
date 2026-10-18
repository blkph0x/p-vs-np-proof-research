"""Bind saved recognition evidence; do not claim fresh expensive proof replay.

Fresh checks: every recorded source hash, all 80 compressed original artifacts,
original occurrence bindings, status coverage, saved statistics arithmetic,
review-to-result coverage, and final test-summary consistency. Mathematical
proof replay is delegated explicitly to the source-bound independent reviews.
"""
from collections import Counter
from datetime import datetime,timezone
import gzip
from hashlib import sha256
import json
from pathlib import Path
import time

HERE=Path(__file__).resolve().parent
CHECKPOINT=HERE.parent
BOUND={}
REFERENCES=0


def require(condition,reason):
    if not condition:raise RuntimeError(reason)


def file_hash(path):
    digest=sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda:stream.read(1<<20),b''):digest.update(chunk)
    return digest.hexdigest()


def bind(path,expected=None):
    global REFERENCES
    path=path.resolve()
    require(path.is_relative_to(CHECKPOINT),'artifact path escapes checkpoint')
    require(path.is_file(),'required artifact missing: '+str(path))
    actual=file_hash(path)
    if expected is not None:
        require(type(expected) is str and actual==expected,'recorded hash mismatch: '+str(path))
        REFERENCES+=1
    if path in BOUND:require(BOUND[path]==actual,'file changed while audit was running: '+str(path))
    BOUND[path]=actual
    return actual


def record(relative,base=None):
    path=HERE/relative;bind(path)
    data=json.loads(path.read_text(encoding='utf-8'))
    base=HERE if base is None else HERE/base
    maps=[]
    if 'source_hashes_before' in data:
        require(data['source_hashes_before']==data['source_hashes_after'],'source snapshots disagree: '+relative)
        maps.append(data['source_hashes_after'])
    for key in ('source_sha256','implementation_sha256'):
        if key in data:maps.append(data[key])
    for mapping in maps:
        require(type(mapping) is dict and mapping,'missing source map: '+relative)
        for name,expected in mapping.items():bind(base/name,expected)
    for flag in ('source_unchanged','source_unchanged_during_run','sources_unchanged_during_run',
                 'source_unchanged_during_tests','sources_unchanged_during_review','source_unchanged_during_review'):
        if flag in data:require(data[flag] is True,'unstable recorded run: '+relative)
    return data


def nonnegative_stats(stats,label):
    require(type(stats) is dict,label+' lacks statistics')
    require(all(type(value) is int and value>=0 for value in stats.values()),label+' has invalid operation counts')


def original_hash(n,clauses):
    digest=sha256(b'xor3-occurrence-grouping-v1\0')
    for value in [n,len(clauses),*(item for clause in clauses for item in (len(clause),*clause))]:
        require(type(value) is int,'original formula contains noninteger metadata')
        raw=abs(value).to_bytes(max(1,(abs(value).bit_length()+7)//8),'big')
        digest.update(bytes([value<0])+len(raw).to_bytes(8,'big')+raw)
    return digest.hexdigest()


def affine_request_hash(value):
    """Independent implementation of the documented typed request binding."""
    digest=sha256(b'affine-partition-recognition-v1')
    def emit(item):
        if type(item) is int:
            raw=abs(item).to_bytes(max(1,(abs(item).bit_length()+7)//8),'little')
            digest.update(b'i'+bytes([item<0])+len(raw).to_bytes(8,'little')+raw)
        elif type(item) is bool:digest.update(b't' if item else b'f')
        elif type(item) is str:
            raw=item.encode();digest.update(b's'+len(raw).to_bytes(8,'little')+raw)
        elif type(item) is list:
            digest.update(b'l');emit(len(item))
            for child in item:emit(child)
        elif type(item) is dict:
            digest.update(b'd');emit(len(item))
            for key in sorted(item):emit(key);emit(item[key])
        else:raise RuntimeError('unrecognized typed request value')
    emit(value)
    return digest.hexdigest()


def grouping():
    folder='affine_grouping_plan_lab'
    data=record(folder+'/RESULTS.json',folder)
    review=record(folder+'/INDEPENDENT_REVIEW.json',folder)
    bind(HERE/folder/'RESULTS.md');bind(HERE/folder/'INDEPENDENT_REVIEW.md')
    rows=data['cases'];review_rows=review['cases']
    require(len(rows)==len(review_rows)==review['gzip_original_artifacts']==80,'grouping case coverage')
    require(len({(row['dataset'],row['name']) for row in rows})==80,'duplicate grouping request identity')
    summary={key:Counter() for key in ('stress22','original58')}
    work=Counter();new=[];regressions=[];artifacts={};blocks=occurrences=0
    for row,replayed in zip(rows,review_rows):
        path=HERE/folder/row['artifact']
        actual=bind(path,row['artifact_sha256']);artifacts[row['artifact']]=actual
        require(review['artifact_sha256'].get(row['artifact'])==actual,'grouping review artifact mismatch')
        with gzip.open(path,'rt',encoding='utf-8') as stream:full=json.load(stream)
        request=full['original_request'];proposal=full['proposal'];planned=full['plan_verification']
        result=full['result'];verified=full['verification']
        for key in ('dataset','name','n','expected_count','previous_status','previous_certified',
                    'reference_artifact','reference_case_index'):
            require(request[key]==row[key],'original/summary mismatch: '+key)
        require(len(request['clauses'])==row['clauses'],'original clause count')
        digest=original_hash(request['n'],request['clauses'])
        require(digest==row['original_input_sha256']==proposal['input_sha256']==proposal['certificate']['input_sha256'],
                'original occurrence binding')
        require(proposal['status']=='EXACT' and planned['valid'] is True and planned['status']=='VERIFIED','grouping proposal status')
        order=planned['order']
        require(all(type(i) is int for i in order) and sorted(order)==list(range(row['clauses'])),'original occurrence permutation')
        require(order==proposal['order']==proposal['certificate']['order'],'recorded order mismatch')
        count_blocks=len(proposal['certificate']['groups']);blocks+=count_blocks;occurrences+=len(order)
        require(proposal['stats']['blocks']==planned['stats']['blocks']==replayed['blocks']==count_blocks,'block statistics')
        certified=bool(result['status']=='EXACT' and verified and verified['valid'] is True)
        status='VERIFIED_EXACT' if certified else ('VERIFICATION_UNKNOWN' if result['status']=='EXACT' else 'UNKNOWN')
        require(row['status']==replayed['status']==status and full['certified_exact'] is certified,'grouping status coverage')
        require((replayed['dataset'],replayed['name'])==(row['dataset'],row['name']),'review original identity')
        require(replayed['independently_verified_original_occurrences']==len(order),'review original occurrence coverage')
        if certified:
            require(result['count']==row['count']==request['expected_count'],'grouping original count')
            require(verified['status']=='VERIFIED' and verified['value']==result['value'],'saved solver replay result')
        else:
            require(result['status']=='UNKNOWN' and result['count'] is None and result['certificate'] is None
                    and verified is None,'UNKNOWN carries result claim')
        for key,nested in [('planner_stats',proposal['stats']),('planner_verification_stats',planned['stats']),
                           ('solver_stats',result['stats']),('verification_stats',verified['stats'] if verified else None)]:
            require(row[key]==nested,'summary statistics mismatch: '+key)
            if nested is not None:nonnegative_stats(nested,key)
        require(replayed['fresh_planner_verifier_stats']==planned['stats'],'bound planner replay counts')
        require(replayed['fresh_solver_verifier_stats']==(verified['stats'] if verified else None),'bound solver replay counts')
        planning=proposal['stats']['work']+planned['stats']['work']
        total=planning+result['stats']['work'];with_replay=total+(verified['stats']['work'] if verified else 0)
        for key,value in [('planning_work',planning),('planner_plus_solver_work',total),('total_work_including_solver_replay',with_replay)]:
            require(full[key]==row[key]==value,'pipeline work arithmetic: '+key);work[key]+=value
        alignment=full['completed_tree_alignment']
        require(alignment==row['completed_tree_alignment']==replayed['completed_tree_alignment'],'tree alignment record')
        if alignment:
            require(alignment['groups']==count_blocks and alignment['exact_factor_subtrees']+alignment['not_exact_factor_subtrees']==count_blocks,
                    'tree alignment arithmetic')
        is_new=certified and not request['previous_certified'];is_regression=request['previous_certified'] and not certified
        require(row['newly_certified'] is is_new and row['certification_regression'] is is_regression,'improvement classification')
        if is_new:new.append(row['name'])
        if is_regression:regressions.append(row['name'])
        summary[row['dataset']][status]+=1
    summary={name:dict(values) for name,values in summary.items()}
    require(summary==data['summary']==review['summary'],'grouping summary totals')
    require(new==data['newly_certified']==review['newly_certified'],'newly certified coverage')
    require(regressions==data['certification_regressions']==review['certification_regressions'],'regression coverage')
    require(blocks==review['complete_blocks_checked'] and occurrences==review['original_occurrence_permutation_entries'],'review occurrence totals')
    require(review['local_original_truth_patterns_checked']==8*blocks,'review block truth pattern arithmetic')
    require(set(artifacts)==set(review['artifact_sha256']),'gzip review coverage')
    return dict(summary=summary,original_artifacts=80,gzip_sha256=artifacts,
                original_occurrences=occurrences,complete_blocks=blocks,newly_certified=new,
                regressions=regressions,total_operation_counters=dict(work),
                delegated_solver_proofs=sum(row['status']=='VERIFIED_EXACT' for row in rows),
                proof_replay_record=folder+'/INDEPENDENT_REVIEW.json')


def partition():
    folder='affine_partition_compression_lab'
    data=record(folder+'/RESULTS.json');review=record(folder+'/INDEPENDENT_REVIEW.json')
    bind(HERE/folder/'INDEPENDENT_REVIEW.md')
    cases=sum((data[key] for key in ('named_controls','all_three_bit_affine_partitions',
             'all_three_bit_sign_tables','seeded_partitions')),[])
    statuses=Counter(case['result']['status'] for case in cases)
    totals=dict(statuses,cases=len(cases),direct_assignments=sum(case.get('direct_oracle',{}).get('assignments',0) for case in cases),
                norm_certificates=sum('norm_certificate' in case for case in cases),
                norm_block_checks=sum(case.get('norm_certificate',{}).get('block_checks',0) for case in cases),
                rejected_mutations=len(data['mutations']))
    require(totals==data['totals'],'partition totals arithmetic')
    for case in cases:
        result=case['result'];nonnegative_stats(result['stats'],'partition')
        if result['status']=='EXACT':
            require(case['verification']['valid'] is True,'partition saved proof replay')
            request=case['original_request']
            require(result['certificate']['input_sha256']==affine_request_hash({key:request[key] for key in ('n','retained','messages')}),
                    'partition original request binding')
        else:require(result['message'] is None and result['certificate'] is None,'partition failed claim')
    rt=review['totals']
    require(rt['saved_cases']==len(cases) and all(rt[s]==v for s,v in statuses.items()),'partition review coverage')
    require(rt['exact_certificates_replayed']==statuses['EXACT'],'partition exact replay coverage')
    require(rt['saved_norms_replayed']==totals['norm_certificates'] and rt['saved_norm_products']==totals['norm_block_checks'],
            'partition norm review coverage')
    small=[case for case in cases if len(case['original_request']['retained'])<=8 and case['result']['status']!='UNKNOWN']
    require(rt['independent_status_classifications']==len(small),'partition small classification coverage')
    require(rt['original_assignments']==sum(1<<len(case['original_request']['retained']) for case in small),'partition truth count')
    require(sum(review['unsupported_reason_checks'].values())==statuses['UNSUPPORTED'],'partition rejection reason coverage')
    require(rt['additional_cases']==len(review['additional_cases']) and
            rt['additional_EXACT']+rt['additional_UNSUPPORTED']==rt['additional_cases'],'partition additional statuses')
    require(rt['additional_assignments']==sum(1<<len(case['original_request']['retained']) for case in review['additional_cases']),
            'partition additional truth count')
    require(review['resource_cap_repair']['after_core_sha256']==bind(HERE/folder/'partition.py'),'partition repaired core binding')
    require(all(m['verification']['status']=='INVALID' for m in data['mutations']),'partition mutation verdicts')
    return dict(totals=totals,delegated_review_counts=rt,proof_replay_record=folder+'/INDEPENDENT_REVIEW.json',
                resolved_cap_repair=review['resource_cap_repair'])


def design_review():
    data=record('AFFINE_ONE_PIECE_RECOGNITION_REVIEW.json')
    cases=data['cases']+data['named_controls']
    counts=Counter(case['review']['status'] for case in cases)
    require(len(cases)==data['requests'] and dict(counts)==data['statuses'],'design review coverage')
    require(sum(1<<case['n'] for case in cases)==data['original_truth_words'],'design truth count')
    require(sum(case['review']['queries'] for case in cases)==data['restricted_and_final_norm_queries'],'design norm query count')
    require(sum(case['review']['pair_contractions'] for case in cases)==data['explicit_pair_contractions'],'design pair count')
    return {key:data[key] for key in ('requests','statuses','original_truth_words','restricted_and_final_norm_queries','explicit_pair_contractions','scope')}


def decision_review():
    data=record('COUNTING_VS_DECISION_AUDIT.json');review=record('COUNTING_VS_DECISION_REVIEW.json')
    require(len(data['cases'])==len(review['saved_original_requests'])==4,'decision original coverage')
    for original,checked in zip(data['cases'],review['saved_original_requests']):
        require(original['name']==checked['name'] and original['n']==checked['n'] and len(original['clauses'])==checked['clauses'],
                'decision original identity')
        require(original['counting_status']==checked['counting_status']=='UNKNOWN','decision/counting distinction')
        require(original['decision_result']['status']==checked['decision_status'] and checked['original_witness_or_unit_proof_checked'] is True,
                'decision review claim binding')
    require(review['saved_original_literal_occurrences']==sum(len(c) for row in data['cases'] for c in row['clauses']),'decision literal count')
    require(review['total_original_formulas']==review['exhaustive_two_variable_formulas']+review['seeded_original_formulas']==sum(review['probe_statuses'].values()),
            'decision probe status arithmetic')
    require(review['unit_proof_mutations']==review['valid_alternative_unit_proofs']+review['rejected_unit_proof_variants'],
            'decision mutation arithmetic')
    return dict(originals=review['saved_original_requests'],small_formulas=review['total_original_formulas'],
                statuses=review['probe_statuses'],unit_proof_mutations=review['unit_proof_mutations'],
                proof_replay_record='COUNTING_VS_DECISION_REVIEW.json',scope=review['scope'])


def limits_review():
    data=record('AFFINE_RECOGNITION_LIMITS.json');review=record('AFFINE_RECOGNITION_LIMITS_REVIEW.json')
    require([row['n'] for row in data['cases']]==[row['n'] for row in review['cases']]==[3,16,64],'limits width coverage')
    require(review['totals']['cases']==len(data['cases'])==3,'limits case totals')
    for case,checked in zip(data['cases'],review['cases']):
        require(len(case['local_compression']['messages'])==checked['local_output_pieces']==5,'limits local count')
        require(case['minimum_piece_count']==checked['verified_minimum_pieces']==2,'limits minimum count')
        require(checked['compression_verification']['valid'] is True and checked['norm_verification']['valid'] is True
                and checked['norm_verification']['equal'] is True,'limits replay verdict')
        require(checked['norm_products']==case['equality_norm']['block_checks'],'limits norm count')
    require(sum(row['norm_products'] for row in review['cases'])==review['totals']['norm_products']==84,'limits norm arithmetic')
    require(sum(row['relevant_truth_words'] for row in review['cases'])==review['totals']['relevant_truth_words']==24,'limits truth count')
    return dict(totals=review['totals'],proof_replay_record='AFFINE_RECOGNITION_LIMITS_REVIEW.json',scope=review['scope'])


def strong_recognition():
    # Missing producer or independent-review records prevent VERIFIED.
    data=record('affine_one_piece_lab/RESULTS.json')
    review=record('affine_one_piece_lab/INDEPENDENT_REVIEW.json')
    bind(HERE/'affine_one_piece_lab/INDEPENDENT_REVIEW.md')
    cases=sum((data[key] for key in ('named_controls','all_small_ternary_tables',
             'all_three_bit_sign_tables','seeded_explicit_sums')),[])
    statuses=Counter(case['result']['status'] for case in cases)
    totals=dict(statuses,cases=len(cases),direct_truth_values=sum(len(case.get('independent_truth_values',[])) for case in cases),
                verified_obstructions=sum(case['result']['status']=='UNSUPPORTED' and case['verification']['valid'] for case in cases),
                rejected_mutations=len(data['mutations']),
                producer_norm_queries=sum(case['result']['stats']['norm_queries'] for case in cases),
                producer_pair_contractions=sum(case['result']['stats']['pair_contractions'] for case in cases),
                checker_pair_contractions=sum(case.get('verification',{}).get('stats',{}).get('pair_contractions',0) for case in cases))
    require(totals==data['totals'],'strong recognition totals arithmetic')
    for case in cases:
        result=case['result'];request=case['original_request']
        nonnegative_stats(result['stats'],'strong recognizer')
        if result['status']=='UNKNOWN':
            require(result['message'] is None and result['certificate'] is None,'strong UNKNOWN carries a claim')
            continue
        require(case['verification']['valid'] is True,'strong saved proof replay verdict')
        require(result['certificate']['input_sha256']==affine_request_hash(dict(format='explicit-one-piece-v1',
                **{key:request[key] for key in ('n','retained','messages')})),'strong original request binding')
        if result['status']=='UNSUPPORTED':require(result['message'] is None,'strong negative claim carries message')
        else:require(result['message'] is not None,'strong positive claim lacks message')
        if 'independent_truth_values' in case:
            require(len(case['independent_truth_values'])==1<<len(request['retained']),'strong truth-table length')
            require(case['independent_classification'] is (result['status']=='EXACT'),'strong saved direct classification')
    require(all(row['verification']['status']=='INVALID' for row in data['mutations']),'strong mutation verdicts')
    replay=review['saved_claim_replay']
    require(replay['requests']==len(cases)==len(replay['cases']) and replay['statuses']==dict(statuses),'strong review claim coverage')
    require(replay['original_truth_values']==totals['direct_truth_values'],'strong independent truth coverage')
    wide=0
    for index,(case,checked) in enumerate(zip(cases,replay['cases'])):
        request=case['original_request'];result=case['result']
        require(checked['name']==request.get('name','saved_'+str(index).zfill(3)) and checked['status']==result['status'],
                'strong saved/review request identity')
        if result['status']=='UNKNOWN':continue
        require(checked['kind']==result['certificate']['kind'] and checked['fresh_verifier_stats']==case['verification']['stats'],
                'strong delegated proof replay statistics')
        if 'independent_classification' in checked:
            require(checked['original_truth_words']==len(case['independent_truth_values']),'strong classification word count')
            require((checked['independent_classification']['classification']!='NOT_ONE_PIECE')==(result['status']=='EXACT'),
                    'strong independent classification status')
        if 'independent_ordered_pair_norm_products' in checked:
            require(result['status']=='EXACT' and len(request['retained'])>8 and checked['independent_ordered_pair_norm_products']>0,
                    'strong wide norm coverage');wide+=1
    require(wide==replay['independent_wide_norms'],'strong wide norm arithmetic')
    own=review['independent_originals'];previous=review['earlier_compression_originals']
    for label,section in [('independent',own),('earlier',previous)]:
        require(section['requests']==len(section['cases']) and section['statuses']==dict(Counter(row['status'] for row in section['cases'])),
                'strong '+label+' review coverage')
        for row in section['cases']:
            nonnegative_stats(row['producer_stats'],'strong '+label+' producer statistics')
            if row['status']!='UNKNOWN':nonnegative_stats(row['fresh_verifier_stats'],'strong '+label+' checker statistics')
    require(own['original_truth_words']==sum(row['original_truth_words'] for row in own['cases']),
            'strong independent truth arithmetic')
    require(all((row['independent_classification']['classification']!='NOT_ONE_PIECE')==(row['status']=='EXACT') for row in own['cases']),
            'strong independent classifications')
    previous_originals=json.loads((HERE/'affine_sum_compression_lab/RESULTS.json').read_text(encoding='utf-8'))['controls']
    require([row['name'] for row in previous['cases']]==[row['name'] for row in previous_originals],
            'earlier compression original coverage')
    require(review['adversarial_mutations']['rejected']==len(review['adversarial_mutations']['cases']),
            'strong mutation arithmetic')
    require(review['checker_discovery_disabled'] is True and review['huge_dimension_guard'] is True,'strong checker/guard controls')
    for control in review['critical_failed_fast_candidate_caps']:
        require(control['result']['status']=='UNKNOWN' and control['result']['message'] is None and control['result']['certificate'] is None,
                'failed fast candidate cap incorrectly decides')
    limits=review['minimum_two_whole_sum_controls']
    require([row['n'] for row in limits]==[3,16,64] and all(row['status'] in ('UNSUPPORTED','UNKNOWN') for row in limits),
            'strong whole-sum minimum-two controls')
    return dict(totals=totals,delegated_saved_proofs=statuses['EXACT']+statuses['UNSUPPORTED'],
                independent_wide_norms=wide,independent_requests=own['requests'],independent_statuses=own['statuses'],
                independent_truth_words=own['original_truth_words'],rejected_mutations=review['adversarial_mutations']['rejected'],
                earlier_compression_requests=previous['requests'],earlier_compression_statuses=previous['statuses'],
                minimum_two_statuses=[row['status'] for row in limits],proof_replay_record='affine_one_piece_lab/INDEPENDENT_REVIEW.json',
                scope=review['scope'])


def tests():
    data=record('AFFINE_RECOGNITION_TEST_SUMMARY.json')
    bind(HERE/'AFFINE_RECOGNITION_TEST_OUTPUT.txt')
    require(data['all_tests_passed'] is True and data['source_unchanged_during_tests'] is True,'final test summary not passing/stable')
    require(data['suite_count']==len(data['suites']) and data['test_count']==sum(row['test_count'] for row in data['suites']),
            'final test count arithmetic')
    require(all(row['passed'] is True and row['returncode']==0 for row in data['suites']),'individual test suite failed')
    return dict(suites=data['suite_count'],tests=data['test_count'],all_passed=True,
                execution_record='AFFINE_RECOGNITION_TEST_SUMMARY.json',fresh_execution_by_this_auditor=False)


def main():
    started=time.perf_counter();bind(Path(__file__))
    sections=dict(grouping=grouping(),partition=partition(),design_review=design_review(),
                  decision_review=decision_review(),limits_review=limits_review(),
                  strong_recognition=strong_recognition(),tests=tests())
    before=dict(BOUND)
    for path,expected in before.items():require(file_hash(path)==expected,'file changed during audit: '+str(path))
    output=dict(status='VERIFIED_ARTIFACT_BINDINGS',timestamp_utc=datetime.now(timezone.utc).isoformat(),
                source_unchanged_during_audit=True,recorded_hash_references_checked=REFERENCES,
                unique_bound_files=len(before),hash_path_base='canonical checkpoint: parent of this script directory',
                artifact_sha256={str(path.relative_to(CHECKPOINT)).replace('\\','/'):value
                  for path,value in sorted(before.items())},sections=sections,seconds=time.perf_counter()-started,
                scope='Fresh file/source hashes, original bindings, status coverage and saved arithmetic. Full mathematical proof replay and test execution are delegated to the explicitly bound independent review/test records; this audit does not repeat them or rerun solver search.')
    (HERE/'AFFINE_RECOGNITION_ARTIFACT_AUDIT.json').write_text(json.dumps(output,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({key:output[key] for key in ('status','recorded_hash_references_checked','unique_bound_files','seconds')},indent=2))


if __name__=='__main__':main()
