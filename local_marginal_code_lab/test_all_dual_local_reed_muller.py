"""Adversarial tests for the combined RM all-dual/local certificate."""

from __future__ import annotations

import copy
import json
import unittest
from fractions import Fraction
from pathlib import Path

from all_dual_local_reed_muller import (
    local_witness_atom_count,
    make_certificate,
    verify_certificate,
)
from local_marginal import orthogonal_basis, span
from reed_muller import generator_rows


ROOT = Path(__file__).resolve().parent


class AllDualLocalReedMullerTests(unittest.TestCase):
    def test_saved_results_replay(self):
        payload = json.loads((ROOT / "REED_MULLER_ALL_DUAL_LOCAL_RESULTS.json").read_text())
        self.assertEqual(payload["schema"], "reed_muller_all_dual_local_results_v1")
        self.assertEqual(len(payload["records"]), 3)
        for record in payload["records"]:
            self.assertTrue(verify_certificate(record["certificate"])["valid"])

    def test_exact_rm1_scope_rule_and_counts(self):
        certificate = make_certificate(1)["certificate"]
        self.assertEqual(certificate["level"], 3)
        self.assertEqual(certificate["word_replay"]["word_count"], 16)
        self.assertEqual(certificate["scope_count"], 93)
        self.assertEqual(certificate["local_witness_atom_count"], local_witness_atom_count(8, 3))
        self.assertEqual(certificate["fractional_feasible_weight"], "10/3")
        self.assertEqual(certificate["combined_relaxation_optimum"], "10/3")
        self.assertEqual(certificate["integrality_ratio"], "6/5")

    def test_rm2_exact_word_replay_and_rm3_theorem_scope(self):
        rm2 = make_certificate(2)["certificate"]
        rm3 = make_certificate(3)["certificate"]
        self.assertEqual(rm2["word_replay"], {
            "status": "EXACT",
            "word_count": 65536,
            "minimum_distance": 8,
            "pinned_minimum": 8,
        })
        self.assertEqual(rm2["level"], 7)
        self.assertEqual(rm3["level"], 15)
        self.assertEqual(rm3["word_replay"], {"status": "THEOREM_ONLY", "word_count": None})
        self.assertEqual(rm3["integrality_ratio"], "120/71")

    def test_next_level_rejects_one_hot_on_a_minimum_dual_support(self):
        rows = generator_rows(1)
        dual = span(orthogonal_basis(rows, 8), 1 << 20)
        support = next(word for word in dual if word.bit_count() == 4 and not word & 1)
        scope = tuple(index for index in range(8) if support >> index & 1)
        pinned = [word for word in span(rows) if word & 1]
        projected = {tuple((word >> index) & 1 for index in scope) for word in pinned}
        self.assertNotIn((1, 0, 0, 0), projected)

    def test_projection_support_requires_strict_distance_slack(self):
        certificate = make_certificate(1)["certificate"]
        forged = copy.deepcopy(certificate)
        forged["projection_support"]["one_hot_boundary_assignments_supported"] = False
        self.assertFalse(verify_certificate(forged)["valid"])

    def test_mutated_product_and_optimum_rejected(self):
        certificate = make_certificate(2)["certificate"]
        forged = copy.deepcopy(certificate)
        forged["local_sparse_marginal"]["one_hot_coordinate_mass"] = str(Fraction(1, 6))
        self.assertFalse(verify_certificate(forged)["valid"])
        forged = copy.deepcopy(certificate)
        forged["combined_relaxation_optimum"] = "6"
        self.assertFalse(verify_certificate(forged)["valid"])


if __name__ == "__main__":
    unittest.main()
