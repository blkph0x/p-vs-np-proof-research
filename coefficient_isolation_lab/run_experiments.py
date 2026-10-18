"""Reproduce exact coefficient controls and save their original requests and hashes."""
from collections import Counter
from datetime import datetime,timezone
import hashlib
import itertools
import json
from pathlib import Path
import platform
import random
from time import perf_counter

from coefficient import (binary_ladder_coefficient,packed_integer_coefficient,
                         prime_field_filter,reconstruct_bounded_count,sparse_coefficient)

HERE=Path(__file__).resolve().parent
SOURCES=('coefficient.py','test_coefficient.py','run_experiments.py','THEOREM.md')


def hashes():
    return {name:hashlib.sha256((HERE/name).read_bytes()).hexdigest() for name in SOURCES}


def request_hash(request):
    return hashlib.sha256(json.dumps(request,sort_keys=True,separators=(',',':')).encode()).hexdigest()


def oracle(choices):
    return Counter(sum(pair[bit] for pair,bit in zip(choices,bits))
                   for bits in itertools.product((0,1),repeat=len(choices)))


def exhaustive_counts():
    cases=families=choice_words=0
    for q in range(4):
        for choices in itertools.product(list(itertools.product(range(3),repeat=2)),repeat=q):
            expected=oracle(choices)
            families+=1
            choice_words+=1<<q
            for target in range(7):
                assert packed_integer_coefficient(choices,target)['coefficient']==expected[target]
                assert sparse_coefficient(choices,target)['coefficient']==expected[target]
                cases+=1
    return {'families':families,'original_choice_words':choice_words,'target_queries':cases,
            'all_packed_and_sparse_counts_match':True}


def filter_case(name,choices,target,p,order,omega):
    request={'choices':[list(pair) for pair in choices],'target':target,'p':p,'order':order,'omega':omega}
    counts=oracle(choices)
    result=prime_field_filter(**request)
    folded=sum(count for degree,count in counts.items() if degree%order==target%order)
    assert result['filter_residue']==folded%p
    if 'exact_coefficient' in result:
        assert result['exact_coefficient']==counts[target]
    return {'name':name,'request':request,'request_sha256':request_hash(request),
            'original_coefficients':[[degree,count] for degree,count in sorted(counts.items())],
            'target_count':counts[target],'folded_integer_count':folded,'result':result}


def replay_filters(cases):
    for case in cases:
        assert request_hash(case['request'])==case['request_sha256']
        assert prime_field_filter(**case['request'])==case['result']
        counts=oracle(case['request']['choices'])
        assert counts[case['request']['target']]==case['target_count']
        assert [[degree,count] for degree,count in sorted(counts.items())]==case['original_coefficients']
    return {'filter_cases_replayed':len(cases),'all_exact_modular_evaluations_reproduced':True}


def main():
    before,started=hashes(),perf_counter()
    cancellation=[(0,1)]*5+[(0,2)]*2
    gap=[(1,6)]+[(0,36)]*3
    filters=[filter_case('alias_free_characteristic_cancellation',cancellation,4,13,12,2),
             filter_case('second_count_residue',cancellation,4,37,12,8),
             filter_case('large_characteristic_exact_count',cancellation,4,257,16,pow(3,16,257)),
             filter_case('exponent_aliasing_false_positive',gap,36,11,5,3),
             filter_case('tiny_characteristic_cancellation',[(0,0)],0,2,1,1),
             filter_case('outside_degree_residue_wrap',[(0,1)],2,5,2,4),
             filter_case('aliased_zero_rejects',[(0,2)]*2,1,17,2,16)]
    rng=random.Random(2026101907)
    for index in range(80):
        choices=[(rng.randrange(9),rng.randrange(9)) for _ in range(rng.randrange(7))]
        target=rng.randrange(55)
        order=rng.choice([1,2,4,8,16])
        filters.append(filter_case('seeded_'+str(index),choices,target,17,order,pow(3,16//order,17)))
    packed=[]
    for name,choices,target in [('gcd_shift_zero_factors',[(10,16),(2,8),(5,5)],23),
                                ('absent_gap',gap,36),('positive_count26',cancellation,4)]:
        request={'choices':[list(pair) for pair in choices],'target':target}
        digit=packed_integer_coefficient(**request)
        sparse=sparse_coefficient(**request)
        expected=oracle(choices)[target]
        assert digit['coefficient']==sparse['coefficient']==expected
        packed.append({'name':name,'request':request,'request_sha256':request_hash(request),
                       'expected_count':expected,'packed':digit,'sparse':sparse})
    large={'choices':[[0,1<<i] for i in range(40)],'target':(1<<39)-1}
    large_control={'request':large,'request_sha256':request_hash(large),
                   'packed':packed_integer_coefficient(**large),'sparse':sparse_coefficient(**large,max_states=64),
                   'binary_ladder':binary_ladder_coefficient(**large),
                   'reference':'complete binary-expansion identity; every coefficient in range is one',
                   'minimum_unaliased_order_for_full_degree':1<<40}
    assert large_control['packed']['status']==large_control['sparse']['status']=='UNKNOWN'
    assert large_control['binary_ladder']['coefficient']==1
    congruences=[(case['result']['p'],case['result']['filter_residue']) for case in filters[:2]]
    crt=reconstruct_bounded_count(congruences,128)
    assert crt['coefficient']==26
    residue_witnesses=[{'modulus':m,'choice_bits':bits,'cost':sum(pair[b] for pair,b in zip(gap,bits))}
                       for m,bits in [(2,[1,0,0,0]),(3,[1,0,0,0]),(5,[0,0,0,0]),(7,[0,0,0,0])]]
    assert all(row['cost']%row['modulus']==36%row['modulus'] for row in residue_witnesses)
    data={'schema':'coefficient_isolation_controls_v1','finished_utc':datetime.now(timezone.utc).isoformat(),
          'python':platform.python_version(),'all_executable_arithmetic_exact':True,
          'no_general_polynomial_coefficient_solver_claimed':True,'seed':2026101907,
          'exhaustive_counts':exhaustive_counts(),'packed_controls':packed,'filters':filters,
          'large_degree_special_case':large_control,
          'verified_same_count_CRT':{'source_filter_names':[c['name'] for c in filters[:2]],
                                     'congruences':congruences,'count_bound':128,'result':crt},
          'unbound_CRT_caveat':{'fabricated_congruences':[[13,1],[37,1]],
                               'result':reconstruct_bounded_count([(13,1),(37,1)],128),
                               'actual_coefficient':26,'original_polynomial_binding_claimed':False},
          'separate_residue_witnesses':{'choices':gap,'target':36,'witnesses':residue_witnesses,
                                       'modulus_product':210,'degree':114,'target_count':0},
          'whole_product_PIT_caveat':{'choices':[[0,1]],'target':2,'whole_polynomial_nonzero':True,
                                     'value_at_one':2,'target_count':0},
          'finite_field_function_collision':{'p':5,'first_choices':[[0,1]],'second_choices':[[0,5]],
              'target':1,'target_counts':[1,0],
              'all_field_evaluations':[[x,(1+x)%5,(1+pow(x,5,5))%5] for x in range(5)]},
          'near_zero_precision_control':{'W':1<<20,'W_input_bits':21,
              'polynomials':'1+z^W versus 1+z^(W+1)','evaluation_point':'1/2',
              'exact_value_gap':'2^(-W-1)','required_strict_absolute_error':'less than 2^(-W-2)',
              'fractional_precision_scale_bits':(1<<20)+2,'floating_point_computation_used':False},
          'serialized_filter_replay':replay_filters(json.loads(json.dumps(filters)))}
    after=hashes()
    assert before==after
    data.update(source_sha256_before=before,source_sha256_after=after,
                sources_unchanged_during_run=True,seconds=perf_counter()-started)
    (HERE/'RESULTS.json').write_text(json.dumps(data,indent=2)+'\n',encoding='utf-8')
    summary=("# Coefficient-isolation results\n\n"
             f"All {data['exhaustive_counts']['target_queries']:,} exhaustive coefficient queries agreed "
             "between independent choice enumeration, sparse counting and carry-free integer digits. "
             f"All {len(filters)} exact prime-field filter cases were serialized and replayed, including "
             "complete saved modular evaluation tables.\n\n"
             "The alias-free characteristic-13 filter returns zero for the positive coefficient 26. "
             "A large characteristic or verified same-count CRT recovers 26 exactly. The saved "
             "missing-target example returns a positive folded residue when exponent aliasing is allowed. "
             "Separate residue tests use different witnesses and do not establish one exact matching.\n\n"
             "A 40-factor binary-ladder product has an exact coefficient of one at the saved target. "
             "The generic packed and sparse methods return UNKNOWN under their explicit caps, while "
             "the proved binary-ladder identity returns the count immediately. This distinguishes a "
             "method limitation from inherent difficulty of that family.\n\n"
             "The results include normalization, zero-factor multiplicities, whole-product identity-test "
             "and finite-field evaluation counterexamples, the CRT binding caveat, and an exact precision "
             "calculation for near-zero evaluation. No floating-point result is used as a certificate.\n\n"
             "Run `python -m unittest -v test_coefficient` and `python run_experiments.py` here. "
             "Original requests and before/after source hashes are saved in RESULTS.json. "
             f"Measured experiment time: {data['seconds']:.6f}s. No novelty or P-versus-NP resolution is claimed.\n")
    (HERE/'RESULTS.md').write_text(summary,encoding='utf-8')
    print(json.dumps({'coefficient_queries':data['exhaustive_counts']['target_queries'],
                      'field_filters':len(filters),'all_replayed':True,'seconds':data['seconds']}))


if __name__=='__main__':
    main()
