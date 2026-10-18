"""Adversarial tests for the RM(2,5) affine-flat star control."""

from __future__ import annotations

import copy
import json
import unittest
from fractions import Fraction
from pathlib import Path

from REED_MULLER_LEVEL_D_FLAT_STAR_INDEPENDENT_REVIEW import replay


ROOT = Path(__file__).resolve().parent


class ReedMullerFlatStarTests(unittest.TestCase):
    def test_saved_result_replays(self):
        payload = json.loads((ROOT / "REED_MULLER_LEVEL_D_FLAT_STAR_RESULTS.json").read_text())
        result = replay(payload["records"][0]["certificate"])
        self.assertTrue(result["valid"])
        self.assertEqual(result["star_relaxation_optimum"], "38/7")
        self.assertEqual(result["full_level_d_status"], "UNRESOLVED")

    def test_exact_marginal_arithmetic(self):
        self.assertEqual(Fraction(4, 7) * Fraction(2, 8), Fraction(1, 7))
        self.assertEqual(Fraction(1) + Fraction(155, 35), Fraction(38, 7))

    def test_mutated_point_is_rejected(self):
        payload = json.loads((ROOT / "REED_MULLER_LEVEL_D_FLAT_STAR_RESULTS.json").read_text())
        forged = copy.deepcopy(payload["records"][0]["certificate"])
        forged["point"][1] = "1/8"
        with self.assertRaises(ValueError):
            replay(forged)

    def test_mutated_status_cannot_claim_full_level_d(self):
        payload = json.loads((ROOT / "REED_MULLER_LEVEL_D_FLAT_STAR_RESULTS.json").read_text())
        forged = copy.deepcopy(payload["records"][0]["certificate"])
        forged["full_level_d_status"] = "PROVED"
        with self.assertRaises(ValueError):
            replay(forged)


if __name__ == "__main__":
    unittest.main()
