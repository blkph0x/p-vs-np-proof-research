from collections import Counter
import itertools
import random
import unittest

from coefficient import (binary_ladder_coefficient, normalize, packed_integer_coefficient,
                         prime_field_filter, reconstruct_bounded_count, sparse_coefficient)


def counts(choices):
    return Counter(sum(pair[bit] for pair,bit in zip(choices,bits))
                   for bits in itertools.product((0,1),repeat=len(choices)))


class CoefficientTests(unittest.TestCase):
    def test_exhaustive_integer_digits_and_sparse_counts(self):
        pairs=list(itertools.product(range(3),repeat=2))
        for q in range(4):
            for choices in itertools.product(pairs,repeat=q):
                expected=counts(choices)
                for target in range(7):
                    self.assertEqual(packed_integer_coefficient(choices,target)['coefficient'],expected[target])
                    self.assertEqual(sparse_coefficient(choices,target)['coefficient'],expected[target])

    def test_normalization_handles_huge_offsets_gcd_and_zero_factors(self):
        huge=1<<15000
        choices=[(huge,huge+30),(huge,huge+60),(huge,huge)]
        self.assertEqual(packed_integer_coefficient(choices,3*huge+30)['coefficient'],2)
        self.assertEqual(packed_integer_coefficient(choices,3*huge+31)['coefficient'],0)
        self.assertEqual(normalize(choices,3*huge+60)['symmetric_target'],1)

    def test_caps_return_unknown_without_a_count(self):
        choices=[(0,1<<i) for i in range(40)]
        target=(1<<39)-1
        result=packed_integer_coefficient(choices,target,max_pack_bits=10000)
        self.assertEqual(result['status'],'UNKNOWN')
        self.assertNotIn('coefficient',result)
        result=sparse_coefficient(choices,target,max_states=32)
        self.assertEqual(result['status'],'UNKNOWN')
        self.assertNotIn('coefficient',result)

    def test_binary_ladder_exact_shortcut(self):
        for q in range(8):
            choices=[(0,1<<i) for i in range(q)]
            for target in range(1<<q):
                self.assertEqual(binary_ladder_coefficient(choices,target)['coefficient'],1)
        choices=[(0,1<<i) for i in range(40)]
        self.assertEqual(binary_ladder_coefficient(choices,(1<<39)-1)['coefficient'],1)
        self.assertEqual(binary_ladder_coefficient([(0,1),(0,1)],1)['status'],'UNKNOWN')

    def test_root_filter_equals_independent_folded_sum(self):
        rng=random.Random(1718)
        for _ in range(60):
            choices=[(rng.randrange(8),rng.randrange(8)) for _ in range(rng.randrange(7))]
            target=rng.randrange(50)
            order=rng.choice([1,2,4,8,16])
            result=prime_field_filter(choices,target,17,order,pow(3,16//order,17))
            expected=sum(c for exponent,c in counts(choices).items() if exponent%order==target%order)%17
            self.assertEqual(result['filter_residue'],expected)
            if 'exact_coefficient' in result:
                self.assertEqual(result['exact_coefficient'],counts(choices)[target])

    def test_no_aliasing_does_not_prevent_characteristic_cancellation(self):
        choices=[(0,1)]*5+[(0,2)]*2
        self.assertEqual(counts(choices)[4],26)
        result=prime_field_filter(choices,4,13,12,2)
        self.assertTrue(result['alias_free'])
        self.assertEqual(result['filter_residue'],0)
        self.assertEqual(result['coefficient_decision'],'UNKNOWN')
        tiny=prime_field_filter([(0,0)],0,2,1,1)
        self.assertEqual(tiny['filter_residue'],0)
        self.assertEqual(tiny['coefficient_decision'],'UNKNOWN')

    def test_large_characteristic_and_crt_recover_the_exact_count(self):
        choices=[(0,1)]*5+[(0,2)]*2
        large=prime_field_filter(choices,4,257,16,pow(3,16,257))
        self.assertEqual(large['exact_coefficient'],26)
        first=prime_field_filter(choices,4,13,12,2)
        second=prime_field_filter(choices,4,37,12,8)
        combined=reconstruct_bounded_count([(13,first['filter_residue']),(37,second['filter_residue'])],128)
        self.assertEqual(combined['coefficient'],26)
        self.assertEqual(reconstruct_bounded_count([(13,0)],128)['status'],'UNKNOWN')

    def test_aliasing_false_positive_and_outside_degree(self):
        choices=[(1,6)]+[(0,36)]*3
        result=prime_field_filter(choices,36,11,5,3)
        self.assertEqual(counts(choices)[36],0)
        self.assertEqual(result['filter_residue'],2)
        self.assertEqual(result['coefficient_decision'],'UNKNOWN')
        outside=prime_field_filter([(0,1)],2,5,2,4)
        self.assertEqual(outside['filter_residue'],1)
        self.assertEqual(outside['exact_coefficient'],0)
        folded_zero=prime_field_filter([(0,2)]*2,1,17,2,16)
        self.assertFalse(folded_zero['alias_free'])
        self.assertEqual(folded_zero['exact_coefficient'],0)

    def test_whole_product_and_finite_field_evaluations_do_not_isolate(self):
        self.assertEqual(counts([(0,1)])[2],0)
        self.assertEqual(sum(counts([(0,1)]).values()),2)
        for point in range(5):
            self.assertEqual((1+point)%5,(1+pow(point,5,5))%5)
        self.assertEqual(counts([(0,1)])[1],1)
        self.assertEqual(counts([(0,5)])[1],0)

    def test_separate_residue_witnesses_do_not_give_one_matching(self):
        choices=[(1,6)]+[(0,36)]*3
        support=set(counts(choices))
        target=36
        witnesses={2:6,3:6,5:1,7:1}
        self.assertGreater(2*3*5*7,max(support))
        for modulus,cost in witnesses.items():
            self.assertIn(cost,support)
            self.assertEqual(cost%modulus,target%modulus)
        self.assertNotIn(target,support)
        self.assertFalse(any(all(cost%m==target%m for m in witnesses) for cost in support))

    def test_invalid_parameters_and_budgeted_field_checks(self):
        for choices,target in [([(0,-1)],0),([(0,True)],0),([],True)]:
            with self.assertRaises(ValueError):
                packed_integer_coefficient(choices,target)
        with self.assertRaises(ValueError):
            prime_field_filter([(0,1)],0,15,2,14)
        with self.assertRaises(ValueError):
            prime_field_filter([(0,1)],0,13,12,1)
        with self.assertRaises(ValueError):
            reconstruct_bounded_count([(6,0),(9,0)],100)
        self.assertEqual(prime_field_filter([(0,1)],0,257,16,249,max_evaluations=4)['status'],'UNKNOWN')
        self.assertEqual(prime_field_filter([(0,1)],0,257,16,249,max_prime_trials=0)['status'],'UNKNOWN')
        self.assertEqual(reconstruct_bounded_count([(7,6)],5)['status'],'INVALID')

    def test_crt_arithmetic_does_not_validate_polynomial_residues(self):
        actual=counts([(0,1)]*5+[(0,2)]*2)[4]
        unrelated=reconstruct_bounded_count([(13,1),(37,1)],128)
        self.assertEqual(unrelated['coefficient'],1)
        self.assertNotEqual(unrelated['coefficient'],actual)


if __name__=='__main__':
    unittest.main()
