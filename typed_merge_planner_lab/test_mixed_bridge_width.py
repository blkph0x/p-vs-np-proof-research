"""Finite controls for width preservation under the mixed gadget."""
import json
from pathlib import Path
import unittest

from mixed_bridge_width import all_three_subsets, width_pair


HERE = Path(__file__).resolve().parent


class MixedBridgeWidthTests(unittest.TestCase):
    def test_all_four_variable_families(self):
        clauses = all_three_subsets(4)
        for mask in range(1 << len(clauses)):
            formula = tuple(clauses[i] for i in range(len(clauses)) if mask >> i & 1)
            original, transformed = width_pair(formula, 4)
            self.assertLessEqual(original, transformed)
            self.assertLessEqual(transformed, original + 2)

    def test_empty_and_malformed(self):
        self.assertEqual(width_pair(tuple(), 0), (0, 0))
        with self.assertRaises(ValueError):
            width_pair(((0, 1, 3),), 3)

    def test_saved_review(self):
        artifact = json.loads((HERE / "MIXED_BRIDGE_WIDTH_RESULTS.json").read_text(encoding="utf-8"))
        review = json.loads((HERE / "MIXED_BRIDGE_WIDTH_REVIEW.json").read_text(encoding="utf-8"))
        self.assertTrue(artifact["all_bounds_hold"])
        self.assertEqual(review["status"], "PASS")
        self.assertTrue(review["source_hashes_match"])


if __name__ == "__main__":
    unittest.main()
