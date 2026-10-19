"""Adversarial tests for the finite SOS-strengthened RM(2,5) optimum."""
from __future__ import annotations

import copy
import json
import unittest
from fractions import Fraction
from pathlib import Path

try:
    from REED_MULLER_SOS_STRENGTHENED_INDEPENDENT_REVIEW import _cut_vector, replay
except ModuleNotFoundError:  # Also support invoking this test from the repository root.
    from local_marginal_code_lab.REED_MULLER_SOS_STRENGTHENED_INDEPENDENT_REVIEW import _cut_vector, replay


HERE = Path(__file__).resolve().parent


class StrengthenedCertificateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = json.loads((HERE / "REED_MULLER_LEVEL_D_FULL_RESULTS.json").read_text(encoding="utf-8"))
        cls.certificate = json.loads((HERE / "REED_MULLER_SOS_STRENGTHENED_RESULTS.json").read_text(encoding="utf-8"))

    def test_independent_replay_accepts_saved_exact_optimum(self):
        result = replay(self.source, self.certificate)
        self.assertTrue(result["valid"])
        self.assertEqual(result["status"], "EXACT_OPTIMUM")

    def test_exact_optimum_and_zero_gap(self):
        self.assertEqual(self.certificate["certified_lower_bound"], "7037/1095")
        self.assertEqual(self.certificate["certified_upper_bound"], "7037/1095")
        self.assertEqual(self.certificate["unresolved_optimum_gap"], "0")
        self.assertEqual(Fraction("7037/1095"), Fraction(self.certificate["dual_objective"]))
        self.assertEqual(self.certificate["dual_reduced_cost_minimum"], "0")

    def test_exact_dual_basis_metadata(self):
        basis = self.certificate["dual_basis"]
        self.assertEqual(basis["basis_column_count"], 1890)
        self.assertEqual(len(basis["basis_column_indices"]), 1890)
        self.assertEqual(len(set(basis["basis_column_indices"])), 1890)

    def test_cut_vector_has_only_nonpin_singleton_and_pair_columns(self):
        q = _cut_vector(self.source)
        self.assertEqual(sum(value != 0 for value in q), 2)
        self.assertIn(Fraction("-1767/5"), q)
        self.assertIn(Fraction(930), q)

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

    def test_cut_constant_mutation_is_rejected(self):
        mutated = copy.deepcopy(self.certificate)
        mutated["cut"]["q_constant"] = "962/25"
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
