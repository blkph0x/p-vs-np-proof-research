import unittest

from nonlinear_circuit_compression import (
    accumulator_width, circuit_gate_counts, circuit_weight, parity_bits,
    ripple_weight_bits,
)


class NonlinearCircuitCompressionTests(unittest.TestCase):
    def test_ripple_circuit_reconstructs_weight(self):
        forms = (1, 2, 3, 5, 9, 17, 7)
        self.assertEqual(accumulator_width(len(forms)), 3)
        for assignment in range(32):
            expected = sum((form & assignment).bit_count() & 1 for form in forms)
            self.assertEqual(circuit_weight(forms, assignment), expected)
            self.assertEqual(sum(bit << i for i, bit in enumerate(
                ripple_weight_bits(forms, assignment))), expected)

    def test_gate_counts_are_exact(self):
        forms = (1, 3, 7, 8)
        counts = circuit_gate_counts(forms)
        self.assertEqual(counts['output_bits'], 3)
        self.assertEqual(counts['parity_xor_gates'], 0 + 1 + 2 + 0)
        self.assertEqual(counts['accumulator_xor_gates'], 12)
        self.assertEqual(counts['accumulator_and_gates'], 12)
        self.assertEqual(counts['total_gates'], 27)

    def test_empty_system_has_zero_output(self):
        self.assertEqual(parity_bits((), 0), ())
        self.assertEqual(circuit_weight((), 0), 0)


if __name__ == '__main__':
    unittest.main()
