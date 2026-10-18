import json
import sys
from pathlib import Path
import unittest

LAB = Path(__file__).resolve().parent / 'semantic_frontier_expander_lab'
sys.path.insert(0, str(LAB))
import verify_semantic_frontier as verifier


class SemanticFrontierExpanderIntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.artifact = json.loads((LAB / 'RESULTS.json').read_text(encoding='utf-8'))

    def test_artifact_is_independently_replayable(self):
        self.assertTrue(self.artifact['all_checks_passed'])
        for row in self.artifact['rows']:
            expansion = verifier.expansion(row['n'], row['edges'])
            self.assertEqual(row['expansion'], expansion)
            for saved in row['sampled_orders']:
                pairs = verifier.productive(row['n'], row['edges'], saved['order'])
                self.assertEqual(saved['pairs'], [list(pair) for pair in pairs])
                self.assertTrue(verifier.productive_valid(row['n'], row['edges'], saved['order'], pairs))

    def test_every_saved_order_has_distinct_residual_witnesses(self):
        for row in self.artifact['rows']:
            for saved in row['sampled_orders']:
                pairs = verifier.productive(row['n'], row['edges'], saved['order'])
                valid, checked = verifier.separation_valid(row['n'], row['edges'], pairs)
                self.assertTrue(valid)
                self.assertEqual(checked, saved['separation']['patterns_checked'])

    def test_bounds_and_adversarial_mutation(self):
        for row in self.artifact['rows']:
            self.assertTrue(all(saved['productive_width'] >= row['theorem_lower_bound']
                                for saved in row['sampled_orders']))
        forged = json.loads(json.dumps(self.artifact['rows'][0]))
        forged['theorem_lower_bound'] = max(saved['productive_width']
                                            for saved in forged['sampled_orders']) + 1
        self.assertFalse(all(saved['productive_width'] >= forged['theorem_lower_bound']
                             for saved in forged['sampled_orders']))


if __name__ == '__main__':
    unittest.main()
