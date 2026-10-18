import copy
from fractions import Fraction
import random
import unittest
from review_oracles import (canonical,controls,exhaustive_equal,norm_identity,
                            verify_norm_identity,nonconfluence_schedules,point)


class ReviewOracles(unittest.TestCase):
    def test_all_exact_countercontrols(self):
        for control in controls():
            with self.subTest(control['name']):
                oracle=exhaustive_equal(3,[0,1,2],control['left'],control['right'])
                proof=norm_identity(3,[0,1,2],control['left'],control['right'],save_proofs=True)
                self.assertEqual(oracle['equal'],control['valid'])
                self.assertEqual(proof['equal'],control['valid'])
                checked=verify_norm_identity(3,[0,1,2],control['left'],control['right'],proof)
                self.assertTrue(checked['valid'],checked)
                self.assertEqual(checked['equal'],control['valid'])

    def test_wide_symbolic_controls(self):
        for control in controls(64):
            proof=norm_identity(64,list(range(64)),control['left'],control['right'],save_proofs=True)
            checked=verify_norm_identity(64,list(range(64)),control['left'],control['right'],proof)
            self.assertTrue(checked['valid'],checked)
            self.assertEqual(checked['equal'],control['valid'])

    def test_nonconfluence(self):
        result=nonconfluence_schedules()
        self.assertEqual(result['four_lines']['final_count'],4)
        self.assertEqual(result['one_space']['final_count'],1)
        self.assertEqual(result['four_lines']['directions'],[1,2,4,7])

    def test_signed_rational_seeded(self):
        rng=random.Random(1910261301)
        for n in range(5):
            ids=list(range(n))
            for _ in range(15):
                sets=[]
                for _side in range(2):
                    messages=[]
                    for _piece in range(rng.randrange(4)):
                        equations=[[rng.randrange(1<<n),rng.randrange(2)] for _ in range(rng.randrange(3))]
                        phase=[mask for mask in range(1<<n) if mask.bit_count()<=2 and rng.randrange(4)==0]
                        messages.append(canonical(n,ids,equations,phase,Fraction(rng.randrange(-3,4),rng.randrange(1,5))))
                    sets.append(messages)
                expected=exhaustive_equal(n,ids,*sets)['equal']
                proof=norm_identity(n,ids,*sets,save_proofs=True)
                checked=verify_norm_identity(n,ids,*sets,proof)
                self.assertTrue(checked['valid'],checked)
                self.assertEqual(checked['equal'],expected)

    def test_proof_mutations_and_external_input(self):
        control=controls()[1]
        left,right=control['left'],control['right']
        proof=norm_identity(3,[0,1,2],left,right,save_proofs=True)
        mutations=[]
        for path,value in [(['equal'],False),(['block_checks'],5),(['squared_norm'],[1,1]),
                (['products',0,'pair'],[0,1]),(['products',0,'value'],[0,1]),
                (['products',0,'request','scalar'],[0,1]),
                (['products',0,'result','message','scalar'],[0,1])]:
            changed=copy.deepcopy(proof);target=changed
            for key in path[:-1]:target=target[key]
            target[path[-1]]=value;mutations.append(changed)
        changed=copy.deepcopy(proof);changed['products'].pop();mutations.append(changed)
        for changed in mutations:
            self.assertFalse(verify_norm_identity(3,[0,1,2],left,right,changed)['valid'])
        changed_left=copy.deepcopy(left);changed_left[0]['scalar']=[4,7]
        self.assertFalse(verify_norm_identity(3,[0,1,2],changed_left,right,proof)['valid'])
        self.assertFalse(verify_norm_identity(3,[2,1,0],left,right,proof)['valid'])

    def test_caps_and_noncanonical_phase_constant(self):
        c=controls()[0];proof=norm_identity(3,[0,1,2],c['left'],c['right'],save_proofs=True)
        for caps in [dict(max_products=5),dict(max_work=0),dict(max_scalar_bits=0)]:
            checked=verify_norm_identity(3,[0,1,2],c['left'],c['right'],proof,**caps)
            self.assertFalse(checked['valid']);self.assertEqual(checked['status'],'UNKNOWN')
        # The block checker permits an equivalent noncanonical output. Its
        # actual closed function, rather than bare scalar, must be consumed.
        changed=copy.deepcopy(proof)
        message=changed['products'][0]['result']['message']
        message['phase']=[0];message['scalar'][0]*=-1
        self.assertTrue(verify_norm_identity(3,[0,1,2],c['left'],c['right'],changed)['valid'])


if __name__=='__main__':unittest.main()
