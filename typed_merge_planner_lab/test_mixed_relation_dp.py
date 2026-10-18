"""Finite controls for the proof-producing mixed relation DP."""
import json
from itertools import combinations
from pathlib import Path
import unittest

from mixed_horn_affine_reduction import transformed_sat
from mixed_relation_dp import Constraint, solve


HERE = Path(__file__).resolve().parent
H = frozenset(((0, 0, 0), (1, 1, 0), (0, 0, 1)))
A = frozenset(((0, 1, 0, 0), (0, 0, 1, 0),
               (1, 0, 0, 1), (1, 1, 1, 1)))


def transformed_constraints(clauses, variables):
    result = []
    for i, (x, y, w) in enumerate(clauses):
        z0, z1 = variables + 2 * i, variables + 2 * i + 1
        result.extend((Constraint((x, z0, z1), H), Constraint((y, w, z0, z1), A)))
    return tuple(result)


class MixedRelationDPTests(unittest.TestCase):
    def test_all_four_variable_reductions(self):
        triples = tuple(combinations(range(4), 3))
        for mask in range(1 << len(triples)):
            clauses = tuple(triples[i] for i in range(len(triples)) if mask >> i & 1)
            n = 4 + 2 * len(clauses)
            result = solve(n, transformed_constraints(clauses, 4), tuple(range(n)))
            self.assertEqual(result["sat"], transformed_sat(clauses, 4))
            self.assertEqual(result["certificate"]["sat"], result["sat"])

    def test_empty_and_bad_orders(self):
        result = solve(0, tuple(), tuple())
        self.assertTrue(result["sat"])
        with self.assertRaises(ValueError):
            solve(2, tuple(), (0, 0))
        with self.assertRaises(ValueError):
            solve(1, (Constraint((0,), frozenset(((2,),))),), (0,))

    def test_saved_independent_review(self):
        artifact = json.loads((HERE / "MIXED_RELATION_DP_RESULTS.json").read_text(encoding="utf-8"))
        review = json.loads((HERE / "MIXED_RELATION_DP_REVIEW.json").read_text(encoding="utf-8"))
        self.assertTrue(artifact["all_results_match_direct"])
        self.assertEqual(review["status"], "PASS")
        self.assertTrue(review["certificates_match"])
        self.assertTrue(review["source_hashes_match"])


if __name__ == "__main__":
    unittest.main()
