"""Independent bounded classification, adversarial checks and frozen-proof replay.

No producer code is used by the finite support/phase oracle below. Only the
review JSON is written; production and frozen result files remain unchanged.
"""
from fractions import Fraction
from collections import Counter
import copy
from hashlib import sha256
import importlib.util
from itertools import product
import json
from pathlib import Path
import random
import sys
import time

HERE=Path(__file__).resolve().parent
NIGHT=HERE.parent
PRODUCER_HASH='ee05d4fc52fec551e57bd61941786531c0ebdbbccaaae03abcecf5843231c248'
PARTITION_HASH='e5b27146e10c185fbd5fcbbbb33314c02e7653d2aa3421e2f50d8bdd9f8ae035'
PHASE_CAPS=dict(max_variables=128,max_pieces=32,max_work=3000000,max_norm_queries=200,
                max_pair_contractions=10000,max_point_evaluations=10000,max_certificate_products=20000)


def require(condition, explanation):
    if not condition:
        raise RuntimeError(explanation)


def scalar(value):
    return Fraction(*value) if type(value) in (list,tuple) else Fraction(value)


def point(message, word):
    if message['zero'] or any((word&mask).bit_count()%2 != rhs for mask,rhs in message['equations']):
        return Fraction(0)
    sign=sum((word&term)==term for term in message['phase'])%2
    return scalar(message['scalar'])*(-1 if sign else 1)


def original_values(n, retained, messages):
    require(len(retained)<=8,'independent truth-table review cap')
    require(len(set(retained))==len(retained) and all(type(i) is int and 0<=i<n for i in retained),'invalid original coordinate IDs')
    values=[]
    for local in range(1<<len(retained)):
        physical=sum(((local>>j)&1)<<i for j,i in enumerate(retained))
        values.append(sum((point(message,physical) for message in messages),Fraction(0)))
    return values


def classify_values(values):
    """Complete tiny oracle: direct support closure and full sign Mobius transform."""
    require(values and len(values)&(len(values)-1)==0,'truth-table dimension is not a power of two')
    support=[x for x,value in enumerate(values) if value]
    if not support:
        return dict(classification='ZERO',support_size=0,hull_size=0)
    anchor=support[0];directions={0}
    for x in support:
        delta=x^anchor
        directions|={old^delta for old in list(directions)}
    hull={anchor^x for x in directions}
    if hull!=set(support):
        return dict(classification='NOT_ONE_PIECE',reason='support is not affine',support_size=len(support),hull_size=len(hull))
    image=[0]
    for delta in sorted(directions):
        if delta not in image:
            image += [old^delta for old in image]
    coordinates=[anchor^x for x in image];coefficient=values[anchor]
    if any(abs(values[x])!=abs(coefficient) for x in support):
        return dict(classification='NOT_ONE_PIECE',reason='nonconstant magnitude',support_size=len(support),hull_size=len(hull))
    coefficients=[int(values[x]!=coefficient) for x in coordinates]
    d=len(image).bit_length()-1
    for bit in range(d):
        for mask in range(1<<d):
            if mask>>bit&1:
                coefficients[mask]^=coefficients[mask^(1<<bit)]
    degree=max((mask.bit_count() for mask,value in enumerate(coefficients) if value),default=0)
    return dict(classification='ONE_PIECE' if degree<=2 else 'NOT_ONE_PIECE',
                reason='quadratic sign' if degree<=2 else 'higher-degree sign',
                support_size=len(support),hull_size=len(hull),sign_degree=degree)


def direct_squared_norm(n, retained, left, right=()):
    a=original_values(n,retained,left);b=original_values(n,retained,right)
    return sum(((x-y)**2 for x,y in zip(a,b)),Fraction(0))


def axis_message(n, retained, pins=(), phase=(), coefficient=1):
    """Independent canonical fixture constructor: coordinate-aligned supports."""
    c=Fraction(coefficient);retained=list(retained)
    if not c:
        return dict(n=n,retained=retained,zero=True,equations=[],phase=[],scalar=[0,1],free_ids=[])
    prescribed=dict(pins);free=[i for i in retained if i not in prescribed]
    require(set(prescribed).issubset(retained),'fixture pin outside retained coordinates')
    require(all(type(v) is int and v in (0,1) for v in prescribed.values()),'fixture pin is not Boolean')
    allowed=sum(1<<i for i in free)
    require(all(type(term) is int and term>0 and term.bit_count()<=2 and not term&~allowed for term in phase),'fixture phase not canonical on free coordinates')
    return dict(n=n,retained=retained,zero=False,equations=[[1<<i,prescribed[i]] for i in retained if i in prescribed],
                phase=sorted(set(phase)),scalar=[c.numerator,c.denominator],free_ids=free)


def point_pin(n, retained, local_word, coefficient=1):
    return axis_message(n,retained,[(i,local_word>>j&1) for j,i in enumerate(retained)],coefficient=coefficient)


def independent_requests():
    """Small exhaustive and seeded original functions, not fitted candidates."""
    yield dict(name='gapped_zero_canonical_anchor',n=2,retained=[0,1],messages=[point_pin(2,[0,1],x) for x in (1,2,3)])
    yield dict(name='cubic_sign_full_support',n=3,retained=[0,1,2],messages=[point_pin(3,[0,1,2],x,-1 if x==7 else 1) for x in range(8)])
    yield dict(name='overlap_cancellation_halfspace',n=3,retained=[0,1,2],messages=[axis_message(3,[0,1,2]),axis_message(3,[0,1,2],[(0,0)],coefficient=-1)])
    yield dict(name='cancelled_outlier_smaller_hull',n=2,retained=[0,1],messages=[point_pin(2,[0,1],0),point_pin(2,[0,1],2),point_pin(2,[0,1],2,-1)])
    yield dict(name='cancellation_to_zero',n=3,retained=[0,1,2],messages=[axis_message(3,[0,1,2],phase=[3],coefficient=Fraction(2,7)),axis_message(3,[0,1,2],phase=[3],coefficient=Fraction(-2,7))])
    yield dict(name='gapped_support_with_outside_halfspace',n=5,retained=[4,1,0],messages=[point_pin(5,[4,1,0],x) for x in (2,4,6)])
    for index,values in enumerate(product((-1,0,1),repeat=4)):
        yield dict(name='ternary_two_bit_'+str(index),n=2,retained=[0,1],messages=[point_pin(2,[0,1],x,value) for x,value in enumerate(values) if value])
    for pattern in range(256):
        yield dict(name='three_bit_signs_'+str(pattern),n=3,retained=[0,1,2],messages=[point_pin(3,[0,1,2],x,-1 if pattern>>x&1 else 1) for x in range(8)])
    rng=random.Random(2026101923)
    for index in range(200):
        n=rng.randrange(7);retained=rng.sample(range(n),rng.randrange(n+1));messages=[]
        for _ in range(rng.randrange(9)):
            pins={i:rng.randrange(2) for i in retained if rng.randrange(3)==0}
            free=[i for i in retained if i not in pins]
            terms=[1<<i for i in free]+[(1<<i)|(1<<j) for i in free for j in free if i<j]
            phase=rng.sample(terms,rng.randrange(len(terms)+1))
            messages.append(axis_message(n,retained,pins.items(),phase,Fraction(rng.randrange(-3,4),rng.randrange(1,5))))
        yield dict(name='seeded_axis_'+str(index),n=n,retained=retained,messages=messages)


def semantic_proof_mutations(result):
    """Only changes known to invalidate the original typed certificate claim."""
    cert=result['certificate'];mutations=[]
    def add(label,edit):
        changed=copy.deepcopy(result);edit(changed);mutations.append((label,changed))
    add('wrong_original_binding',lambda r:r['certificate'].__setitem__('input_sha256','0'*64))
    add('wrong_root_norm',lambda r:r['certificate']['root_norm'].__setitem__('value',[-1,1]))
    if cert['root_norm']['products']:
        add('omitted_original_pair',lambda r:r['certificate']['root_norm']['products'].pop())
        add('duplicated_pair_id',lambda r:r['certificate']['root_norm']['products'][0].__setitem__('pair',[True,0]))
        add('wrong_closed_product_value',lambda r:r['certificate']['root_norm']['products'][0]['result']['message'].__setitem__('scalar',[17,1]))
    if cert.get('difference_norm'):
        add('wrong_difference_norm',lambda r:r['certificate']['difference_norm'].__setitem__('value',[-1,1]))
        add('lost_difference_pair',lambda r:r['certificate']['difference_norm']['products'].pop())
    if cert.get('points'):
        add('invalid_support_point',lambda r:r['certificate']['points'].__setitem__(0,True))
        add('duplicate_support_witness',lambda r:r['certificate']['points'].append(r['certificate']['points'][0]))
        add('wrong_hull_coefficient',lambda r:r['certificate']['hull'].__setitem__('scalar',[2,1]))
    if cert.get('outside_norms'):
        add('missing_hull_halfspace',lambda r:r['certificate']['outside_norms'].pop())
        add('wrong_hull_halfspace',lambda r:r['certificate']['outside_norms'][0].__setitem__('restriction',[]))
    if cert.get('samples'):
        add('wrong_sample_word',lambda r:r['certificate']['samples'][0].__setitem__('word',True))
        def wrong_sample(r):
            item=r['certificate']['samples'][0]['value'];item[0]+=item[1]
        add('wrong_sample_value',wrong_sample)
    if result['status']=='EXACT':
        add('wrong_reported_message',lambda r:r.__setitem__('message',None))
    else:
        add('negative_claim_with_message',lambda r:r.__setitem__('message',r['certificate']['hull']))
    return mutations


def digest(path):
    h=sha256()
    with path.open('rb') as stream:
        for data in iter(lambda:stream.read(1<<20),b''):h.update(data)
    return h.hexdigest()


def load(name,path):
    spec=importlib.util.spec_from_file_location('one_piece_independent_'+name,path)
    module=importlib.util.module_from_spec(spec);sys.modules[spec.name]=module;spec.loader.exec_module(module)
    return module


def complete_check(engine,request,result,caps=None):
    n,ids,messages=request['n'],request['retained'],request['messages']
    status=result['status']
    if status=='UNKNOWN':
        require(result['message'] is None and result['certificate'] is None,'UNKNOWN contains a representation claim')
        return dict(status=status,reason=result['reason'])
    require(status in ('EXACT','UNSUPPORTED'),'unexpected recognition status')
    checked=engine.verify_one_piece(n,ids,messages,result,**(caps or {}))
    require(checked['valid'] and checked['recognition']==status,'recognition proof failed: '+request['name']+' '+str(checked))
    record=dict(status=status,kind=result['certificate']['kind'],fresh_verifier_stats=checked['stats'])
    if len(ids)<=8:
        values=original_values(n,ids,messages);classification=classify_values(values)
        require((status=='EXACT')==(classification['classification']!='NOT_ONE_PIECE'),'false tiny representation decision: '+request['name'])
        if status=='EXACT':
            require(original_values(n,ids,[result['message']])==values,'incorrect exact output function')
        record['independent_classification']=classification;record['original_truth_words']=len(values)
    return record


def main():
    started=time.perf_counter();saved=json.loads((HERE/'RESULTS.json').read_text())
    require(saved['source_hashes_before']==saved['source_hashes_after'] and saved['source_unchanged_during_run'] is True,'author sources were not frozen')
    source_hashes={name:digest(NIGHT/name) for name in saved['source_hashes_before']}
    require(source_hashes==saved['source_hashes_before'],'stale author source hash')
    require(source_hashes['affine_one_piece_lab/one_piece.py']==PRODUCER_HASH and source_hashes['affine_partition_compression_lab/partition.py']==PARTITION_HASH,'unreviewed production revision')
    for name in ['affine_one_piece_lab/RESULTS.json','affine_one_piece_lab/INDEPENDENT_REVIEW.py',
                 'affine_one_piece_lab/INDEPENDENT_REVIEW.md','affine_sum_compression_lab/RESULTS.json',
                 'AFFINE_RECOGNITION_LIMITS.json']:
        source_hashes[name]=digest(NIGHT/name)
    engine=load('producer',HERE/'one_piece.py')
    norm_oracle=load('norm_oracle',NIGHT/'affine_compression_review'/'review_oracles.py')
    saved_rows=[r for key in ('named_controls','all_small_ternary_tables','all_three_bit_sign_tables','seeded_explicit_sums') for r in saved[key]]
    counts=Counter();replays=[];truth_words=wide_norms=0
    for index,row in enumerate(saved_rows):
        request=dict(row['original_request']);request.setdefault('name','saved_'+str(index).zfill(3))
        result=row['result'];caps=request.get('caps',{})
        checked=complete_check(engine,request,result,caps);counts[result['status']]+=1
        if result['status']!='UNKNOWN':
            require(row['verification']['valid'] and row['verification']['recognition']==result['status'],'saved verification outcome mismatch')
        if 'independent_classification' in checked:
            values=original_values(request['n'],request['retained'],request['messages'])
            require(row['independent_truth_values']==[[v.numerator,v.denominator] for v in values],'saved original truth values differ')
            require(row['independent_classification']==(checked['independent_classification']['classification']!='NOT_ONE_PIECE'),'author finite classification differs')
            truth_words+=len(values)
        if result['status']=='EXACT' and len(request['retained'])>8:
            independent=norm_oracle.norm_identity(request['n'],request['retained'],request['messages'],[result['message']],save_proofs=True)
            norm_check=norm_oracle.verify_norm_identity(request['n'],request['retained'],request['messages'],[result['message']],independent)
            require(norm_check['valid'] and norm_check['equal'],'independent wide ordered-pair norm disagrees')
            checked['independent_ordered_pair_norm_products']=independent['block_checks'];wide_norms+=1
        replays.append(dict(name=request['name'],**checked))
        if (index+1)%100==0:print('replayed '+str(index+1)+' saved recognition claims',flush=True)
    require(len(saved_rows)==494 and dict(counts)=={'EXACT':276,'UNSUPPORTED':210,'UNKNOWN':8},'saved claim coverage differs')
    require(truth_words==saved['totals']['direct_truth_values']==3230,'saved truth-value count differs')
    own=[];own_counts=Counter();own_words=0;mutation_bases=[];kinds=set()
    for index,request in enumerate(independent_requests()):
        result=engine.recognize(request['n'],request['retained'],request['messages'])
        require(result['status']!='UNKNOWN','small independent request unexpectedly capped')
        checked=complete_check(engine,request,result);own_counts[result['status']]+=1;own_words+=checked['original_truth_words']
        own.append(dict(original_request=request,**checked,producer_stats=result['stats']))
        kind=result['certificate']['kind']
        if index<6 or kind not in kinds:
            mutation_bases.append((request,result));kinds.add(kind)
        if (index+1)%100==0:print('classified '+str(index+1)+' independent original sums',flush=True)
    rejected=[]
    for request,result in mutation_bases:
        for name,forged in semantic_proof_mutations(result):
            checked=engine.verify_one_piece(request['n'],request['retained'],request['messages'],forged)
            require(checked['status']=='INVALID','invalid mutation not rejected: '+request['name']+'/'+name+' '+str(checked))
            rejected.append(dict(control=request['name'],mutation=name))
        # Hash refresh cannot excuse a changed original coefficient: norm pairs
        # are reconstructed from the external operands, not merely digest-matched.
        changed=copy.deepcopy(request['messages']);nonzero=next((m for m in changed if not m['zero']),None)
        if nonzero is not None:
            nonzero['scalar'][0]*=2
            forged=copy.deepcopy(result)
            forged['certificate']['input_sha256']=engine.partition.digest(dict(format='explicit-one-piece-v1',n=request['n'],retained=request['retained'],messages=changed))
            checked=engine.verify_one_piece(request['n'],request['retained'],changed,forged)
            require(checked['status']=='INVALID','rehashed changed original coefficient was accepted')
            rejected.append(dict(control=request['name'],mutation='rehashed_changed_original_coefficient'))
        zero=axis_message(request['n'],request['retained'],coefficient=0)
        require(engine.verify_one_piece(request['n'],request['retained'],request['messages']+[zero],result)['status']=='INVALID','omitted canonical zero original not source-bound')
        rejected.append(dict(control=request['name'],mutation='unbound_appended_zero_original'))
    # Verification must not call producer search, support discovery or norm production.
    old=(engine.recognize,engine.input_hull,engine.point_hull,engine.Norms.query)
    def forbidden(*args,**kwargs):raise RuntimeError('checker called producer discovery')
    try:
        engine.recognize=engine.input_hull=engine.point_hull=engine.Norms.query=forbidden
        for request,result in mutation_bases:
            require(engine.verify_one_piece(request['n'],request['retained'],request['messages'],result)['valid'],'verifier depended on discovery')
    finally:
        engine.recognize,engine.input_hull,engine.point_hull,engine.Norms.query=old
    critical=[]
    for request,caps in [(mutation_bases[0][0],dict(max_norm_queries=1)),(mutation_bases[1][0],dict(max_norm_queries=2))]:
        result=engine.recognize(request['n'],request['retained'],request['messages'],**caps)
        require(result['status']=='UNKNOWN' and result['message'] is None and result['certificate'] is None,'failed enclosing candidate caused false rejection under cap')
        critical.append(dict(name=request['name'],caps=caps,result=result))
    require(engine.recognize(10**9,[],[])['status']=='UNKNOWN','huge dimension was not guarded')
    first_request,first_result=mutation_bases[0]
    for cap in ['max_work','max_norm_queries','max_pair_contractions','max_certificate_products']:
        checked=engine.verify_one_piece(first_request['n'],first_request['retained'],first_request['messages'],first_result,**{cap:0})
        require(checked['status']=='UNKNOWN' and not checked['valid'] and checked['message'] is None,'verification cap produced a decision')
    # Explicit earlier compression originals, including wide/capped requests.
    phase=json.loads((NIGHT/'affine_sum_compression_lab'/'RESULTS.json').read_text());phase_counts=Counter();phase_rows=[]
    for row in phase['controls']:
        request=dict(name=row['name'],n=row['n'],retained=row['retained'],messages=row['originals'])
        result=engine.recognize(request['n'],request['retained'],request['messages'],**PHASE_CAPS)
        checked=complete_check(engine,request,result,PHASE_CAPS);phase_counts[result['status']]+=1
        phase_rows.append(dict(name=request['name'],**checked,producer_stats=result['stats']))
    limits=json.loads((NIGHT/'AFFINE_RECOGNITION_LIMITS.json').read_text());limit_rows=[]
    for row in limits['cases']:
        n,ids,messages=row['n'],row['retained'],row['originals']
        require(all(not p['phase'] and all(mask<8 for mask,rhs in p['equations']) for p in messages),'minimum-two control has unexpected high-coordinate dependence')
        values=original_values(n,[0,1,2],messages)
        require(values==[2,1,1,1,1,1,1,1] and classify_values(values)['classification']=='NOT_ONE_PIECE','minimum-two obstruction is not independently valid')
        result=engine.recognize(n,ids,messages,**PHASE_CAPS)
        require(result['status']!='EXACT','minimum-two whole sum accepted as one piece')
        checked=complete_check(engine,dict(name='minimum_two_'+str(n),n=n,retained=ids,messages=messages),result,PHASE_CAPS)
        limit_rows.append(dict(n=n,**checked,producer_stats=result['stats']))
    require(all(digest(NIGHT/name)==value for name,value in source_hashes.items()),'source or artifact changed during independent review')
    output=dict(verdict='CLEAN: exact equalities and complete one-piece obstructions independently checked',source_sha256=source_hashes,source_unchanged_during_run=True,
                saved_claim_replay=dict(requests=494,statuses=dict(counts),original_truth_values=truth_words,independent_wide_norms=wide_norms,cases=replays),
                independent_originals=dict(seed=2026101923,requests=len(own),statuses=dict(own_counts),original_truth_words=own_words,cases=own),
                adversarial_mutations=dict(rejected=len(rejected),cases=rejected),checker_discovery_disabled=True,
                critical_failed_fast_candidate_caps=critical,huge_dimension_guard=True,verification_unknown_cap_controls=4,
                earlier_compression_originals=dict(requests=len(phase_rows),caps=PHASE_CAPS,statuses=dict(phase_counts),cases=phase_rows),
                minimum_two_whole_sum_controls=limit_rows,seconds=time.perf_counter()-started,
                scope='Standalone recognition of an explicit canonical rational sum. Tiny classification is independent of producer discovery; wide equality uses a separate ordered-pair norm assembly over the frozen block checker. UNKNOWN remains unclaimed. No minimum-piece or succinct-SAT result is inferred.')
    (HERE/'INDEPENDENT_REVIEW.json').write_text(json.dumps(output,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(dict(verdict=output['verdict'],saved_statuses=dict(counts),independent_requests=len(own),independent_statuses=dict(own_counts),mutations_rejected=len(rejected),earlier_phase_statuses=dict(phase_counts),minimum_two_statuses=[r['status'] for r in limit_rows],source_unchanged=True)),flush=True)


if __name__=='__main__':main()
