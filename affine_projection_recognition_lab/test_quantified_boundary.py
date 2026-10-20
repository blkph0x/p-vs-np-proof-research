import copy
import itertools
import json
from pathlib import Path
import unittest

import quantified_boundary as producer
import review_quantified_boundary as reviewer


class QuantifiedBoundaryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.saved = json.loads(Path(__file__).with_name("QUANTIFIED_RESULTS.json").read_text(encoding="utf-8"))

    def test_committed_artifact_before_regeneration(self):
        self.assertTrue(reviewer.verify_artifact(self.saved))
        self.assertEqual(self.saved, producer.build_artifact())

    def test_all_1536_source_formulas_and_quantifier_splits(self):
        count = 0
        for spec in producer.campaign_sources():
            row = producer.record(spec)
            self.assertTrue(reviewer.verify_record(row, spec))
            self.assertEqual(row["formula_evaluations"], 20)
            self.assertEqual(row["projection_affine"], row["qbf_true"])
            count += 1
        self.assertEqual(count, 1536)

    def test_quantifiers_are_not_replaced_by_sat(self):
        true = producer.record(producer.source(1, 1, [[-1, 2], [1, -2]]))
        self.assertEqual(true["source_witness_counts"], [1, 1])
        self.assertTrue(true["qbf_true"])
        partial = producer.record(producer.source(1, 1, [[1]]))
        self.assertEqual(partial["source_witness_counts"], [0, 2])
        self.assertFalse(partial["qbf_true"])
        self.assertEqual(partial["ternary_violation"], {
            "universal_mask": 0, "parents": [0, 1, 2], "missing": 3})

    def test_zero_width_empty_clause_tautology_duplicates(self):
        for spec in producer.examples():
            self.assertTrue(reviewer.verify_record(producer.record(spec), spec))
        self.assertTrue(producer.record(producer.source(0, 0, []))["qbf_true"])
        self.assertFalse(producer.record(producer.source(0, 0, [[]]))["qbf_true"])

    def test_rank_affinity_matches_ternary_closure_including_empty(self):
        for subset in range(256):
            points = [x for x in range(8) if subset & (1 << x)]
            members = set(points)
            closure = bool(points) and all(a ^ b ^ c in members
                for a, b, c in itertools.product(points, repeat=3))
            self.assertEqual(producer.affine_by_rank(points), closure)

    def test_complete_replay_rejects_all_adversarial_controls(self):
        controls = reviewer.adversarial_controls(self.saved)
        self.assertEqual(len(controls), 8)

    def test_specific_failures_bind_certificate_to_source(self):
        spec = producer.source(1, 1, [[1]])
        good = producer.record(spec)
        for field, value in [("projection_bits", [1] * 8), ("qbf_true", True),
                             ("lifted_clauses", []), ("source", producer.source(1, 1, []))]:
            corrupt = copy.deepcopy(good)
            corrupt[field] = value
            with self.assertRaisesRegex(reviewer.VerificationError, field + " mismatch"):
                reviewer.verify_record(corrupt, spec)

    def test_caps_never_become_mathematical_answers(self):
        spec = producer.source(1, 1, [[1]])
        for cap in (0, 1, 19):
            row = producer.record(spec, cap)
            self.assertEqual(row["status"], "UNKNOWN_CAP")
            self.assertNotIn("projection_affine", row)
            with self.assertRaises(reviewer.VerificationError):
                reviewer.verify_record(row, spec)
        self.assertEqual(producer.record(spec, 20)["status"], "EXACT")
        large = producer.source(1000000, 0, [])
        self.assertEqual(producer.record(large)["status"], "UNKNOWN_CAP")

    def test_malformed_partitions_and_literals_are_rejected(self):
        for args in [(-1, 1, []), (True, 1, []), (1.0, 1, []),
                     (1, 0, [[0]]), (1, 0, [[2]]), (1, 0, [[True]]),
                     (1, 0, [["1"]]), (1, 0, [1])]:
            with self.assertRaises(ValueError):
                producer.source(*args)


if __name__ == "__main__":
    unittest.main(verbosity=2)
