"""Exact arithmetic controls for the written all-D proof, not its replacement."""
from fractions import Fraction
from itertools import combinations
from math import comb
import unittest

import rm2_virtual_dimension as subject


def gaussian(n, k):
    if n < k or k < 0:
        return 0
    numerator = denominator = 1
    for j in range(k):
        numerator *= 2**(n-j) - 1
        denominator *= 2**(k-j) - 1
    return numerator // denominator


def expanded_coefficient(d, e, w):
    """Direct subspace-lattice inversion, without the simplified formulas."""
    result = 0
    for size in range(w, d+5):
        h = sum((-1)**(e-j) * 2**comb(e-j, 2) * gaussian(e, j)
                * gaussian(d-size+j, 2) for j in range(e+1))
        result += (-1)**size * comb(d+4-w, size-w) * h
    return result


class VirtualDimensionTests(unittest.TestCase):
    def test_binomial_expansion_and_closed_coefficients(self):
        for d in range(3, 31):
            self.assertEqual(subject.independent_empty_numerator(d),
                             expanded_coefficient(d, 0, 0))
            for e, minimum in ((1, 3), (2, 5), (3, 6)):
                for w in range(minimum, d+5):
                    self.assertEqual(subject.relation_coefficient(d, e, w),
                                     expanded_coefficient(d, e, w), (d, e, w))

    def test_base_empty_formulas(self):
        expected = {
            4: {1: {3: -1}, 2: {}, 3: {}},
            5: {1: {4: 1}, 2: {5: -1}, 3: {6: 1}},
            6: {1: {3: -7, 5: -1}, 2: {5: 1, 6: 1}, 3: {6: -4, 7: -1}},
            7: {1: {3: -8, 4: 7, 6: 1}, 2: {5: -7, 6: -1, 7: -1},
                3: {6: 10, 7: 4, 8: 1}},
        }
        for d in expected:
            for e, minimum in ((1, 3), (2, 5), (3, 6)):
                actual = {w: expanded_coefficient(d, e, w)
                          for w in range(minimum, d+5)
                          if expanded_coefficient(d, e, w)}
                self.assertEqual(actual, expected[d][e])
        self.assertEqual(subject.independent_empty_numerator(6), 46)
        self.assertEqual(subject.independent_empty_numerator(7), 104)

    def test_dimension_three_base_distribution(self):
        for size in range(8):
            # Arbitrary-rank independent coordinates expose the virtual case;
            # lower-rank controls use all seven points of a genuine 3-space.
            for points in (tuple(1 << i for i in range(size)), tuple(range(1, size+1))):
                denominator, table = subject.checked_scope_table(points, 3)
                self.assertEqual(denominator, 7)
                expected = [0]*(1 << size)
                expected[0] = 7-size
                for i in range(size):
                    expected[1 << i] = 1
                self.assertEqual(table, expected)

    def test_lower_bound_recurrences_and_coefficient_minima(self):
        self.assertEqual(subject.empty_lower_bound(8), 13)
        self.assertEqual(subject.empty_lower_bound(9), 22)
        for d in range(8, 81):
            bound = subject.empty_lower_bound(d)
            self.assertGreater(bound, 0)
            increment = (Fraction((d-4)*(d+7), 2) if d % 2 == 0
                         else Fraction((d-6)*(d-1)*(8*d-25), 6))
            self.assertEqual(subject.empty_lower_bound(d+2) - 9*bound, increment)
            lower = {
                1: -subject.independent_empty_numerator(d-2),
                2: -(subject.independent_empty_numerator(d-3)
                     - subject.independent_empty_numerator(d-4)),
                3: -comb(d-2, 3) if d % 2 == 0 else 0,
            }
            for e, minimum in ((1, 3), (2, 5), (3, 6)):
                for w in range(minimum, d+5):
                    self.assertGreaterEqual(subject.relation_coefficient(d, e, w), lower[e])

    def test_induction_polynomials_as_coefficient_identities(self):
        # Polynomial degree<=3, so equality at four distinct rational
        # arguments certifies the polynomial identities (not just samples).
        p = lambda j: 8*j*j + 36*j + 37
        q = lambda j: 8*j*j + 28*j + 23
        for j in map(Fraction, (0, 1, 2, 3)):
            self.assertEqual(9*p(j)-p(j+2), 64*(j+1)*(j+3))
            self.assertEqual(9*q(j)-q(j+2), 32*(2*j*j+6*j+3))
        self.assertEqual(27*3, p(1))
        self.assertGreater(9*3**3, q(3))

    def test_conditional_moment_identity(self):
        for d in range(5, 35):
            for rank in range(d+2):
                self.assertEqual(
                    Fraction(gaussian(d-1-rank, 2), gaussian(d-1, 2)),
                    Fraction(gaussian(d-1-rank, 2), gaussian(d, 2))
                    / Fraction(gaussian(d-1, 2), gaussian(d, 2)))
            self.assertEqual(Fraction(gaussian(d-1, 2), gaussian(d, 2)),
                             Fraction(2**(d-2)-1, 2**d-1))

    def test_actual_six_dimensional_subspace_distribution(self):
        points = (1, 2, 4, 8, 12, 16, 20, 24, 28, 32)
        kernels = set()
        for a, b in combinations(range(1, 64), 2):
            kernels.add(tuple(x for x in range(64)
                              if not ((a & x).bit_count() % 2)
                              and not ((b & x).bit_count() % 2)))
        actual = [0]*1024
        for kernel in kernels:
            actual[sum(1 << i for i, x in enumerate(points) if x in kernel)] += 1
        denominator, table = subject.checked_scope_table(points, 6)
        self.assertEqual(denominator, 651)
        self.assertEqual(table, actual)

    def test_first_failure_and_manual_mutation(self):
        for d in range(3, 9):
            points, mask = subject.first_failure_scope(d)
            self.assertEqual(len(points), d+5)
            self.assertEqual(subject.binary_rank(points), d+1)
            table = subject.raw_atom_numerators(points, d)
            self.assertEqual(table[mask], -1)
            with self.assertRaisesRegex(ValueError, "exceeds"):
                subject.checked_scope_table(points, d)
            for removed in range(d-3, len(points)):
                smaller = points[:removed] + points[removed+1:]
                _, small_table = subject.checked_scope_table(smaller, d)
                self.assertEqual(small_table[mask], 0)
        # A single added singleton numerator changes normalization/objective;
        # this is checked against a genuine distribution above, not a hash.
        points = (1, 2, 4)
        denominator, table = subject.checked_scope_table(points, 6)
        table[1] += 1
        self.assertNotEqual(sum(table), denominator)

    def test_input_and_locality_guards(self):
        for points in ((0,), (1, 1), (-1,), (True,)):
            with self.assertRaises(ValueError):
                subject.checked_scope_table(points, 6)
        for dimension in (0, 2, 6.0, "6", True):
            with self.assertRaises(ValueError):
                subject.checked_scope_table((1,), dimension)


if __name__ == "__main__":
    unittest.main()
