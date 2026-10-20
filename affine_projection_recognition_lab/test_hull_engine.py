"""Producer-focused smoke and accounting tests; independent checker is separate."""
import unittest
from affine_hull import canonical_equations,compile_outside,recover


class HullProducerTests(unittest.TestCase):
    def test_nonaffine_projection_can_have_exact_full_hull(self):
        result=recover(2,0,[[1,2]])
        self.assertEqual((result['status'],result['equations'],result['dimension']),('EXACT_HULL',[],2))
        self.assertEqual(len(result['queries']),3)
        self.assertTrue(all(q['result']['status']=='SAT' for q in result['queries']))

    def test_hidden_variables_and_final_unsat_trace(self):
        original=[[-1,2],[1,-2],[3]]
        result=recover(2,1,original)
        self.assertEqual((result['status'],result['equations'],result['dimension']),('EXACT_HULL',[[3,0]],1))
        self.assertEqual(result['queries'][-1]['result']['status'],'UNSAT')
        self.assertTrue(any(e['kind']=='terminal-empty' for e in result['queries'][-1]['result']['proof']))
        for key,total in result['solver_totals'].items():
            self.assertEqual(total,sum(q['result']['stats'][key] for q in result['queries']))
        self.assertLessEqual(result['solver_totals']['conflicts'],result['solver_totals']['decisions']+len(result['queries']))

    def test_empty_and_zero_width_conventions(self):
        result=recover(1,0,[[1],[-1]])
        self.assertEqual((result['status'],result['equations'],result['dimension']),('EMPTY',[[0,1]],None))
        result=recover(0,0,[])
        self.assertEqual((result['status'],result['equations'],result['dimension']),('EXACT_HULL',[],0))
        self.assertEqual(len(result['queries']),1)
        self.assertEqual(recover(0,0,[[]])['status'],'EMPTY')

    def test_decision_cap_is_aggregate_and_zero_still_allows_propagation(self):
        result=recover(2,0,[],max_decisions=2)
        self.assertEqual(result['status'],'UNKNOWN')
        self.assertEqual(result['solver_totals']['decisions'],2)
        self.assertIsNone(result['equations']);self.assertIsNone(result['dimension'])
        result=recover(1,0,[[1]],max_decisions=0)
        self.assertEqual((result['status'],result['equations']),('EXACT_HULL',[[1,1]]))
        self.assertEqual(result['solver_totals']['decisions'],0)

    def test_call_and_input_caps_have_no_exact_output(self):
        for options in [dict(max_calls=0),dict(max_calls=1),dict(max_input_vars=0),dict(max_input_clauses=0)]:
            result=recover(1,0,[[1]],**options)
            self.assertEqual(result['status'],'UNKNOWN');self.assertIsNone(result['equations']);self.assertIsNone(result['dimension'])
        self.assertEqual(recover(10**9,0,[])['reason'],'INPUT_VARIABLE_CAP')

    def test_strict_inputs_and_helper_conventions(self):
        for m,q,clauses in [(True,0,[]),(1,False,[]),(1,0,[[True]]),(1,0,[[1.0]]),
                            (1,0,[['1']]),(1,0,[[0]]),(1,0,[[2]]),(1,0,[None])]:
            with self.assertRaises(ValueError):recover(m,q,clauses)
        for name in ['max_decisions','max_calls','max_input_vars','max_input_clauses']:
            for value in [-1,True,1.0]:
                with self.assertRaises(ValueError):recover(1,0,[],**{name:value})
        self.assertEqual(canonical_equations(3,[1,7]),([[1,1],[6,0]],1))
        self.assertEqual(canonical_equations(0,[]),([[0,1]],None))
        self.assertEqual(compile_outside(1,[[1]],[]),(1,[[1],[]]))
        self.assertEqual(compile_outside(1,[[1]],[[0,1]]),(1,[[1]]))
        self.assertEqual(compile_outside(2,[],[[3,0]]),
                         (3,[[-1,2,3],[1,-2,3],[1,2,-3],[-1,-2,-3],[3]]))


if __name__=='__main__':unittest.main()
