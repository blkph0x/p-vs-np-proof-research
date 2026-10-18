"""Tests for the independent proof/frontier comparison."""
import json
from pathlib import Path
import unittest

from review_frontier import independent_frontier, all_assignment_clauses, pigeonhole

HERE = Path(__file__).resolve().parent


class FrontierComparisonTests(unittest.TestCase):
    def test_saved_rows_cover_both_families(self):
        artifact = json.loads((HERE / "FRONTIER_RESULTS.json").read_text(encoding="utf-8"))
        self.assertEqual({row["family"] for row in artifact["rows"]},
                         {"all_assignments", "pigeonhole"})
        self.assertEqual(len(artifact["rows"]), 14)

    def test_all_assignment_closed_form(self):
        for n in range(1, 8):
            result = independent_frontier(n, all_assignment_clauses(n), list(range(n)))
            self.assertEqual(result["stats"], {
                "max_width": max(0, n - 1),
                "states": 2 ** n - 1,
                "transitions": 2 ** n - 2,
            })

    def test_pigeonhole_boundary_closed_form(self):
        for holes in range(1, 8):
            nvars, clauses = pigeonhole(holes + 1, holes)
            result = independent_frontier(nvars, clauses, list(range(nvars)))
            self.assertEqual(result["stats"]["max_width"], holes ** 2)
            self.assertFalse(result["sat"])

    def test_replay_and_source_review_passed(self):
        review = json.loads((HERE / "FRONTIER_REVIEW.json").read_text(encoding="utf-8"))
        self.assertEqual(review["status"], "PASS")
        self.assertTrue(review["frontier_replay_matches"])
        self.assertTrue(review["cdcl_rows_match"])
        self.assertTrue(review["closed_forms_match"])
        self.assertTrue(review["source_hashes_match"])


if __name__ == "__main__":
    unittest.main()
