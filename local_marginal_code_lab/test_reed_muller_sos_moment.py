"""Adversarial tests for the exact SOS moment cut audit."""

from __future__ import annotations

import copy
import json
import unittest
from pathlib import Path

from REED_MULLER_SOS_MOMENT_INDEPENDENT_REVIEW import replay


ROOT = Path(__file__).resolve().parent


class SosMomentTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.certificate = json.loads(
            (ROOT / "REED_MULLER_LEVEL_D_FULL_RESULTS.json").read_text(encoding="utf-8")
        )
        cls.audit = json.loads(
            (ROOT / "REED_MULLER_SOS_MOMENT_RESULTS.json").read_text(encoding="utf-8")
        )

    def test_exact_cut_replay(self):
        result = replay(self.certificate, self.audit)
        self.assertTrue(result["valid"])
        self.assertEqual(result["scaled_square_expectation"], "-992/7")
        self.assertEqual(result["square_expectation"], "-992/175")

    def test_boolean_square_is_strictly_positive(self):
        self.assertEqual(self.audit["boolean_control"]["minimum_scaled_square"], 1)
        self.assertTrue(self.audit["boolean_control"]["all_nonnegative"])
        self.assertEqual(self.audit["boolean_control"]["checked_counts"], 32)

    def test_mutated_moment_is_rejected(self):
        forged = copy.deepcopy(self.audit)
        forged["moments"]["pair_moment"] = "2/35"
        with self.assertRaises(ValueError):
            replay(self.certificate, forged)

    def test_mutated_boolean_control_is_rejected(self):
        forged = copy.deepcopy(self.audit)
        forged["boolean_control"]["minimum_scaled_square"] = 0
        with self.assertRaises(ValueError):
            replay(self.certificate, forged)


if __name__ == "__main__":
    unittest.main()
