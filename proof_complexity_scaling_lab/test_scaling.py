"""Tests for the proof-producing scaling campaign."""
import json
import hashlib
from pathlib import Path
import unittest

from families import all_assignment_clauses, controls, pigeonhole
from review_scaling import expected_all_assignment_stats, replay


HERE = Path(__file__).resolve().parent


class ScalingTests(unittest.TestCase):
    def test_family_sizes_are_exact(self):
        self.assertEqual(len(all_assignment_clauses(5)), 32)
        nvars, clauses = pigeonhole(4, 3)
        self.assertEqual(nvars, 12)
        self.assertEqual(len(clauses), 34)

    def test_saved_campaign_has_both_adversarial_families(self):
        artifact = json.loads((HERE / "SCALING_RESULTS.json").read_text(encoding="utf-8"))
        families = {row["family"] for row in artifact["rows"]}
        self.assertEqual(families, {"all_assignments", "pigeonhole"})
        self.assertEqual(len(artifact["rows"]), 18)

    def test_all_assignment_scaling_law(self):
        artifact = json.loads((HERE / "SCALING_RESULTS.json").read_text(encoding="utf-8"))
        rows = [row for row in artifact["rows"] if row["family"] == "all_assignments"]
        for row in rows:
            expected = expected_all_assignment_stats(row["parameter"])
            for key, value in expected.items():
                self.assertEqual(row["stats"][key], value)

    def test_saved_proofs_replay(self):
        certificates = json.loads(
            (HERE / "SCALING_CERTIFICATES.json").read_text(encoding="utf-8")
        )
        for saved in certificates:
            self.assertTrue(replay(saved["nvars"], saved["clauses"], saved["result"]))

    def test_independent_review_passed(self):
        review = json.loads((HERE / "SCALING_REVIEW.json").read_text(encoding="utf-8"))
        self.assertEqual(review["status"], "PASS")
        self.assertTrue(review["proofs_match"])
        self.assertTrue(review["scaling_laws_match"])
        self.assertTrue(review["source_hashes_match"])

    def test_runtime_chart_tracks_scaling_artifact(self):
        chart = json.loads((HERE.parent / "assets/data/scaling-runtime.json").read_text(encoding="utf-8"))
        digest = hashlib.sha256((HERE / "SCALING_RESULTS.json").read_bytes()).hexdigest()
        self.assertEqual(chart["source_sha256"]["proof_complexity_scaling_lab/SCALING_RESULTS.json"], digest)
        self.assertTrue(any(dataset["id"] == "cdcl-pigeonhole" for dataset in chart["datasets"]))


if __name__ == "__main__":
    unittest.main()
