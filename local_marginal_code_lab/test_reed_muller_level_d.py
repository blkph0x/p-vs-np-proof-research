"""Adversarial tests for the exact RM(1,3) level-four certificate."""

from __future__ import annotations

import copy
import json
import unittest
from pathlib import Path

from REED_MULLER_LEVEL_D_INDEPENDENT_REVIEW import model_data, replay_certificate


ROOT = Path(__file__).resolve().parent


class ReedMullerLevelDTests(unittest.TestCase):
    def test_saved_certificate_replays_exactly(self):
        certificate = json.loads((ROOT / "REED_MULLER_LEVEL_D_DUAL.json").read_text())
        result = replay_certificate(certificate)
        self.assertTrue(result["valid"])
        self.assertEqual(result["combined_relaxation_optimum"], "4")
        self.assertEqual(result["dual_entry_count"], 113)

    def test_saved_result_and_review_bind_the_certificate(self):
        results = json.loads((ROOT / "REED_MULLER_LEVEL_D_RESULTS.json").read_text())
        review = json.loads(
            (ROOT / "REED_MULLER_LEVEL_D_INDEPENDENT_REVIEW.json").read_text()
        )
        self.assertEqual(results["schema"], "reed_muller_level_d_results_v1")
        self.assertEqual(review["schema"], "reed_muller_level_d_independent_review_v1")
        self.assertTrue(review["valid"])
        self.assertEqual(results["records"][0]["verification"], review["records"][0])

    def test_rebuilt_model_counts_are_fixed(self):
        data = model_data()
        self.assertEqual(len(data["scopes"]), 163)
        self.assertEqual(len(data["variables"]), 982)
        self.assertEqual(len(data["pinned"]), 8)
        self.assertIn(15, data["words"])

    def test_mutated_multiplier_is_rejected(self):
        certificate = json.loads((ROOT / "REED_MULLER_LEVEL_D_DUAL.json").read_text())
        forged = copy.deepcopy(certificate)
        forged["entries"][0]["multiplier"] += 1
        with self.assertRaises(ValueError):
            replay_certificate(forged)

    def test_mutated_scope_assignment_is_rejected(self):
        certificate = json.loads((ROOT / "REED_MULLER_LEVEL_D_DUAL.json").read_text())
        forged = copy.deepcopy(certificate)
        forged["entries"][2]["assignment"] = [1]
        with self.assertRaises(ValueError):
            replay_certificate(forged)

    def test_mutated_shape_claim_is_rejected(self):
        certificate = json.loads((ROOT / "REED_MULLER_LEVEL_D_DUAL.json").read_text())
        forged = copy.deepcopy(certificate)
        forged["variable_count"] += 1
        with self.assertRaises(ValueError):
            replay_certificate(forged)


if __name__ == "__main__":
    unittest.main()
