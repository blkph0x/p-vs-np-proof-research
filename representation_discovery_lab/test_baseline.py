import itertools
import random
import unittest

from engine import _xor3_clauses, project, rename_variables, xor_chain
from gaussian_baseline import recover_xor_relation


def direct_projection(clauses, shared):
    variables=sorted(set(shared)|{abs(lit)-1 for clause in clauses for lit in clause})
    output=[0]*(1<<len(shared))
    for word in range(1<<len(variables)):
        assignment={v:(word>>i)&1 for i,v in enumerate(variables)}
        if all(any(assignment[abs(lit)-1]==int(lit>0) for lit in clause) for clause in clauses):
            index=sum(assignment[v]<<i for i,v in enumerate(shared))
            output[index]=1
    return tuple(output)


def decoded(result, width):
    return tuple(int(sum((word>>i)&1 for i in result.support)%2==result.rhs) for word in range(1<<width))


class BaselineRepairTests(unittest.TestCase):
    def test_added_binary_and_empty_clause_are_not_ignored(self):
        original=xor_chain(3)
        original_bits=direct_projection(original['clauses'],original['shared'])
        for added in [((1,2),), ((),), ((1,2,3),), ((1,2,3,4),)]:
            clauses=original['clauses']+added
            self.assertEqual(recover_xor_relation(clauses,original['shared']).status,'UNKNOWN')
        self.assertNotEqual(direct_projection(original['clauses']+((1,2),),original['shared']),original_bits)

    def test_positive_unit_and_sparse_ordered_shared_ids(self):
        original=xor_chain(4)
        clauses=original['clauses'][:-1]+((-original['clauses'][-1][0],),)
        mapping={v:50-3*v for v in range(7)}
        clauses=tuple(tuple((1 if lit>0 else -1)*(mapping[abs(lit)-1]+1) for lit in clause) for clause in clauses)
        shared=tuple(mapping[v] for v in (2,0,3,1))+(100,)
        result=recover_xor_relation(clauses,shared)
        self.assertEqual((result.status,result.support,result.rhs),('EXACT_AFFINE',(0,1,2,3),1))
        self.assertEqual(decoded(result,len(shared)),direct_projection(clauses,shared))

    def test_every_clause_and_unresolved_equation_must_be_covered(self):
        original=xor_chain(3)
        variants=[original['clauses'][:-1],original['clauses']+((1,),),
                  original['clauses']+_xor3_clauses(8,9,10),
                  original['clauses']+_xor3_clauses(0,1,2),
                  original['clauses'][:-1]+((20,),)]
        for clauses in variants:
            self.assertEqual(recover_xor_relation(clauses,original['shared']).status,'UNKNOWN')

    def test_duplicate_clauses_literals_units_and_tautologies_are_safe(self):
        original=xor_chain(3)
        clauses=tuple(clause+(clause[0],) for clause in original['clauses'])+original['clauses']+((1,-1,100),)
        result=recover_xor_relation(clauses,original['shared'])
        self.assertEqual(result.status,'EXACT_AFFINE')
        self.assertEqual(decoded(result,3),direct_projection(clauses,original['shared']))
        self.assertGreater(result.work,recover_xor_relation(original['clauses'],original['shared']).work)

    def test_malformed_literals_and_shared_ids_raise_value_error(self):
        original=xor_chain(3)
        for literal in [0,True,False,1.0,'1',None]:
            with self.subTest(literal=literal), self.assertRaises(ValueError):
                recover_xor_relation(original['clauses']+((literal,),),original['shared'])
        for shared in [(0,0,2),(False,1,2),(0,1.0,2),(0,-1,2),(0,'1',2)]:
            with self.subTest(shared=shared),self.assertRaises(ValueError):
                recover_xor_relation(original['clauses'],shared)
        for clauses in [None,'123',((1,),None)]:
            with self.assertRaises(ValueError):recover_xor_relation(clauses,(0,))

    def test_all_three_variable_clause_subsets_with_both_units(self):
        vocabulary=list(itertools.product((-1,1),(-2,2),(-3,3)))
        exact=0
        for subset in range(256):
            clauses=tuple(c for i,c in enumerate(vocabulary) if subset>>i&1)
            for unit in [-3,3]:
                original=clauses+((unit,),)
                result=recover_xor_relation(original,(0,1))
                if result.status=='EXACT_AFFINE':
                    exact+=1;self.assertEqual(decoded(result,2),direct_projection(original,(0,1)))
        self.assertEqual(exact,2)

    def test_seeded_original_networks_against_independent_assignment_oracle(self):
        rng=random.Random(20261020);exact=0
        for case in range(180):
            width=rng.randrange(2,5);known=list(range(width));clauses=[]
            for _ in range(rng.randrange(1,4)):
                left,right=rng.sample(known,2);helper=len(known)
                clauses.extend(_xor3_clauses(left,right,helper));known.append(helper)
            target=rng.choice(known);clauses.append(((target+1)*rng.choice([-1,1]),))
            if case%3==0:clauses.append(tuple((v+1)*rng.choice([-1,1]) for v in rng.sample(known,2)))
            permutation=rng.sample(known,len(known))
            original=tuple(tuple((1 if lit>0 else -1)*(permutation[abs(lit)-1]+1) for lit in c) for c in clauses)
            shared=tuple(permutation[v] for v in rng.sample(list(range(width)),width))
            result=recover_xor_relation(original,shared)
            if result.status=='EXACT_AFFINE':
                exact+=1;self.assertEqual(decoded(result,width),direct_projection(original,shared))
            else:self.assertEqual(result.status,'UNKNOWN')
        self.assertEqual(exact,120)

    def test_failed_substitution_scans_are_charged(self):
        original=xor_chain(5)
        reversed_ids=rename_variables(original,{v:8-v for v in range(9)})
        first=recover_xor_relation(original['clauses'],original['shared'])
        second=recover_xor_relation(reversed_ids['clauses'],reversed_ids['shared'])
        self.assertEqual((first.support,first.rhs),(second.support,second.rhs))
        self.assertGreater(second.work,first.work)

    def test_project_rejects_shared_local_overlap_and_invalid_inputs(self):
        for clauses,shared,local in [(((1,),),(0,),(0,)),(((0,),),(0,),()),
                                      (((2,),),(0,),()),(((True,),),(0,),()),
                                      (((1,),),(0,0),()),(((1,),),(False,),())]:
            with self.assertRaises(ValueError):project(clauses,shared,local)

    def test_unit_only_constants_and_empty_input_scope(self):
        for unit in [-1,1]:
            result=recover_xor_relation(((unit,),),(0,1))
            self.assertEqual(decoded(result,2),direct_projection(((unit,),),(0,1)))
        for clauses in [(),((),),((1,),(-1,))]:
            self.assertEqual(recover_xor_relation(clauses,(0,)).status,'UNKNOWN')
        cancelling=_xor3_clauses(0,1,2)+_xor3_clauses(0,2,3)+_xor3_clauses(1,3,4)
        for unit in [-5,5]:
            clauses=cancelling+((unit,),)
            result=recover_xor_relation(clauses,(0,1))
            self.assertEqual((result.status,result.support,result.rhs),('EXACT_AFFINE',(),int(unit>0)))
            self.assertEqual(decoded(result,2),direct_projection(clauses,(0,1)))


if __name__=='__main__':unittest.main()
