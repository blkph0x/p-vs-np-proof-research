import json
from pathlib import Path
import unittest

from explicit_code_family import (
    field_modulus, irreducible, parameters, verify_sampled_transforms,
)


HERE = Path(__file__).resolve().parent


class ExplicitCodeFamilyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.payload = json.loads((HERE / 'EXPLICIT_CODE_FAMILY_RESULTS.json').read_text(encoding='utf-8'))

    def test_parameters_beat_low_weight_budget(self):
        for k in (7, 8, 9):
            spec = parameters(k)
            self.assertGreater(spec['minimum_code_distance'], spec['low_weight_budget'])
            self.assertEqual(spec['state_lower_bound'], 1 << spec['binary_rank'])

    def test_field_certificates(self):
        for k in (7, 8, 9):
            modulus = field_modulus(k)
            self.assertTrue(irreducible(modulus, k))

    def test_saved_and_sampled_k7_replay(self):
        saved = self.payload['records'][0]
        replay = verify_sampled_transforms(7, transform_count=2)
        self.assertEqual(replay['column_digest'], saved['column_digest'])
        self.assertEqual(replay['distinct_columns'], saved['distinct_columns'])
        self.assertTrue(all(row['exceptional_rank'] == 14 for row in replay['sampled_stats']))


if __name__ == '__main__':
    unittest.main()
