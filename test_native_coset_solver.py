"""Independent exhaustive support oracles for the native graph/coset route.

These tests enumerate feasible bit vectors directly; no rank, path, matching,
or syndrome helper from the implementation is used by the oracle.
"""
from copy import deepcopy
from itertools import product
from random import Random
import unittest

from native_coset_solver import minimum_tjoin, solve_native, verify_native_result


def rows_from_columns(columns, row_count):
    return tuple(sum(1 << j for j, value in enumerate(columns) if value >> i & 1)
                 for i in range(row_count))


def brute_affine_words(rows, n, target=0, require_nonzero=True, fixed=None):
    """All feasible original supports, optionally fixing coordinate bits."""
    fixed = fixed or {}
    return [word for word in range(int(require_nonzero), 1 << n)
            if sum(((word & row).bit_count() % 2) << i for i, row in enumerate(rows)) == target
            and all((word >> j & 1) == bit for j, bit in fixed.items())]


def brute_words(rows, n, fixed=None):
    return brute_affine_words(rows, n, fixed=fixed)


def brute_affine_graph(vertex_count, edges, target):
    """Enumerate graph supports and calculate odd nonground degrees directly."""
    candidates = []
    for chosen in range(1 << len(edges)):
        degree = [0] * vertex_count
        word = 0
        for j, (u, v, coordinate) in enumerate(edges):
            if chosen >> j & 1:
                degree[u] += 1
                degree[v] += 1
                word |= 1 << coordinate
        actual = sum(1 << v for v in range(vertex_count - 1) if degree[v] % 2)
        if actual == target:
            candidates.append(word)
    return min((word.bit_count() for word in candidates), default=None), candidates


class NativeCosetSolverTests(unittest.TestCase):
    def assert_exact_against_supports(self, rows, n, **kwargs):
        result = solve_native(rows, n, **kwargs)
        target = kwargs.get("target", 0)
        require_nonzero = kwargs.get("require_nonzero", True)
        words = brute_affine_words(rows, n, target, require_nonzero)
        optimum = min((word.bit_count() for word in words), default=None)
        self.assertEqual(result["status"], "EXACT")
        self.assertEqual(result["distance"], optimum)
        self.assertEqual(result["upper_bound"], optimum)
        if optimum is None:
            self.assertIsNone(result["word"])
        else:
            self.assertIn(result["word"], words)
            self.assertEqual(result["word"].bit_count(), optimum)
        self.assertTrue(verify_native_result(rows, n, result, target=target,
                                            require_nonzero=require_nonzero)["valid"])
        exceptional = result["exceptional_coordinates"]
        for branch in result["branches"]:
            fixed = {j: branch["assignment"] >> i & 1 for i, j in enumerate(exceptional)}
            conditioned = brute_affine_words(rows, n, target, require_nonzero, fixed)
            fixed_weight = sum(fixed.values())
            branch_optimum = min((word.bit_count() - fixed_weight for word in conditioned), default=None)
            if branch["kind"] == "INFEASIBLE":
                self.assertEqual(conditioned, [])
            else:
                self.assertEqual(branch["weight"], branch_optimum)
                if branch_optimum is not None:
                    fixed_word = sum(1 << j for j, bit in fixed.items() if bit)
                    self.assertIn(fixed_word | branch["word"], conditioned)
        return result

    def test_affine_targets_exhaustive_small_and_three_row_controls(self):
        cases = 0
        for row_count, max_n in ((0, 4), (1, 4), (2, 4), (3, 2)):
            for n in range(max_n + 1):
                for columns in product(range(1 << row_count), repeat=n):
                    rows = rows_from_columns(columns, row_count)
                    for target in range(1 << row_count):
                        for require_nonzero in (False, True):
                            self.assert_exact_against_supports(rows, n, target=target,
                                                               require_nonzero=require_nonzero)
                            cases += 1
        for columns in ((1, 2, 4), (3, 5, 6), (7, 7, 7), (0, 1, 2, 7),
                        (1, 2, 4, 7), (0, 0, 0, 7), (1, 1, 6, 7),
                        (1, 2, 3, 7), (3, 5, 6, 7), (7, 7, 7, 7)):
            for target in range(8):
                for require_nonzero in (False, True):
                    self.assert_exact_against_supports(rows_from_columns(columns, 3), len(columns),
                                                       target=target, require_nonzero=require_nonzero)
                    cases += 1
        self.assertEqual(cases, 4190)

    def test_affine_target_transformation_and_request_binding(self):
        # The caller's target is always expressed in the original row basis.
        for transform in product(range(8), repeat=3):
            span = {0}
            for row in transform:
                span |= {value ^ row for value in tuple(span)}
            if len(span) != 8:
                continue
            for columns, targets in (((1, 1, 7), (6, 2)), ((1, 2, 4, 7), (0, 5))):
                rows = rows_from_columns(columns, 3)
                for target in targets:
                    for require_nonzero in (False, True):
                        self.assert_exact_against_supports(rows, len(columns), row_transform=transform,
                                                           target=target, require_nonzero=require_nonzero)
        rows = rows_from_columns((1, 2, 4, 7), 3)
        result = solve_native(rows, 4, target=5, require_nonzero=False)
        self.assertFalse(verify_native_result(rows, 4, result)["valid"])
        self.assertFalse(verify_native_result(rows, 4, result, target=5, require_nonzero=True)["valid"])
        for field, value in (("target", 0), ("target", True), ("require_nonzero", True),
                             ("require_nonzero", 0)):
            changed = deepcopy(result)
            changed[field] = value
            self.assertFalse(verify_native_result(rows, 4, changed, target=5,
                                                  require_nonzero=False)["valid"])

    def test_all_small_column_configurations(self):
        # Exhaust all ordered configurations, including zeros, repetitions,
        # dependent rows, weight-one ground edges and weight-three exceptions.
        cases = 0
        for row_count, max_n in ((0, 5), (1, 5), (2, 5), (3, 4)):
            for n in range(max_n + 1):
                for columns in product(range(1 << row_count), repeat=n):
                    with self.subTest(rows=row_count, columns=columns):
                        self.assert_exact_against_supports(rows_from_columns(columns, row_count), n)
                    cases += 1
        self.assertEqual(cases, 6115)

    def test_all_small_graph_affine_targets(self):
        # All 400 multigraph column configurations of <=3 edges in three rows.
        # Every target is checked, not only homogeneous/even-cardinality targets.
        row_count = 3
        allowed = [column for column in range(8) if column.bit_count() <= 2]
        cases = 0
        for n in range(4):
            for columns in product(allowed, repeat=n):
                edges = []
                for j, column in enumerate(columns):
                    endpoints = [i for i in range(row_count) if column >> i & 1]
                    u, v = ((3, 3) if not endpoints else
                            (endpoints[0], 3) if len(endpoints) == 1 else endpoints)
                    # Nonconsecutive IDs exercise original-coordinate recovery.
                    edges.append((u, v, 2 * j + 1))
                for target in range(8):
                    expected, words = brute_affine_graph(4, edges, target)
                    result = minimum_tjoin(4, edges, target)
                    if expected is None:
                        self.assertEqual(result["kind"], "INFEASIBLE")
                    else:
                        self.assertEqual(result["kind"], "TJOIN")
                        self.assertEqual(result["weight"], expected)
                        self.assertIn(result["word"], words)
                    cases += 1
        self.assertEqual(cases, 3200)

    def test_random_larger_columns_and_exception_assignments(self):
        rng = Random(181026)
        for row_count in (3, 4, 5):
            for _ in range(30):
                n = rng.randrange(5, 10)
                columns = [rng.randrange(1 << row_count) for _ in range(n)]
                self.assert_exact_against_supports(rows_from_columns(columns, row_count), n,
                                                   max_branches=1 << n)

    def test_all_invertible_three_row_transforms(self):
        transforms = []
        for rows in product(range(8), repeat=3):
            span = {0}
            for row in rows:
                span |= {value ^ row for value in tuple(span)}
            if len(span) == 8:
                transforms.append(rows)
        self.assertEqual(len(transforms), 168)
        for columns in ((1, 2, 3, 4, 5, 6, 7), (0, 1, 1, 2, 7), (7, 7), (1, 2, 4)):
            original = rows_from_columns(columns, 3)
            for transform in transforms:
                self.assert_exact_against_supports(original, len(columns), row_transform=transform)

    def test_budget_upper_bound_can_strictly_exceed_true_optimum(self):
        # Branch zero supplies a triangle of weight3; only assignment3 exposes
        # the parallel exceptional columns' weight2 codeword.
        rows = rows_from_columns((1, 2, 3, 7, 7), 3)
        for budget in range(4):
            result = solve_native(rows, 5, max_branches=budget)
            self.assertEqual(result["status"], "UNKNOWN")
            self.assertIsNone(result["distance"])
            self.assertEqual(len(result["branches"]), budget)
            self.assertEqual(result["upper_bound"], 3 if budget else None)
            self.assertTrue(verify_native_result(rows, 5, result)["valid"])
        self.assertEqual(self.assert_exact_against_supports(rows, 5)["distance"], 2)
        rows = rows_from_columns((7,), 3)
        result = solve_native(rows, 1, max_branches=1)
        self.assertEqual(result["status"], "UNKNOWN")
        self.assertIsNone(result["upper_bound"])
        rows = rows_from_columns((1, 2, 3, 7, 7), 3)
        for budget, upper in ((1, None), (2, 2), (3, 2)):
            result = solve_native(rows, 5, target=4, require_nonzero=False, max_branches=budget)
            self.assertEqual(result["status"], "UNKNOWN")
            self.assertIsNone(result["distance"])
            self.assertEqual(result["upper_bound"], upper)
            self.assertTrue(verify_native_result(rows, 5, result, target=4,
                                                require_nonzero=False)["valid"])

    def test_empty_zero_and_full_codes(self):
        for rows, n, expected in (((), 0, None), ((0, 0), 0, None),
                                  ((), 4, 1), ((0, 0, 0), 4, 1),
                                  ((1, 2, 4, 8), 4, None)):
            self.assertEqual(self.assert_exact_against_supports(rows, n)["distance"], expected)

    def test_later_loop_beats_earlier_parallel_pair(self):
        rows = rows_from_columns((1, 1, 0), 1)
        result = self.assert_exact_against_supports(rows, 3)
        self.assertEqual(result["distance"], 1)
        self.assertEqual(result["word"], 4)

    def test_disconnected_odd_terminal_obstruction(self):
        edges = [(0, 1, 0), (2, 3, 1)]
        # Nonground terminals0,2 give one terminal in each component.
        result = minimum_tjoin(4, edges, 5)
        self.assertEqual(result["kind"], "INFEASIBLE")
        expected, _ = brute_affine_graph(4, edges, 5)
        self.assertIsNone(expected)
        # Nonground terminal2 implies ground3, giving a feasible edge.
        self.assertEqual(minimum_tjoin(4, edges, 4)["word"], 2)

    def test_reject_tampered_result_certificates(self):
        rows = rows_from_columns(tuple(range(1, 8)), 3)
        result = solve_native(rows, 7)
        malformed = [None, [], {}, "result"]
        for field in ("schema", "n", "row_transform", "exceptional_coordinates", "dimension",
                      "branch_count", "branches"):
            changed = deepcopy(result)
            del changed[field]
            malformed.append(changed)
        for field, value in (("status", "UNKNOWN"), ("distance", 0), ("upper_bound", 2),
                             ("word", 1), ("dimension", 0), ("n", 8),
                             ("row_transform", [1, 1, 4]), ("branch_count", 1),
                             ("exceptional_coordinates", [0]), ("branches", result["branches"][:1]),
                             ("branches", result["branches"][::-1])):
            changed = deepcopy(result)
            changed[field] = value
            malformed.append(changed)
        for branch_id, field, value in ((0, "kind", "TJOIN"), (0, "word", 0),
                                        (0, "weight", 2), (1, "assignment", 0),
                                        (1, "kind", "CYCLE"), (1, "word", 0),
                                        (1, "weight", 0), (1, "matching_certificate", {})):
            changed = deepcopy(result)
            changed["branches"][branch_id][field] = value
            malformed.append(changed)
        for bad in malformed:
            with self.subTest(bad=bad):
                self.assertFalse(verify_native_result(rows, 7, bad)["valid"])
        rows = rows_from_columns((7,), 3)
        result = solve_native(rows, 1)
        self.assertEqual(result["branches"][1]["kind"], "INFEASIBLE")
        for component in ([], [0, 0], [True], [-1], [4], [0, 1]):
            changed = deepcopy(result)
            changed["branches"][1]["odd_component"] = component
            self.assertFalse(verify_native_result(rows, 1, changed)["valid"])

    def test_reject_boolean_numeric_claims(self):
        result = solve_native((), 1)
        for field in ("distance", "upper_bound", "word"):
            changed = deepcopy(result)
            changed[field] = True
            self.assertFalse(verify_native_result((), 1, changed)["valid"], field)
        changed = deepcopy(result)
        changed["branches"][0]["weight"] = True
        self.assertFalse(verify_native_result((), 1, changed)["valid"])
        rows = (3, 2, 2)  # Exceptional original coordinate1.
        changed = solve_native(rows, 2)
        changed["exceptional_coordinates"] = [True]
        self.assertFalse(verify_native_result(rows, 2, changed)["valid"])

    def test_invalid_inputs_and_transforms(self):
        for rows, n, kwargs in (((1,), 0, {}), ((-1,), 1, {}), ((True,), 1, {}),
                                ((), -1, {}), ((), True, {}), ((1,), 1, {"row_transform": [0]}),
                                ((1,), 1, {"row_transform": [True]}),
                                ((1,), 1, {"row_transform": [1, 2]}),
                                ((1,), 1, {"max_branches": -1}),
                                ((1,), 1, {"max_branches": True}),
                                ((1,), 1, {"target": -1}),
                                ((1,), 1, {"target": 2}),
                                ((1,), 1, {"target": True}),
                                ((1,), 1, {"require_nonzero": 1})):
            with self.assertRaises(ValueError):
                solve_native(rows, n, **kwargs)


if __name__ == "__main__":
    unittest.main()
