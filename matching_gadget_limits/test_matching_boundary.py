import unittest

from matching_boundary import (
    alternating_exchange, bipartite_cost_example, boundary_signature,
    encoded_and, even_delta_audit, threshold_support_audit, valid_domain, verify_matching,
)


class MatchingBoundaryTests(unittest.TestCase):
    def test_exact_three_copy_equality_fails_exchange(self):
        checked = even_delta_audit([0, 63], 6)
        self.assertFalse(checked["is_even_delta_matroid"])
        self.assertEqual(checked["exchange_failure"]["A"], 0)
        self.assertEqual(checked["exchange_failure"]["B"], 63)

    def test_double_rail_and_fails_on_output_rail(self):
        for inputs in (2, 3):
            feasible = set(encoded_and(inputs))
            all_bits = (1 << (2 * (inputs + 1))) - 1
            output_rail = 2 * inputs
            self.assertIn(0, feasible)
            self.assertIn(all_bits, feasible)
            self.assertTrue(all((1 << output_rail) ^ (1 << f) not in feasible
                                for f in range(2 * (inputs + 1)) if f != output_rail))
            self.assertFalse(even_delta_audit(feasible, 2 * (inputs + 1))["is_even_delta_matroid"])

    def test_promised_domain_copy_is_realizable(self):
        edges = [(0, 5, 0), (1, 2, 0), (3, 4, 0)]
        signature = boundary_signature(6, edges, range(6))
        self.assertTrue(even_delta_audit(signature, 6)["is_even_delta_matroid"])
        self.assertEqual(set(signature) & set(valid_domain(3)), {0, 63})
        self.assertEqual(len(signature), 8)

    def test_validity_is_realizable_but_union_is_not_intersection(self):
        copy = [(0, 5, 0), (1, 2, 0), (3, 4, 0)]
        validity = [(0, 1, 0), (2, 3, 0), (4, 5, 0)]
        first = set(boundary_signature(6, copy, range(6)))
        second = set(boundary_signature(6, validity, range(6)))
        union_graph = set(boundary_signature(6, copy + validity, range(6)))
        self.assertEqual(second, set(valid_domain(3)))
        self.assertEqual(first & second, {0, 63})
        self.assertEqual(union_graph & second, second)
        self.assertNotEqual(union_graph, first & second)

    def test_positive_threshold_is_not_covered_by_zero_theorem(self):
        signature = boundary_signature(6, bipartite_cost_example([1, 2, 3, 4]), range(4))
        threshold = {state for state, value in signature.items() if value["cost"] <= 5}
        self.assertEqual(threshold, {6, 9, 10, 12})
        self.assertFalse(even_delta_audit(threshold, 4)["is_even_delta_matroid"])
        self.assertTrue(threshold_support_audit(threshold, 4)["passes_necessary_threshold_conditions"])

    def test_exact_copy_violates_two_sided_threshold_exchange(self):
        for logical_ports in (2, 3, 4):
            audit = threshold_support_audit([0, (1 << (2 * logical_ports)) - 1], 2 * logical_ports)
            self.assertFalse(audit["passes_necessary_threshold_conditions"])

    def test_exact_and_violates_two_sided_threshold_exchange(self):
        for inputs in (1, 2, 3):
            feasible = set(encoded_and(inputs))
            arity = 2 * (inputs + 1)
            full, output_rail = (1 << arity) - 1, 2 * inputs
            for f in range(arity):
                if f != output_rail:
                    pair = (1 << output_rail) ^ (1 << f)
                    self.assertNotIn(pair, feasible)
                    self.assertNotIn(full ^ pair, feasible)
            self.assertFalse(threshold_support_audit(feasible, arity)["passes_necessary_threshold_conditions"])

    def test_promised_domain_and_is_realizable(self):
        edges = [(0, 4, 0), (1, 5, 0), (2, 4, 0), (3, 5, 0), (0, 3, 0)]
        signature = boundary_signature(6, edges, range(6))
        self.assertEqual(set(signature) & set(valid_domain(3)), set(encoded_and(2)))
        self.assertTrue(even_delta_audit(signature, 6)["is_even_delta_matroid"])
        self.assertTrue(set(signature) - set(valid_domain(3)))

    def test_every_signed_example_threshold_obeys_two_sided_exchange(self):
        edges = bipartite_cost_example([1, -1, 2, -2])
        signature = boundary_signature(6, edges, range(4))
        for cutoff in sorted({row["cost"] for row in signature.values()}):
            support = {state for state, row in signature.items() if row["cost"] <= cutoff}
            self.assertTrue(threshold_support_audit(support, 4)["passes_necessary_threshold_conditions"])
            for A in support:
                for B in support:
                    for e in range(4):
                        if (A ^ B) >> e & 1:
                            proof = alternating_exchange(6, edges, range(4), A, B, e,
                                                         signature[A]["matching"], signature[B]["matching"])
                            cost_A = sum(edges[j][2] for j in proof["matching_neighbor_A"])
                            cost_B = sum(edges[j][2] for j in proof["matching_neighbor_B"])
                            self.assertLessEqual(min(cost_A, cost_B), cutoff)

    def test_signed_zero_support_can_fail(self):
        signature = boundary_signature(6, bipartite_cost_example([1, -1, 2, -2]), range(4))
        zeros = {state for state, value in signature.items() if value["cost"] == 0}
        self.assertEqual(zeros, {3, 12})
        self.assertFalse(even_delta_audit(zeros, 4)["is_even_delta_matroid"])
        self.assertLess(min(value["cost"] for value in signature.values()), 0)

    def test_alternating_exchange_with_internal_vertices_and_signed_costs(self):
        edges = bipartite_cost_example([1, -1, 2, -2])
        signature = boundary_signature(6, edges, range(4))
        for A in signature:
            for B in signature:
                for e in range(4):
                    if (A ^ B) >> e & 1:
                        witness = alternating_exchange(6, edges, range(4), A, B, e,
                                                       signature[A]["matching"], signature[B]["matching"])
                        self.assertNotEqual(witness["e"], witness["f"])
                        self.assertEqual(witness["old_total_cost"], witness["new_total_cost"])

    def test_zero_edges_reproduce_nonnegative_zero_optimum(self):
        edges = [(0, 1, 0), (0, 2, 3), (1, 3, 0), (2, 3, 0)]
        signature = boundary_signature(4, edges, range(4))
        zeros = {state for state, value in signature.items() if value["cost"] == 0}
        zero_graph = set(boundary_signature(4, [e for e in edges if e[2] == 0], range(4)))
        self.assertEqual(zeros, zero_graph)

    def test_empty_relation_is_not_called_a_delta_matroid(self):
        signature = boundary_signature(1, [], [])
        self.assertEqual(signature, {})
        self.assertFalse(even_delta_audit(signature, 0)["is_even_delta_matroid"])

    def test_matching_replay_rejects_wrong_boundary_and_duplicates(self):
        edges = [(0, 1, 0)]
        self.assertTrue(verify_matching(2, edges, (0, 1), 0, [0]))
        self.assertFalse(verify_matching(2, edges, (0, 1), 1, [0]))
        self.assertFalse(verify_matching(2, edges, (0, 1), 0, [0, 0]))


if __name__ == "__main__":
    unittest.main()
