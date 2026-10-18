"""Integration tests for bounded proof-carrying XOR closure."""
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


closure = load("xor_closure")
reviewer = load("review_xor_closure")


class XORClosureTests(unittest.TestCase):
    def test_chain_has_proof_carrying_target(self):
        artifact = json.loads((ROOT / "XOR_CLOSURE_RESULTS.json").read_text())
        result = artifact["positive_result"]
        target = [relation for relation in result["relations"]
                  if relation["support"] == [0, 1, 2, 3, 4, 5, 14]]
        self.assertEqual(result["status"], "BOUNDED_COMPLETE")
        self.assertEqual(len(target), 1)
        self.assertEqual(target[0]["proof_blocks"], [0, 1, 2, 3, 4])

    def test_mutation_does_not_preserve_target(self):
        artifact = json.loads((ROOT / "XOR_CLOSURE_RESULTS.json").read_text())
        result = closure.bounded_closure(artifact["mutated_clauses"], **artifact["parameters"])
        self.assertFalse(any(relation["support"] == [0, 1, 2, 3, 4, 5, 14]
                             for relation in result["relations"]))

    def test_cap_and_independent_review(self):
        artifact = json.loads((ROOT / "XOR_CLOSURE_RESULTS.json").read_text())
        capped = closure.bounded_closure(artifact["branching_clauses"],
                                         max_rounds=2, max_support=8,
                                         max_relations=10)
        self.assertEqual(capped["status"], "UNKNOWN_CAP")
        result = reviewer.review()
        self.assertEqual(result["status"], "PASS")
        self.assertTrue(result["source_hashes_match"])


if __name__ == "__main__":
    unittest.main()

