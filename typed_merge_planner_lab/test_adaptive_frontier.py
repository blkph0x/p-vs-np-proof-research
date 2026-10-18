"""Adversarial controls for the adaptive frontier solver."""
import json
from itertools import product
from pathlib import Path
import unittest

from adaptive_frontier import Constraint, primal_graph, solve


HERE = Path(__file__).resolve().parent
EQ = frozenset(((0, 0), (1, 1)))
NEQ = frozenset(((0, 1), (1, 0)))
EXACT1 = frozenset(((0, 0, 1), (0, 1, 0), (1, 0, 0)))


def direct(n, constraints):
    for assignment in product((0, 1), repeat=n):
        if all(tuple(assignment[v] for v in c.scope) in c.relation
               for c in constraints):
            return True
    return False


class AdaptiveFrontierTests(unittest.TestCase):
    def test_empty_and_sparse_sat(self):
        self.assertEqual(primal_graph(0, tuple()), ())
        result = solve(5, tuple(Constraint((i, i + 1), EQ) for i in range(4)))
        self.assertEqual(result["status"], "SAT")
        self.assertTrue(result["sat"])
        self.assertEqual(result["width"], 1)
        self.assertEqual(result["max_states"], 2)

    def test_contradictory_units_are_unsat(self):
        constraints = (Constraint((0,), frozenset(((0,),))),
                       Constraint((0,), frozenset(((1,),))))
        result = solve(1, constraints)
        self.assertEqual(result["status"], "UNSAT")
        self.assertFalse(result["sat"])
        self.assertFalse(direct(1, constraints))

    def test_dense_scope_charges_width(self):
        n = 6
        relation = frozenset(row for row in product((0, 1), repeat=n)
                             if sum(row) % 2 == 0)
        result = solve(n, (Constraint(tuple(range(n)), relation),))
        self.assertEqual(result["status"], "SAT")
        self.assertEqual(result["width"], n - 1)
        self.assertEqual(result["order_search"]["subsets"], 1 << n)
        self.assertTrue(result["max_states"] <= (1 << (n - 1)))

    def test_mixed_relations_match_direct_enumeration(self):
        fixtures = (
            (3, (Constraint((0, 1, 2), EXACT1),
                 Constraint((1, 2), EQ))),
            (3, (Constraint((0, 1, 2), EXACT1),
                 Constraint((1, 2), NEQ))),
            (4, (Constraint((0, 1), EQ), Constraint((2, 3), NEQ),
                 Constraint((1, 2), EQ))),
        )
        for n, constraints in fixtures:
            result = solve(n, constraints)
            self.assertEqual(result["sat"], direct(n, constraints))
            self.assertIn(result["status"], ("SAT", "UNSAT"))

    def test_order_cap_is_conservative_unknown(self):
        result = solve(4, tuple(), max_order_variables=3)
        self.assertEqual(result["status"], "UNKNOWN")
        self.assertIsNone(result["sat"])
        self.assertEqual(result["reason"], "ORDER_DISCOVERY_CAP")
        self.assertIsNone(result["certificate"]["order"])

    def test_saved_artifact_and_independent_review(self):
        artifact = json.loads((HERE / "ADAPTIVE_FRONTIER_RESULTS.json").read_text(encoding="utf-8"))
        review = json.loads((HERE / "ADAPTIVE_FRONTIER_REVIEW.json").read_text(encoding="utf-8"))
        self.assertTrue(artifact["all_bounded_results_match_direct"])
        self.assertEqual(review["status"], "PASS")
        self.assertTrue(review["certificates_match"])
        self.assertTrue(review["source_hashes_match"])


if __name__ == "__main__":
    unittest.main()
