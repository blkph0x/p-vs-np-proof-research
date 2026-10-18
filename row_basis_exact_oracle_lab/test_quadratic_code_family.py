import copy
import json
from pathlib import Path
import unittest
import quadratic_code_family as producer
import verify_quadratic_code_family as verifier

HERE=Path(__file__).resolve().parent

class QuadraticCodeFamilyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.artifact=json.loads((HERE/'QUADRATIC_CODE_FAMILY_RESULTS.json').read_text(encoding='utf-8'))

    def test_quadratic_scaling_formula(self):
        for degree in range(4,13):
            spec=producer.parameters(degree)
            self.assertGreater(spec['minimum_code_distance'],spec['low_weight_budget'])
            self.assertGreaterEqual(spec['binary_rank'],spec['field_size']//4)
            self.assertLess(spec['columns'],16*spec['binary_rank']*spec['binary_rank'])
            self.assertEqual(spec['state_lower_bound'],1<<spec['binary_rank'])

    def test_saved_degrees_and_states(self):
        self.assertEqual(self.artifact['degrees_checked'],[4,5,6,7])
        self.assertEqual([row['parameters']['binary_rank'] for row in self.artifact['records']],[8,15,30,63])
        self.assertEqual([row['parameters']['columns'] for row in self.artifact['records']],[240,992,4032,16256])

    def test_independent_replay(self):
        self.assertTrue(all(verifier.verify_record(row) for row in self.artifact['records']))

    def test_sampled_exceptional_rank(self):
        self.assertTrue(all(saved['exceptional_rank']==row['parameters']['binary_rank'] for row in self.artifact['records'] for saved in row['sampled_stats']))

    def test_forged_record_rejected(self):
        forged=copy.deepcopy(self.artifact['records'][0]); forged['parameters']['state_lower_bound']=0
        self.assertFalse(verifier.verify_record(forged))

    def test_distance_bound_is_strict(self):
        for row in self.artifact['formula_sweep']:
            self.assertGreater(row['minimum_code_distance'],row['low_weight_budget'])

if __name__=='__main__': unittest.main()
