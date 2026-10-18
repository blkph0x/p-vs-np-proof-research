"""Integration tests for bounded hidden-XOR discovery."""
import importlib.util
import json
import sys
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parent / "proof_motif_candidate_lab"
sys.path.insert(0, str(ROOT))


def load(name):
    spec = importlib.util.spec_from_file_location(name, ROOT / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


indirect = load("indirect_xor")
reviewer = load("review_indirect_xor")


class HiddenXorTests(unittest.TestCase):
    def test_pair_cancels_shared_variable(self):
        artifact = json.loads((ROOT / "INDIRECT_XOR_RESULTS.json").read_text())
        clauses = [tuple(clause) for clause in artifact["positive_clauses"]]
        candidates = indirect.detect_hidden_xor_pairs(clauses)
        self.assertEqual([reviewer.jsonable(candidate) for candidate in candidates],
                         artifact["positive_candidates"])
        self.assertEqual(list(candidates[0]["support"]), [0, 1, 2, 3])
        self.assertEqual(candidates[0]["rhs"], 1)

    def test_mutation_and_disjoint_controls_reject(self):
        artifact = json.loads((ROOT / "INDIRECT_XOR_RESULTS.json").read_text())
        for key in ("mutated_clauses", "disjoint_clauses"):
            clauses = [tuple(clause) for clause in artifact[key]]
            self.assertEqual(indirect.detect_hidden_xor_pairs(clauses), [])

    def test_independent_artifact_review(self):
        result = reviewer.review()
        self.assertEqual(result["status"], "PASS")
        self.assertTrue(result["source_hashes_match"])


if __name__ == "__main__":
    unittest.main()
