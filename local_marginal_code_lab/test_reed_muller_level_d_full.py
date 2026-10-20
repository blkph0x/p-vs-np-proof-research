
"""Tests for the exact full RM(2,5) level-eight certificate."""
from __future__ import annotations

import json
import math
import copy
import unittest
from fractions import Fraction
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from reed_muller_full_level8 import PINNED, build_model, verify_primal  # noqa: E402
from REED_MULLER_LEVEL_D_FULL_INDEPENDENT_REVIEW import replay  # noqa: E402


class FullLevelEightTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.model = build_model()
        cls.certificate = json.loads(
            (HERE / "REED_MULLER_LEVEL_D_FULL_RESULTS.json").read_text(encoding="utf-8")
        )
        cls.masses = tuple(Fraction(value) for value in cls.certificate["primal_orbit_masses"])

    def test_scope_orbit_coverage(self):
        for size, masks in self.model["scope_reps"].items():
            total = sum(self.model["scope_orbit_sizes"][str(mask)] for mask in masks)
            self.assertEqual(total, math.comb(32, int(size)))

    def test_exact_support_and_negative_control(self):
        self.assertEqual(len(self.model["allowed_reps"]["510"]), 128)
        self.assertNotIn(0, self.model["allowed_reps"]["510"])
        self.assertEqual(
            self.model["allowed_reps"],
            self.certificate["allowed_projection_representatives"],
        )

    def test_quotient_shape(self):
        self.assertEqual(self.model["variable_orbit_count"], 2174)
        self.assertEqual(self.model["row_orbit_count"], 27926)
        self.assertEqual(self.model["quotient_nonzero_count"], 214059)
        self.assertEqual(self.model["affine_flat_span_rank"], 16)

    def test_saved_structure_matches_rebuild(self):
        self.assertEqual(self.model["variable_orbits"], self.certificate["variable_orbits"])
        self.assertEqual(self.model["rows"], self.certificate["row_orbits"])
        self.assertEqual(self.model["rhs"], self.certificate["rhs"])
        self.assertEqual(
            [{str(index): value for index, value in sorted(row.items())}
             for row in self.model["matrix"]],
            self.certificate["quotient_matrix"],
        )

    def test_exact_primal_certificate(self):
        result = verify_primal(self.model, self.masses)
        self.assertTrue(result["valid"])
        self.assertEqual(result["full_level_8_optimum"], "31/5")
        self.assertEqual(result["full_level_8_total_optimum"], "36/5")

    def test_primal_mutation_is_rejected(self):
        perturbed = list(self.masses)
        perturbed[0] += Fraction(1, 35)
        with self.assertRaises(ValueError):
            verify_primal(self.model, perturbed)

    def test_pinned_integer_optimum(self):
        self.assertEqual(len(PINNED), 32768)
        self.assertEqual(min(word.bit_count() for word in PINNED), 8)
        self.assertEqual(self.certificate["integer_pinned_optimum"], "7")
        self.assertEqual(self.certificate["integer_pinned_nonpin_optimum"], "7")
        self.assertEqual(self.certificate["integer_pinned_total_optimum"], "8")

    def test_scope_510_support_mutation_is_rejected(self):
        wrong = set(self.model["allowed_reps"]["510"])
        wrong.add(0)
        self.assertNotEqual(wrong, set(self.model["allowed_reps"]["510"]))

    def test_independent_reviewer_accepts_saved_certificate(self):
        result = replay(self.certificate, run_controls=False)
        self.assertTrue(result["valid"])
        self.assertEqual(result["full_level_8_optimum"], "31/5")
        self.assertEqual(result["full_level_8_total_optimum"], "36/5")

    def test_independent_reviewer_rejects_matrix_mutation(self):
        corrupted = copy.deepcopy(self.certificate)
        first_key = next(iter(corrupted["quotient_matrix"][0]))
        corrupted["quotient_matrix"][0][first_key] += 1
        with self.assertRaisesRegex(ValueError, "quotient matrix replay mismatch"):
            replay(corrupted, run_controls=False)

    def test_independent_reviewer_rejects_objective_mutation(self):
        corrupted = copy.deepcopy(self.certificate)
        corrupted["objective"][0] += 1
        with self.assertRaisesRegex(ValueError, "objective vector reconstruction mismatch"):
            replay(corrupted, run_controls=False)


if __name__ == "__main__":
    unittest.main()
