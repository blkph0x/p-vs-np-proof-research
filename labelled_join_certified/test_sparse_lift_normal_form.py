"""Independent finite tests of supplied sparse-U graph-quotient normalization."""
from copy import deepcopy
from itertools import product
import json
import random
import unittest
from unittest.mock import patch

import sparse_lift_normal_form as normal


def rows_from_columns(columns, r):
    return tuple(sum(((column >> i) & 1) << j for j, column in enumerate(columns))
                 for i in range(r))


def apply_rows(rows, vector):
    return sum(((row & vector).bit_count() % 2) << i for i, row in enumerate(rows))


def brute_rank(vectors):
    span = {0}
    for vector in vectors:
        span |= {value ^ vector for value in tuple(span)}
    return len(span).bit_length() - 1


def direct_H(B, U, V, n):
    # Independently form each output coordinate as B_j + U V_j.
    r = len(B)
    columns = []
    for j in range(n):
        value = sum(((row >> j) & 1) << i for i, row in enumerate(B))
        for k, column in enumerate(U):
            if V[k] >> j & 1:
                value ^= column
        columns.append(value)
    return rows_from_columns(columns, r)


class SparseLiftNormalFormTests(unittest.TestCase):
    def check_case(self, B, U, V, n, target=0, check_words=False):
        result = normal.build_sparse_lift_normal_form(B, U, V, n, target=target)
        self.assertEqual(result["status"], "EXACT")
        certificate = result["certificate"]
        checked = normal.verify_sparse_lift_normal_form(B, U, V, n, certificate, target=target)
        self.assertTrue(checked["valid"], checked)
        r, p = len(B), brute_rank(U)
        self.assertEqual(certificate["label_rows"], p)
        self.assertEqual(certificate["graph_rows"], r - p)
        self.assertEqual(brute_rank(certificate["row_transform"]), r)
        H = direct_H(B, U, V, n)
        self.assertEqual(certificate["H_rows"], list(H))
        Q = certificate["row_transform"]
        expected_columns = [apply_rows(Q, sum(((row >> j) & 1) << i for i, row in enumerate(H)))
                            for j in range(n)]
        self.assertEqual(certificate["rows"], list(rows_from_columns(expected_columns, r)))
        self.assertEqual(certificate["transformed_target"], apply_rows(Q, target))
        top_mask = (1 << (r - p)) - 1
        for column in expected_columns:
            self.assertLessEqual((column & top_mask).bit_count(), 2)
        for functional in Q[:r - p]:
            self.assertTrue(all((functional & column).bit_count() % 2 == 0 for column in U))
        if check_words:
            for word in range(1 << n):
                original = apply_rows(H, word)
                transformed = apply_rows(certificate["rows"], word)
                self.assertEqual(transformed, apply_rows(Q, original))
                self.assertEqual(original == target, transformed == certificate["transformed_target"])
        self.assertEqual(len(result["provenance"]["module_sha256"]), 64)
        self.assertEqual(len(result["provenance"]["input_sha256"]), 64)
        return result

    def test_exhaustive_three_row_two_column_single_U_factor(self):
        sparse = [value for value in range(8) if value.bit_count() <= 2]
        cases = 0
        for columns in product(sparse, repeat=2):
            B = rows_from_columns(columns, 3)
            for column in sparse:
                for V in range(4):
                    self.check_case(B, (column,), (V,), 2, target=(column ^ V) & 7,
                                    check_words=True)
                    cases += 1
        self.assertEqual(cases, 1372)

    def test_seeded_dependent_factors_and_target_equivalence(self):
        rng = random.Random(20261018)
        for _ in range(300):
            r, n, s = rng.randrange(7), rng.randrange(9), rng.randrange(11)

            def sparse_column():
                return sum(1 << i for i in rng.sample(range(r), rng.randrange(min(r, 2) + 1)))

            B = rows_from_columns([sparse_column() for _ in range(n)], r)
            U = tuple(sparse_column() for _ in range(s))
            V = tuple(rng.randrange(1 << n) for _ in range(s))
            self.check_case(B, U, V, n, target=rng.randrange(1 << r), check_words=True)

    def test_component_collapse_preserves_original_edge_coordinates(self):
        B = rows_from_columns((3, 5, 9, 1, 0, 3), 4)
        U, V = (3, 6, 8, 0, 3), (1, 2, 4, 8, 16)
        result = self.check_case(B, U, V, 6, target=13, check_words=True)
        certificate = result["certificate"]
        self.assertEqual(certificate["components"], [[0, 1, 2], [3, 4]])
        self.assertEqual(certificate["row_transform"], [7, 2, 4, 8])
        self.assertEqual(certificate["graph_rows"], 1)
        self.assertEqual(certificate["rows"][0], 12)
        self.assertEqual(certificate["n"], 6)
        self.assertEqual(certificate["forest_columns"], [0, 1, 2])

    def test_empty_zero_rank_and_full_rank(self):
        for n in (0, 5):
            self.check_case((), (), (), n, check_words=True)
            self.check_case((0, 0, 0), (), (), n, target=7, check_words=True)
            self.check_case((0, 0, 0), (1, 2, 4, 0, 1), (0,) * 5, n,
                            target=5, check_words=True)

    def test_invalid_inputs(self):
        invalid = [((1, 1, 1), (), (), 1, 0), ((0, 0, 0), (7,), (0,), 1, 0),
                   ((0,), (2,), (0,), 1, 0), ((0,), (1,), (), 1, 0),
                   ((2,), (), (), 1, 0), ((0,), (1,), (2,), 1, 0),
                   ((True,), (), (), 1, 0), ((0,), (True,), (0,), 1, 0),
                   ((0,), (1,), (False,), 1, 0), ((0,), (), (), True, 0),
                   ((0,), (), (), 1, 2), ((0,), (), (), 1, True),
                   ((-1,), (), (), 1, 0), ((0,), (-1,), (0,), 1, 0)]
        for B, U, V, n, target in invalid:
            with self.subTest(B=B, U=U, V=V, n=n, target=target):
                with self.assertRaises(ValueError):
                    normal.build_sparse_lift_normal_form(B, U, V, n, target=target)
                self.assertFalse(normal.verify_sparse_lift_normal_form(B, U, V, n, {}, target=target)["valid"])

    def test_exact_work_boundaries_and_unknown(self):
        B, U, V, n = (5, 6, 0), (3, 6, 0), (1, 3, 7), 3
        result = self.check_case(B, U, V, n)
        count = result["stats"]["work_units"]
        self.assertEqual(normal.build_sparse_lift_normal_form(B, U, V, n, max_work=count)["status"], "EXACT")
        short = normal.build_sparse_lift_normal_form(B, U, V, n, max_work=count - 1)
        self.assertEqual(short["status"], "UNKNOWN")
        self.assertIsNone(short["certificate"])
        self.assertLessEqual(short["stats"]["work_units"], count - 1)
        cert = result["certificate"]
        count = normal.verify_sparse_lift_normal_form(B, U, V, n, cert)["stats"]["work_units"]
        self.assertTrue(normal.verify_sparse_lift_normal_form(B, U, V, n, cert, verification_work_limit=count)["valid"])
        short = normal.verify_sparse_lift_normal_form(B, U, V, n, cert, verification_work_limit=count - 1)
        self.assertFalse(short["valid"])
        self.assertEqual(short["status"], "UNKNOWN")
        for invalid in (-1, True, 1.5):
            with self.assertRaises(ValueError):
                normal.build_sparse_lift_normal_form(B, U, V, n, max_work=invalid)
            self.assertEqual(normal.verify_sparse_lift_normal_form(B, U, V, n, cert,
                                                                  verification_work_limit=invalid)["status"], "INVALID")

    def test_certificate_mutations_and_input_mismatch(self):
        B, U, V, n = (5, 6, 8, 0), (3, 6, 0), (1, 3, 7), 4
        original = self.check_case(B, U, V, n, target=9)["certificate"]
        mutations = []
        for key, value in (("format", "fake"), ("n", True), ("r", 99), ("input_hash", "0" * 64),
                           ("graph_rows", 0), ("label_rows", True), ("target", 0),
                           ("transformed_target", original["transformed_target"] ^ 1),
                           ("forest_columns", [0, 0]), ("forest_columns", [0, 10]),
                           ("components", [[0, 1, 2, 3, 4]])):
            changed = deepcopy(original)
            changed[key] = value
            mutations.append(changed)
        for field in ("H_rows", "rows", "row_transform"):
            changed = deepcopy(original)
            changed[field][0] ^= 1
            mutations.append(changed)
        changed = deepcopy(original)
        changed["row_transform"][-1] = changed["row_transform"][0]
        mutations.append(changed)
        changed = deepcopy(original)
        changed["components"][0][0] = False
        mutations.append(changed)
        for cert in mutations + [None, [], {}, {**original, "extra": 0}]:
            self.assertFalse(normal.verify_sparse_lift_normal_form(B, U, V, n, cert, target=9)["valid"])
        self.assertFalse(normal.verify_sparse_lift_normal_form(B, U, (1, 3, 6), n, original, target=9)["valid"])

    def test_json_roundtrip_and_verifier_does_not_call_producer(self):
        B, U, V, n = (5, 6, 0), (3, 6, 0), (1, 3, 7), 3
        cert = json.loads(json.dumps(self.check_case(B, U, V, n)["certificate"]))
        with patch.object(normal, "build_sparse_lift_normal_form", side_effect=AssertionError("producer invoked")):
            self.assertTrue(normal.verify_sparse_lift_normal_form(B, U, V, n, cert)["valid"])


if __name__ == "__main__":
    unittest.main()
