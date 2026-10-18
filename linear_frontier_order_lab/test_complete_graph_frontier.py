import copy
import json
from pathlib import Path
import unittest

import complete_graph_frontier as producer
import verify_complete_graph_frontier as verifier

HERE = Path(__file__).resolve().parent


class CompleteGraphFrontierTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.artifact = json.loads((HERE / 'COMPLETE_GRAPH_FRONTIER_RESULTS.json').read_text(encoding='utf-8'))

    def test_formula_sweep(self):
        self.assertEqual([row['vertices'] for row in self.artifact['formula_sweep']], list(range(4, 65)))
        for row in self.artifact['formula_sweep']:
            self.assertEqual(row, producer.half_parameters(row['vertices']))
            self.assertEqual(row['state_lower_bound'], 1 << row['half_cut_lambda_lower_bound'])

    def test_exhaustive_half_cuts_match_theorem(self):
        for row in self.artifact['records']:
            self.assertEqual(row['exhaustive'], producer.exhaustive_half_cut(row['parameters']['vertices']))
            self.assertGreaterEqual(row['exhaustive']['minimum_lambda'],
                                    row['parameters']['half_cut_lambda_lower_bound'])

    def test_independent_replay(self):
        self.assertTrue(all(verifier.verify_record(row) for row in self.artifact['records']))

    def test_sampled_orders_hit_the_half_cut_bound(self):
        for row in self.artifact['records']:
            bound = row['parameters']['half_cut_lambda_lower_bound']
            self.assertTrue(all(saved['half_cut_lambda'] >= bound for saved in row['sampled_orders']))
            self.assertTrue(all(saved['width'] >= bound for saved in row['sampled_orders']))

    def test_forged_bound_rejected(self):
        forged = copy.deepcopy(self.artifact['records'][0])
        forged['parameters']['half_cut_lambda_lower_bound'] += 1
        self.assertFalse(verifier.verify_record(forged))

    def test_easy_family_scope(self):
        self.assertIn('easy satisfiable', (HERE / 'COMPLETE_GRAPH_FRONTIER_REPORT.md').read_text(encoding='utf-8'))


if __name__ == '__main__':
    unittest.main()
