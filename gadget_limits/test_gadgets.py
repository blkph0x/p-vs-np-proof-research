from fractions import Fraction
import unittest

from validate_gadgets import (alternative_encoding_controls, exhaustive_audit,
                              first_submodularity_violation, parity_controls,
                              terminal_cut_values)


class GadgetTests(unittest.TestCase):
    def test_cut_conventions_and_auxiliary_minimum(self):
        # Variable0; source1; sink2.
        self.assertEqual(terminal_cut_values(1, 0, [(1, 0, 3)]), [0, 3])
        self.assertEqual(terminal_cut_values(1, 0, [(0, 2, 3)]), [3, 0])
        self.assertEqual(terminal_cut_values(1, 0, [(1, 2, 3)]), [3, 3])
        self.assertEqual(terminal_cut_values(1, 0, [(2, 1, 3), (0, 0, 7)]), [0, 0])
        # Directed terminal-auxiliary-terminal chain acts as a unit cut arc.
        self.assertEqual(terminal_cut_values(2, 1, [(0, 2, 1), (2, 1, 1)]), [0, 0, 1, 0])

    def test_exact_rational_and_parallel_arcs(self):
        weight = Fraction(1, 3)
        self.assertEqual(terminal_cut_values(1, 0, [(1, 0, weight), (1, 0, weight)]),
                         [0, Fraction(2, 3)])
        self.assertEqual(terminal_cut_values(0, 2, []), [0])

    def test_all_complements_of_both_parities(self):
        cases = parity_controls()
        self.assertEqual(len(cases), 16)
        for case in cases:
            self.assertEqual(case["violation"]["slack"], -2)

    def test_alternative_encodings_are_not_overexcluded(self):
        controls = alternative_encoding_controls()
        self.assertTrue(controls["matching_feasible_iff_even_parity"])
        self.assertEqual(controls["one_hot_restricted_values"], [1, 0, 0, 1])

    def test_small_exhaustive_control(self):
        result = exhaustive_audit(max_terminals=2, max_auxiliaries=1, max_arcs=2)
        self.assertEqual(result["status"], "PASS")
        self.assertGreater(result["graphs"], 300)

    def test_invalid_inputs(self):
        for terminals, auxiliaries, arcs in [(-1, 0, []), (True, 0, []),
                (1, -1, []), (1, 0, [(0, 3, 1)]), (1, 0, [(True, 0, 1)]),
                (1, 0, [(0, 1, -1)]), (1, 0, [(0, 1, True)]),
                (1, 0, [(0, 1, 0.5)]), (1, 0, [(0, 1)])]:
            with self.assertRaises(ValueError):
                terminal_cut_values(terminals, auxiliaries, arcs)
        for values in [[], [0, 1, 2]]:
            with self.assertRaises(ValueError):
                first_submodularity_violation(values)


if __name__ == "__main__":
    unittest.main()
