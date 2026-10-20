"""Independent finite controls for the written all-order theorem."""
from fractions import Fraction
from itertools import combinations
from random import Random
import unittest

import witness


def rank(vectors):
    basis = {}
    for value in vectors:
        while value:
            pivot = value.bit_length() - 1
            if pivot in basis:
                value ^= basis[pivot]
            else:
                basis[pivot] = value
                break
    return len(basis)


def gaussian(n, r):
    if n < r or n < 0:
        return 0
    value = Fraction(1)
    for j in range(r):
        value *= Fraction((1 << (n - j)) - 1, (1 << (r - j)) - 1)
    if value.denominator != 1:
        raise ValueError("nonintegral Gaussian coefficient")
    return value.numerator


def mobius_table(points, order):
    k = len(points)
    denominator = gaussian(order + 2, order)
    values = [Fraction(gaussian(order + 2 - rank(points[i] for i in range(k)
                                               if mask >> i & 1), order), denominator)
              for mask in range(1 << k)]
    for bit in range(k):
        for mask in range(1 << k):
            if not mask >> bit & 1:
                values[mask] -= values[mask | (1 << bit)]
    return {tuple(points[i] for i in range(k) if mask >> i & 1): value
            for mask, value in enumerate(values) if value}


def projection_basis(points, order, ambient):
    # Constant coefficient is fixed to one; all other coefficients are free.
    basis = {}
    for degree in range(1, order + 1):
        for axes in combinations(range(ambient), degree):
            mask = sum(1 << axis for axis in axes)
            vector = sum((int(point & mask == mask) << i) for i, point in enumerate(points))
            while vector:
                pivot = vector.bit_length() - 1
                if pivot in basis:
                    vector ^= basis[pivot]
                else:
                    basis[pivot] = vector
                    break
    return basis


def supported(atom, points, basis):
    vector = sum((int(point not in atom) << i) for i, point in enumerate(points))
    while vector:
        pivot = vector.bit_length() - 1
        if pivot not in basis:
            return False
        vector ^= basis[pivot]
    return True


def independent_check(points, order, table):
    if any(mass < 0 for mass in table.values()):
        raise ValueError("negative mass")
    if sum(table.values()) != 1:
        raise ValueError("normalization")
    denominator = gaussian(order + 2, order)
    for size in range(len(points) + 1):
        for required in combinations(points, size):
            expected = Fraction(gaussian(order + 2 - rank(required), order), denominator)
            actual = sum(mass for atom, mass in table.items() if set(required) <= set(atom))
            if actual != expected:
                raise ValueError("moment mismatch")
    return True


class BoundaryTests(unittest.TestCase):
    def test_parameters_and_objective(self):
        for order in range(1, 13):
            d, denominator = witness.parameters(order)
            self.assertEqual(denominator, gaussian(order + 2, order))
            for ambient in range(order + 2, order + 7):
                reduced, total, integer = witness.objective(order, ambient)
                self.assertEqual(reduced, ((1 << ambient) - 1) *
                                 Fraction(gaussian(order + 1, order), denominator))
                self.assertEqual(integer - total,
                                 Fraction((d - 2) * ((1 << ambient) - 2 * d), d * (2 * d - 1)))
                self.assertGreaterEqual(integer, total)

    def test_all_power_two_line_controls_in_dimension_four(self):
        checked = 0
        for size in (4, 8):
            bound = (size - 1) * (size - 2) // 6
            maximum = 0
            for points in combinations(range(1, 16), size):
                actual = sum(a ^ b ^ c == 0 for a, b, c in combinations(points, 3))
                self.assertLessEqual(actual, bound)
                maximum = max(maximum, actual)
                checked += 1
            self.assertEqual(maximum, bound)
        self.assertEqual(checked, 7800)

    def test_mobius_and_all_delete_one_marginals(self):
        rng = Random(20261020)
        cases = [(1, tuple(s)) for s in combinations(range(1, 8), 4)]
        cases += [(2, tuple(sorted(rng.sample(range(1, 64), 8)))) for _ in range(40)]
        cases += [(3, tuple(sorted(rng.sample(range(1, 128), 12)))) for _ in range(12)]
        for order, points in cases:
            table = witness.checked_table(points, order)
            self.assertEqual(table, mobius_table(points, order))
            for deleted in points:
                marginalized = {}
                for atom, mass in table.items():
                    key = tuple(x for x in atom if x != deleted)
                    marginalized[key] = marginalized.get(key, Fraction()) + mass
                self.assertEqual(marginalized,
                                 witness.checked_table(tuple(x for x in points if x != deleted), order))

    def test_full_boundary_and_pinned_projection_support(self):
        rng = Random(31102026)
        for order, ambient, count in ((1, 4, 40), (2, 6, 80), (3, 7, 80), (4, 8, 40)):
            d = 1 << (order + 1)
            scopes = [tuple(range(1, d + 1)), tuple(range(d, 2 * d))]
            scopes += [tuple(sorted(rng.sample(range(1, 1 << ambient), d))) for _ in range(count)]
            for points in scopes:
                table = witness.checked_table(points, order)
                basis = projection_basis(points, order, ambient)
                self.assertEqual(sum(table.values()), 1)
                for atom, mass in table.items():
                    self.assertGreater(mass, 0)
                    self.assertTrue(supported(atom, points, basis))

    def test_genuine_subspaces_in_dimension_four(self):
        points = tuple(range(1, 9))
        spaces = {tuple(sorted((a, b, a ^ b))) for a, b in combinations(range(1, 16), 2)}
        counts = {}
        for space in spaces:
            atom = tuple(x for x in points if x in space)
            counts[atom] = counts.get(atom, 0) + 1
        self.assertEqual(len(spaces), 35)
        self.assertEqual(witness.checked_table(points, 2),
                         {atom: Fraction(count, 35) for atom, count in counts.items()})

    def test_first_failure_is_negative_and_deletions_pass(self):
        for order in range(1, 7):
            points = witness.first_failure_scope(order)
            atoms, denominator = witness.raw_numerators(points, order)
            self.assertEqual(atoms[(1,)], -1)
            self.assertEqual(sum(atoms.values()), denominator)
            with self.assertRaisesRegex(ValueError, "exceeds"):
                witness.checked_table(points, order)
            for deleted in points:
                table = witness.checked_table(tuple(x for x in points if x != deleted), order)
                self.assertEqual(sum(table.values()), 1)

    def test_invalid_input_and_mutated_mass(self):
        for order in (0, -1, True, 2.5):
            with self.assertRaises(ValueError):
                witness.parameters(order)
        for points in ((0,), (1, 1), (-1,), (True,)):
            with self.assertRaises(ValueError):
                witness.checked_table(points, 2)
        points = (1, 2, 3, 4, 8, 16, 32, 33)
        original = witness.checked_table(points, 2)
        self.assertTrue(independent_check(points, 2, original))
        corrupted = dict(original)
        key = next(iter(corrupted))
        corrupted[key] += Fraction(1, 35)
        with self.assertRaisesRegex(ValueError, "normalization"):
            independent_check(points, 2, corrupted)
        second = dict(original)
        keys = list(second)
        second[keys[0]] += Fraction(1, 1000)
        second[keys[1]] -= Fraction(1, 1000)
        with self.assertRaisesRegex(ValueError, "moment mismatch"):
            independent_check(points, 2, second)


if __name__ == "__main__":
    unittest.main()
