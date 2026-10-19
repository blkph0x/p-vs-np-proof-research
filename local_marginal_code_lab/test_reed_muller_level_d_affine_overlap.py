"""Adversarial tests for the affine-overlap RM(2,5) certificate."""

from __future__ import annotations

import copy
import json
import unittest
from fractions import Fraction
from pathlib import Path

from REED_MULLER_LEVEL_D_AFFINE_OVERLAP_INDEPENDENT_REVIEW import _rebuild, replay


ROOT = Path(__file__).resolve().parent


class ReedMullerAffineOverlapTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.payload = json.loads((ROOT / "REED_MULLER_LEVEL_D_AFFINE_OVERLAP_RESULTS.json").read_text())
        cls.model = _rebuild()

    def test_saved_result_replays(self):
        result = replay(self.payload, self.model)
        self.assertTrue(result["valid"])
        self.assertEqual(result["selected_model_optimum"], "31/5")
        self.assertEqual(result["full_level_8_status"], "UNRESOLVED")

    def test_scope_and_orbit_counts(self):
        result = replay(self.payload, self.model)
        self.assertEqual(result["scope_counts"], {"1": 32, "2": 496, "4": 1240, "8": 620})
        self.assertEqual(result["variable_orbits"], 28)
        self.assertEqual(result["row_orbits"], 53)

    def test_dual_and_primal_match_exactly(self):
        result = replay(self.payload, self.model)
        self.assertEqual(result["dual_reduced_cost_minimum"], "0")
        self.assertEqual(result["full_level_8_lower_bound"], "31/5")

    def test_compact_dual_identity(self):
        """The saved dual reduces the objective gap to six nonnegative orbit masses."""
        _, _, _, _, _, _, matrix, rhs, objective, _ = self.model
        dual = [Fraction(value) for value in self.payload["dual_row_values"]]
        reduced = [
            objective[index]
            - sum(Fraction(row.get(index, 0)) * dual[row_index]
                  for row_index, row in enumerate(matrix))
            for index in range(len(objective))
        ]
        expected = {
            2: Fraction(434, 5),
            3: Fraction(682, 5),
            4: Fraction(124, 5),
            7: Fraction(496, 5),
            8: Fraction(1736, 5),
            9: Fraction(248),
        }
        self.assertEqual({index: value for index, value in enumerate(reduced) if value}, expected)
        self.assertEqual(sum(value * target for value, target in zip(dual, rhs)), Fraction(31, 5))

    def test_mutated_primal_is_rejected(self):
        forged = copy.deepcopy(self.payload)
        forged["primal_orbit_masses"][0] = "1/8"
        with self.assertRaises(ValueError):
            replay(forged, self.model)

    def test_mutated_dual_is_rejected(self):
        forged = copy.deepcopy(self.payload)
        forged["dual_row_values"][5] = "-123/5"
        with self.assertRaises(ValueError):
            replay(forged, self.model)

    def test_mutated_matrix_is_rejected(self):
        forged = copy.deepcopy(self.payload)
        forged["quotient_matrix"][0]["0"] += 1
        with self.assertRaises(ValueError):
            replay(forged, self.model)

    def test_full_level_status_cannot_be_promoted(self):
        forged = copy.deepcopy(self.payload)
        forged["full_level_8_status"] = "PROVED"
        with self.assertRaises(ValueError):
            replay(forged, self.model)


if __name__ == "__main__":
    unittest.main()
