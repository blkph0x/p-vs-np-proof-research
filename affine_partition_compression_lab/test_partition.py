from copy import deepcopy
import unittest
from unittest.mock import patch
from partition import recognize,verify_partition,digest,fit_phase,Meter,Exhausted
from controls import (oracle,named_controls,all_affine_partitions_three,
                      seeded_partitions,mutations)


class PartitionTests(unittest.TestCase):
    def test_named_and_wide_controls(self):
        for case in named_controls():
            with self.subTest(case['name']):
                n,ids,messages=case['n'],case['retained'],case['messages'];caps=case.get('caps',{})
                result=recognize(n,ids,messages,**caps)
                self.assertEqual(result['status'],case['expected_status'],result)
                if result['status']=='EXACT':
                    checked=verify_partition(n,ids,messages,result,**caps)
                    self.assertTrue(checked['valid'],checked)
                    norm=oracle.norm_identity(n,ids,messages,[result['message']])
                    self.assertTrue(norm['equal'])
                    if 'expected_message' in case:
                        self.assertEqual(result['message'],case['expected_message'])
                else:
                    self.assertIsNone(result['message']);self.assertIsNone(result['certificate'])

    def test_every_affine_partition_of_three_bits(self):
        count=0
        for messages in all_affine_partitions_three():
            result=recognize(3,[0,1,2],messages)
            self.assertEqual(result['status'],'EXACT')
            self.assertTrue(verify_partition(3,[0,1,2],messages,result)['valid'])
            self.assertEqual(result['message'],oracle.canonical(3,[0,1,2]))
            count+=1
        self.assertGreater(count,100)

    def test_all_three_bit_sign_tables(self):
        singles=next(c['messages'] for c in named_controls() if c['name']=='eight_singletons')
        exact=unsupported=0
        for truth in range(256):
            messages=deepcopy(singles)
            for v,m in enumerate(messages):m['scalar']=[-1 if truth>>v&1 else 1,1]
            # The unique cubic ANF coefficient is parity of all eight values.
            expected='EXACT' if truth.bit_count()%2==0 else 'UNSUPPORTED'
            result=recognize(3,[0,1,2],messages)
            self.assertEqual(result['status'],expected)
            if expected=='EXACT':
                exact+=1;self.assertTrue(verify_partition(3,[0,1,2],messages,result)['valid'])
                self.assertEqual(oracle.direct_norm(3,[0,1,2],messages,[result['message']])['squared_norm'],[0,1])
            else:unsupported+=1
        self.assertEqual((exact,unsupported),(128,128))

    def test_seeded_quadratic_partitions(self):
        for case in seeded_partitions():
            n,ids,messages=case['n'],case['retained'],case['messages']
            result=recognize(n,ids,messages)
            self.assertEqual(result['status'],'EXACT')
            self.assertTrue(verify_partition(n,ids,messages,result)['valid'])
            self.assertEqual(result['message'],case['expected_message'])
            self.assertEqual(oracle.direct_norm(n,ids,messages,[result['message']])['squared_norm'],[0,1])

    def test_certificate_and_rebound_semantic_mutations(self):
        case=named_controls()[0];messages=case['messages']
        result=recognize(3,[0,1,2],messages)
        for name,changed in mutations(result):
            with self.subTest(name):self.assertEqual(verify_partition(3,[0,1,2],messages,changed)['status'],'INVALID')
        # Rehashing the external request cannot turn a false phase or support
        # assertion into a valid certificate.
        for mode in ('phase','overlap','magnitude'):
            changed=deepcopy(messages)
            if mode=='phase':changed[0]['scalar']=[-1,1]
            elif mode=='overlap':changed[0]=deepcopy(changed[1])
            else:changed[0]['scalar']=[2,1]
            forged=deepcopy(result)
            forged['certificate']['input_sha256']=digest(dict(n=3,retained=[0,1,2],messages=changed))
            self.assertEqual(verify_partition(3,[0,1,2],changed,forged)['status'],'INVALID')

    def test_inputs_and_budget_fail_closed(self):
        case=named_controls()[0];m=case['messages'];result=recognize(3,[0,1,2],m)
        for caps in ({'max_work':0},{'max_pieces':3},{'max_pairs':5},{'max_variables':2},{'max_scalar_bits':0}):
            checked=verify_partition(3,[0,1,2],m,result,**caps)
            self.assertEqual(checked['status'],'UNKNOWN');self.assertIsNone(checked['message'])
        for n,ids in [(True,[0]),(3,[0,0]),(3,[False,1,2]),(2,[0,1,2])]:
            with self.assertRaises(ValueError):recognize(n,ids,m)
            self.assertEqual(verify_partition(n,ids,m,result)['status'],'INVALID')
        altered=deepcopy(m);altered[0]['scalar']=[True,1]
        with self.assertRaises(ValueError):recognize(3,[0,1,2],altered)
        self.assertEqual(verify_partition(3,[0,1,2],altered,result)['status'],'INVALID')
        with self.assertRaises(ValueError):recognize(3,[0,1,2],m,max_work=True)

    def test_unknown_cap_precedes_quadratic_monomial_allocation(self):
        # A caller may raise the coordinate cap while keeping the unknown cap
        # tiny. Reject before even beginning the quadratic combinations.
        meter=Meter({'max_variables':512,'max_unknowns':1})
        with patch('partition.combinations',side_effect=AssertionError('premature monomial allocation')) as pairs:
            with self.assertRaisesRegex(Exhausted,'quadratic unknown cap'):
                fit_phase([],list(range(300)),[],[],[],meter)
            pairs.assert_not_called()
        self.assertEqual(meter.stats['fit_unknowns'],0)
        self.assertEqual(meter.stats['work'],0)
        messages=[oracle.canonical(3,[0,1,2])]
        rejected=recognize(3,[0,1,2],messages,max_unknowns=6)
        self.assertEqual(rejected['status'],'UNKNOWN')
        self.assertIsNone(rejected['message']);self.assertIsNone(rejected['certificate'])
        accepted=recognize(3,[0,1,2],messages,max_unknowns=7)
        self.assertEqual(accepted['status'],'EXACT')
        self.assertTrue(verify_partition(3,[0,1,2],messages,accepted)['valid'])


if __name__=='__main__':unittest.main()
