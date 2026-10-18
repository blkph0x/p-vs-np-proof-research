import unittest

import semantic_frontier as sf


class SemanticFrontierTests(unittest.TestCase):
    def test_controls_have_exact_expansion_certificates(self):
        for control in sf.controls():
            expansion = sf.expansion_certificate(control['n'], control['edges'])
            self.assertGreaterEqual(expansion['epsilon_numerator'], 1)
            self.assertGreaterEqual(expansion['maximum_degree'], 3)

    def test_productive_sequences_and_separation(self):
        for index, control in enumerate(sf.controls()):
            expansion = sf.expansion_certificate(control['n'], control['edges'])
            lower = sf.theorem_lower_bound(
                control['n'], expansion['maximum_degree'],
                expansion['epsilon_numerator'], expansion['epsilon_denominator'])
            for order in sf.sampled_orders(control['n'], 20261018 + index)[:3]:
                pairs = sf.productive_sequence(control['n'], control['edges'], order)
                self.assertGreaterEqual(len(pairs), lower)
                self.assertTrue(sf.verify_productive_sequence(
                    control['n'], control['edges'], order, pairs))
                self.assertTrue(sf.verify_residual_separation(
                    control['n'], control['edges'], pairs)['valid'])


if __name__ == '__main__':
    unittest.main()
