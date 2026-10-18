"""Tests for the proof-producing scaling campaign."""
import json
import hashlib
import math
from pathlib import Path
import unittest

from families import all_assignment_clauses, controls, pigeonhole
from review_scaling import expected_all_assignment_stats, replay


HERE = Path(__file__).resolve().parent


def normalized_sha256(path):
    text = path.read_text(encoding="utf-8")
    return hashlib.sha256(text.replace("\r\n", "\n").replace("\r", "\n").encode()).hexdigest()


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
        self.assertEqual(
            chart["source_sha256"]["proof_complexity_scaling_lab/SCALING_RESULTS.json"],
            normalized_sha256(HERE / "SCALING_RESULTS.json"),
        )
        self.assertEqual(
            chart["source_sha256"]["NATIVE_RESULTS.json"],
            normalized_sha256(HERE.parent / "NATIVE_RESULTS.json"),
        )
        self.assertTrue(any(dataset["id"] == "cdcl-pigeonhole" for dataset in chart["datasets"]))

    def test_runtime_chart_axes_match_point_fields(self):
        chart = json.loads((HERE.parent / "assets/data/scaling-runtime.json").read_text(encoding="utf-8"))
        self.assertIn(chart["default_x_axis"], chart["x_axes"])
        points = [point for dataset in chart["datasets"] for point in dataset["points"]]
        self.assertTrue(points, "the chart must contain at least one point")
        for axis in chart["x_axes"]:
            self.assertTrue(all(axis in point and isinstance(point[axis], (int, float)) for point in points))
            self.assertTrue(all(math.isfinite(point[axis]) for point in points))


if __name__ == "__main__":
    unittest.main()
