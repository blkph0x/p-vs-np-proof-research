import unittest

from affine_weight_signature import (
    exact_signature_equality, full_signature, minimum_nonzero_rows_for_target,
    objective, signature, signature_difference,
)
from explicit_code_family import generate_columns, parameters


class AffineWeightSignatureTests(unittest.TestCase):
    def test_duplicate_affine_rows_preserve_function(self):
        left = (((1, 0), (2, 0), (3, 1)), (2, 2, 3))
        right = (((1, 0), (1, 0), (2, 0), (2, 0), (3, 1), (3, 1), (3, 1)),
                 (1, 1, 1, 1, 1, 1, 1))
        self.assertTrue(exact_signature_equality(*left, *right, 3))
        for assignment in range(8):
            self.assertEqual(objective(*left, assignment), objective(*right, assignment))

    def test_constant_and_nonzero_signature_are_complete(self):
        rows = ((0, 1), (1, 0), (1, 1))
        weights = (2, 3, 1)
        self.assertEqual(full_signature(rows, 1, weights), (8, {1: 2}))
        self.assertEqual(signature_difference(rows, weights, ((0, 1), (1, 0)), (2, 1), 1),
                         {'constant_numerator': 3, 'nonzero': {1: 1}})

    def test_signed_offset_control_and_explicit_family(self):
        rows = ((1, 0), (1, 1), (2, 0))
        self.assertEqual(signature(rows, 2, (2, -1, 1)), {1: 3, 2: 1})
        spec = parameters(7)
        _, forms = generate_columns(7)
        affine_rows = [(form, 0) for form in forms]
        self.assertEqual(minimum_nonzero_rows_for_target(
            affine_rows, spec['binary_rank'], [1] * len(forms)), spec['columns'])


if __name__ == '__main__':
    unittest.main()
