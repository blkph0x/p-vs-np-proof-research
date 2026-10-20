"""Bounded independent controls for the ten-point RM2 inequality.

No LP optimizer is imported. The row-space check rebuilds the old geometry
through its frozen independent reviewer, then derives the new mixed rows by
counting original scope atoms. The new inequality is checked pointwise.
"""
from collections import Counter
from fractions import Fraction
from itertools import combinations
import unittest

import review_rm2_nine_scope as old


SCOPE = (1, 2, 4, 8, 12, 16, 20, 24, 28, 32)
ANCHOR = (1, 2)
OTHERS = SCOPE[2:]


def rank(points):
    basis = {}
    for point in points:
        while point:
            pivot = point.bit_length() - 1
            if pivot in basis:
                point ^= basis[pivot]
            else:
                basis[pivot] = point
                break
    return len(basis)


def rank_moment(points, ambient=5):
    r = rank(points)
    top = ambient - r
    numerator = 0 if top < 2 else (2**top - 1) * (2**top - 2) // 6
    denominator = (2**ambient - 1) * (2**ambient - 2) // 6
    return Fraction(numerator, denominator)


def atom_by_direct_inclusion_exclusion(scope, selected, ambient=5):
    remaining = tuple(point for point in scope if point not in selected)
    total = Fraction()
    for mask in range(1 << len(remaining)):
        extension = tuple(point for i, point in enumerate(remaining) if mask >> i & 1)
        total += (-1)**mask.bit_count() * rank_moment(selected + extension, ambient)
    return total


def rebuilt_compact_rows():
    """Reconstruct the 40-column model from original per-atom incidences."""
    allowed, var_for, base_rows, base_rhs, _ = old._base()
    flat, outside = tuple(range(16, 24)), 24
    groups = {}
    for atom in allowed[flat]:
        groups.setdefault(var_for[(flat, atom)], []).append(atom)
    orbits = sorted(groups)
    if orbits != list(range(5, 11)):
        raise ValueError("changed base orbit order")
    rows, rhs = [dict(row) for row in base_rows], list(base_rhs)
    for index, orbit in enumerate(orbits):
        rows.append({28 + index: 1, 34 + index: 1, orbit: -1})
        rhs.append(0)
    for subset in ((), (16,), (16, 17), (16, 17, 18), (16, 17, 18, 19)):
        selected = sum(1 << flat.index(point) for point in subset)
        row = Counter()
        for index, orbit in enumerate(orbits):
            row[28 + index] = sum(atom & selected == selected for atom in groups[orbit])
        for column, count in old.base_moment((outside,) + subset)["coefficients"].items():
            row[column] -= count
        rows.append({column: count for column, count in row.items() if count})
        rhs.append(0)
    return rows, rhs


def is_row_consequence(rows, rhs, target, target_rhs, columns):
    """Exact row-span test, including the constant column."""
    basis = {}
    for row, value in zip(rows, rhs):
        vector = [Fraction(row.get(i, 0)) for i in range(columns)] + [Fraction(value)]
        for pivot, reducer in sorted(basis.items()):
            coefficient = vector[pivot]
            if coefficient:
                vector = [a - coefficient * b for a, b in zip(vector, reducer)]
        pivot = next((i for i, value in enumerate(vector) if value), None)
        if pivot is not None:
            coefficient = vector[pivot]
            basis[pivot] = [value / coefficient for value in vector]
    vector = [Fraction(target.get(i, 0)) for i in range(columns)] + [Fraction(target_rhs)]
    for pivot, reducer in sorted(basis.items()):
        coefficient = vector[pivot]
        if coefficient:
            vector = [a - coefficient * b for a, b in zip(vector, reducer)]
    return not any(vector)


class LevelTenControlTests(unittest.TestCase):
    def test_scope_rank_and_all_distinct_quotient_directions(self):
        self.assertEqual(rank(SCOPE), 6)
        self.assertEqual({a for a in SCOPE if rank(ANCHOR + (a,)) == 2}, set(ANCHOR))
        self.assertEqual(len({min(a ^ b for b in (0, 1, 2, 3)) for a in OTHERS}), 8)
        self.assertTrue(all(rank(ANCHOR + (a,)) == 3 for a in OTHERS))
        self.assertTrue(all(rank(ANCHOR + pair) == 4 for pair in combinations(OTHERS, 2)))

    def test_bonferroni_on_all_original_assignments(self):
        for word in range(1024):
            bits = [(word >> i) & 1 for i in range(10)]
            event, t = bits[0] * bits[1], sum(bits[2:])
            expanded = event - sum(event * x for x in bits[2:])
            expanded += sum(event * x * y for x, y in combinations(bits[2:], 2))
            self.assertEqual(expanded, event * (t - 1) * (t - 2) // 2)
            self.assertGreaterEqual(expanded, 0)

    def test_missing_pair_and_wrong_linear_coefficient_fail(self):
        # Every one of the 28 terms is needed in this particular pointwise
        # degree-four expansion: set just its two outside bits to one.
        for pair in combinations(range(2, 10), 2):
            bits = [int(i in (0, 1) + pair) for i in range(10)]
            value = 1 - sum(bits[2:])
            value += sum(bits[i] * bits[j] for i, j in combinations(range(2, 10), 2)
                         if (i, j) != pair)
            self.assertEqual(value, -1)
        # A purported q-9r+28v symmetrized row has negative pointwise value
        # when interpreted with equal weights on the eight triple terms.
        self.assertEqual(1 - Fraction(9, 8), Fraction(-1, 8))

    def test_old_witness_atom_and_moment_row_are_both_negative(self):
        atom = atom_by_direct_inclusion_exclusion(SCOPE, ANCHOR)
        q, r, v = (rank_moment(ANCHOR), rank_moment(ANCHOR + (4,)),
                   rank_moment(ANCHOR + (4, 8)))
        self.assertEqual(atom, Fraction(-1, 155))
        self.assertEqual(q - 8 * r + 28 * v, atom)
        # The same atom on each nine-point deletion is nonnegative.
        for deleted in OTHERS:
            self.assertEqual(atom_by_direct_inclusion_exclusion(
                tuple(x for x in SCOPE if x != deleted), ANCHOR), 0)

    def test_equality_face_forces_the_obstruction(self):
        # Variables p,q,r,c,b2. These equalities are direct specializations
        # of independently counted incidence identities after all strictly
        # positive terms in the old lower certificate vanish.
        rows = [
            {0: 1}, {1: 1, 4: -7}, {2: 1, 4: -1},
            {3: -Fraction(1, 4), 1: Fraction(1, 8), 0: -Fraction(1, 56)},
            {2: Fraction(3, 2), 3: -Fraction(1, 4),
             1: -Fraction(5, 8), 0: Fraction(5, 56)},
        ]
        rhs = [Fraction(7, 31), 0, 0, 0, 0]
        for column, value in enumerate((Fraction(7, 31), Fraction(7, 155),
                                        Fraction(1, 155), Fraction(1, 155),
                                        Fraction(1, 155))):
            self.assertTrue(is_row_consequence(rows, rhs, {column: 1}, value, 5))
        self.assertTrue(is_row_consequence(rows, rhs, {1: 1, 2: -8},
                                          Fraction(-1, 155), 5))

    def test_new_identity_from_rebuilt_original_geometry(self):
        rows, rhs = rebuilt_compact_rows()
        # Extra nonnegative column 40 is C=q-8r+28v.
        cut = Counter({40: -1})
        for points, coefficient in (((1, 2), 1), ((1, 2, 4), -8), ((1, 2, 4, 8), 28)):
            for column, count in old.base_moment(points)["coefficients"].items():
                cut[column] += coefficient * count
        rows.append(dict(cut))
        rhs.append(0)
        target = {27: 25641, 2: -61824, 30: -164332, 31: -745164,
                  32: -281512, 37: -87836, 39: -30212, 40: -945}
        self.assertTrue(is_row_consequence(rows, rhs, target, 5796, 41))
        self.assertFalse(is_row_consequence(rows, rhs, target, 5797, 41))
        corrupted = dict(target)
        corrupted[40] += 1
        self.assertFalse(is_row_consequence(rows, rhs, corrupted, 5796, 41))
        self.assertEqual(Fraction(5796, 25641), Fraction(644, 2849))
        self.assertEqual(Fraction(644, 2849) - Fraction(7, 31), Fraction(21, 88319))

    def test_genuine_six_dimensional_subspace_control(self):
        # Independent enumeration: kernels of all pairs of independent
        # linear functionals, deduplicated as actual 16-point sets.
        kernels = set()
        for a, b in combinations(range(1, 64), 2):
            kernels.add(frozenset(x for x in range(64)
                                 if (a & x).bit_count() % 2 == 0
                                 and (b & x).bit_count() % 2 == 0))
        self.assertEqual(len(kernels), 651)
        self.assertTrue(all(0 in kernel and len(kernel) == 16 for kernel in kernels))
        moments = [Fraction(sum(set(points) <= kernel for kernel in kernels), 651)
                   for points in ((1,), (1, 2), (1, 2, 4), (1, 2, 4, 8))]
        self.assertEqual(moments, [Fraction(155, 651), Fraction(35, 651),
                                   Fraction(7, 651), Fraction(1, 651)])
        self.assertEqual(moments[1] - 8 * moments[2] + 28 * moments[3], Fraction(7, 651))
        actual_atom = Fraction(sum(kernel.intersection(SCOPE) == set(ANCHOR)
                                   for kernel in kernels), 651)
        self.assertEqual(actual_atom, atom_by_direct_inclusion_exclusion(SCOPE, ANCHOR, 6))
        self.assertGreaterEqual(actual_atom, 0)


if __name__ == "__main__":
    unittest.main()
