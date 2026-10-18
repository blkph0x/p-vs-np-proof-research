import unittest
from pathlib import Path
import sys

ROOT = Path(__file__).parent
sys.path.insert(0, str(ROOT))

import residual_equivalence_barrier as barrier


class TestResidualEquivalenceBarrier(unittest.TestCase):
    def test_empty_satisfiable_formula_keeps_two_residuals(self):
        row = barrier.exact_equivalence_record((), 3)
        self.assertTrue(row["g_satisfiable"])
        self.assertFalse(row["future_equivalent"])
        self.assertTrue(barrier.verify_reduction_record(row))

    def test_unit_contradiction_merges_residuals(self):
        row = barrier.exact_equivalence_record(((1,), (-1,)), 1)
        self.assertFalse(row["g_satisfiable"])
        self.assertTrue(row["future_equivalent"])
        self.assertTrue(barrier.verify_reduction_record(row))

    def test_exhaustive_two_variable_formula_family(self):
        rows = barrier.exhaustive_small_records(2)
        self.assertEqual(len(rows), 256)
        self.assertTrue(all(barrier.verify_reduction_record(row) for row in rows))
        self.assertEqual(sum(r["g_satisfiable"] for r in rows),
                         sum(not r["future_equivalent"] for r in rows))

    def test_boundary_stays_one(self):
        row = barrier.exact_equivalence_record(((1, 2), (-1, 2)), 2)
        self.assertEqual(row["boundary_width"], 1)
        self.assertTrue(barrier.verify_reduction_record(row))


if __name__ == "__main__":
    unittest.main()

