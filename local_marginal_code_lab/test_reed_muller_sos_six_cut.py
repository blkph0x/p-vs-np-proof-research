"""Adversarial tests for the exact sixth-cut RM(2,5) certificate."""
from __future__ import annotations

import copy
import json
import unittest
from fractions import Fraction
from pathlib import Path

try:
    from REED_MULLER_SOS_SIX_CUT_INDEPENDENT_REVIEW import _q_vectors, replay
except ModuleNotFoundError:
    from local_marginal_code_lab.REED_MULLER_SOS_SIX_CUT_INDEPENDENT_REVIEW import _q_vectors, replay

HERE = Path(__file__).resolve().parent


class SixCutCertificateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = json.loads((HERE / "REED_MULLER_LEVEL_D_FULL_RESULTS.json").read_text(encoding="utf-8"))
        cls.certificate = json.loads((HERE / "REED_MULLER_SOS_SIX_CUT_RESULTS.json").read_text(encoding="utf-8"))

    def test_independent_replay_accepts_saved_exact_optimum(self):
        result = replay(self.source, self.certificate)
        self.assertTrue(result["valid"])
        self.assertEqual(result["status"], "EXACT_OPTIMUM")

    def test_exact_endpoints_and_zero_gap(self):
        expected = "22465669893401/3255387995415"
        self.assertEqual(self.certificate["certified_lower_bound"], expected)
        self.assertEqual(self.certificate["certified_upper_bound"], expected)
        self.assertEqual(self.certificate["dual_objective"], expected)
        self.assertEqual(self.certificate["unresolved_optimum_gap"], "0")
        self.assertEqual(self.certificate["dual_reduced_cost_minimum"], "0")
        self.assertEqual(self.certificate["dual_zero_reduced_cost_count"], 2147)

    def test_exact_basis_metadata(self):
        basis = self.certificate["dual_basis"]
        self.assertEqual(basis["basis_column_count"], 2133)
        self.assertEqual(len(basis["basis_column_indices"]), 2133)
        self.assertEqual(len(set(basis["basis_column_indices"])), 2133)
        self.assertEqual(basis["basis_row_count"], 2133)
        self.assertEqual(len(basis["basis_row_indices"]), 2133)

    def test_sixth_cut_vectors_have_expected_signed_support(self):
        q1, q2, q3, q4, q5, q6 = _q_vectors(self.source)
        self.assertEqual(sum(value != 0 for value in q1), 2)
        self.assertEqual(sum(value != 0 for value in q2), 2)
        self.assertGreater(sum(value != 0 for value in q3), 2)
        self.assertGreater(sum(value != 0 for value in q4), 2)
        self.assertGreater(sum(value != 0 for value in q5), 2)
        self.assertGreater(sum(value != 0 for value in q6), 2)
        self.assertTrue(any(value > 0 for value in q5))
        self.assertTrue(any(value < 0 for value in q5))
        self.assertTrue(any(value > 0 for value in q6))
        self.assertTrue(any(value < 0 for value in q6))

    def test_integer_polynomials_are_nonnegative_on_weights(self):
        self.assertTrue(all(t * (31 - t) * (t - 3) * (t - 4) * (t + 28) >= 0
                            for t in range(32)))
        self.assertTrue(all(t * (31 - t) * (t - 3) * (t - 4) >= 0
                            for t in range(32)))
        self.assertTrue(all((t - 6) * (t - 7) * (31 - t) * (t + 32) ** 2 >= 0
                            for t in range(32)))
        values = self.certificate["primal_cut_values"]
        self.assertEqual(values["integer_adjacent_product_6_23"], "0")
        self.assertEqual(values["integer_adjacent_boundary_square_6_7"], "0")

    def test_primal_mutation_is_rejected(self):
        mutated = copy.deepcopy(self.certificate)
        mutated["primal_orbit_masses"][0] = str(Fraction(mutated["primal_orbit_masses"][0]) + 1)
        with self.assertRaises(ValueError):
            replay(self.source, mutated)

    def test_dual_mutation_is_rejected(self):
        mutated = copy.deepcopy(self.certificate)
        row = next(iter(mutated["dual_row_values"]))
        mutated["dual_row_values"][row] = str(Fraction(mutated["dual_row_values"][row]) + 1)
        with self.assertRaises(ValueError):
            replay(self.source, mutated)

    def test_sixth_cut_constant_mutation_is_rejected(self):
        mutated = copy.deepcopy(self.certificate)
        next(cut for cut in mutated["cuts"] if cut["name"] == "integer_adjacent_boundary_square_6_7")["q_constant"] = "1"
        with self.assertRaises(ValueError):
            replay(self.source, mutated)

    def test_sixth_multiplier_mutation_is_rejected(self):
        mutated = copy.deepcopy(self.certificate)
        next(cut for cut in mutated["cuts"] if cut["name"] == "integer_adjacent_boundary_square_6_7")["dual_multiplier"] = "1"
        with self.assertRaises(ValueError):
            replay(self.source, mutated)

    def test_source_matrix_mutation_is_rejected(self):
        mutated_source = copy.deepcopy(self.source)
        row = mutated_source["quotient_matrix"][0]
        column = next(iter(row))
        row[column] = int(row[column]) + 1
        with self.assertRaises(ValueError):
            replay(mutated_source, self.certificate)


if __name__ == "__main__":
    unittest.main()
