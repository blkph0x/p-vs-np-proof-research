"""Adversarial tests for the exact three-cut RM(2,5) certificate."""
from __future__ import annotations

import copy
import json
import unittest
from fractions import Fraction
from pathlib import Path

try:
    from REED_MULLER_SOS_THREE_CUT_INDEPENDENT_REVIEW import _q_vectors, replay
except ModuleNotFoundError:
    from local_marginal_code_lab.REED_MULLER_SOS_THREE_CUT_INDEPENDENT_REVIEW import _q_vectors, replay

HERE = Path(__file__).resolve().parent


class ThreeCutCertificateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = json.loads((HERE / "REED_MULLER_LEVEL_D_FULL_RESULTS.json").read_text(encoding="utf-8"))
        cls.certificate = json.loads((HERE / "REED_MULLER_SOS_THREE_CUT_RESULTS.json").read_text(encoding="utf-8"))

    def test_independent_replay_accepts_saved_exact_optimum(self):
        result = replay(self.source, self.certificate)
        self.assertTrue(result["valid"])
        self.assertEqual(result["status"], "EXACT_OPTIMUM")

    def test_exact_endpoints_and_zero_gap(self):
        self.assertEqual(self.certificate["certified_lower_bound"], "5231/801")
        self.assertEqual(self.certificate["certified_upper_bound"], "5231/801")
        self.assertEqual(self.certificate["dual_objective"], "5231/801")
        self.assertEqual(self.certificate["unresolved_optimum_gap"], "0")
        self.assertEqual(self.certificate["dual_reduced_cost_minimum"], "0")

    def test_exact_dual_basis_metadata(self):
        basis = self.certificate["dual_basis"]
        self.assertEqual(basis["basis_column_count"], 1183)
        self.assertEqual(len(basis["basis_column_indices"]), 1183)
        self.assertEqual(len(set(basis["basis_column_indices"])), 1183)

    def test_three_cut_vectors_have_expected_support(self):
        q1, q2, q3 = _q_vectors(self.source)
        self.assertEqual(sum(value != 0 for value in q1), 2)
        self.assertEqual(sum(value != 0 for value in q2), 2)
        self.assertGreater(sum(value != 0 for value in q3), 2)
        self.assertIn(Fraction("-1767/5"), q1)
        self.assertIn(Fraction(930), q1)
        self.assertIn(Fraction(-372), q2)
        self.assertIn(Fraction(930), q2)

    def test_third_integer_polynomial_is_nonnegative_on_weights(self):
        self.assertTrue(all((t - 6) * (t - 7) * (t - 23) * (t - 24) >= 0 for t in range(32)))
        self.assertEqual(self.certificate["primal_cut_values"]["integer_adjacent_product_6_23"], "0")

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

    def test_third_cut_constant_mutation_is_rejected(self):
        mutated = copy.deepcopy(self.certificate)
        next(cut for cut in mutated["cuts"] if cut["name"] == "integer_adjacent_product_6_23")["q_constant"] = "23185"
        with self.assertRaises(ValueError):
            replay(self.source, mutated)

    def test_third_multiplier_mutation_is_rejected(self):
        mutated = copy.deepcopy(self.certificate)
        next(cut for cut in mutated["cuts"] if cut["name"] == "integer_adjacent_product_6_23")["dual_multiplier"] = "8/9612"
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
