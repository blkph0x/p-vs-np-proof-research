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

    def test_exact_small_order_optima(self):
        artifact = json.loads((HERE / "ORDER_RESULTS.json").read_text(encoding="utf-8"))
        self.assertEqual([row["optimal_width"] for row in artifact["rows"]], [1, 3, 7, 11])
        self.assertEqual([row["row_major_width"] for row in artifact["rows"]], [1, 4, 9, 16])

    def test_order_review_passed(self):
        review = json.loads((HERE / "ORDER_REVIEW.json").read_text(encoding="utf-8"))
        self.assertEqual(review["status"], "PASS")
        self.assertTrue(review["recurrence_matches"])
        self.assertTrue(review["orders_are_permutations"])
        self.assertTrue(review["source_hashes_match"])


if __name__ == "__main__":
    unittest.main()
