import unittest

from saturated_clause import (
    boundary_signature, encoded_or, even_delta_audit, exact_or_exchange_witness,
    raw_or_graph, saturated_or_graph, threshold_support_audit, valid_domain,
    verify_matching,
)


class SaturatedClauseTests(unittest.TestCase):
    def test_exact_flat_or_has_minimal_exchange_witness(self):
        for k in range(2, 6):
            proof = exact_or_exchange_witness(k)
            self.assertEqual(proof["A"] ^ proof["B"], 15)
            self.assertEqual([row["neighbor_A"] for row in proof["rejected_neighbors"]], [0, 6, 10])
            self.assertFalse(even_delta_audit(encoded_or(k), 2 * k)["is_even_delta_matroid"])

    def test_one_input_is_outside_obstruction(self):
        self.assertTrue(even_delta_audit(encoded_or(1), 2)["is_even_delta_matroid"])
        with self.assertRaises(ValueError):
            exact_or_exchange_witness(1)

    def test_raw_pair_graph_exactly_implements_or_threshold(self):
        for k in range(1, 5):
            request = raw_or_graph(k)
            signature = boundary_signature(**request)
            self.assertEqual(set(signature), set(valid_domain(k)))
            support = {s for s, row in signature.items() if row["cost"] <= k - 1}
            self.assertEqual(support, set(encoded_or(k)))
            self.assertTrue(threshold_support_audit(support, 2 * k)["passes_necessary_threshold_conditions"])

    def test_scalar_saturation_is_the_boolean_clause_penalty(self):
        for k in range(1, 10):
            for true_count in range(k + 1):
                self.assertEqual(max(0, k - true_count - (k - 1)), int(true_count == 0))

    def test_promised_flat_or_graphs_and_matching_replay(self):
        for k in range(1, 4):
            request = saturated_or_graph(k)
            signature = boundary_signature(**request)
            for state in valid_domain(k):
                self.assertEqual(signature[state]["cost"], int(state == 0))
            for state, row in signature.items():
                self.assertTrue(verify_matching(request["n"], request["edges"], request["terminals"],
                                                state, row["matching"]))
            minima = {s for s, row in signature.items() if row["cost"] == 0}
            self.assertTrue(even_delta_audit(minima, 2 * k)["is_even_delta_matroid"])

    def test_smallest_positive_control_exposes_invalid_zero_states(self):
        signature = boundary_signature(**saturated_or_graph(2))
        self.assertEqual({s: row["cost"] for s, row in signature.items()},
                         {0: 1, 3: 0, 6: 0, 9: 0, 12: 0, 15: 0})
        self.assertEqual(set(signature) - set(valid_domain(2)), {6, 9})

    def test_two_clause_reward_compensation_counterexample(self):
        true_counts = [0, 2]
        self.assertLessEqual(sum(2 - j for j in true_counts), 2)
        self.assertEqual(sum(max(0, 1 - j) for j in true_counts), 1)
        self.assertTrue(any(j == 0 for j in true_counts))


if __name__ == "__main__":
    unittest.main()
