import unittest

from circuit_cnf import (at_most, build_circuit, build_threshold_circuit,
                          clauses_satisfied, evaluate_gates, pin_integer,
                          pin_variables)


class CircuitCNFTests(unittest.TestCase):
    def test_small_circuit_outputs_exact_hamming_weight(self):
        forms = (1, 2, 3, 5, 9, 17, 7)
        circuit = build_circuit(forms, 5)
        for assignment in range(32):
            values = evaluate_gates(circuit, assignment)
            self.assertTrue(clauses_satisfied(circuit['clauses'], values))
            output = sum(values[var] << bit for bit, var in enumerate(circuit['output_bits']))
            expected = sum((form & assignment).bit_count() & 1 for form in forms)
            self.assertEqual(output, expected)

    def test_pin_helpers_preserve_exact_units(self):
        circuit = build_circuit((1, 2), 2)
        clauses = pin_variables(circuit['clauses'], (1, 2), (1, 0))
        clauses = pin_integer(clauses, circuit['output_bits'], 1)
        values = evaluate_gates(circuit, 1)
        self.assertTrue(clauses_satisfied(clauses, values))
        wrong = pin_integer(pin_variables(circuit['clauses'], (1, 2), (1, 0)),
                           circuit['output_bits'], 0)
        self.assertFalse(clauses_satisfied(wrong, values))

    def test_gate_counts_and_order_are_well_formed(self):
        circuit = build_circuit((1, 3, 7), 3)
        self.assertEqual(circuit['order'], list(range(circuit['variables'])))
        self.assertEqual(circuit['gate_counts']['total_gates'], len(circuit['gates']))

    def test_finite_output_comparator(self):
        circuit = build_circuit((1, 2), 2)
        clauses = at_most(circuit['clauses'], circuit['output_bits'], 0)
        for assignment in range(4):
            values = evaluate_gates(circuit, assignment)
            accepted = clauses_satisfied(clauses, values)
            self.assertEqual(accepted, assignment == 0)

    def test_compact_threshold_circuit_matches_all_outputs(self):
        for threshold in range(5):
            circuit = build_threshold_circuit((1, 2, 3, 4, 5, 6, 7), 3, threshold)
            accept = circuit['comparator']['accept_variable']
            for assignment in range(8):
                values = evaluate_gates(circuit, assignment)
                output = sum(values[var] << bit for bit, var in enumerate(circuit['output_bits']))
                self.assertEqual(bool(values[accept]), output <= threshold)


if __name__ == '__main__':
    unittest.main()
