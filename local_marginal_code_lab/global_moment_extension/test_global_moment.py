import random
import unittest
from fractions import Fraction

import moments


def span_oracle(columns):
    """Independent set closure, not Gaussian elimination."""
    values = {0}
    for column in columns:
        values |= {value ^ column for value in values}
    return values


def original_moment(D, points):
    dimension = len(span_oracle(points)).bit_length() - 1
    t = D - dimension
    if t < 2:
        return Fraction(0)
    return Fraction(((1 << t) - 1) * ((1 << t) - 2),
                    ((1 << D) - 1) * ((1 << D) - 2))


def polynomial_square_expectation(D, m, terms, beta):
    """Expand a Boolean polynomial square and use original rank moments."""
    result = Fraction(0)
    for left, a in terms.items():
        for right, b in terms.items():
            old = original_moment(D, left | right)
            result += a * b * ((1 - beta) * old + beta)
    return result


def exact_psd(matrix):
    """Independent rational elimination, with the zero-pivot PSD condition."""
    work = [row[:] for row in matrix]
    for index in range(len(work)):
        pivot = work[index][index]
        if pivot < 0:
            return False
        if not pivot:
            if any(work[index][j] for j in range(index + 1, len(work))):
                return False
            continue
        for i in range(index + 1, len(work)):
            for j in range(i, len(work)):
                work[i][j] -= work[i][index] * work[index][j] / pivot
                work[j][i] = work[i][j]
    return True


def projected_code_words(m, scope):
    """Enumerate the row span of actual constant/linear/quadratic evaluations."""
    points = (0,) + tuple(scope)
    rows = [(1 << len(points)) - 1]
    rows += [sum(((point >> i) & 1) << j for j, point in enumerate(points))
             for i in range(m)]
    rows += [sum((((point >> i) & 1) * ((point >> h) & 1)) << j
                 for j, point in enumerate(points))
             for i in range(m) for h in range(i)]
    words = span_oracle(rows)
    return {word >> 1 for word in words if word & 1}


def local_review(D, m, scope):
    old = moments.scope_table(D, m, scope, repaired=False)
    new = moments.scope_table(D, m, scope)
    data = moments.parameters(D, m)
    if min(old) < 0 or min(new) < 0 or sum(new) != 1:
        raise AssertionError("local distribution")
    support = projected_code_words(m, scope)
    if any(value and atom not in support for atom, value in enumerate(new)):
        raise AssertionError("actual pinned-code projection")
    for mask in range(1 << len(scope)):
        points = {scope[i] for i in range(len(scope)) if mask >> i & 1}
        expected = (1 - data["beta"]) * original_moment(D, points) + data["beta"]
        actual = sum(value for atom, value in enumerate(new) if atom & mask == mask)
        if actual != expected:
            raise AssertionError("direct superset moment")
    return {"atoms": len(new), "moments": 1 << len(scope),
            "support_size": len(support)}


class GlobalMomentTests(unittest.TestCase):
    def test_existing_finite_square_is_reproduced(self):
        data = moments.parameters(4, 5)
        self.assertEqual(data["old_variance"], Fraction(-992, 175))
        self.assertEqual(data["beta"], Fraction(2, 217))
        self.assertEqual(data["reduced_objective"], Fraction(45, 7))
        self.assertEqual(data["total_objective"], Fraction(52, 7))
        self.assertEqual(data["additive_gap"], Fraction(4, 7))

    def test_formulas_and_threshold_over_dimensions(self):
        for D in range(3, 33):
            for m in (D, D + 1, D + 5, D + 17):
                data = moments.parameters(D, m)
                N, Q, p, q = (data[key] for key in ("N", "Q", "p", "q"))
                self.assertEqual(q, data["a"] * (data["a"] - 1) / Fraction(Q * (Q - 1)))
                self.assertEqual(data["old_variance"],
                                 N * p * (1 - p) * (Q - N) / (Q - 1))
                self.assertEqual(data["mixed_variance"], 0)
                self.assertEqual(data["reduced_objective"], Fraction(data["a"] * (N - 1), Q - 1))
                self.assertEqual(data["additive_gap"], Fraction(N - Q, 2 * (Q - 1)))
                self.assertGreater(data["contrast"], 0)
                if m > D:
                    self.assertTrue(0 < data["beta"] < 1)
                    self.assertLess(data["old_variance"], 0)
                    self.assertGreater(data["additive_gap"], 0)
                    for beta, expected_sign in ((data["beta"] / 2, -1),
                                                ((1 + data["beta"]) / 2, 1)):
                        mp, mq = (1 - beta) * p + beta, (1 - beta) * q + beta
                        variance = N * mp + N * (N - 1) * mq - (N * mp) ** 2
                        self.assertGreater(expected_sign * variance, 0)
                else:
                    self.assertEqual(data["beta"], 0)
                    self.assertEqual(data["additive_gap"], 0)

    def test_dense_matrix_psd_and_explicit_gram_identity(self):
        for D, m in ((3, 3), (3, 4), (4, 5), (5, 6)):
            matrix = moments.dense_moment_matrix(D, m)
            data = moments.parameters(D, m)
            N, p, alpha = data["N"], data["mixed_p"], data["contrast"]
            self.assertTrue(exact_psd(matrix))
            self.assertEqual(exact_psd(moments.dense_moment_matrix(D, m, repaired=False)), m == D)
            for i, row in enumerate(matrix):
                for j, value in enumerate(row):
                    outer = (p if i else 1) * (p if j else 1)
                    correction = alpha * (Fraction(i == j) - Fraction(1, N)) if i and j else 0
                    self.assertEqual(value, outer + correction)
            # This is the actual zero eigenvector, not merely a test direction.
            vector = [-data["reduced_objective"]] + [Fraction(1)] * N
            self.assertEqual([sum(a * b for a, b in zip(row, vector)) for row in matrix],
                             [0] * (N + 1))

    def test_moment_mutations_break_psd(self):
        data = moments.parameters(4, 5)
        for beta in (Fraction(0), data["beta"] / 2):
            p = (1 - beta) * data["p"] + beta
            q = (1 - beta) * data["q"] + beta
            N = data["N"]
            matrix = [[Fraction(1)] + [p] * N]
            matrix += [[p] + [p if i == j else q for j in range(N)] for i in range(N)]
            self.assertFalse(exact_psd(matrix))
        broken = moments.dense_moment_matrix(4, 5)
        broken[1][2] = broken[2][1] = 2
        self.assertFalse(exact_psd(broken))

    def test_full_local_tables_and_actual_code_projection(self):
        rng = random.Random(20261020)
        for D, m, count in ((3, 4, 12), (4, 5, 12), (5, 6, 6), (6, 7, 4)):
            for _ in range(count):
                scope = rng.sample(range(1, 1 << m), D + 4)
                local_review(D, m, scope)

    def test_genuine_equal_dimension_subspace_distribution(self):
        for D in (3, 4):
            kernels = set()
            for first in range(1, 1 << D):
                for second in range(first + 1, 1 << D):
                    word = sum(1 << (point - 1) for point in range(1, 1 << D)
                               if (first & point).bit_count() % 2 == 0
                               and (second & point).bit_count() % 2 == 0)
                    kernels.add(word)
            self.assertEqual(len(kernels), moments.gaussian_two(D))
            matrix = moments.dense_moment_matrix(D, D)
            for i in range(1 << D):
                for j in range(1 << D):
                    expectation = Fraction(sum(
                        (1 if i == 0 else (word >> (i - 1)) & 1) *
                        (1 if j == 0 else (word >> (j - 1)) & 1)
                        for word in kernels), len(kernels))
                    self.assertEqual(expectation, matrix[i][j])

    def test_degree_four_square_by_original_monomial_expansion(self):
        for D, m in ((3, 4), (4, 5), (5, 6)):
            data = moments.parameters(D, m)
            N, Q, c = data["N"], data["Q"], data["degree_four_coupling"]
            closed = Fraction((N - Q) * (Q + 1) * (3 * N * Q - N + Q - 3),
                              32 * N * (Q - 1) ** 3)
            self.assertEqual(c, closed)
            self.assertGreater(c, 0)
            terms = {frozenset(): -data["reduced_objective"]}
            terms.update({frozenset((point,)): Fraction(1) for point in range(1, N + 1)})
            terms[frozenset((1, 2))] = -c / data["mixed_q"]
            actual = polynomial_square_expectation(D, m, terms, data["beta"])
            self.assertEqual(actual, data["degree_four_square_value"])
            self.assertLess(actual, 0)
            # Reversing the coefficient destroys this negative-square witness.
            terms[frozenset((1, 2))] *= -1
            self.assertGreater(polynomial_square_expectation(D, m, terms, data["beta"]), 0)

    def test_independent_linear_square_expansion(self):
        for D, m in ((3, 4), (4, 5)):
            data = moments.parameters(D, m)
            terms = {frozenset(): -data["N"] * data["p"]}
            terms.update({frozenset((point,)): Fraction(1) for point in range(1, data["N"] + 1)})
            self.assertEqual(polynomial_square_expectation(D, m, terms, Fraction(0)),
                             data["old_variance"])

    def test_input_and_allocation_guards(self):
        for D, m in ((True, 4), (3, True), (2, 4), (5, 4), (3, 4097)):
            with self.assertRaises(ValueError):
                moments.parameters(D, m)
        for scope in ([0], [1, 1], [32], [True]):
            with self.assertRaises(ValueError):
                moments.scope_table(4, 5, scope)
        with self.assertRaises(ValueError):
            moments.scope_table(4, 5, list(range(1, 9)), max_points=7)
        with self.assertRaises(ValueError):
            moments.dense_moment_matrix(5, 64)
        with self.assertRaises(ValueError):
            moments.dense_moment_matrix(4, 5, repaired=1)
        self.assertEqual(moments.scope_table(3, 4, []), [1])


if __name__ == "__main__":
    unittest.main()
