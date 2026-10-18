from copy import deepcopy
from fractions import Fraction
from itertools import product
from pathlib import Path
import importlib.util
import sys
import unittest
from unittest.mock import patch

import fast_recognition as fast

spec=importlib.util.spec_from_file_location('_fast_test_controls',fast.NIGHT/'affine_one_piece_lab'/'controls.py')
controls=importlib.util.module_from_spec(spec);sys.modules[spec.name]=controls;spec.loader.exec_module(controls)


def request(values,n=3,ids=None):
    ids=list(range(n)) if ids is None else ids
    messages=[]
    for index,value in enumerate(values):
        if value:
            rows=[(1<<v,(index>>i)&1) for i,v in enumerate(ids)]
            messages.append(controls.oracle.canonical(n,ids,rows,scalar=value))
    return dict(n=n,retained=ids,messages=messages)


def controls_for_kind():
    return [request([2,1,1,1,1,1,1,1]),request([0,1,1,1,0,0,0,0]),request([1,1,1,1,1,1,1,-1])]


class FastRecognitionTests(unittest.TestCase):
    def test_three_obstructions_without_fallback_or_norms(self):
        for req,kind in zip(controls_for_kind(),['magnitude','affine_hole','cubic_sign']):
            with patch.object(fast.strong,'recognize',side_effect=AssertionError('fallback called')),patch.object(fast.strong.Norms,'query',side_effect=AssertionError('norm called')):
                result=fast.recognize(**req)
                self.assertEqual(result['status'],'UNSUPPORTED')
                self.assertEqual(result['certificate']['witness']['kind'],kind)
                self.assertEqual(result['stats']['norm_queries'],0)
                with patch.object(fast.Discovery,'run',side_effect=AssertionError('search called')):
                    self.assertTrue(fast.verify_one_piece(**req,result=result)['valid'])

    def test_all_small_ternary_and_three_bit_sign_tables(self):
        count=0
        for n in range(3):
            for values in product((-1,0,1),repeat=1<<n):
                req=request(values,n); expected=controls.classify_values(list(map(Fraction,values)))
                result=fast.recognize(**req)
                self.assertEqual(result['status'],'EXACT' if expected else 'UNSUPPORTED')
                self.assertTrue(fast.verify_one_piece(**req,result=result)['valid'])
                count+=1
        for values in product((-1,1),repeat=8):
            req=request(values);expected=controls.classify_values(list(map(Fraction,values)))
            result=fast.recognize(**req)
            self.assertEqual(result['status'],'EXACT' if expected else 'UNSUPPORTED')
            self.assertTrue(fast.verify_one_piece(**req,result=result)['valid'])
            count+=1
        self.assertEqual(count,349)

    def test_local_limits_are_inconclusive_and_preserve_aggregate_work(self):
        req=request([1,1,1,1,1,1,1,1])
        for cap in ('max_probe_samples','max_probe_work'):
            result=fast.probe(**req,**{cap:0})
            self.assertEqual(result['status'],'INCONCLUSIVE')
            self.assertIsNone(result['certificate'])
            result=fast.recognize(**req,**{cap:0})
            self.assertEqual(result['status'],'EXACT')
            self.assertEqual(result['stats']['fallback_calls'],1)
            self.assertEqual(result['stats']['work'],result['stats']['parse_work']+result['stats']['probe_work']+result['stats']['fallback_work'])
            self.assertTrue(fast.verify_one_piece(**req,result=result)['valid'])
        exact=fast.recognize(**req,max_probe_work=0)
        capped=fast.recognize(**req,max_probe_work=0,max_work=exact['stats']['work']-1)
        self.assertEqual(capped['status'],'UNKNOWN')
        self.assertIsNone(capped['message']);self.assertIsNone(capped['certificate'])
        self.assertGreater(capped['stats']['work'],capped['stats']['parse_work'])

    def test_global_caps_do_not_become_negative_claims(self):
        req=controls_for_kind()[0]
        for cap in ('max_work','max_point_evaluations','max_variables','max_pieces','max_scalar_bits'):
            result=fast.recognize(**req,**{cap:0})
            self.assertEqual(result['status'],'UNKNOWN',cap)
            self.assertIsNone(result['certificate'])
        result=fast.recognize(**req)
        self.assertEqual(fast.verify_one_piece(**req,result=result,max_point_evaluations=0)['status'],'UNKNOWN')
        self.assertEqual(fast.verify_one_piece(**req,result=result,max_work=0)['status'],'UNKNOWN')

    def test_mutations_and_external_original_binding(self):
        for req in controls_for_kind():
            result=fast.recognize(**req)
            bad=deepcopy(result);bad['status']='EXACT'
            self.assertFalse(fast.verify_one_piece(**req,result=bad)['valid'])
            bad=deepcopy(result);bad['certificate']['input_sha256']='0'*64
            self.assertFalse(fast.verify_one_piece(**req,result=bad)['valid'])
            bad=deepcopy(result);bad['certificate']['witness']['extra']=0
            self.assertFalse(fast.verify_one_piece(**req,result=bad)['valid'])
            changed=deepcopy(req);changed['messages']=changed['messages']+changed['messages'][:1]
            self.assertFalse(fast.verify_one_piece(**changed,result=result)['valid'])
            witness=result['certificate']['witness']
            key='nonzero_points' if witness['kind']=='affine_hole' else 'points'
            for field,value in [('word',True),('word',8),('value',[99,1]),('value',[1,True])]:
                bad=deepcopy(result);bad['certificate']['witness'][key][0][field]=value
                self.assertFalse(fast.verify_one_piece(**req,result=bad)['valid'])
        req=controls_for_kind()[1];result=fast.recognize(**req)
        for selector in (0,2,8,True,-1):
            bad=deepcopy(result);bad['certificate']['witness']['selector']=selector
            self.assertFalse(fast.verify_one_piece(**req,result=bad)['valid'])
        req=controls_for_kind()[2];result=fast.recognize(**req)
        for directions in ([1,2,True],[1,2,8],[1,1,4]):
            bad=deepcopy(result);bad['certificate']['witness']['directions']=directions
            self.assertFalse(fast.verify_one_piece(**req,result=bad)['valid'])

    def test_substantively_false_witnesses_with_fresh_binding(self):
        # Correctly re-bound external inputs must still satisfy the mathematics.
        for req in controls_for_kind():
            result=fast.recognize(**req)
            constant=request([1]*8)
            budget=fast.Budget({});_,_,_,binding=fast.request(**constant,budget=budget)
            result['certificate']['input_sha256']=binding
            witness=result['certificate']['witness']
            if witness['kind']=='affine_hole':
                samples=witness['nonzero_points']+[witness['zero']]
            else:samples=witness['points']
            for p in samples:p['value']=[1,1]
            self.assertEqual(fast.verify_one_piece(**constant,result=result)['status'],'INVALID')

    def test_sparse_reordered_ids_and_wide_magnitude(self):
        req=request([1,1,1,1,1,1,1,-1],n=12,ids=[8,2,11])
        result=fast.recognize(**req)
        self.assertEqual(result['certificate']['witness']['kind'],'cubic_sign')
        self.assertTrue(fast.verify_one_piece(**req,result=result)['valid'])
        for n in (3,16,64):
            messages=[controls.oracle.canonical(n,list(range(n))),controls.oracle.canonical(n,list(range(n)),[(1,0),(2,0),(4,0)])]
            req=dict(n=n,retained=list(range(n)),messages=messages)
            result=fast.recognize(**req)
            self.assertEqual(result['status'],'UNSUPPORTED')
            self.assertEqual(result['stats']['probe_samples_completed'],2)
            self.assertEqual(result['stats']['fallback_calls'],0)
            self.assertTrue(fast.verify_one_piece(**req,result=result)['valid'])

    def test_positive_cancellation_empty_and_fallback_mutations(self):
        for values,n in [([],0),([0],0),([1],0),([1,1,1,1],2),([0,1,0,1],2)]:
            req=request(values,n)
            result=fast.recognize(**req)
            self.assertEqual(result['status'],'EXACT')
            self.assertTrue(fast.verify_one_piece(**req,result=result)['valid'])
            bad=deepcopy(result);bad['message']['scalar']=[7,1]
            self.assertFalse(fast.verify_one_piece(**req,result=bad)['valid'])
        req=request([1,1,1,1],2)
        result=fast.recognize(**req)
        result['stats']={'untrusted_history':True}
        self.assertTrue(fast.verify_one_piece(**req,result=result)['valid'])
        result['certificate']['result']['certificate']['root_norm']['value']=[999,1]
        self.assertFalse(fast.verify_one_piece(**req,result=result)['valid'])

    def test_strict_inputs_caps_and_large_binary_coefficients(self):
        req=controls_for_kind()[0]
        for cap in ('max_probe_samples','max_probe_cubes','max_probe_work','max_work'):
            for value in (True,-1,1.2):
                with self.assertRaises(ValueError):fast.recognize(**req,**{cap:value})
        with self.assertRaises(ValueError):fast.recognize(**req,unrecognized_cap=2)
        malformed=deepcopy(req);malformed['retained'][0]=True
        with self.assertRaises(ValueError):fast.recognize(**malformed)
        req=request([1<<15000,(1<<15000)+1],1)
        result=fast.recognize(**req)
        self.assertEqual(result['status'],'UNSUPPORTED')
        self.assertTrue(fast.verify_one_piece(**req,result=result)['valid'])
        self.assertGreaterEqual(result['stats']['peak_scalar_bits'],15001)


if __name__=='__main__':unittest.main()
