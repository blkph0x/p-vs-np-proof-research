from copy import deepcopy
import unittest
from dag_review import dag,requests,direct_audit,mutations,audit_all_node_rewrites


class DagReview(unittest.TestCase):
    def test_original_mixed_factors_and_every_node(self):
        for request in requests():
            result=dag.solve_factors(request['n'],request['factors'],order=request['order'])
            self.assertEqual(result['status'],'EXACT')
            self.assertTrue(dag.verify_factors(request['n'],request['factors'],result,order=request['order'])['valid'])
            direct_audit(request,result)
            audit_all_node_rewrites(result)

    def test_original_source_and_cross_product_mutations(self):
        n=5;clauses=[[1],[-1,2],[2,3],[-3,4],[4,5]]
        result=dag.solve_formula(n,clauses)
        self.assertEqual(result['status'],'EXACT')
        for name,changed in mutations(result):
            with self.subTest(name):self.assertFalse(dag.verify_formula(n,clauses,changed)['valid'])
        self.assertFalse(dag.verify_formula(n,clauses+[[]],result)['valid'])
        altered=deepcopy(result)
        for node in altered['certificate']['nodes']:
            node['compression']['stats']={key:0 for key in node['compression']['stats']}
        self.assertTrue(dag.verify_formula(n,clauses,altered)['valid'])
        self.assertEqual(dag.verify_formula(n,clauses,altered,compression_caps={'max_work':0})['status'],'UNKNOWN')

    def test_aggregate_budget_not_reset(self):
        n=4;clauses=[[1],[2],[3],[4]]
        exact=dag.solve_formula(n,clauses)
        for caps in [{'max_inputs':2},{'max_generated':1},{'max_steps':4},{'max_pairs':1},{'max_work':1}]:
            result=dag.solve_formula(n,clauses,compression_caps=caps)
            self.assertEqual(result['status'],'UNKNOWN')
            self.assertIsNone(result['value']);self.assertIsNone(result['certificate'])
            self.assertEqual(dag.verify_formula(n,clauses,exact,compression_caps=caps)['status'],'UNKNOWN')


if __name__=='__main__':unittest.main()
