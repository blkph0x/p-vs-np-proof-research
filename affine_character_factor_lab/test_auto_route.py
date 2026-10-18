import unittest

import auto_route
import elimination_controls


class AutoRouteTests(unittest.TestCase):
    def test_chain_is_discovered_and_solved(self):
        factors = elimination_controls.connected_chain(16)
        result = auto_route.solve_auto(32, factors, width_cap=3)
        self.assertEqual(result["status"], "EXACT")
        self.assertEqual(result["value"], [1, 1])
        checked = auto_route.verify_auto(32, factors, result, width_cap=3)
        self.assertTrue(checked["valid"], checked)

    def test_complete_graph_discovery_returns_no(self):
        factors = [{'kind': 'or', 'literals': [i + 1, j + 1]}
                   for i in range(8) for j in range(i + 1, 8)]
        result = auto_route.solve_auto(8, factors, width_cap=2)
        self.assertEqual(result["status"], "NO")
        self.assertNotIn("value", result)
        self.assertTrue(auto_route.verify_auto(8, factors, result, width_cap=2)["valid"])

    def test_discovery_cap_is_unknown(self):
        factors = [{'kind': 'or', 'literals': [i + 1, i + 2]}
                   for i in range(31)]
        result = auto_route.solve_auto(32, factors, width_cap=1, max_states=1)
        self.assertEqual(result["status"], "UNKNOWN")
        self.assertNotIn("value", result)
        self.assertTrue(auto_route.verify_auto(32, factors, result,
                                               width_cap=1, max_states=1)["valid"])

    def test_weighted_certificate_mutation_is_rejected(self):
        factors = elimination_controls.connected_chain(4)
        result = auto_route.solve_auto(8, factors, width_cap=3)
        self.assertEqual(result["status"], "EXACT")
        result["weighted_result"]["value"] = [2, 1]
        checked = auto_route.verify_auto(8, factors, result, width_cap=3)
        self.assertFalse(checked["valid"])
        self.assertEqual(checked["status"], "INVALID")


if __name__ == "__main__":
    unittest.main()
