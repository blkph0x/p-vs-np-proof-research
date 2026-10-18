import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent
LAB = ROOT / "proof_motif_candidate_lab"
sys.path.insert(0, str(LAB))

import sequential_counter as sc


class TestSequentialCounter(unittest.TestCase):
    def test_positive_projection_and_structure(self):
        cert = sc.certificate(5, 2)
        clauses = sc.expected_clauses(5, 2)
        result = sc.verify_certificate(clauses, cert)
        self.assertEqual(result["status"], "ACCEPT")
        self.assertEqual(result["semantic"]["status"], "PASS")

    def test_mutations_and_wrong_threshold_reject(self):
        cert = sc.certificate(4, 2)
        clauses = list(sc.expected_clauses(4, 2))
        clauses.pop(0)
        self.assertEqual(sc.verify_certificate(clauses, cert)["status"], "REJECT")
        wrong = sc.certificate(4, 1)
        self.assertEqual(sc.verify_certificate(sc.expected_clauses(4, 2), wrong)["status"], "REJECT")

    def test_role_permutation_requires_certificate(self):
        cert = sc.certificate(3, 1)
        mapping = {index: 20 - index for index in range(9)}
        inputs = tuple(mapping[index] for index in cert["inputs"])
        states = tuple(tuple(mapping[index] for index in row) for row in cert["states"])
        clauses = [tuple((1 if lit > 0 else -1) * (mapping[abs(lit) - 1] + 1)
                         for lit in clause) for clause in sc.expected_clauses(3, 1)]
        self.assertEqual(sc.verify_certificate(clauses, sc.certificate(3, 1, inputs, states))["status"], "ACCEPT")
        self.assertEqual(sc.discover_canonical(clauses, max_inputs=3, max_threshold=2)["status"], "NOT_FOUND")
        self.assertEqual(sc.discover_isomorphic(clauses, 3, 1)["status"], "FOUND")
        self.assertEqual(sc.discover_isomorphic(clauses, 3, 1, max_variables=4)["status"], "UNKNOWN_CAP")

    def test_saved_independent_review(self):
        result = json.loads((LAB / "SEQUENTIAL_COUNTER_RESULTS.json").read_text(encoding="utf-8"))
        review = json.loads((LAB / "SEQUENTIAL_COUNTER_REVIEW.json").read_text(encoding="utf-8"))
        self.assertTrue(result["all_checks_passed"])
        self.assertTrue(review["all_checks_passed"])


if __name__ == "__main__":
    unittest.main()
