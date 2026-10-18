from copy import deepcopy
import unittest
from one_piece import recognize,verify_one_piece,partition
from controls import (oracle,named_controls,small_complete_requests,signed_three_requests,
                       seeded_requests,direct_values,classify_values,mutations)


class OnePieceTests(unittest.TestCase):
    def check_case(self,case):
        n,ids,m=case['n'],case['retained'],case['messages'];caps=case.get('caps',{})
        result=recognize(n,ids,m,**caps)
        self.assertEqual(result['status'],case['expected'],(case,result))
        if result['status']=='UNKNOWN':
            self.assertIsNone(result['message']);self.assertIsNone(result['certificate']);return result
        checked=verify_one_piece(n,ids,m,result,**caps)
        self.assertTrue(checked['valid'],checked)
        self.assertEqual(checked['recognition'],result['status'])
        if result['status']=='EXACT':
            if len(ids)<=8:self.assertEqual(oracle.direct_norm(n,ids,m,[result['message']])['squared_norm'],[0,1])
        else:
            self.assertIsNone(result['message'])
            if len(ids)<=8:self.assertFalse(classify_values(direct_values(n,ids,m)))
        if case.get('fallback'):self.assertGreater(result['stats']['norm_queries'],2)
        if case.get('zero'):self.assertTrue(result['message']['zero'])
        if 'kind' in case:self.assertEqual(result['certificate']['kind'],case['kind'])
        if 'difference' in case:self.assertEqual(result['certificate']['difference_norm']['value'],case['difference'])
        return result

    def test_named_wide_and_resource_controls(self):
        for case in named_controls():
            with self.subTest(case['name']):self.check_case(case)

    def test_all_ternary_truth_tables_through_two_bits(self):
        for case in small_complete_requests():self.check_case(case)

    def test_all_three_bit_sign_tables(self):
        for case in signed_three_requests():self.check_case(case)

    def test_seeded_arbitrary_signed_sums(self):
        for case in seeded_requests():self.check_case(case)

    def test_complete_source_norm_hull_sample_mutations(self):
        names={'four_nonparallel_lines','shifted_zero_anchor_with_outside','cubic_final_norm_four','nonuniform_magnitude'}
        for case in named_controls():
            if case['name'] not in names:continue
            result=self.check_case(case)
            for name,changed in mutations(result):
                # Zero is a valid support point in full-support phase/magnitude
                # cases; reserve that mutation for the zero-anchor obstruction.
                if name=='zero_support_point' and result['certificate']['kind']!='anchor_zero':continue
                check=verify_one_piece(case['n'],case['retained'],case['messages'],changed)
                self.assertEqual(check['status'],'INVALID',(case['name'],name,check))
            altered=deepcopy(case['messages'])
            first=next(m for m in altered if not m['zero']);first['scalar'][0]*=2
            forged=deepcopy(result)
            forged['certificate']['input_sha256']=partition.digest(dict(format='explicit-one-piece-v1',n=case['n'],retained=case['retained'],messages=altered))
            self.assertEqual(verify_one_piece(case['n'],case['retained'],altered,forged)['status'],'INVALID')

    def test_fail_closed_caps_headers_and_constant_phase(self):
        case=next(c for c in named_controls() if c['name']=='four_nonparallel_lines')
        result=self.check_case(case)
        for caps in ({'max_work':0},{'max_norm_queries':0},{'max_pair_contractions':0},{'max_certificate_products':0}):
            check=verify_one_piece(3,[0,1,2],case['messages'],result,**caps)
            self.assertEqual(check['status'],'UNKNOWN');self.assertIsNone(check['message'])
        for n,ids in [(True,[0]),(3,[0,0]),(3,[False,1,2])]:
            with self.assertRaises(ValueError):recognize(n,ids,case['messages'])
            self.assertEqual(verify_one_piece(n,ids,case['messages'],result)['status'],'INVALID')
        # An equivalent closed block phase must be evaluated with its sign.
        changed=deepcopy(result)
        m=changed['certificate']['root_norm']['products'][0]['result']['message']
        self.assertFalse(m['zero']);m['phase']=[0];m['scalar'][0]*=-1
        self.assertTrue(verify_one_piece(3,[0,1,2],case['messages'],changed)['valid'])

    def test_large_binary_rational_binding_and_derived_bits(self):
        coefficient=1<<15000
        messages=[oracle.canonical(1,[0],scalar=coefficient)]
        result=recognize(1,[0],messages)
        self.assertEqual(result['status'],'EXACT')
        self.assertTrue(verify_one_piece(1,[0],messages,result)['valid'])
        self.assertEqual(result['message']['scalar'],[coefficient,1])
        # Original input fits this limit, but its squared coefficient does not.
        limited=recognize(1,[0],messages,max_scalar_bits=15001)
        self.assertEqual(limited['status'],'UNKNOWN')
        self.assertIsNone(limited['message']);self.assertIsNone(limited['certificate'])


if __name__=='__main__':unittest.main()
