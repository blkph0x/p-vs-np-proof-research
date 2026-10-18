"""Regression checks for the charged-work artifact."""
import json
from pathlib import Path
import unittest

from charged_work_review import replay


HERE = Path(__file__).resolve().parent


class ChargedWorkReviewTests(unittest.TestCase):
    def test_every_saved_exact_case_meets_bound(self):
        records = replay()
        self.assertEqual(len(records), 24)
        self.assertTrue(all(row["status"] == "EXACT" for row in records))
        self.assertTrue(all(row["bound_holds"] for row in records))

    def test_saved_artifact_agrees(self):
        artifact = json.loads((HERE / "CHARGED_WORK_REVIEW.json").read_text(encoding="utf-8"))
        self.assertEqual(artifact["format"], "coordinate-conditioning-charged-work-v1")
        self.assertEqual(artifact["exact_records"], 24)
        self.assertTrue(artifact["all_exact_bounds_hold"])


if __name__ == "__main__":
    unittest.main()
