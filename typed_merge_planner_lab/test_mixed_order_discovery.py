"""Finite controls for mixed relation order discovery."""
import json
from pathlib import Path
import unittest

from mixed_bridge_width import transformed_primal
from mixed_order_discovery import discover, order_width


HERE = Path(__file__).resolve().parent


class MixedOrderDiscoveryTests(unittest.TestCase):
    def test_complete_graph_control(self):
        n = 6
        adj = tuple(((1 << n) - 1) ^ (1 << v) for v in range(n))
        result = discover(adj)
        self.assertEqual(result["width"], 5)
        self.assertEqual(order_width(adj, tuple(result["order"])), 5)
        self.assertEqual(result["subsets"], 1 << n)

    def test_transformed_controls_have_reconstructed_orders(self):
        from itertools import combinations
        triples = tuple(combinations(range(4), 3))
        for mask in range(16):
            clauses = tuple(triples[i] for i in range(4) if mask >> i & 1)
            adj = transformed_primal(clauses, 4)
            result = discover(adj)
            self.assertEqual(result["width"], order_width(adj, tuple(result["order"])))

    def test_saved_review(self):
        artifact = json.loads((HERE / "MIXED_ORDER_DISCOVERY_RESULTS.json").read_text(encoding="utf-8"))
        review = json.loads((HERE / "MIXED_ORDER_DISCOVERY_REVIEW.json").read_text(encoding="utf-8"))
        self.assertTrue(artifact["all_orders_optimal"])
        self.assertEqual(review["status"], "PASS")
        self.assertTrue(review["orders_match"])
        self.assertTrue(review["source_hashes_match"])


if __name__ == "__main__":
    unittest.main()
