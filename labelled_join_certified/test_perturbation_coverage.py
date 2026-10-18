"""Finite arithmetic controls for dense-U representation coverage."""
import itertools
import unittest

import perturbation_coverage as c


def rref(rows, n):
    rows = list(rows)
    pivot = 0
    for bit in range(n - 1, -1, -1):
        hit = next((j for j in range(pivot, len(rows)) if rows[j] >> bit & 1), None)
        if hit is None:
            continue
        rows[pivot], rows[hit] = rows[hit], rows[pivot]
        for j in range(len(rows)):
            if j != pivot and rows[j] >> bit & 1:
                rows[j] ^= rows[pivot]
        pivot += 1
        if pivot == len(rows):
            break
    return tuple(sorted(row for row in rows if row))


class PerturbationCoverageTests(unittest.TestCase):
    def test_graph_column_counts(self):
        self.assertEqual([c.graph_column_choices(r) for r in range(5)], [1, 2, 4, 7, 11])

    def test_small_description_enumeration_is_below_bound(self):
        n, r, p = 3, 2, 1
        graph = range(1 << r)
        graph = [mask for mask in graph if mask.bit_count() <= 2]
        matrices = set()
        for columns in itertools.product(graph, repeat=n):
            for u in range(1 << r):
                for labels in itertools.product(range(1 << p), repeat=n):
                    rows = []
                    for i in range(r):
                        row = sum(1 << j for j, col in enumerate(columns) if col >> i & 1)
                        if u >> i & 1:
                            row ^= sum(1 << j for j, label in enumerate(labels) if label & 1)
                        rows.append(row)
                    matrices.add(rref(rows, n))
        self.assertLessEqual(len(matrices), c.representation_upper_bound(n, r, p))

    def test_systematic_spaces_are_distinct(self):
        n, r = 4, 2
        spaces = set()
        for suffix in range(1 << (r * (n - r))):
            rows = []
            for i in range(r):
                row = 1 << (n - 1 - i)
                for j in range(n - r):
                    if suffix >> (i * (n - r) + j) & 1:
                        row |= 1 << j
                rows.append(row)
            spaces.add(rref(rows, n))
        self.assertEqual(len(spaces), c.systematic_rowspace_lower_bound(n, r))

    def test_logarithmic_label_bound_eventually_excludes_coverage(self):
        self.assertTrue(c.excludes_universal_coverage(128, 64, 7))
        self.assertTrue(c.excludes_universal_coverage(256, 128, 16))
        self.assertTrue(c.excludes_universal_coverage(512, 256, 27))
        self.assertFalse(c.excludes_universal_coverage(16, 8, 12))
        self.assertTrue(c.excludes_universal_coverage_any_row_count(128, 7))
        self.assertTrue(c.excludes_universal_coverage_any_row_count(256, 16))
        self.assertTrue(c.excludes_universal_coverage_any_row_count(512, 27))

    def test_exact_all_row_thresholds(self):
        self.assertEqual(c.largest_excluded_label_budget(128), 9)
        self.assertEqual(c.largest_excluded_label_budget(256), 24)
        self.assertEqual(c.largest_excluded_label_budget(512), 55)

    def test_invalid_dimensions(self):
        for call in (lambda: c.graph_column_choices(-1),
                     lambda: c.representation_upper_bound(2, 3, 1),
                     lambda: c.systematic_rowspace_lower_bound(2, 3)):
            with self.assertRaises(ValueError):
                call()
        with self.assertRaises(ValueError):
            c.excludes_universal_coverage_any_row_count(2, 1, 3)


if __name__ == '__main__':
    unittest.main()
