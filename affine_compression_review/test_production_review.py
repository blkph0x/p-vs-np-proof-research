from copy import deepcopy
import unittest
from review_oracles import controls,direct_norm,canonical,norm_identity,verify_norm_identity
from production_review import (compression,seeded_requests,certificate_mutations,
                               forged_invalid_identity,actual_nonconfluence)


class ProductionReview(unittest.TestCase):
    def test_all_original_assignment_sums(self):
        for request in seeded_requests():
            n,ids,original=request['n'],request['retained'],request['messages']
            result=compression.compress(n,ids,original)
            self.assertEqual(result['status'],'EXACT')
            check=compression.verify_compression(n,ids,original,result)
            self.assertTrue(check['valid'],check)
            self.assertEqual(direct_norm(n,ids,original,result['messages'])['squared_norm'],[0,1])

    def test_source_binding_and_consumption_mutations(self):
        for control in controls()[:5]:
            result=compression.compress(3,[0,1,2],control['left'])
            for name,changed in certificate_mutations(result):
                with self.subTest(control=control['name'],mutation=name):
                    self.assertFalse(compression.verify_compression(3,[0,1,2],control['left'],changed)['valid'])
            changed=deepcopy(control['left']);changed[0]['scalar'][0]*=2
            self.assertFalse(compression.verify_compression(3,[0,1,2],changed,result)['valid'])
            self.assertFalse(compression.verify_compression(3,[0,1,2],control['left']+[control['left'][0]],result)['valid'])

    def test_semantic_forged_identities(self):
        for control in controls()[5:]:
            forged=forged_invalid_identity(control)
            check=compression.verify_compression(3,[0,1,2],control['left'],forged)
            self.assertEqual(check['status'],'INVALID',control['name'])

    def test_nonconfluence_matches_actual_streaming(self):
        result=actual_nonconfluence()
        self.assertEqual(len(result['four_lines']['result']['messages']),4)
        self.assertEqual(len(result['one_space']['result']['messages']),1)

    def test_sparse_order_rationals_and_wide_symbolic(self):
        n=193;ids=[192,0,80]
        left=[canonical(n,ids,[[1<<192,b]],[1|(1<<80)],[5 if b==0 else -5,11]) for b in range(2)]
        result=compression.compress(n,ids,left)
        self.assertTrue(compression.verify_compression(n,ids,left,result)['valid'])
        self.assertEqual(direct_norm(n,ids,left,result['messages'])['squared_norm'],[0,1])
        for control in controls(128)[:5]:
            result=compression.compress(128,list(range(128)),control['left'])
            self.assertTrue(compression.verify_compression(128,list(range(128)),control['left'],result)['valid'])
            proof=norm_identity(128,list(range(128)),control['left'],result['messages'],save_proofs=True)
            checked=verify_norm_identity(128,list(range(128)),control['left'],result['messages'],proof)
            self.assertTrue(checked['valid'] and checked['equal'])

    def test_budget_and_zero_source_controls(self):
        left=controls()[0]['left']
        exact=compression.compress(3,[0,1,2],left)
        for caps in [dict(max_inputs=1),dict(max_generated=0),dict(max_pairs=0),dict(max_steps=0),dict(max_work=0),dict(max_live_pieces=0)]:
            result=compression.compress(3,[0,1,2],left,**caps)
            self.assertEqual(result['status'],'UNKNOWN')
            self.assertIsNone(result['messages']);self.assertIsNone(result['certificate'])
            self.assertEqual(compression.verify_compression(3,[0,1,2],left,exact,**caps)['status'],'UNKNOWN')
        zero=canonical(3,[0,1,2],scalar=0)
        exact=compression.compress(3,[0,1,2],[zero])
        self.assertTrue(compression.verify_compression(3,[0,1,2],[zero],exact)['valid'])
        wrong=deepcopy(exact);wrong['certificate']['events'].pop()
        self.assertFalse(compression.verify_compression(3,[0,1,2],[zero],wrong)['valid'])


if __name__=='__main__':unittest.main()
