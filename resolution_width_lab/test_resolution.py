"""Controls for complete bounded-width resolution closure."""
import json
from itertools import product
from pathlib import Path
import unittest

from resolution import BoundedResolution, weakenings
from incremental import run_ladder
from indexed import IndexedBoundedResolution
from bitset import BitsetBoundedResolution
from pebble import BooleanPebbleGame


HERE = Path(__file__).resolve().parent


def direct(nvars, clauses):
    return any(all(any(assignment[abs(lit) - 1] == (lit > 0)
                       for lit in clause) for clause in clauses)
               for assignment in product((False, True), repeat=nvars))


def all_assignment_clauses(nvars):
    return tuple(tuple((v + 1) if not bit else -(v + 1)
                       for v, bit in enumerate(bits))
                 for bits in product((0, 1), repeat=nvars))


def pigeonhole(pigeons, holes):
    variable = lambda pigeon, hole: pigeon * holes + hole + 1
    clauses = [tuple(variable(pigeon, hole) for hole in range(holes))
               for pigeon in range(pigeons)]
    for pigeon in range(pigeons):
        for left in range(holes):
            for right in range(left + 1, holes):
                clauses.append((-variable(pigeon, left), -variable(pigeon, right)))
    for hole in range(holes):
        for left in range(pigeons):
            for right in range(left + 1, pigeons):
                clauses.append((-variable(left, hole), -variable(right, hole)))
    return pigeons * holes, tuple(clauses)


class ResolutionWidthTests(unittest.TestCase):
    def test_weakenings_are_complete_and_non_tautological(self):
        rows = list(weakenings((1,), 3, 2))
        self.assertEqual(len(rows), 1 + 4)
        self.assertEqual(len(set(rows)), len(rows))
        self.assertTrue(all(len(row) <= 2 and all(-lit not in row for lit in row)
                            for row in rows))

    def test_unit_contradiction_has_width_one_refutation(self):
        result = BoundedResolution(1, ((1,), (-1,)), 1).solve()
        self.assertEqual(result["status"], "UNSAT")
        self.assertEqual(result["stats"]["resolution_steps"], 1)

    def test_width_boundary_and_complete_small_unsat(self):
        clauses = all_assignment_clauses(3)
        narrow = BoundedResolution(3, clauses, 2).solve()
        wide = BoundedResolution(3, clauses, 3).solve()
        self.assertEqual(narrow["status"], "UNKNOWN")
        self.assertEqual(narrow["reason"], "NO_WIDTH_W_REFUTATION")
        self.assertEqual(wide["status"], "UNSAT")
        self.assertFalse(direct(3, clauses))

    def test_pigeonhole_and_sat_controls(self):
        nvars, clauses = pigeonhole(3, 2)
        result = BoundedResolution(nvars, clauses, 3).solve()
        self.assertEqual(result["status"], "UNSAT")
        sat = ((1, 2), (-1, 2))
        result = BoundedResolution(2, sat, 2).solve()
        self.assertEqual(result["status"], "UNKNOWN")
        self.assertTrue(direct(2, sat))

    def test_minimum_refutation_widths_are_exact_on_controls(self):
        def minimum_width(nvars, clauses):
            for width in range(max((len(clause) for clause in clauses), default=0) + 1):
                if BoundedResolution(nvars, clauses, width).solve()["status"] == "UNSAT":
                    return width
            return None

        self.assertEqual(minimum_width(1, ((1,), (-1,))), 1)
        all_assignments = all_assignment_clauses(3)
        self.assertEqual(minimum_width(3, all_assignments), 3)
        nvars, pigeon = pigeonhole(3, 2)
        self.assertEqual(minimum_width(nvars, pigeon), 2)
        self.assertIsNone(minimum_width(2, ((1, 2), (-1, 2))))

    def test_caps_are_conservative_unknown(self):
        clauses = all_assignment_clauses(4)
        result = BoundedResolution(4, clauses, 4, max_clauses=3).solve()
        self.assertEqual(result["status"], "UNKNOWN")
        self.assertEqual(result["reason"], "CLAUSE_CAP")

    def test_saved_artifact_and_independent_review(self):
        artifact = json.loads((HERE / "RESULTS.json").read_text(encoding="utf-8"))
        review = json.loads((HERE / "REVIEW.json").read_text(encoding="utf-8"))
        self.assertTrue(artifact["all_cases_replayed"])
        self.assertEqual(review["status"], "PASS")
        self.assertTrue(review["closures_match"])
        self.assertTrue(review["proofs_match"])
        self.assertTrue(review["source_hashes_match"])

    def test_incremental_ladder_matches_fresh_closure(self):
        clauses = all_assignment_clauses(3)
        ladder = run_ladder(3, clauses, max_clauses=10000, max_steps=100000)
        self.assertEqual([row["baseline"]["status"] for row in ladder],
                         ["UNKNOWN", "UNKNOWN", "UNKNOWN", "UNSAT"])
        for row in ladder:
            self.assertEqual(row["baseline"]["clause_digest"],
                             row["incremental"]["clause_digest"])

    def test_incremental_ladder_saves_pigeonhole_work(self):
        nvars, clauses = pigeonhole(4, 3)
        ladder = run_ladder(nvars, clauses, max_clauses=100000, max_steps=500000)
        final = ladder[-1]
        self.assertEqual(final["baseline"]["status"], "UNSAT")
        self.assertEqual(final["incremental"]["status"], "UNSAT")
        self.assertLess(final["incremental"]["candidate_steps"],
                        final["baseline"]["candidate_steps"])

    def test_saved_incremental_review_passed(self):
        artifact = json.loads((HERE / "INCREMENTAL_RESULTS.json").read_text(encoding="utf-8"))
        review = json.loads((HERE / "INCREMENTAL_REVIEW.json").read_text(encoding="utf-8"))
        self.assertEqual(len(artifact["rows"]), 7)
        self.assertTrue(artifact["all_closures_match"])
        self.assertEqual(review["status"], "PASS")
        self.assertTrue(review["fresh_and_incremental_closures_match"])
        self.assertTrue(review["source_hashes_match"])

    def test_indexed_closure_matches_reference_controls(self):
        controls = [
            (1, ((1,), (-1,)), 1),
            (3, all_assignment_clauses(3), 3),
            (*pigeonhole(3, 2), 2),
            (2, ((1, 2), (-1, 2)), 2),
        ]
        for nvars, clauses, width in controls:
            reference = BoundedResolution(
                nvars, clauses, width, max_clauses=100000, max_steps=500000
            ).solve()
            indexed = IndexedBoundedResolution(
                nvars, clauses, width, max_clauses=100000, max_steps=500000
            ).solve()
            self.assertEqual(indexed["status"], reference["status"])
            self.assertEqual(indexed.get("reason"), reference.get("reason"))
            self.assertEqual({tuple(c) for c in indexed["clauses"]},
                             {tuple(c) for c in reference["clauses"]})
            self.assertGreaterEqual(indexed["stats"]["indexed_resolution_pairs"],
                                    indexed["stats"]["resolution_steps"])

    def test_saved_indexed_stress_review_passed(self):
        artifact = json.loads((HERE / "INDEXED_RESULTS.json").read_text(encoding="utf-8"))
        review = json.loads((HERE / "INDEXED_REVIEW.json").read_text(encoding="utf-8"))
        self.assertEqual(artifact["exact_control_count"], 7)
        stress = [row for row in artifact["rows"] if row["name"] == "pigeonhole_5_4"]
        self.assertEqual([row["width"] for row in stress], [3, 4])
        self.assertEqual([row["status"] for row in stress], ["UNKNOWN", "UNKNOWN"])
        self.assertEqual(stress[0]["reason"], "NO_WIDTH_W_REFUTATION")
        self.assertEqual(stress[1]["reason"], "STEP_CAP")
        self.assertEqual(review["status"], "PASS")
        self.assertTrue(review["exact_rows_match"])
        self.assertTrue(review["stress_cap_replayed"])
        self.assertTrue(review["source_hashes_match"])

    def test_bitset_closure_matches_indexed_controls(self):
        controls = [
            (1, ((1,), (-1,)), 1),
            (3, all_assignment_clauses(3), 3),
            (*pigeonhole(3, 2), 2),
            (*pigeonhole(4, 3), 3),
        ]
        for nvars, clauses, width in controls:
            indexed = IndexedBoundedResolution(
                nvars, clauses, width, max_clauses=100000, max_steps=500000
            ).solve()
            bitset = BitsetBoundedResolution(
                nvars, clauses, width, max_clauses=100000, max_steps=500000
            ).solve()
            self.assertEqual(bitset["status"], indexed["status"])
            self.assertEqual(bitset.get("reason"), indexed.get("reason"))
            self.assertEqual({tuple(c) for c in bitset["clauses"]},
                             {tuple(c) for c in indexed["clauses"]})

    def test_saved_bitset_stress_review_passed(self):
        artifact = json.loads((HERE / "BITSET_RESULTS.json").read_text(encoding="utf-8"))
        review = json.loads((HERE / "BITSET_REVIEW.json").read_text(encoding="utf-8"))
        self.assertEqual(artifact["exact_control_count"], 7)
        self.assertTrue(artifact["exact_controls_match"])
        stress = [row for row in artifact["rows"] if row["family"] == "pigeonhole_stress"]
        self.assertEqual([row["width"] for row in stress], [3, 4])
        self.assertEqual(stress[0]["closure_size"], 2230)
        self.assertEqual(stress[1]["status"], "UNKNOWN")
        self.assertEqual(stress[1]["reason"], "STEP_CAP")
        self.assertEqual(stress[1]["candidate_steps"], 10000001)
        self.assertEqual(review["status"], "PASS")
        self.assertTrue(review["stress_width3_match"])
        self.assertTrue(review["stress_cap_control"])
        self.assertTrue(review["source_hashes_match"])

    def test_pebble_game_matches_width_boundary_controls(self):
        # The theorem uses (w + 1) pebbles for width w.  These controls have
        # initial clauses no wider than the target width, so the game result
        # and the complete closure agree at the boundary.
        unit = BooleanPebbleGame(1, ((1,), (-1,)), 2).solve()
        self.assertEqual(unit["status"], "SPOILER_WINS")
        pigeon = pigeonhole(4, 3)
        game = BooleanPebbleGame(*pigeon, 4).solve()
        self.assertEqual(game["status"], "SPOILER_WINS")

    def test_saved_pebble_width_bridge_review_passed(self):
        artifact = json.loads((HERE / "PEBBLE_RESULTS.json").read_text(encoding="utf-8"))
        review = json.loads((HERE / "PEBBLE_REVIEW.json").read_text(encoding="utf-8"))
        php = artifact["php_5_4_width_conclusion"]
        self.assertEqual(php["minimum_refutation_width"], 4)
        rows = {row["name"]: row["result"]["status"] for row in artifact["rows"]}
        self.assertEqual(rows["pigeonhole_5_4_pebbles_4"], "DUPLICATOR_WINS")
        self.assertEqual(rows["pigeonhole_5_4_pebbles_5"], "SPOILER_WINS")
        self.assertEqual(review["status"], "PASS")
        self.assertTrue(review["php_5_4_spoiler_width4_bridge"])
        self.assertTrue(review["php_5_4_width3_closure_bridge"])
        self.assertTrue(review["source_hashes_match"])


if __name__ == "__main__":
    unittest.main()
