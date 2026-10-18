import copy
import json
import sys
from pathlib import Path
import unittest

LAB = Path(__file__).resolve().parent / 'row_basis_exact_oracle_lab'
sys.path.insert(0, str(LAB))
import quadratic_code_family as producer
import verify_quadratic_code_family as verifier


class QuadraticCodeFamilyIntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.artifact = json.loads((LAB / 'QUADRATIC_CODE_FAMILY_RESULTS.json').read_text(encoding='utf-8'))

    def test_saved_degrees_and_states(self):
        self.assertEqual(self.artifact['degrees_checked'], [4, 5, 6, 7])
        self.assertEqual([row['parameters']['binary_rank'] for row in self.artifact['records']], [8, 15, 30, 63])
        self.assertEqual([row['parameters']['columns'] for row in self.artifact['records']], [240, 992, 4032, 16256])

    def test_independent_replay(self):
        self.assertTrue(all(verifier.verify_record(row) for row in self.artifact['records']))

    def test_formula_sweep_has_quadratic_length(self):
        for spec in self.artifact['formula_sweep']:
            self.assertGreater(spec['minimum_code_distance'], spec['low_weight_budget'])
            self.assertGreaterEqual(spec['binary_rank'], spec['field_size'] // 4)
            self.assertLess(spec['columns'], 16 * spec['binary_rank'] ** 2)
            self.assertEqual(spec['state_lower_bound'], 1 << spec['binary_rank'])

    def test_all_sampled_transforms_have_full_exceptional_rank(self):
        for row in self.artifact['records']:
            self.assertTrue(all(saved['exceptional_rank'] == row['parameters']['binary_rank']
                                for saved in row['sampled_stats']))

    def test_forged_record_rejected(self):
        forged = copy.deepcopy(self.artifact['records'][0])
        forged['parameters']['state_lower_bound'] = 0
        self.assertFalse(verifier.verify_record(forged))

    def test_artifact_scope_is_route_specific(self):
        self.assertIn('route', self.artifact['scope'])


if __name__ == '__main__':
    unittest.main()
