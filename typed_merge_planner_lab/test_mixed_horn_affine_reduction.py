"""Finite replay of the mixed Horn/affine exact-one reduction."""
from itertools import combinations
import unittest

from mixed_horn_affine_reduction import (
    AFFINE_WITNESS,
    HORN_WITNESS,
    all_three_subsets,
    original_sat,
    transformed_sat,
)


class MixedReductionTests(unittest.TestCase):
    def test_fixed_factors_have_declared_closures(self):
        self.assertTrue(all(tuple(a[i] & b[i] for i in range(3)) in HORN_WITNESS
                            for a in HORN_WITNESS for b in HORN_WITNESS))
        self.assertTrue(all(tuple(a[i] ^ b[i] ^ c[i] for i in range(4)) in AFFINE_WITNESS
                            for a in AFFINE_WITNESS for b in AFFINE_WITNESS
                            for c in AFFINE_WITNESS))

    def test_all_four_variable_clause_families(self):
        clauses = all_three_subsets(4)
        for mask in range(1 << len(clauses)):
            formula = tuple(clauses[i] for i in range(len(clauses)) if mask >> i & 1)
            self.assertEqual(original_sat(formula, 4), transformed_sat(formula, 4), formula)

    def test_empty_and_malformed_inputs(self):
        self.assertTrue(original_sat(tuple(), 0))
        self.assertTrue(transformed_sat(tuple(), 0))
        with self.assertRaises(ValueError):
            original_sat(((0, 0, 1),), 2)
        with self.assertRaises(ValueError):
            transformed_sat(((0, 1, 3),), 3)

    def test_independent_review_artifact(self):
        import json
        from pathlib import Path
        review = json.loads((Path(__file__).resolve().parent /
                             "MIXED_REDUCTION_REVIEW.json").read_text(encoding="utf-8"))
        self.assertEqual(review["status"], "PASS")
        self.assertEqual(review["formula_count"], 16)
        self.assertTrue(review["all_answers_match"])


if __name__ == "__main__":
    unittest.main()
