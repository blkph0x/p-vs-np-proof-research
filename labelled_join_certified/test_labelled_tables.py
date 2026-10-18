"""Independent support-oracle and adversarial certificate tests.

The oracle never calls a producer shortest-path routine. It enumerates original
edge subsets, preserving loop and parallel-edge IDs. Run in this directory with
``python -m unittest -v test_labelled_tables``.
"""

from copy import deepcopy
from itertools import combinations, combinations_with_replacement, product
import json
from pathlib import Path
from random import Random
from tempfile import TemporaryDirectory
import unittest

from labelled_tables import build_tables, load_verified_tables, verify_tables


def describe_word(n, edges, word):
    if type(word) is not int or word < 0 or word >> len(edges):
        raise AssertionError("invalid edge support")
    boundary = label = weight = 0
    for eid, (u, v, a, cost) in enumerate(edges):
        if word >> eid & 1:
            boundary ^= (1 << u) ^ (1 << v)
            label ^= a
            weight += cost
    return boundary, label, weight


def support_oracle(n, edges):
    result = {}
    for word in range(1 << len(edges)):
        boundary, label, weight = describe_word(n, edges, word)
        key = boundary, label
        if key not in result or weight < result[key]:
            result[key] = weight
    return result


class LabelledTableTests(unittest.TestCase):
    def make_tables(self, n, edges, p):
        produced = build_tables(n, edges, p)
        self.assertEqual(produced["status"], "EXACT", produced)
        certificate = produced["certificate"]
        verdict = verify_tables(n, edges, p, certificate)
        self.assertTrue(verdict["valid"], verdict)
        self.assertEqual(verdict["status"], "EXACT", verdict)
        tables = load_verified_tables(n, edges, p, certificate)
        return tables, certificate

    def assert_query(self, n, edges, oracle, answer, boundary, label):
        self.assertEqual(answer["status"], "EXACT")
        optimum = oracle.get((boundary, label))
        self.assertEqual(answer["weight"], optimum)
        if optimum is None:
            self.assertIsNone(answer["word"])
        else:
            self.assertEqual(
                describe_word(n, edges, answer["word"]),
                (boundary, label, optimum),
            )

    def assert_graph(self, n, edges, p, *, inspect_lifts=False):
        tables, certificate = self.make_tables(n, edges, p)
        oracle = support_oracle(n, edges)
        for z in range(1 << p):
            self.assert_query(n, edges, oracle, tables.eulerian_join(z), 0, z)
            for u, v in combinations(range(n), 2):
                self.assert_query(
                    n, edges, oracle, tables.pair_join(u, v, z),
                    (1 << u) ^ (1 << v), z,
                )
        if inspect_lifts:
            for u in range(n):
                for v in range(n):
                    for z in range(1 << p):
                        distance = tables.lift_distance(u, v, z)
                        word = tables.lift_word(u, v, z)
                        if distance is None:
                            self.assertIsNone(word)
                        else:
                            boundary, label, weight = describe_word(n, edges, word)
                            self.assertEqual(boundary, (1 << u) ^ (1 << v))
                            self.assertEqual(label, z)
                            self.assertLessEqual(weight, distance)
        return tables, certificate

    def assert_invalid(self, n, edges, p, certificate):
        verdict = verify_tables(n, edges, p, certificate)
        self.assertFalse(verdict["valid"], verdict)
        self.assertEqual(verdict["status"], "INVALID", verdict)
        with self.assertRaises(ValueError):
            load_verified_tables(n, edges, p, certificate)

    def test_all_small_one_bit_simple_graphs(self):
        count = 0
        for n in range(5):
            pairs = list(combinations(range(n), 2))
            for choices in product(range(3), repeat=len(pairs)):
                edges = [(u, v, choice - 1, 1)
                         for (u, v), choice in zip(pairs, choices) if choice]
                self.assert_graph(n, edges, 1)
                count += 1
        self.assertEqual(count, 761)

    def test_all_two_edge_two_bit_multigraphs(self):
        types = [(u, v, a, w) for u, v in [(0, 0), (0, 1), (1, 1)]
                 for a in range(4) for w in [0, 1]]
        count = 0
        for m in range(3):
            for selected in combinations_with_replacement(types, m):
                self.assert_graph(2, list(selected), 2)
                count += 1
        self.assertEqual(count, 325)

    def test_seeded_weighted_multigraphs(self):
        rng = Random(1081801)
        for _ in range(120):
            n, p = rng.randrange(6), rng.randrange(4)
            edges = []
            if n:
                edges = [(rng.randrange(n), rng.randrange(n),
                          rng.randrange(1 << p), rng.randrange(8))
                         for _ in range(rng.randrange(9))]
            self.assert_graph(n, edges, p, inspect_lifts=True)

    def test_disconnected_and_cancelled_walks(self):
        edges = [(0, 1, 0, 1), (2, 3, 1, 1), (3, 4, 0, 1), (4, 2, 0, 1)]
        tables, _ = self.assert_graph(5, edges, 1, inspect_lifts=True)
        self.assertIsNone(tables.lift_distance(0, 1, 1))
        self.assertEqual(tables.pair_join(0, 1, 1)["weight"], 4)
        edges.append((0, 2, 0, 100))
        tables, _ = self.assert_graph(5, edges, 1, inspect_lifts=True)
        self.assertEqual(tables.lift_distance(0, 1, 1), 204)
        walk_word = tables.lift_word(0, 1, 1)
        self.assertEqual(describe_word(5, edges, walk_word), (3, 1, 4))
        self.assertEqual(tables.pair_join(0, 1, 1)["weight"], 4)

    def test_label_closure_and_big_integers(self):
        edges = [(0, 1, 1, 1), (1, 2, 0, 1), (2, 0, 0, 1),
                 (3, 4, 2, 1), (4, 5, 0, 1), (5, 3, 0, 1)]
        tables, certificate = self.assert_graph(6, edges, 2)
        self.assertIsNone(certificate["closed_cost"][3])
        self.assertEqual(tables.eulerian_join(3)["weight"], 6)
        huge = 10 ** 120
        edges = [(0, 0, 1, huge), (0, 1, 2, huge + 1),
                 (0, 1, 0, huge - 1), (1, 1, 3, 0)]
        tables, certificate = self.assert_graph(2, edges, 2, inspect_lifts=True)
        roundtrip = json.loads(json.dumps(certificate))
        self.assertTrue(verify_tables(2, edges, 2, roundtrip)["valid"])
        self.assertEqual(tables.eulerian_join(3)["weight"], 0)

    def test_empty_graphs_and_zero_label_dimension(self):
        for n in range(4):
            for p in range(3):
                self.assert_graph(n, [], p, inspect_lifts=True)
        self.assert_graph(3, [(0, 0, 0, 0), (0, 1, 0, 4),
                              (0, 1, 0, 2), (1, 2, 0, 1)], 0)

    def test_producer_and_verifier_budgets(self):
        edges = [(0, 1, 1, 0)]
        _, certificate = self.make_tables(2, edges, 1)
        for caps in [dict(max_states=3), dict(max_total_states=9),
                     dict(max_relaxations=0)]:
            result = build_tables(2, edges, 1, **caps)
            self.assertEqual(result["status"], "UNKNOWN", result)
            self.assertIsNone(result["certificate"])
        result = build_tables(2, edges, 1, max_states=4,
                              max_total_states=10, max_relaxations=100)
        self.assertEqual(result["status"], "EXACT", result)
        needed = result["stats"]["relaxations"]
        self.assertGreater(needed, 0)
        self.assertEqual(build_tables(2, edges, 1, max_relaxations=needed)["status"], "EXACT")
        partial = build_tables(2, edges, 1, max_relaxations=needed - 1)
        self.assertEqual(partial["status"], "UNKNOWN")
        self.assertEqual(partial["stats"]["relaxations"], needed - 1)
        verified = verify_tables(2, edges, 1, certificate)
        arcs = verified["stats"]["arc_checks"]
        self.assertEqual(verify_tables(2, edges, 1, certificate,
                                      verification_arc_limit=arcs)["status"], "EXACT")
        partial = verify_tables(2, edges, 1, certificate,
                                verification_arc_limit=arcs - 1)
        self.assertEqual(partial["status"], "UNKNOWN")
        self.assertEqual(partial["stats"]["arc_checks"], arcs - 1)
        for caps in [dict(verification_state_limit=9),
                     dict(verification_arc_limit=0)]:
            verdict = verify_tables(2, edges, 1, certificate, **caps)
            self.assertFalse(verdict["valid"])
            self.assertEqual(verdict["status"], "UNKNOWN", verdict)
        for caps in [dict(max_states=0), dict(max_total_states=0)]:
            self.assertEqual(build_tables(0, [], 0, **caps)["status"], "UNKNOWN")
        self.assertEqual(build_tables(0, [], 0, max_relaxations=0)["status"], "EXACT")
        # The dimension guard must precede construction of enormous tables.
        self.assertEqual(build_tables(0, [], 1000000)["status"], "UNKNOWN")

    def test_reject_invalid_requests(self):
        invalid = [(-1, [], 0), (True, [], 0), (1.0, [], 0),
                   (1, [], -1), (1, [], True), (1, [], 1.0),
                   (0, [(0, 0, 0, 0)], 0),
                   (1, [(True, 0, 0, 0)], 0),
                   (1, [(0, 1, 0, 0)], 0),
                   (1, [(0, 0, True, 0)], 1),
                   (1, [(0, 0, 2, 0)], 1),
                   (1, [(0, 0, -1, 0)], 1),
                   (1, [(0, 0, 0, True)], 0),
                   (1, [(0, 0, 0, -1)], 0),
                   (1, [(0, 0, 0, 0.5)], 0),
                   (1, [(0, 0, 0)], 0)]
        for n, edges, p in invalid:
            with self.subTest(n=n, edges=edges, p=p):
                with self.assertRaises(ValueError):
                    build_tables(n, edges, p)
                verdict = verify_tables(n, edges, p, {})
                self.assertFalse(verdict["valid"])
                self.assertEqual(verdict["status"], "INVALID")
        for name in ["max_states", "max_total_states", "max_relaxations"]:
            for value in [-1, True, 0.5, None]:
                with self.assertRaises(ValueError):
                    build_tables(1, [], 0, **{name: value})
        tables, certificate = self.make_tables(2, [], 1)
        for name in ["verification_state_limit", "verification_arc_limit"]:
            for value in [-1, True, 0.5, None]:
                verdict = verify_tables(2, [], 1, certificate, **{name: value})
                self.assertEqual(verdict["status"], "INVALID")
        for label in [-1, 2, True, 0.5]:
            with self.assertRaises(ValueError):
                tables.eulerian_join(label)
            with self.assertRaises(ValueError):
                tables.pair_join(0, 1, label)
        for u, v in [(-1, 1), (0, 2), (True, 1), (0, False)]:
            with self.assertRaises(ValueError):
                tables.pair_join(u, v, 0)
        with self.assertRaises(ValueError):
            tables.pair_join(0, 0, 0)

    def test_saved_json_and_verified_table_isolation(self):
        edges = [(0, 1, 1, 3), (1, 1, 2, 0), (0, 0, 3, 5)]
        tables, certificate = self.make_tables(2, edges, 2)
        expected = [tables.eulerian_join(z) for z in range(4)]
        with TemporaryDirectory() as directory:
            path = Path(directory) / "tables.json"
            path.write_text(json.dumps(certificate), encoding="utf-8")
            saved = json.loads(path.read_text(encoding="utf-8"))
        restored = load_verified_tables(2, edges, 2, saved)
        self.assertEqual([restored.eulerian_join(z) for z in range(4)], expected)
        saved["eulerian"]["dist"][0] = 999
        certificate["lift"][0]["dist"][0] = 999
        copied = tables.as_certificate()
        copied["closed_cost"][0] = 999
        edges[0] = (0, 1, 1, 1000)
        self.assertEqual([tables.eulerian_join(z) for z in range(4)], expected)
        self.assertEqual([restored.eulerian_join(z) for z in range(4)], expected)
        self.assertEqual(tables.as_certificate()["closed_cost"][0], 0)
        with self.assertRaises(AttributeError):
            tables.n = 999

    def test_reject_feasible_but_suboptimal_distance(self):
        edges = [(0, 1, 0, 1), (0, 2, 0, 2), (2, 1, 0, 2)]
        _, certificate = self.make_tables(3, edges, 0)
        altered = deepcopy(certificate)
        # A real rooted path of cost four exists. Only optimality checking
        # against the direct cost-one arc rules out this claimed distance.
        altered["lift"][0]["dist"][1] = 4
        altered["lift"][0]["parent"][1] = [2, 2]
        altered["lift"][0]["depth"][1] = 2
        self.assert_invalid(3, edges, 0, altered)

    def test_metadata_and_structural_mutations(self):
        n, p = 3, 2
        edges = [(0, 1, 1, 0), (1, 2, 2, 0), (2, 0, 0, 0), (1, 1, 3, 1)]
        _, certificate = self.make_tables(n, edges, p)
        for key in certificate:
            altered = deepcopy(certificate)
            del altered[key]
            self.assert_invalid(n, edges, p, altered)
        for key, value in [("format", "wrong"), ("n", True), ("p", False),
                           ("edge_hash", "0" * 64), ("lift", None),
                           ("closed_cost", []), ("closed_source", [])]:
            altered = deepcopy(certificate)
            altered[key] = value
            self.assert_invalid(n, edges, p, altered)
        self.assert_invalid(n, edges + [(0, 0, 0, 0)], p, certificate)
        self.assert_invalid(n + 1, edges, p, certificate)
        self.assert_invalid(n, edges, p + 1, certificate)
        for field, value in [("dist", 1), ("dist", False),
                             ("parent", [0, 0]), ("depth", None),
                             ("depth", False)]:
            altered = deepcopy(certificate)
            altered["lift"][0][field][0] = value
            self.assert_invalid(n, edges, p, altered)
        finite = next(i for i, d in enumerate(certificate["lift"][0]["dist"])
                      if i != 0 and d is not None)
        for field, value in [("dist", -1), ("depth", True), ("depth", 1000000),
                             ("parent", [0, len(edges)]),
                             ("parent", [n * (1 << p), 0]),
                             ("parent", [True, 0]), ("parent", [0, True])]:
            altered = deepcopy(certificate)
            altered["lift"][0][field][finite] = value
            self.assert_invalid(n, edges, p, altered)
        for field in ["dist", "parent", "depth"]:
            altered = deepcopy(certificate)
            altered["lift"][0][field].pop()
            self.assert_invalid(n, edges, p, altered)

    def test_reject_false_unreachability(self):
        edges = [(0, 1, 0, 3)]
        _, certificate = self.make_tables(2, edges, 0)
        altered = deepcopy(certificate)
        for field in ["dist", "parent", "depth"]:
            altered["lift"][0][field][1] = None
        self.assert_invalid(2, edges, 0, altered)
        edges = [(0, 0, 1, 3)]
        _, certificate = self.make_tables(1, edges, 1)
        altered = deepcopy(certificate)
        for field in ["dist", "parent", "depth"]:
            altered["eulerian"][field][1] = None
        self.assert_invalid(1, edges, 1, altered)

    def test_reject_zero_cost_predecessor_cycles(self):
        edges = [(0, 1, 0, 0), (1, 2, 0, 0), (2, 0, 0, 0)]
        _, certificate = self.make_tables(3, edges, 0)
        altered = deepcopy(certificate)
        altered["lift"][0]["parent"][1] = [2, 1]
        altered["lift"][0]["parent"][2] = [1, 1]
        altered["lift"][0]["depth"][1] = 1
        altered["lift"][0]["depth"][2] = 2
        self.assert_invalid(3, edges, 0, altered)
        edges = [(0, 0, 1, 0), (0, 0, 2, 0)]
        _, certificate = self.make_tables(1, edges, 2)
        altered = deepcopy(certificate)
        altered["eulerian"]["parent"][1] = [2, 3]
        altered["eulerian"]["parent"][2] = [1, 3]
        altered["eulerian"]["depth"][1] = 1
        altered["eulerian"]["depth"][2] = 2
        self.assert_invalid(1, edges, 2, altered)

    def test_reject_forged_closed_walk_and_eulerian_values(self):
        edges = [(0, 0, 1, 3), (1, 1, 2, 5)]
        _, certificate = self.make_tables(2, edges, 2)
        for key, index, value in [("closed_cost", 0, False),
                                  ("closed_cost", 1, 0),
                                  ("closed_cost", 3, 8),
                                  ("closed_source", 0, 0),
                                  ("closed_source", 1, None),
                                  ("closed_source", 1, True),
                                  ("closed_source", 1, 1)]:
            altered = deepcopy(certificate)
            altered[key][index] = value
            self.assert_invalid(2, edges, 2, altered)
        for field, index, value in [("dist", 0, False), ("dist", 3, 0),
                                    ("dist", 3, 9), ("depth", 1, True),
                                    ("parent", 1, [0, True]),
                                    ("parent", 1, [0, 0])]:
            altered = deepcopy(certificate)
            altered["eulerian"][field][index] = value
            self.assert_invalid(2, edges, 2, altered)


if __name__ == "__main__":
    unittest.main()
