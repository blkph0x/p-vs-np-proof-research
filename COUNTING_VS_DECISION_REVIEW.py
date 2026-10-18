"""Independent finite review of decision evidence; no source-result edits."""
import copy
from hashlib import sha256
import importlib.util
from itertools import product
import json
from pathlib import Path
import random
import time

HERE = Path(__file__).resolve().parent
SOURCES = ['counting_vs_decision_audit.py', 'COUNTING_VS_DECISION_AUDIT.json',
           'AFFINE_COMPRESSION_CROSSCHECK.json', 'COUNTING_VS_DECISION_REVIEW.py',
           'COUNTING_VS_DECISION_REVIEW.md']


def require(condition, description):
    if not condition: raise RuntimeError(description)


def hashes():
    return {name:sha256((HERE/name).read_bytes()).hexdigest() for name in SOURCES}


def original_witness(n, clauses, assignment):
    if type(assignment) is not list or len(assignment) != n or any(type(x) is not int or x not in (0,1) for x in assignment):
        return False
    positive = sum(bit << i for i,bit in enumerate(assignment))
    negative = ((1<<n)-1) ^ positive
    return all(any((positive if literal > 0 else negative) & (1 << (abs(literal)-1)) for literal in clause) for clause in clauses)


def unit_mask_check(n, clauses, proof):
    """Separate positive/negative masks, no clause residual sets or search."""
    if type(proof) is not dict or set(proof) != {'steps','conflict_clause'} or type(proof['steps']) is not list or len(proof['steps']) > n:
        return False
    masks = []
    for clause in clauses:
        pos = neg = 0
        for literal in clause:
            if literal > 0: pos |= 1 << (literal-1)
            else: neg |= 1 << (-literal-1)
        masks.append((pos,neg))
    ones = zeros = 0
    for step in proof['steps']:
        if type(step) is not dict or set(step) != {'clause','literal'}: return False
        index,lit = step['clause'],step['literal']
        if type(index) is not int or not 0 <= index < len(clauses) or type(lit) is not int or not 0 < abs(lit) <= n: return False
        bit = 1 << (abs(lit)-1)
        if bit & (ones|zeros): return False
        pos,neg = masks[index]
        if pos & ones or neg & zeros: return False
        if (pos|neg) & ~(ones|zeros) != bit: return False
        if bool(pos & bit) != (lit > 0) or bool(neg & bit) != (lit < 0): return False
        if lit > 0: ones |= bit
        else: zeros |= bit
    index = proof['conflict_clause']
    if type(index) is not int or not 0 <= index < len(clauses): return False
    pos,neg = masks[index]
    return not ((pos|neg) & ~(ones|zeros) or pos & ones or neg & zeros)


def proof_mutations(proof, n, m):
    for conflict in [-1,True,*range(m),m]:
        altered = copy.deepcopy(proof); altered['conflict_clause'] = conflict; yield altered
    for i,step in enumerate(proof['steps']):
        for literal in [True,0,*range(-n,0),*range(1,n+1)]:
            altered = copy.deepcopy(proof); altered['steps'][i]['literal'] = literal; yield altered
        for index in [-1,True,*range(m),m]:
            altered = copy.deepcopy(proof); altered['steps'][i]['clause'] = index; yield altered
        altered = copy.deepcopy(proof); del altered['steps'][i]; yield altered
        altered = copy.deepcopy(proof); altered['steps'].insert(i,copy.deepcopy(step)); yield altered
    altered = copy.deepcopy(proof); altered['steps'].reverse(); yield altered
    yield {'steps':None,'conflict_clause':0}
    yield {'steps':[],'conflict_clause':0,'invented':1}


def main():
    before = hashes(); started = time.perf_counter()
    spec = importlib.util.spec_from_file_location('independent_decision_probe',HERE/'counting_vs_decision_audit.py')
    probe = importlib.util.module_from_spec(spec); spec.loader.exec_module(probe)
    saved = json.loads((HERE/'COUNTING_VS_DECISION_AUDIT.json').read_text())
    counted = json.loads((HERE/'AFFINE_COMPRESSION_CROSSCHECK.json').read_text())
    for name,expected in saved['source_sha256'].items():
        require(sha256((HERE/name).read_bytes()).hexdigest() == expected,'stale probe provenance')
    require(saved['source_unchanged'] is True,'probe sources were not stable')
    unresolved = {r['name']:r for r in counted['cases'] if r['result']['status']=='UNKNOWN'}
    require(len(unresolved)==len(saved['cases'])==4,'original UNKNOWN coverage differs')
    rows = []; literal_occurrences = 0; witness_flips = 0
    for row in saved['cases']:
        original = unresolved[row['name']]
        require(row['n']==original['n'] and row['clauses']==original['clauses'] and row['expected_count']==original['expected_count'],'saved decision input differs')
        require(row['counting_status']=='UNKNOWN' and row['independently_verified'] is True,'saved status evidence differs')
        result = row['decision_result']; n,clauses=row['n'],row['clauses']
        require(probe.probe(n,clauses,**saved['caps'])==result,'bounded decision replay differs')
        if result['status']=='SAT':
            require(original_witness(n,clauses,result['assignment']),'saved witness violates an original clause')
            for i in range(n):
                changed=result['assignment'].copy();changed[i]^=1
                require(probe.verify_witness(n,clauses,changed)==original_witness(n,clauses,changed),'flipped witness verifier mismatch')
                witness_flips+=1
            require(row['expected_count']>0,'SAT witness conflicts with original reference count')
        else:
            require(result['status']=='UNSAT' and unit_mask_check(n,clauses,result['proof']),'saved unit contradiction fails independent replay')
            require(row['expected_count']==0,'unit contradiction conflicts with original reference count')
        literal_occurrences += sum(map(len,clauses))
        rows.append(dict(name=row['name'],n=n,clauses=len(clauses),counting_status='UNKNOWN',decision_status=result['status'],
                         original_witness_or_unit_proof_checked=True,recorded_search_stats=result['stats']))
    formulas = words = mutations = accepted_variants = rejected_variants = 0
    statuses = {'SAT':0,'UNSAT':0,'UNKNOWN':0}
    def check_formula(n,clauses,mutate=False):
        nonlocal formulas,words,mutations,accepted_variants,rejected_variants
        truth = False
        for assignment in product((0,1),repeat=n):
            truth |= original_witness(n,clauses,list(assignment));words+=1
        result=probe.probe(n,clauses);formulas+=1;statuses[result['status']]+=1
        if result['status']=='SAT': require(truth and original_witness(n,clauses,result['assignment']),'unsound SAT claim')
        elif result['status']=='UNSAT':
            require(not truth and unit_mask_check(n,clauses,result['proof']),'unsound UNSAT claim')
            if mutate:
                for altered in proof_mutations(result['proof'],n,len(clauses)):
                    expected=unit_mask_check(n,clauses,altered)
                    require(probe.verify_unit_contradiction(n,clauses,altered)==expected,'unit mutation checker disagreement')
                    require(not expected or not truth,'forged proof accepted for satisfiable original')
                    mutations+=1;accepted_variants+=expected;rejected_variants+=not expected
        else:
            require(result['assignment'] is None and result['proof'] is None,'UNKNOWN contains a claim')
    atoms=[[],[1],[-1],[2],[-2],[1,2],[1,-2],[-1,2],[-1,-2]]
    for mask in range(512): check_formula(2,[c for i,c in enumerate(atoms) if mask>>i&1],True)
    rng=random.Random(2026101917)
    for _ in range(300):
        n=rng.randrange(7)
        clauses=[[rng.choice((-1,1))*rng.randrange(1,n+1) for _ in range(rng.randrange(5))] if n else []
                 for _ in range(rng.randrange(10))]
        check_formula(n,clauses,True)
    # Branch exhaustion on a non-unit unsatisfiable formula must not export UNSAT.
    branched_unsat=[[1,2],[1,-2],[-1,2],[-1,-2]]
    require(probe.probe(2,branched_unsat)['status']=='UNKNOWN','unexported branching refutation became a claim')
    for n,clauses,limits in [(2,[[1,2]],{'max_nodes':0}),(1,[[1]],{'max_literal_visits':0})]:
        result=probe.probe(n,clauses,**limits)
        require(result['status']=='UNKNOWN' and result['assignment'] is None and result['proof'] is None,'resource exhaustion exported a claim')
    invalid_controls=[
        (2,[[1],[-1,2],[-2]],{'steps':[{'clause':1,'literal':2}],'conflict_clause':2}),
        (1,[[1]],{'steps':[{'clause':0,'literal':1}],'conflict_clause':0}),
        (1,[[1,-1]],{'steps':[{'clause':0,'literal':1}],'conflict_clause':0}),
        (2,[[-1,2],[1,-2],[-1,-2]],{'steps':[{'clause':0,'literal':2},{'clause':1,'literal':1}],'conflict_clause':2}),
        (1,[[1],[-1]],{'steps':[{'clause':0,'literal':True}],'conflict_clause':1}),
        (1,[[1],[-1]],{'steps':[{'clause':0,'literal':1},{'clause':0,'literal':1}],'conflict_clause':1}),
    ]
    for n,clauses,proof in invalid_controls:
        require(not unit_mask_check(n,clauses,proof) and not probe.verify_unit_contradiction(n,clauses,proof),'invalid implication accepted')
    malformed_witnesses=[None,[],[True,0],[0,2],[0.0,1],[1,0,1]]
    for assignment in malformed_witnesses:
        require(not probe.verify_witness(2,[],assignment),'malformed witness accepted')
    after=hashes();require(before==after,'reviewed sources changed during run')
    report=dict(verdict='CLEAN within the bounded witness/unit-refutation scope',source_sha256=before,source_unchanged_during_run=True,
                saved_original_requests=rows,saved_original_literal_occurrences=literal_occurrences,saved_witness_single_bit_mutations=witness_flips,
                exhaustive_two_variable_formulas=512,seeded_original_formulas=300,seed=2026101917,
                total_original_formulas=formulas,total_original_truth_words=words,probe_statuses=statuses,
                unit_proof_mutations=mutations,valid_alternative_unit_proofs=accepted_variants,rejected_unit_proof_variants=rejected_variants,
                explicitly_invalid_unit_controls=len(invalid_controls),malformed_witness_controls=len(malformed_witnesses),
                nonunit_unsat_unknown_controls=1,explicit_cap_unknown_controls=2,seconds=time.perf_counter()-started,
                scope='Decision witnesses and original-clause unit contradictions only. Exact counting remains UNKNOWN for the four originals. No completeness, polynomial complexity, generic hardness or comparative speed conclusion.')
    (HERE/'COUNTING_VS_DECISION_REVIEW.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({k:report[k] for k in ('verdict','total_original_formulas','total_original_truth_words','unit_proof_mutations','valid_alternative_unit_proofs','rejected_unit_proof_variants','source_unchanged_during_run')}))


if __name__=='__main__':
    main()
