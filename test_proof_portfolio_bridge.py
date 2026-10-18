import unittest
from pathlib import Path
import sys

ROOT = Path(__file__).parent
sys.path.insert(0, str(ROOT))

import proof_portfolio_bridge as bridge


class TestProofPortfolioBridge(unittest.TestCase):
    def test_small_actual_proof_units(self):
        result = bridge.build_bridge(groups=4, width=3)
        self.assertTrue(result["symbolic_check"])
        self.assertEqual(result["positive_unit_nodes"], 4)
        self.assertEqual(result["raw_interpolant_literals"], 4)
        self.assertEqual(result["proof_empty_clause"], [])

    def test_larger_symbolic_receiver_check(self):
        result = bridge.build_bridge(groups=8, width=4)
        self.assertTrue(result["symbolic_check"])
        self.assertEqual(result["proof_nodes"], 65)
        self.assertEqual(len(result["unit_fragments"]), 8)

    def test_proof_node_cap_fails_closed(self):
        with self.assertRaises(ValueError):
            bridge.build_bridge(groups=1, width=4, max_nodes=6)

    def test_clique_coloring_boundary_is_unknown(self):
        result = bridge.hard_control()
        self.assertEqual(result["status"], "UNKNOWN")
        self.assertGreater(result["shared_count"], result["max_shared"])

    def test_unlabelled_bounded_subdag_scan(self):
        proof, _, _ = bridge.proof_engine.build_fused_partitioned_proof(8, 4)
        result = bridge.scan_bounded_subdags(proof, max_boundary=2, max_local=6, max_nodes=32)
        self.assertEqual(result["considered_nodes"], 42)
        self.assertEqual(result["status_counts"], {"FOUND": 16, "NO_COMPACT": 24, "UNKNOWN": 2})
        self.assertEqual(result["candidate_kind_counts"], {"PB": 8, "TRUTH_TABLE": 24, "UNIT": 8})


if __name__ == "__main__":
    unittest.main()
