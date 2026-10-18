import unittest

from nonlinear_weight_compression import (
    compressed_objective, digit_count, nonlinear_row_values, source_weight,
    threshold_row,
)


class NonlinearWeightCompressionTests(unittest.TestCase):
    def test_binary_digits_reconstruct_source_weight(self):
        forms = (1, 2, 3, 5, 9, 17, 7)
        self.assertEqual(digit_count(len(forms)), 3)
        for assignment in range(32):
            self.assertEqual(compressed_objective(forms, assignment),
                             source_weight(forms, assignment))
            self.assertEqual(sum(value << bit for bit, value in enumerate(
                nonlinear_row_values(forms, assignment))), source_weight(forms, assignment))

    def test_threshold_row_is_exact_decision_control(self):
        forms = (1, 2, 4)
        for assignment in range(8):
            expected = int(source_weight(forms, assignment) <= 1)
            self.assertEqual(threshold_row(forms, assignment, 1), expected)

    def test_empty_form_system_still_has_one_zero_digit_row(self):
        self.assertEqual(digit_count(0), 1)
        self.assertEqual(compressed_objective((), 0), 0)


if __name__ == '__main__':
    unittest.main()
