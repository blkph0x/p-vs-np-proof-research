import importlib.util
from itertools import product
from itertools import combinations
import json
from pathlib import Path
import sys
import unittest


HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("backdoor", HERE / "backdoor_solver.py")
backdoor = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = backdoor
spec.loader.exec_module(backdoor)


def brute_force(n, constraints):
    return [bits for bits in product((0, 1), repeat=n)
            if all(tuple(bits[v] for v in c.scope) in c.relation for c in constraints)]


def exact_one(*scope):
    return frozenset(row for row in product((0, 1), repeat=len(scope)) if sum(row) == 1)


class BackdoorTests(unittest.TestCase):
    def test_affine_backdoor_solves_exact_one_gadget(self):
        # Pinning one variable in each exact-one clause leaves either XOR or a
        # singleton, both affine.  The supplied backdoor is deliberately not
        # discovered by the solver.
        constraints = (
            backdoor.Constraint((0, 1, 2), exact_one(0, 1, 2)),
            backdoor.Constraint((2, 3, 4), exact_one(0, 1, 2)),
        )
        expected = brute_force(5, constraints)
        result = backdoor.solve_with_backdoor(5, constraints, (2,), "AFFINE")
        self.assertEqual(result["status"], "SAT")
        self.assertIn(tuple(result["witness"]), expected)
        self.assertEqual(result["enumerated_assignments"], 1)

    def test_affine_backdoor_proves_unsat(self):
        # x+y+z=1 and x+y+z=2 share a one-variable affine backdoor only after
        # adding a second pin; the branch certificate must enumerate all four
        # assignments and reject every residual system.
        one = frozenset(row for row in product((0, 1), repeat=3) if sum(row) == 1)
        two = frozenset(row for row in product((0, 1), repeat=3) if sum(row) == 2)
        constraints = (backdoor.Constraint((0, 1, 2), one),
                       backdoor.Constraint((0, 1, 2), two))
        result = backdoor.solve_with_backdoor(3, constraints, (0, 1), "AFFINE")
        self.assertEqual(result["status"], "UNSAT")
        self.assertEqual(result["enumerated_assignments"], 4)
        self.assertFalse(brute_force(3, constraints))

    def test_non_strong_backdoor_is_unknown(self):
        # Exact-one remains non-affine when no variable is pinned.
        c = backdoor.Constraint((0, 1, 2), exact_one(0, 1, 2))
        result = backdoor.solve_with_backdoor(3, (c,), (), "AFFINE")
        self.assertEqual(result["status"], "UNKNOWN")
        self.assertEqual(result["reason"], "NOT_STRONG_BACKDOOR")

    def test_horn_relation_solver_matches_brute_force(self):
        implication = frozenset(((0, 0), (0, 1), (1, 1)))
        unit = frozenset(((1,),))
        constraints = (backdoor.Constraint((0, 1), implication),
                       backdoor.Constraint((1,), unit))
        sat, witness = backdoor.solve_horn(2, constraints)
        self.assertTrue(sat)
        self.assertEqual(tuple(witness), brute_force(2, constraints)[0])

    def test_affine_solver_matches_brute_force_on_all_small_systems(self):
        parity = frozenset(((0, 0), (1, 1)))
        anti = frozenset(((0, 1), (1, 0)))
        for first in (parity, anti):
            for second in (parity, anti):
                constraints = (backdoor.Constraint((0, 1), first),
                               backdoor.Constraint((0, 1), second))
                sat, witness = backdoor.solve_affine(2, constraints)
                expected = brute_force(2, constraints)
                self.assertEqual(sat, bool(expected))
                if sat:
                    self.assertIn(tuple(witness), expected)

    def test_restriction_preserves_scope_order(self):
        c = backdoor.Constraint((2, 0, 1), frozenset(((0, 1, 0), (1, 0, 1))))
        r = backdoor.restrict(c, {0: 1})
        self.assertEqual(r.scope, (2, 1))
        self.assertEqual(r.relation, frozenset(((0, 0),)))

    def test_exact_one_formula_family_matches_bruteforce_under_affine_backdoor(self):
        triples = list(combinations(range(4), 3))
        relation = exact_one(0, 1, 2)
        for mask in range(1 << len(triples)):
            constraints = tuple(backdoor.Constraint(scope, relation)
                                for i, scope in enumerate(triples) if mask >> i & 1)
            result = backdoor.solve_with_backdoor(4, constraints, (0, 1, 2), "AFFINE")
            expected = brute_force(4, constraints)
            self.assertEqual(result["status"], "SAT" if expected else "UNSAT")
            if expected:
                self.assertIn(tuple(result["witness"]), expected)
            self.assertEqual(result["branch_budget"], 8)

    def test_saved_audit_record_has_consistent_statuses(self):
        artifact = json.loads((HERE / "BACKDOOR_RESULTS.json").read_text(encoding="utf-8"))
        self.assertEqual(artifact["status"], "PASS")
        self.assertEqual(len(artifact["cases"]), 4)
        for case in artifact["cases"]:
            self.assertEqual(case["result"]["status"], case["expected_status"])


if __name__ == "__main__":
    unittest.main()
