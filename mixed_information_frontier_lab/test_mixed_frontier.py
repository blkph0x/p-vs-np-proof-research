import unittest

import mixed_frontier as mf


class MixedFrontierTests(unittest.TestCase):
    def test_duplicate_parity_collapses(self):
        constraints = [{"kind": "parity", "scope": list(range(12)), "rhs": 0} for _ in range(6)]
        row = mf.analyze_cut(12, constraints, 6)
        self.assertEqual(row["naive_product_states"], 64)
        self.assertEqual(row["reachable_local_product_states"], 2)
        self.assertEqual(row["future_classes"], 2)

    def test_independent_crossing_parity_is_full_product(self):
        constraints = [{"kind": "parity", "scope": [i, 6 + i], "rhs": 0} for i in range(6)]
        row = mf.analyze_cut(12, constraints, 6)
        self.assertEqual(row["naive_product_states"], 64)
        self.assertEqual(row["reachable_local_product_states"], 64)
        self.assertEqual(row["future_classes"], 64)

    def test_cardinality_determines_same_scope_parity(self):
        constraints = [
            {"kind": "cardinality", "scope": list(range(12)), "op": "eq", "target": 6},
            {"kind": "parity", "scope": list(range(12)), "rhs": 0},
        ]
        row = mf.analyze_cut(12, constraints, 6)
        self.assertEqual(row["naive_product_states"], 14)
        self.assertEqual(row["reachable_local_product_states"], 7)
        self.assertEqual(row["future_classes"], 7)

    def test_duplicate_cardinality_collapses(self):
        constraints = [{"kind": "cardinality", "scope": list(range(12)), "op": "eq", "target": 6} for _ in range(5)]
        row = mf.analyze_cut(12, constraints, 6)
        self.assertEqual(row["naive_product_states"], 7 ** 5)
        self.assertEqual(row["reachable_local_product_states"], 7)
        self.assertEqual(row["future_classes"], 7)

    def test_partial_scope_parity_keeps_mixed_product(self):
        constraints = [
            {"kind": "cardinality", "scope": list(range(12)), "op": "eq", "target": 6},
            {"kind": "parity", "scope": [0, 1, 2, 6, 7, 8], "rhs": 0},
        ]
        row = mf.analyze_cut(12, constraints, 6)
        self.assertEqual(row["naive_product_states"], 10)
        self.assertEqual(row["reachable_local_product_states"], 10)
        self.assertEqual(row["future_classes"], 10)

    def test_clause_and_parity_are_not_silently_merged(self):
        constraints = [
            {"kind": "clause", "literals": [i + 1, 7 + i]} for i in range(6)
        ] + [{"kind": "parity", "scope": list(range(12)), "rhs": 0}]
        row = mf.analyze_cut(12, constraints, 6)
        self.assertGreater(row["future_classes"], 1)
        self.assertLessEqual(row["future_classes"], row["reachable_local_product_states"])

    def test_malformed_inputs_fail_closed(self):
        with self.assertRaises(ValueError):
            mf.analyze_cut(4, [{"kind": "parity", "scope": [4], "rhs": 0}], 2)
        with self.assertRaises(ValueError):
            mf.analyze_cut(4, [{"kind": "cardinality", "scope": [0], "op": "eq", "target": 2}], 2)


if __name__ == "__main__":
    unittest.main()
