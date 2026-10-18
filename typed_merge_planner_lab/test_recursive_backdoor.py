import importlib.util
from itertools import product
import json
from pathlib import Path
import sys
import unittest


HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("backdoor", HERE / "backdoor_solver.py")
backdoor = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = backdoor
spec.loader.exec_module(backdoor)
spec2 = importlib.util.spec_from_file_location("recursive", HERE / "recursive_backdoor.py")
recursive = importlib.util.module_from_spec(spec2)
sys.modules[spec2.name] = recursive
spec2.loader.exec_module(recursive)


def exact_weight(size, weight):
    return frozenset(row for row in product((0, 1), repeat=size) if sum(row) == weight)


def brute(n, constraints):
    return [bits for bits in product((0, 1), repeat=n)
            if all(tuple(bits[v] for v in c.scope) in c.relation for c in constraints)]


class RecursiveBackdoorTests(unittest.TestCase):
    def test_depth_one_exact_one_sat(self):
        c = backdoor.Constraint((0, 1, 2), exact_weight(3, 1))
        result = recursive.solve_recursive(3, (c,), "AFFINE", 1)
        self.assertEqual(result["status"], "SAT")
        self.assertIn(tuple(result["witness"]), brute(3, (c,)))
        self.assertLessEqual(result["ledger"]["nodes"], 3)

    def test_depth_one_proves_inconsistent_exact_weights(self):
        constraints = (backdoor.Constraint((0, 1, 2), exact_weight(3, 1)),
                       backdoor.Constraint((0, 1, 2), exact_weight(3, 2)))
        result = recursive.solve_recursive(3, constraints, "AFFINE", 1)
        self.assertEqual(result["status"], "UNSAT")
        self.assertFalse(brute(3, constraints))

    def test_depth_limit_is_unknown(self):
        c = backdoor.Constraint((0, 1, 2), exact_weight(3, 1))
        result = recursive.solve_recursive(3, (c,), "AFFINE", 0)
        self.assertEqual(result["status"], "UNKNOWN")
        self.assertEqual(result["reason"], "DEPTH_LIMIT")

    def test_node_budget_is_charged_and_conservative(self):
        c = backdoor.Constraint((0, 1, 2), exact_weight(3, 1))
        result = recursive.solve_recursive(3, (c,), "AFFINE", 2, max_nodes=1)
        self.assertEqual(result["status"], "UNKNOWN")
        self.assertEqual(result["ledger"]["nodes"], 1)

    def test_native_leaf_without_branching(self):
        implication = frozenset(((0, 0), (0, 1), (1, 1)))
        c = backdoor.Constraint((0, 1), implication)
        result = recursive.solve_recursive(2, (c,), "HORN", 0)
        self.assertEqual(result["status"], "SAT")
        self.assertIn(tuple(result["witness"]), brute(2, (c,)))

    def test_saved_artifact_records_all_outcomes(self):
        artifact = json.loads((HERE / "RECURSIVE_BACKDOOR_RESULTS.json").read_text(encoding="utf-8"))
        self.assertEqual(artifact["status"], "PASS")
        self.assertEqual(len(artifact["cases"]), 4)
        self.assertEqual({case["result"]["status"] for case in artifact["cases"]},
                         {"SAT", "UNSAT", "UNKNOWN"})


if __name__ == "__main__":
    unittest.main()
