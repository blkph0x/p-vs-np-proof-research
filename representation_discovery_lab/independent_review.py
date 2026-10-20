"""Independent full-original replay; imports none of the producer modules."""
from __future__ import annotations
import hashlib
import json
from pathlib import Path

HERE=Path(__file__).resolve().parent
SOURCE_NAMES=['engine.py','run_experiment.py','gaussian_baseline.py','nonlinear_control.py',
              'independent_review.py','test_engine.py','test_baseline.py','test_nonlinear_control.py',
              'test_independent_review.py','REPORT.md']
FORMULAS={
    'local_count':'m - 1','clause_count':'4m - 3',
    'encoded_representation_bits':'9 + m*ceil(log2(m))',
    'exhaustive_replay_work':'(4m - 3)*2^(2m - 1)',
    'candidate_search_work':'(2^(m + 1) - 1)*2^m',
    'enumeration_discovery_work':'(4m - 3)*2^(2m - 1) + (2^(m + 1) - 1)*2^m'}


def require(condition,message):
    if not condition:raise AssertionError(message)


def source_sha256(path):
    """Replay the documented text-hash scheme without producer imports."""
    source=path.read_bytes().decode('utf-8')
    canonical=source.replace('\r\n','\n').replace('\r','\n').encode('utf-8')
    return hashlib.sha256(canonical).hexdigest()


def chain(m,order):
    previous=order[0];clauses=[]
    for offset,variable in enumerate(order[1:]):
        helper=m+offset;triple=(previous,variable,helper)
        # Exclude each odd assignment directly; no producer gadget template.
        for word in (1,2,4,7):
            clauses.append([-(v+1) if word>>j&1 else v+1 for j,v in enumerate(triple)])
        previous=helper
    clauses.append([-(previous+1)])
    return dict(shared=list(range(m)),local=list(range(m,2*m-1)),clauses=clauses)


def canonical_original(original):
    return dict(shared=list(original['shared']),local=list(original['local']),
                clauses=sorted(sorted(c) for c in original['clauses']))


def projection(original):
    shared=original['shared'];local=original['local'];clauses=original['clauses']
    ids=shared+local
    require(all(type(v) is int and v>=0 for v in ids) and len(set(ids))==len(ids),'invalid original variable IDs')
    require(all(type(lit) is int and lit!=0 and abs(lit)-1 in ids for c in clauses for lit in c),'invalid original literal')
    require(len(ids)<=16,'independent replay bound exceeded')
    bits=[0]*(1<<len(shared))
    for word in range(1<<len(ids)):
        values={v:(word>>i)&1 for i,v in enumerate(ids)}
        if all(any(values[abs(lit)-1]==int(lit>0) for lit in clause) for clause in clauses):
            bits[word&((1<<len(shared))-1)]=1
    return bits


def baseline_schedule(original):
    # Recompute the published loop-visit charge separately from semantics.
    # Gadget validity uses forbidden assignment masks, not local SAT evaluation.
    raw=original['clauses'];shared=original['shared']
    work=len(shared)+sum(1+len(c)+len(set(c)) for c in raw)
    unique={tuple(sorted(set(c),key=lambda x:(abs(x),x))) for c in raw if not any(-x in c for x in c)}
    work+=sum(1+len(c) for c in unique)
    units=[c[0] for c in unique if len(c)==1]
    unsupported=any(len(c) not in (1,3) for c in unique)
    groups={}
    for c in unique:
        if len(c)==3:groups.setdefault(tuple(sorted(abs(x)-1 for x in c)),[]).append(c)
    valid=[]
    for support,clauses in sorted(groups.items()):
        work+=1
        if len(clauses)!=4:
            unsupported=True;continue
        work+=8*(1+3+4*(1+3))
        forbidden={sum((1<<support.index(abs(lit)-1)) for lit in c if lit<0) for c in clauses}
        if forbidden=={1,2,4,7}:valid.append(support)
        else:unsupported=True
    if unsupported or len(units)!=1:return 'UNKNOWN',work,len(valid)
    known=set(shared);work+=len(shared);pending=valid[:]
    while pending:
        work+=1;next_pending=[];progress=False
        for equation in pending:
            work+=4;new=set(equation)-known
            if len(new)==1:
                known.update(new);work+=1;progress=True
            else:next_pending.append(equation)
        pending=next_pending
        if not progress:return 'UNKNOWN',work,len(valid)
    if abs(units[0])-1 not in known:return 'UNKNOWN',work,len(valid)
    return 'EXACT_AFFINE',work+len(shared),len(valid)


def check_baseline(original,result,actual):
    status,work,gadgets=baseline_schedule(original)
    require(result['status']==status,'baseline stopping status differs from covered structure')
    require(type(result['work']) is int and result['work']==work,'baseline scan charge differs')
    require(type(result['gadget_count']) is int and result['gadget_count']==gadgets,'baseline gadget coverage differs')
    support=result['support'];rhs=result['rhs'];width=len(original['shared'])
    require(isinstance(support,list) and all(type(i) is int and 0<=i<width for i in support)
            and support==sorted(set(support)),'malformed equation support')
    require(type(rhs) is int and rhs in (0,1),'malformed equation RHS')
    if status=='EXACT_AFFINE':
        claimed=[int(sum((word>>i)&1 for i in support)%2==rhs) for word in range(1<<width)]
        require(claimed==actual,'claimed equation differs from full original projection')
    else:
        require(support==[] and rhs==0,'UNKNOWN includes a relation claim')


def controls():
    base=chain(5,list(range(5)));blocks=[base['clauses'][4*i:4*i+4] for i in range(4)]
    reverse=list(reversed(blocks));duplicated=reverse[:1]+[blocks[0]]+reverse[1:]
    renamed=dict(shared=[8-v for v in base['shared']],local=[8-v for v in base['local']],
                 clauses=[[(1 if lit>0 else -1)*(9-(abs(lit)-1)) for lit in c] for c in base['clauses']])
    return dict(reordered_gadgets={**base,'clauses':sum(reverse,[])+base['clauses'][-1:]},
                duplicated_gadget={**base,'clauses':sum(duplicated,[])+base['clauses'][-1:]},
                renamed_all_variables=renamed,
                positive_unit={**base,'clauses':base['clauses'][:-1]+[[-base['clauses'][-1][0]]]},
                added_binary_clause={**base,'clauses':base['clauses']+[[1,2]]},
                added_empty_clause={**base,'clauses':base['clauses']+[[]]},
                duplicate_unit_and_tautology={**base,'clauses':base['clauses']+[base['clauses'][-1],[1,-1,2]]})


def review_payload(payload,check_hashes=True):
    require(payload['schema']=='representation_discovery_hidden_xor_v1','schema changed')
    require(payload['status']=='EXACT_BOUNDED_EXPERIMENT','status changed')
    require(payload['model']['operation_formulas']==FORMULAS,'symbolic schedule formulas changed')
    require(payload['source_unchanged_during_run'] is True,'unstable source record')
    require(payload['source_hash_scheme']=='sha256-utf8-lf-v1','unsupported source hash scheme')
    if check_hashes:
        require(payload['source_sha256']=={name:source_sha256(HERE/name) for name in SOURCE_NAMES},'stale source hash')
    expected_orders=[(m,order) for m in range(3,8) for order in [list(range(m)),list(reversed(range(m)))]]
    require(len(payload['records'])==len(expected_orders),'record coverage differs')
    assignments=exact=unknown=0
    for row,(m,order) in zip(payload['records'],expected_orders):
        require(type(row['shared_count']) is int and row['shared_count']==m
                and all(type(v) is int for v in row['permutation']) and row['permutation']==order,'family parameters changed')
        original=chain(m,order)
        require(canonical_original(row['original_input'])==canonical_original(original),'record original CNF differs')
        actual=projection(row['original_input']);assignments+=1<<(2*m-1)
        require(actual==row['projected_bits'],'saved original projection differs')
        require(row['clause_count']==4*m-3 and row['local_count']==m-1,'original input sizes differ')
        require(row['encoded_representation_bits']==9+m*(m-1).bit_length(),'label encoding differs')
        schedule=(4*m-3)*(1<<(2*m-1));candidate=((1<<(m+1))-1)*(1<<m)
        require(row['exhaustive_replay_work']==schedule and row['enumeration_discovery_work']==schedule+candidate,'symbolic schedule charge differs')
        check_baseline(original,row['linear_algebra_baseline'],actual);exact+=1
    expected_controls=controls()
    require(set(payload['controls'])==set(expected_controls),'control coverage differs')
    for name,original in expected_controls.items():
        row=payload['controls'][name]
        require(canonical_original(row['original_input'])==canonical_original(original),'control original CNF differs: '+name)
        require(row['shared']==original['shared'] and row['clause_count']==len(original['clauses']),'control metadata differs')
        actual=projection(row['original_input']);assignments+=1<<len(original['shared']+original['local'])
        require(row['projected_bits']==actual,'control projection differs')
        check_baseline(original,row,actual)
        exact+=row['status']=='EXACT_AFFINE';unknown+=row['status']=='UNKNOWN'
    nonlinear=payload['nonlinear_control'];original=dict(shared=[0,1,2],local=[],clauses=[[1,2],[1,3]])
    require(nonlinear['clauses']==original['clauses'],'nonlinear original changed')
    actual=projection(original);assignments+=8
    require(nonlinear['projected_bits']==actual,'nonlinear original projection differs')
    points={word for word,bit in enumerate(actual) if bit};anchor=min(points);translated={p^anchor for p in points}
    affine=all(a^b in translated for a in translated for b in translated)
    require(nonlinear['status']==('AFFINE' if affine else 'NOT_AFFINE'),'nonlinear classification differs')
    check_baseline(original,nonlinear['linear_algebra_baseline'],actual);unknown+=1
    return dict(independent_checks_passed=True,records=10,controls=7,nonlinear_originals=1,
                full_original_assignments=assignments,exact_equations_checked=exact,unknown_no_claim_checked=unknown,
                baseline_scan_charges_recomputed=18,source_hashes_current=check_hashes)


def main():
    print(json.dumps(review_payload(json.loads((HERE/'RESULTS.json').read_text(encoding='utf-8')))))


if __name__=='__main__':main()
