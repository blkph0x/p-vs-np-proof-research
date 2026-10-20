"""Tests using direct finite distributions, GF(2) evaluation, and mutations."""

from __future__ import annotations

import unittest
from collections import Counter
from itertools import combinations

import review_rm2_level8_family as review


def direct_planes_m4():
    """All 35 two-dimensional linear subspaces, without a code generator."""
    return sorted({tuple(sorted((a, b, a ^ b)))
                   for a, b in combinations(range(1, 16), 2)})


def marginal(masses, indices):
    result = [0] * (1 << len(indices))
    for atom, mass in enumerate(masses):
        restriction = sum(((atom >> index) & 1) << place
                          for place, index in enumerate(indices))
        result[restriction] += mass
    return result


class LevelEightFamilyTests(unittest.TestCase):
    def test_global_m4_plane_distribution_on_every_eight_point_scope(self):
        """A genuine global pinned RM(2,4) distribution, all 6,435 scopes."""
        planes = [set(plane) for plane in direct_planes_m4()]
        self.assertEqual(len(planes), 35)
        for points in combinations(range(1, 16), 8):
            actual = [0] * 256
            for plane in planes:
                atom = sum((point in plane) << index for index, point in enumerate(points))
                actual[atom] += 1
            self.assertEqual(review.scope_masses(points), actual)

    def test_complete_moments_and_all_marginals(self):
        for points in (tuple(range(1, 8)) + (16,), (1, 2, 4, 8, 16, 32, 64, 128)):
            full = review.scope_masses(points)
            review.check_scope(points, full)
            for mask in range(256):
                selected = [index for index in range(8) if mask >> index & 1]
                expected = review.scope_masses([points[index] for index in selected])
                self.assertEqual(marginal(full, selected), expected)
                review.check_scope([points[index] for index in selected], expected)

    def test_rref_enumeration_small_counts_and_unique_rowspaces(self):
        for k, total in enumerate((1, 2, 5, 16, 67, 374)):
            configurations = list(review.rref_configurations(k))
            self.assertEqual(len(configurations), total)
            spaces = set()
            for rank, points in configurations:
                rows = [sum(((point >> bit) & 1) << column
                            for column, point in enumerate(points)) for bit in range(rank)]
                span = {0}
                for row in rows:
                    span |= {word ^ row for word in tuple(span)}
                spaces.add(tuple(sorted(span)))
                if 0 not in points and len(set(points)) == k:
                    review.check_scope(points, review.scope_masses(points))
            self.assertEqual(len(spaces), total)

    def test_pin_parity_mutation_rejected_before_moments(self):
        points = tuple(range(1, 8))
        masses = review.scope_masses(points)
        masses[1] -= 1
        masses[0] += 1
        self.assertEqual(sum(masses), 35)
        with self.assertRaisesRegex(ValueError, "pinned quadratic projection"):
            review.check_scope(points, masses)

    def test_independent_triple_mutation_has_valid_support_but_wrong_moment(self):
        points = (1, 2, 4)
        masses = review.scope_masses(points)
        masses[0] -= 1
        masses[7] += 1
        basis = review.projection_basis(points)
        self.assertTrue(all(review.in_span(1 | (atom << 1), basis) for atom in range(8)))
        with self.assertRaisesRegex(ValueError, "common-moment"):
            review.check_scope(points, masses)

    def test_dependent_triple_cannot_be_dropped(self):
        points = (1, 2, 3)
        masses = review.scope_masses(points)
        self.assertEqual(masses[7], 1)
        masses[7] = 0
        masses[0] += 1
        with self.assertRaisesRegex(ValueError, "common-moment"):
            review.check_scope(points, masses)

    def test_unpinned_affine_flat_has_only_even_atoms(self):
        points = tuple(range(8, 16))
        masses = review.scope_masses(points)
        self.assertEqual(len(review.line_triples(points)), 0)
        self.assertEqual(Counter(atom.bit_count() for atom, mass in enumerate(masses) if mass),
                         {0: 1, 2: 28})
        review.check_scope(points, masses)
        masses[0] -= 1
        masses[1] += 1
        with self.assertRaisesRegex(ValueError, "pinned quadratic projection"):
            review.check_scope(points, masses)

    def test_ambient_embedding_and_coordinate_permutation(self):
        points = (1, 2, 3, 4, 7, 8, 16, 32)
        image = lambda point: sum(((point >> bit) & 1) << (17 * bit + 5)
                                  for bit in range(6))
        embedded = tuple(image(point) for point in points)
        expected = review.scope_masses(points)
        self.assertEqual(review.scope_masses(embedded), expected)
        review.check_scope(embedded, expected)
        reversed_table = review.scope_masses(points[::-1])
        self.assertEqual(marginal(expected, list(reversed(range(8)))), reversed_table)

    def test_empty_scope_strict_types_and_shapes(self):
        self.assertEqual(review.scope_masses([]), [35])
        review.check_scope([], [35])
        for points in ([0], [1, 1], [True], [-1], [1.0], list(range(1, 10))):
            with self.assertRaises(ValueError):
                review.scope_masses(points)
        for masses in ([True, 34], [28, 6], [28, -1], [28, 7, 0]):
            with self.assertRaises(ValueError):
                review.check_scope([1], masses)
        for width in (True, -1, 9, 2.0):
            with self.assertRaises(ValueError):
                list(review.rref_configurations(width))

    def test_level_nine_is_only_a_witness_obstruction(self):
        control = review.level_nine_control()
        self.assertEqual(control["witness_left_side"], "-1/35")
        self.assertEqual(control["integer_polynomial_values_t_0_through_9"],
                         [0, 1, 0, 0, 4, 15, 36, 70, 120, 189])
        with self.assertRaises(ValueError):
            review.scope_masses(control["nonpin_points"])

    def test_eight_point_bound_extremal_and_low_line_controls(self):
        self.assertEqual(len(review.line_triples(tuple(range(1, 8)) + (16,))), 7)
        self.assertEqual(len(review.line_triples(tuple(1 << bit for bit in range(8)))), 0)
        for rank, points in review.rref_configurations(6):
            if rank and 0 not in points and len(set(points)) == 6:
                self.assertLessEqual(3 * len(review.line_triples(points)), 15)
                review.check_scope(points, review.scope_masses(points))

    def test_provenance_normalizes_line_endings_but_not_content(self):
        self.assertEqual(review.normalized_sha256(b"first\nsecond\n"),
                         review.normalized_sha256(b"first\r\nsecond\r\n"))
        self.assertNotEqual(review.normalized_sha256(b"first\nsecond\n"),
                            review.normalized_sha256(b"first\nchanged\n"))
        with self.assertRaises(ValueError):
            review.normalized_sha256("text is not bytes")


if __name__ == "__main__":
    unittest.main()
