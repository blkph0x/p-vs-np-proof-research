import itertools
import unittest

from circuit_order import (build_edge_or_circuit, clauses_satisfied, evaluate,
                           extend_source_order, primal_edges, source_lower_bound,
                           width_for_order)


class CircuitOrderTests(unittest.TestCase):
    def test_all_ones_is_a_witness_and_gate_tables_are_exact(self):
        circuit = build_edge_or_circuit(4, [(0, 1), (1, 2), (2, 3)])
        for assignment in range(1 << 4):
            values = evaluate(circuit, assignment)
            expected = [values[u + 1] | values[v + 1]
                        for u, v in circuit["edges"]]
            self.assertEqual([values[z] for z in circuit["outputs"]], expected)
        ones = evaluate(circuit, (1 << 4) - 1)
        self.assertTrue(clauses_satisfied(circuit["clauses"], ones))

    def test_source_graph_is_present_in_the_primal_graph(self):
        circuit = build_edge_or_circuit(5, [(0, 1), (1, 3), (2, 4)])
        primal = set(primal_edges(circuit["clauses"], circuit["vertices"]))
        for u, v in circuit["edges"]:
            self.assertIn((u + 1, v + 1), primal)

    def test_lower_bound_for_every_full_order_on_small_case(self):
        circuit = build_edge_or_circuit(3, [(0, 1), (1, 2), (0, 2)])
        primal = primal_edges(circuit["clauses"], circuit["vertices"])
        source = tuple((u + 1, v + 1) for u, v in circuit["edges"])
        for order in itertools.permutations(range(1, circuit["vertices"] + 1)):
            full_width, _ = width_for_order(circuit["vertices"], primal, order)
            source_order = tuple(variable for variable in order if variable <= 3)
            source_width, _ = width_for_order(3, source, source_order)
            self.assertGreaterEqual(full_width, source_width)

    def test_saved_style_controls_have_bound(self):
        for n, edges in (
                (6, [(0, 1), (1, 2), (2, 3), (3, 4), (4, 5)]),
                (6, [(0, i) for i in range(1, 6)]),
                (5, [(u, v) for u in range(3) for v in (3, 4)])):
            result = source_lower_bound(build_edge_or_circuit(n, edges))
            self.assertTrue(result["lower_bound_holds"])
            self.assertTrue(result["additive_upper_bound_holds"])

    def test_extension_is_a_valid_permutation(self):
        circuit = build_edge_or_circuit(4, [(0, 2), (1, 2), (2, 3)])
        order = extend_source_order(circuit, [4, 2, 1, 3])
        self.assertEqual(sorted(order), list(range(1, circuit["vertices"] + 1)))

    def test_additive_bound_exhaustive_on_all_four_vertex_graphs(self):
        graph_edges = list(itertools.combinations(range(4), 2))
        for mask in range(1 << len(graph_edges)):
            edges = [edge for index, edge in enumerate(graph_edges)
                     if mask >> index & 1]
            result = source_lower_bound(build_edge_or_circuit(4, edges))
            self.assertTrue(result["lower_bound_holds"])
            self.assertTrue(result["additive_upper_bound_holds"])


if __name__ == "__main__":
    unittest.main()
