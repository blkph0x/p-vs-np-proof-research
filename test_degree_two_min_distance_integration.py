import json
import sys
from pathlib import Path
import unittest

LAB = Path(__file__).resolve().parent / 'degree_two_min_distance_lab'
sys.path.insert(0, str(LAB))
import verify_degree_two_solver as verifier


class DegreeTwoIntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.artifact = json.loads((LAB / 'RESULTS.json').read_text(encoding='utf-8'))

    def test_saved_solutions_match_independent_bruteforce(self):
        for row in self.artifact['rows']:
            instance = verifier.encode(row['rows'], row['columns'])
            expected = verifier.brute_force(instance)
            saved = row['solution']
            self.assertTrue(verifier.verify_solution(instance, saved))
            self.assertEqual(saved['distance'], None if expected is None else expected['distance'])

    def test_adversarial_mutation_rejected(self):
        row = self.artifact['rows'][0]
        forged = json.loads(json.dumps(row['solution']))
        forged['selected_columns'] = forged['selected_columns'][:-1]
        self.assertFalse(verifier.verify_solution(verifier.encode(row['rows'], row['columns']), forged))

    def test_scope_is_column_weight_two(self):
        self.assertIn('column weight at most two', self.artifact['scope'])


if __name__ == '__main__':
    unittest.main()
