import unittest

from order_discovery import (factor_order_from_variable_order, find_order,
                             primal_adjacency, verify_order)


class OrderDiscoveryTests(unittest.TestCase):
    def test_chain_width_three(self):
        scopes = []
        for i in range(8):
            scopes.append([2 * i, 2 * i + 1])
            if i:
                scopes.append([2 * (i - 1), 2 * (i - 1) + 1, 2 * i, 2 * i + 1])
        result = find_order(16, scopes, 3)
        self.assertEqual(result["status"], "EXACT")
        self.assertLessEqual(result["width"], 3)
        self.assertTrue(verify_order(16, scopes, result["order"], 3)["valid"])

    def test_star_width_one(self):
        scopes = [[0, i] for i in range(1, 20)]
        result = find_order(20, scopes, 1)
        self.assertEqual(result["status"], "EXACT")
        self.assertEqual(result["width"], 1)

    def test_complete_graph_no_width_two_order(self):
        scopes = [[i, j] for i in range(7) for j in range(i + 1, 7)]
        result = find_order(7, scopes, 2)
        self.assertEqual(result["status"], "NO")
        self.assertNotIn("order", result)

    def test_cycle_no_width_one_order(self):
        scopes = [[i, (i + 1) % 8] for i in range(8)]
        result = find_order(8, scopes, 1)
        self.assertEqual(result["status"], "NO")

    def test_state_cap_is_unknown(self):
        scopes = [[i, i + 1] for i in range(7)]
        result = find_order(8, scopes, 1, max_states=1)
        self.assertEqual(result["status"], "UNKNOWN")
        self.assertNotIn("order", result)

    def test_mutated_order_rejected(self):
        scopes = [[0, 1], [1, 2], [2, 3]]
        result = find_order(4, scopes, 1)
        bad = list(result["order"]); bad[0], bad[1] = bad[1], bad[0]
        self.assertFalse(verify_order(4, scopes, bad, 1)["valid"])

    def test_scope_sweep_is_deterministic(self):
        scopes = [[0, 1], [0, 1, 2], [2, 3], [3, 4]]
        order = [0, 1, 2, 3, 4]
        self.assertEqual(factor_order_from_variable_order(scopes, order), [0, 1, 2, 3])
        self.assertEqual(primal_adjacency(3, [[0, 2], [1, 2]]), (4, 4, 3))


if __name__ == "__main__":
    unittest.main()
