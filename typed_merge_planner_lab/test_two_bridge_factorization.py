"""Finite controls for two-bridge Horn/affine factorization."""
import json
from pathlib import Path
import unittest

from two_bridge_factorization import all_controls, exact_one_target, project_pair


HERE = Path(__file__).resolve().parent


class TwoBridgeFactorizationTests(unittest.TestCase):
    def test_all_four_orientations_represent_exact_one(self):
        rows = all_controls()
        self.assertEqual(len(rows), 4)
        self.assertTrue(all(row["target_representable"] for row in rows))
        self.assertEqual([row["factor_pairs"] for row in rows],
                         [37576, 257920, 257920, 37576])
        self.assertEqual([row["target_pair_count"] for row in rows], [8, 2, 2, 8])

    def test_projection_layout_validation(self):
        with self.assertRaises(ValueError):
            project_pair(0, 0, "invalid")
        self.assertEqual(len(exact_one_target()), 3)

    def test_saved_artifact_and_review(self):
        artifact = json.loads((HERE / "TWO_BRIDGE_FACTOR_RESULTS.json").read_text(encoding="utf-8"))
        review = json.loads((HERE / "TWO_BRIDGE_FACTOR_REVIEW.json").read_text(encoding="utf-8"))
        self.assertEqual(artifact["format"], "two-bridge-horn-affine-exhaustive-v1")
        self.assertTrue(artifact["all_orientations_represent"])
        self.assertFalse(artifact["all_orientations_reject"])
        self.assertEqual(review["status"], "PASS")
        self.assertTrue(review["source_hashes_match"])


if __name__ == "__main__":
    unittest.main()
