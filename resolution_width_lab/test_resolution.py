"""Controls for complete bounded-width resolution closure."""
import json
from itertools import product
from pathlib import Path
import unittest

from resolution import BoundedResolution, weakenings


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


if __name__ == "__main__":
    unittest.main()
