"""Independent coverage, local signature and Boolean-composition controls."""
from itertools import product
import json
import unittest

import not_cycle as control


def small_matchings(n, edges, removed=()):
    """Independent bounded recursion, used only on at most twelve vertices."""
    if n > 12:
        raise ValueError("test oracle is capped at twelve vertices")
    remaining = set(range(n)) - set(removed)

    def visit(vertices):
        if not vertices:
            yield ()
            return
        u = min(vertices)
        for edge_id, (a, b) in enumerate(edges):
            if a == u and b in vertices:
                for suffix in visit(vertices - {a, b}):
                    yield (edge_id,) + suffix
            elif b == u and a in vertices:
                for suffix in visit(vertices - {a, b}):
                    yield (edge_id,) + suffix

    return list(visit(remaining))


class MatchingCompositionTests(unittest.TestCase):
    def test_exact_local_signature_and_promised_NOT(self):
        local = control.local_signature()
        self.assertEqual(local["feasible_masks"], [3, 5, 6, 9, 10, 12])
        self.assertEqual(local["promised_feasible_masks"], [3, 12])
        for deleted in range(16):
            removed = [v for v in range(4) if deleted >> v & 1]
            oracle = small_matchings(6, local["edges"], removed)
            self.assertEqual(len(oracle), 2 if deleted.bit_count() == 2 else 0)
            self.assertEqual(local["states"][deleted]["matching_count"], len(oracle))
        for left, right in product((0, 1), repeat=2):
            deleted = 3 * left + 12 * right
            self.assertEqual(deleted in local["feasible_masks"], left != right)

    def test_global_graph_indexing_and_edge_identity(self):
        for k in (1, 2, 3, 4, 5, 7, 11):
            graph = control.build_cycle(k)
            expected = {tuple(sorted((6 * i + t, 6 * i + h)))
                        for i in range(k) for t in range(4) for h in (4, 5)}
            expected |= {tuple(sorted((6 * i + 2 + rail, 6 * ((i + 1) % k) + rail)))
                         for i in range(k) for rail in (0, 1)}
            self.assertEqual(set(map(tuple, graph["edges"])), expected)
            self.assertEqual(len(graph["edges"]), len(expected))
            self.assertEqual((graph["vertices"], len(graph["edges"])), (6 * k, 10 * k))
            self.assertEqual(sorted(sum(graph["local_edge_ids"], []) + sum(graph["wire_edge_ids"], [])),
                             list(range(10 * k)))

    def test_explicit_partial_matching_and_odd_false_positives(self):
        for k in (1, 2, 3, 4, 5, 7, 11):
            graph = control.build_cycle(k)
            matching = control.partial_rail_matching(graph)
            endpoints = [v for edge_id in matching for v in graph["edges"][edge_id]]
            self.assertEqual(sorted(endpoints), list(range(6 * k)))
            self.assertEqual(len(matching), 3 * k)
            self.assertTrue(control.verify_matching(6 * k, graph["edges"], matching)["valid"])
            boundary = control.boundary_states(graph, matching)
            self.assertEqual(boundary["wire_masks"], [1] * k)
            self.assertEqual(boundary["local_deleted_masks"], [5] * k)
            self.assertEqual(boundary["invalid_wires"], list(range(k)))
            self.assertIsNone(boundary["decoded_assignment"])
            boolean = control.enumerate_boolean_assignments(k)
            self.assertEqual(len(boolean["satisfying_assignments"]), 0 if k % 2 else 2)

    def test_every_satisfying_assignment_extends_and_decodes(self):
        for k in range(1, 12):
            graph = control.build_cycle(k)
            expected = []
            for bits in product((0, 1), repeat=k):
                assignment = sum(bit << i for i, bit in enumerate(bits))
                satisfies = all(bits[i] != bits[(i + 1) % k] for i in range(k))
                self.assertEqual(control.boolean_satisfies(k, assignment), satisfies)
                if satisfies:
                    expected.append(assignment)
                    matching = control.boolean_extension(graph, assignment)
                    endpoints = [v for edge_id in matching for v in graph["edges"][edge_id]]
                    self.assertEqual(sorted(endpoints), list(range(6 * k)))
                    states = control.boundary_states(graph, matching)
                    self.assertTrue(states["all_ports_valid"])
                    self.assertEqual(states["decoded_assignment"], assignment)
                    self.assertTrue(all(mask in (3, 12) for mask in states["local_deleted_masks"]))
            self.assertEqual(control.enumerate_boolean_assignments(k)["satisfying_assignments"], sorted(expected))
            with self.assertRaises(ValueError):
                control.boolean_extension(graph, 0)

    def test_all_small_global_matchings_respect_decoding_when_ports_valid(self):
        for k in (1, 2):
            graph = control.build_cycle(k)
            matchings = small_matchings(graph["vertices"], graph["edges"])
            self.assertTrue(matchings)
            decoded = set()
            for matching in matchings:
                states = control.boundary_states(graph, matching)
                if states["all_ports_valid"]:
                    assignment = states["decoded_assignment"]
                    decoded.add(assignment)
                    bits = [(assignment >> i) & 1 for i in range(k)]
                    self.assertTrue(all(bits[i] != bits[(i + 1) % k] for i in range(k)))
            self.assertEqual(decoded, set(control.enumerate_boolean_assignments(k)["satisfying_assignments"]))

    def test_checker_rejects_tampered_matchings_and_graphs(self):
        graph = control.build_cycle(3)
        good = control.partial_rail_matching(graph)
        bad = (good[:-1], good + [good[0]], [True] + good[1:], [-1] + good[1:],
               [len(graph["edges"])] + good[1:])
        for matching in bad:
            self.assertFalse(control.verify_matching(graph["vertices"], graph["edges"], matching)["valid"])
        self.assertFalse(control.verify_matching(graph["vertices"] + 1, graph["edges"], good)["valid"])
        self.assertFalse(control.verify_matching(graph["vertices"], graph["edges"], good, removed=(0,))["valid"])
        self.assertFalse(control.verify_matching(graph["vertices"], graph["edges"], good, removed=(0, 0))["valid"])
        self.assertFalse(control.verify_matching(True, (), ())["valid"])
        self.assertFalse(control.verify_matching(2, [(0, 0)], [0])["valid"])
        self.assertFalse(control.verify_matching(2, [(0, True)], [0])["valid"])
        with self.assertRaises(ValueError):
            control.boundary_states(graph, good[:-1])

    def test_invalid_assignments_and_enumeration_cap(self):
        for k in (0, -1, True, 1.5):
            with self.assertRaises(ValueError):
                control.build_cycle(k)
        for assignment in (-1, True, 8, 1.5):
            with self.assertRaises(ValueError):
                control.boolean_satisfies(3, assignment)
        self.assertEqual(control.enumerate_boolean_assignments(3, max_assignments=8)["assignments_checked"], 8)
        for cap in (7, 0, -1, True):
            with self.assertRaises(ValueError):
                control.enumerate_boolean_assignments(3, max_assignments=cap)
        with self.assertRaises(ValueError):
            control.enumerate_boolean_assignments(10**9)

    def test_serialized_original_graph_and_witness_replay(self):
        graph = control.build_cycle(11)
        matching = control.partial_rail_matching(graph)
        replay = json.loads(json.dumps({"graph": graph, "matching": matching}))
        self.assertEqual(replay["graph"], graph)
        self.assertTrue(control.verify_matching(replay["graph"]["vertices"], replay["graph"]["edges"],
                                               replay["matching"])["valid"])
        self.assertFalse(control.boundary_states(replay["graph"], replay["matching"])["all_ports_valid"])


if __name__ == "__main__":
    unittest.main()
