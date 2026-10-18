import copy
import json
import sys
from pathlib import Path
import unittest

LAB = Path(__file__).resolve().parent / 'linear_frontier_order_lab'
sys.path.insert(0, str(LAB))
import verify_complete_graph_frontier as verifier


class CompleteGraphFrontierIntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.artifact = json.loads((LAB / 'COMPLETE_GRAPH_FRONTIER_RESULTS.json').read_text(encoding='utf-8'))

    def test_formula_sweep_range(self):
        self.assertEqual([row['vertices'] for row in self.artifact['formula_sweep']], list(range(4, 65)))

    def test_cutwise_formula_range(self):
        self.assertEqual([row['vertices'] for row in self.artifact['cutwise_formula']], list(range(4, 65)))
        for row in self.artifact['cutwise_formula']:
            m = row['vertices'] * (row['vertices'] - 1) // 2
            self.assertEqual(len(row['minimum_lambda_by_cut']), m + 1)
            self.assertEqual(row['minimum_lambda_by_cut'],
                             row['minimum_lambda_by_cut'][::-1])

    def test_cutwise_small_controls_are_exhaustive(self):
        for row in self.artifact['cutwise_controls']:
            self.assertEqual(row, verifier.exhaustive_cutwise_minima(row['vertices']))

    def test_state_bound_scales(self):
        self.assertEqual(self.artifact['formula_sweep'][-1]['half_cut_lambda_lower_bound'], 45)
        self.assertEqual(self.artifact['formula_sweep'][-1]['state_lower_bound'], 1 << 45)

    def test_independent_replay(self):
        self.assertTrue(all(verifier.verify_record(row) for row in self.artifact['records']))

    def test_all_sampled_orders_respect_bound(self):
        for row in self.artifact['records']:
            bound = row['parameters']['half_cut_lambda_lower_bound']
            self.assertTrue(all(saved['width'] >= bound for saved in row['sampled_orders']))

    def test_forged_record_rejected(self):
        forged = copy.deepcopy(self.artifact['records'][0])
        forged['parameters']['half_cut_lambda_lower_bound'] += 1
        self.assertFalse(verifier.verify_record(forged))

    def test_scope_is_affine_frontier_only(self):
        self.assertIn('affine frontier', self.artifact['scope'])


if __name__ == '__main__':
    unittest.main()
