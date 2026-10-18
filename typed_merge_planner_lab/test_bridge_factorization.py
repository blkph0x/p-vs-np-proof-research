"""Finite controls for one-bridge Horn/affine factorization."""
import json
from pathlib import Path
import unittest

from bridge_factorization import all_controls, exact_one_target, project_pair


HERE = Path(__file__).resolve().parent


class BridgeFactorizationTests(unittest.TestCase):
    def test_all_four_orientations_reject_exact_one(self):
        records = all_controls()
        self.assertEqual(len(records), 4)
        self.assertTrue(all(not row["target_representable"] for row in records))
        self.assertEqual([row["factor_pairs"] for row in records], [1464, 728, 728, 1464])

    def test_projection_layout_validation(self):
        with self.assertRaises(ValueError):
            project_pair(frozenset(), frozenset(), "bad")
        self.assertEqual(len(exact_one_target()), 3)

    def test_saved_artifact_and_review(self):
        artifact = json.loads((HERE / "BRIDGE_FACTOR_RESULTS.json").read_text(encoding="utf-8"))
        review = json.loads((HERE / "BRIDGE_FACTOR_REVIEW.json").read_text(encoding="utf-8"))
        self.assertEqual(artifact["format"], "one-bridge-horn-affine-exhaustive-v1")
        self.assertTrue(artifact["all_orientations_reject"])
        self.assertEqual(review["status"], "PASS")
        self.assertTrue(review["source_hashes_match"])


if __name__ == "__main__":
    unittest.main()
