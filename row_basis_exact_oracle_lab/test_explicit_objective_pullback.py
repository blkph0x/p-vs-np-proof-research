import json
from pathlib import Path
import unittest

from explicit_code_family import generate_columns, parameters
from explicit_objective_pullback import classify_natural_map


HERE = Path(__file__).resolve().parent


class ExplicitObjectivePullbackTests(unittest.TestCase):
    def test_saved_defects_are_positive(self):
        payload = json.loads((HERE / 'EXPLICIT_OBJECTIVE_PULLBACK_RESULTS.json').read_text(encoding='utf-8'))
        self.assertEqual(payload['degrees_checked'], [7, 8, 9])
        self.assertEqual([row['defect'] for row in payload['records']], [8192, 32768, 131072])

    def test_k7_direct_certificate(self):
        record = classify_natural_map(7)
        self.assertEqual(record['columns'], parameters(7)['columns'])
        self.assertEqual(record['defect'], 8192)
        self.assertEqual(record['values'][0] + record['values'][1] - record['values'][2], 8192)


if __name__ == '__main__':
    unittest.main()
