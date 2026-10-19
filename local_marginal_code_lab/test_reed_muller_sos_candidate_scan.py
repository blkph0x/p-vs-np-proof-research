"""Adversarial tests for the exact RM(2,5) candidate-cut scan."""
from __future__ import annotations

import copy
import json
import unittest
from pathlib import Path

try:
    from REED_MULLER_SOS_CANDIDATE_SCAN_INDEPENDENT_REVIEW import replay
except ModuleNotFoundError:
    from local_marginal_code_lab.REED_MULLER_SOS_CANDIDATE_SCAN_INDEPENDENT_REVIEW import replay

HERE = Path(__file__).resolve().parent


class CandidateScanTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = json.loads((HERE / "REED_MULLER_LEVEL_D_FULL_RESULTS.json").read_text(encoding="utf-8"))
        cls.witness = json.loads((HERE / "REED_MULLER_SOS_SEVEN_CUT_RESULTS.json").read_text(encoding="utf-8"))
        cls.scan = json.loads((HERE / "REED_MULLER_SOS_CANDIDATE_SCAN_RESULTS.json").read_text(encoding="utf-8"))

    def test_independent_replay_accepts_separation_only_scan(self):
        result = replay(self.source, self.witness, self.scan)
        self.assertTrue(result["valid"])
        self.assertEqual(result["status"], "SEPARATION_ONLY")

    def test_selected_cut_is_exact_and_domain_nonnegative(self):
        selected = self.scan["selected_candidate"]
        self.assertEqual(selected["name"], "adjacent_6_7*adjacent_30_31")
        self.assertEqual(selected["polynomial"], [39060, -14652, 1765, -74, 1])
        self.assertEqual(selected["expectation"], "-657769331520/5129253893")
        self.assertTrue(all(sum(c * t**i for i, c in enumerate(selected["polynomial"])) >= 0
                            for t in range(32)))

    def test_mutated_expectation_is_rejected(self):
        mutated = copy.deepcopy(self.scan)
        mutated["selected_candidate"]["expectation"] = "-1"
        with self.assertRaises(ValueError):
            replay(self.source, self.witness, mutated)

    def test_mutated_source_hash_is_rejected(self):
        mutated = copy.deepcopy(self.scan)
        mutated["source_sha256"]["REED_MULLER_LEVEL_D_FULL_RESULTS.json"] = "0" * 64
        with self.assertRaises(ValueError):
            replay(self.source, self.witness, mutated)


if __name__ == "__main__":
    unittest.main()
