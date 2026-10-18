import unittest

from explicit_code_family import generate_columns, parameters
from linear_weight_signature import (
    exact_signature_equality, objective, signature, signature_difference,
)


class LinearWeightSignatureTests(unittest.TestCase):
    def test_duplicate_forms_preserve_signature(self):
        left = ((1, 2, 3), (1, 2, 3))
        right = ((3, 1, 2, 3), (1, 1, 2, 2))
        self.assertTrue(exact_signature_equality(*left, *right, 3))
        for assignment in range(8):
            self.assertEqual(objective(*left, assignment), objective(*right, assignment))

    def test_mismatch_has_exact_difference(self):
        difference = signature_difference((1, 2, 3), (1, 2, 3), (1, 2), (1, 1), 3)
        self.assertEqual(difference, {2: 1, 3: 3})

    def test_explicit_k7_has_one_signature_per_column(self):
        spec = parameters(7)
        _, rows = generate_columns(7)
        self.assertEqual(len(signature(rows, spec['binary_rank'], [1] * len(rows))), spec['columns'])


if __name__ == '__main__':
    unittest.main()
