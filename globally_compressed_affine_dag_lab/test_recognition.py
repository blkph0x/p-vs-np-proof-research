"""Integration invariants beyond the adapted original-factor regressions."""
from copy import deepcopy
from fractions import Fraction
import unittest
from unittest.mock import patch

import dag


def canonical(n,ids,rows=(),phase=(),scalar=1):
    result=dag.boundary_module().normalize_message(n,ids,list(rows),list(phase),scalar)
    if result['status']!='EXACT':raise AssertionError(result)
    return result['message']


def four_lines(n=3,scalar=1,phase=()):
    # Low-bit point sets {0,1}, {4,6}, {3,7}, {2,5}; higher bits are free.
    rows=([[2,0],[4,0]],[[1,0],[4,1]],[[1,1],[2,1]],[[5,0],[6,1]])
    return [canonical(n,list(range(n)),equations,phase,scalar) for equations in rows]


def stage(messages,n=3,**options):
    budget=dag.Budget({})
    compressor=dag.CompressionMeter(budget,None)
    greedy,derived=compressor.reduce(n,list(range(n)),messages)
    recognizer=dag.RecognitionMeter(budget,options.get('policy'),options.get('caps'),options.get('aggregate'))
    recognition,output=recognizer.reduce(n,list(range(n)),derived)
    return budget,greedy,recognition,output


class RecognitionIntegrationTests(unittest.TestCase):
    def test_nonparallel_partition_and_signed_phase_replacement(self):
        for phase,scalar in [([],1),([3,4],Fraction(-3,7))]:
            messages=four_lines(scalar=scalar,phase=phase)
            budget,greedy,recognition,output=stage(messages)
            self.assertEqual(len(greedy['messages']),4)
            self.assertEqual(recognition['result']['status'],'EXACT')
            self.assertEqual(output,[canonical(3,[0,1,2],phase=phase,scalar=scalar)])
            self.assertEqual(budget.stats['recognition_removed_pieces'],3)
            self.assertGreater(budget.stats['recognition_work'],0)
            checking=dag.Budget({});compressor=dag.CompressionMeter(checking,None)
            _,fresh=compressor.reduce(3,[0,1,2],messages,greedy)
            _,verified=dag.RecognitionMeter(checking,None,None,None).reduce(3,[0,1,2],fresh,recognition)
            self.assertEqual(verified,output)

    def test_zero_replacement_and_correct_negative_retention(self):
        lines=four_lines()
        _,greedy,recognized,output=stage(lines+[canonical(3,[0,1,2],scalar=-1)])
        self.assertGreaterEqual(len(greedy['messages']),2)
        self.assertEqual(recognized['result']['status'],'EXACT')
        self.assertTrue(recognized['result']['message']['zero']);self.assertEqual(output,[])
        budget,greedy,recognized,output=stage(lines+[canonical(3,[0,1,2],[[1,0],[2,0],[4,0]])])
        self.assertEqual(recognized['result']['status'],'UNSUPPORTED')
        self.assertEqual(output,greedy['messages']);self.assertEqual(len(output),5)
        self.assertEqual(budget.stats['recognition_rejected'],1)

    def test_recognition_cannot_rescue_failed_mandatory_greedy(self):
        with patch.object(dag,'recognition_module',side_effect=AssertionError('optional stage ran too early')):
            result=dag.solve_formula(2,[[1,2],[1,2]],max_terms=1)
        self.assertEqual(result['status'],'UNKNOWN')
        self.assertEqual(result['stats']['recognition_attempts'],0)
        self.assertIsNone(result['certificate'])

    def test_optional_local_exhaustion_is_charged_identity(self):
        clauses=[[1,2],[1,2]];caps={'recognition_caps':{'max_work':0}}
        result=dag.solve_formula(2,clauses,**caps)
        self.assertEqual(result['status'],'EXACT');self.assertEqual(result['count'],3)
        self.assertGreater(result['stats']['recognition_local_unknown'],0)
        self.assertGreater(result['stats']['recognition_work'],0)
        checked=dag.verify_formula(2,clauses,result,**caps)
        self.assertTrue(checked['valid'],checked)
        self.assertEqual(checked['stats']['recognition_work'],0)
        self.assertEqual(checked['stats']['recognition_unchecked_identity_events'],result['stats']['recognition_local_unknown'])
        changed=deepcopy(result)
        for node in changed['certificate']['nodes']:
            if node['recognition']['attempted']:
                node['recognition']['result']['stats']={'work':-10**100}
        self.assertEqual(dag.verify_formula(2,clauses,changed,**caps),checked)

    def test_aggregate_exhaustion_stops_even_when_attempt_optional(self):
        for aggregate in ({'max_attempts':0},{'max_attempts':1},{'max_work':0}):
            result=dag.solve_formula(2,[[1,2],[1,2]],recognition_aggregate_caps=aggregate)
            self.assertEqual(result['status'],'UNKNOWN',(aggregate,result))
            self.assertIsNone(result['certificate']);self.assertIsNone(result['value'])
        result=dag.solve_formula(2,[[1,2],[1,2]])
        exhausted=dag.solve_formula(2,[[1,2],[1,2]],max_work=result['stats']['work']-1)
        self.assertEqual(exhausted['status'],'UNKNOWN')

    def test_schedule_and_external_policy_binding(self):
        clauses=[[1,2],[1,2]];result=dag.solve_formula(2,clauses)
        self.assertGreater(result['stats']['recognition_attempts'],0)
        for mutation in ('missing','skipped','extra_input','changed_policy'):
            changed=deepcopy(result)
            node=next(node for node in changed['certificate']['nodes'] if node['recognition']['attempted'])
            if mutation=='missing':del node['recognition']
            elif mutation=='skipped':node['recognition']={'attempted':False,'result':None}
            elif mutation=='extra_input':node['recognition']['inputs']=[]
            else:changed['certificate']['recognition_policy']['max_retained']=0
            self.assertEqual(dag.verify_formula(2,clauses,changed)['status'],'INVALID',mutation)
        self.assertEqual(dag.verify_formula(2,clauses,result,recognition_policy={'max_retained':0})['status'],'INVALID')

    def test_positive_replacement_is_bound_to_fresh_greedy_sum(self):
        messages=four_lines();_,greedy,recognition,_=stage(messages)
        changed=deepcopy(recognition);changed['result']['message']['scalar']=[17,1]
        with self.assertRaises(ValueError):
            dag.RecognitionMeter(dag.Budget({}),None,None,None).reduce(3,[0,1,2],greedy['messages'],changed)
        other=deepcopy(greedy['messages']);other[0]['scalar']=[2,1]
        with self.assertRaises(ValueError):
            dag.RecognitionMeter(dag.Budget({}),None,None,None).reduce(3,[0,1,2],other,recognition)

    def test_all_claimed_recognition_statistics_are_ignored_on_replay(self):
        clauses=[[1,2],[1,2]];result=dag.solve_formula(2,clauses)
        expected=dag.verify_formula(2,clauses,result);self.assertTrue(expected['valid'])
        changed=deepcopy(result);changed['stats']={'work':-1}
        for node in changed['certificate']['nodes']:
            if node['recognition']['attempted']:
                node['recognition']['result']['stats']={'work':-999999,'pair_contractions':10**100}
        actual=dag.verify_formula(2,clauses,changed)
        self.assertEqual(actual,expected)

    def test_width_policy_skips_without_hidden_calls(self):
        messages=four_lines(n=16)
        with patch.object(dag,'recognition_module',side_effect=AssertionError('width trigger ignored')):
            budget,greedy,recognized,output=stage(messages,n=16)
        self.assertEqual(recognized,{'attempted':False,'result':None})
        self.assertEqual(output,greedy['messages']);self.assertEqual(budget.stats['recognition_attempts'],0)

    def test_configuration_types_fail_closed(self):
        for kwargs in [{'recognition_caps':{'max_work':True}},
                       {'recognition_aggregate_caps':{'max_attempts':-1}},
                       {'recognition_policy':{'min_pieces':1}},
                       {'recognition_policy':{'max_pieces':1}},
                       {'recognition_caps':{'unknown_setting':1}}]:
            with self.assertRaises(ValueError):dag.solve_formula(2,[[1,2]],**kwargs)


if __name__=='__main__':unittest.main()
