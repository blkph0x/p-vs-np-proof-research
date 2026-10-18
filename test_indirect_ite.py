"""Integration tests for compact ITE motif recognition."""
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


ite = load("indirect_ite")
reviewer = load("review_indirect_ite")


class CompactITETests(unittest.TestCase):
    def test_exact_roles_are_recovered(self):
        artifact = json.loads((ROOT / "INDIRECT_ITE_RESULTS.json").read_text())
        clauses = [tuple(clause) for clause in artifact["positive_clauses"]]
        candidates = ite.detect_compact_ite(clauses)
        normalized = [{**candidate, "support": list(candidate["support"]),
                       "clause_indices": list(candidate["clause_indices"])}
                      for candidate in candidates]
        self.assertEqual(normalized, artifact["positive_candidates"])
        self.assertEqual(reviewer.independent_candidates(clauses),
                         artifact["positive_candidates"])
        self.assertEqual(len(candidates), 2)

    def test_mutation_and_decoy_reject(self):
        artifact = json.loads((ROOT / "INDIRECT_ITE_RESULTS.json").read_text())
        for key in ("mutated_clauses", "decoy_clauses"):
            clauses = [tuple(clause) for clause in artifact[key]]
            self.assertEqual(ite.detect_compact_ite(clauses), [])

    def test_independent_artifact_review(self):
        result = reviewer.review()
        self.assertEqual(result["status"], "PASS")
        self.assertTrue(result["source_hashes_match"])


if __name__ == "__main__":
    unittest.main()
