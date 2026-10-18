import copy
import unittest
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

import repeated_subdag_templates as templates


class TestRepeatedSubdagTemplates(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.artifact = templates.scan_repeated_templates()

    def test_label_free_scan_counts(self):
        self.assertEqual(self.artifact["considered_nodes"], 42)
        self.assertEqual(self.artifact["status_counts"],
                         {"FOUND": 16, "NO_COMPACT": 24, "UNKNOWN": 2})
        self.assertEqual(self.artifact["candidate_kind_counts"],
                         {"PB": 8, "TRUTH_TABLE": 24, "UNIT": 8})

    def test_canonical_templates_repeat(self):
        groups = self.artifact["template_groups"]
        self.assertEqual(sorted(group["occurrences"] for group in groups), [8, 8, 24])
        self.assertEqual(sorted(group["canonical_candidate"]["kind"] for group in groups),
                         ["PB", "TRUTH_TABLE", "UNIT"])

    def test_reuse_charges_each_projection(self):
        for group in self.artifact["template_groups"]:
            self.assertGreater(group["naive_work"], group["reused_work"])
            self.assertEqual(group["saved_work"], group["naive_work"] - group["reused_work"])
        unit = next(group for group in self.artifact["template_groups"]
                    if group["canonical_candidate"]["kind"] == "UNIT")
        self.assertEqual(unit["occurrences"], 8)

    def test_unknown_records_remain_explicit(self):
        unknown = [row for row in self.artifact["records"] if row["status"] == "UNKNOWN"]
        self.assertEqual(len(unknown), 2)
        self.assertTrue(all(row["candidate"] is None for row in unknown))
        self.assertTrue(all(row["reason"] for row in unknown))

    def test_scale_scan_keeps_projection_cap_explicit(self):
        scale = templates.scan_repeated_templates(groups=256, width=8,
                                                   max_boundary=2, max_local=6,
                                                   max_nodes=32)
        self.assertEqual(scale["considered_nodes"], 2306)
        self.assertEqual(scale["status_counts"],
                         {"FOUND": 256, "NO_COMPACT": 1792, "UNKNOWN": 258})
        self.assertEqual(sum(row["unknown_stage"] == "projection_cap"
                             for row in scale["records"] if row["status"] == "UNKNOWN"), 256)

    def test_cap_sweep_recovers_the_unit_template(self):
        cap = templates.scan_repeated_templates(groups=256, width=8,
                                                 max_boundary=2, max_local=7,
                                                 max_nodes=32)
        self.assertEqual(cap["status_counts"],
                         {"FOUND": 512, "NO_COMPACT": 1792, "UNKNOWN": 2})
        self.assertEqual(cap["candidate_kind_counts"],
                         {"PB": 256, "TRUTH_TABLE": 1792, "UNIT": 256})
        self.assertEqual(sorted(group["occurrences"] for group in cap["template_groups"]),
                         [256, 256, 1792])

    def test_forged_candidate_is_rejected(self):
        row = next(row for row in self.artifact["records"] if row["candidate"] is not None)
        forged = copy.deepcopy(row["candidate"])
        if forged["kind"] == "UNIT":
            forged["value"] = not bool(forged["value"])
        elif forged["kind"] == "PB":
            forged["bound"] = int(forged["bound"]) + 1
        elif forged["kind"] == "XOR":
            forged["rhs"] = 1 - int(forged["rhs"])
        else:
            forged["accepted_mask"] = int(forged["accepted_mask"]) ^ 1
        self.assertFalse(templates.candidate_matches_relation(
            forged, row["boundary"], row["relation_bits"]))


if __name__ == "__main__":
    unittest.main()
