import json
from itertools import product
from pathlib import Path
import unittest

import engine as planner
from invented_relation_bridge import (RESULTS_PATH, build_catalog_artifact,
                                      classify_table, direct_signature,
                                      truth_table_rows, verify_catalog_artifact)

ARTIFACT_PATH = Path(__file__).with_name("INVENTED_RELATION_SIGNATURES.json")


def table_for_rows(rows, arity):
    relation = set(rows)
    table = 0
    for bits in product((0, 1), repeat=arity):
        index = 0
        for bit in bits:
            index = (index << 1) | bit
        if bits in relation:
            table |= 1 << index
    return table


class InventedRelationBridgeTests(unittest.TestCase):
    def test_truth_table_decoder_round_trips_all_small_relations(self):
        for arity in range(4):
            for table in range(1 << (1 << arity)):
                rows = truth_table_rows(table, arity)
                self.assertEqual(table_for_rows(rows, arity), table)

    def test_independent_signature_matches_typed_planner_exhaustively(self):
        for arity in range(4):
            for table in range(1 << (1 << arity)):
                rows = truth_table_rows(table, arity)
                independent = direct_signature(rows, arity)
                self.assertEqual(independent,
                                 planner.relation_signature(rows, arity),
                                 (arity, table))

    def test_known_routes_and_pin_boundary(self):
        parity = table_for_rows(
            [bits for bits in product((0, 1), repeat=3) if sum(bits) % 2 == 0], 3)
        exact_one = table_for_rows(
            [bits for bits in product((0, 1), repeat=3) if sum(bits) == 1], 3)
        p = classify_table(parity, 3)
        q = classify_table(exact_one, 3)
        self.assertEqual(p["signature"], ["MIN", "ZERO"])
        self.assertEqual(p["planner_types"], ["AFFINE"])
        self.assertEqual(p["unpinned_status"]["status"], "POLY_COMMON_SCHAEFER")
        self.assertEqual(q["signature"], [])
        self.assertEqual(q["unpinned_status"]["status"], "NP_COMPLETE_FIXED_LANGUAGE")
        self.assertEqual(q["pinned_status"]["status"], "NP_COMPLETE_PINNED_LANGUAGE")

    def test_saved_invented_catalog_replays_exactly(self):
        artifact = build_catalog_artifact(RESULTS_PATH)
        self.assertEqual(artifact["relation_count"], 32)
        self.assertEqual(verify_catalog_artifact(RESULTS_PATH, artifact)["valid"], True)
        saved = json.loads(ARTIFACT_PATH.read_text(encoding="utf-8"))
        self.assertEqual(verify_catalog_artifact(RESULTS_PATH, saved)["valid"], True)
        for record in artifact["relations"]:
            self.assertIn("unpinned_status", record)
            self.assertIn("pinned_status", record)

    def test_catalog_artifact_mutation_is_rejected(self):
        artifact = build_catalog_artifact(RESULTS_PATH)
        altered = json.loads(json.dumps(artifact))
        altered["relations"][0]["signature"] = ["MIN"]
        self.assertFalse(verify_catalog_artifact(RESULTS_PATH, altered)["valid"])


if __name__ == "__main__":
    unittest.main()
