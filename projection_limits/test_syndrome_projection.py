"""Small exhaustive checks independent of the projection dependency search."""
from copy import deepcopy
from itertools import product
import unittest

import syndrome_projection as projection


def span_rank(rows):
    span = {0}
    for row in rows:
        span |= {word ^ row for word in tuple(span)}
    return len(span).bit_length() - 1


def direct_syndrome(rows, word):
    return sum((sum((row >> j & 1) * (word >> j & 1) for j in range(max(row.bit_length(), word.bit_length()))) % 2) << i
               for i, row in enumerate(rows))


class SyndromeProjectionTests(unittest.TestCase):
    def test_all_matrices_through_three_rows_four_columns(self):
        cases = 0
        for n in range(5):
            for m in range(4):
                for rows in product(range(1 << n), repeat=m):
                    q = span_rank(rows)
                    result = projection.dependency_witness(rows, n)
                    self.assertEqual(result["rank"], q)
                    if n == q:
                        self.assertEqual(result["status"], "NO_NONZERO_KERNEL")
                        self.assertIsNone(result["word"])
                        self.assertFalse(any(direct_syndrome(rows, word) == 0 for word in range(1, 1 << n)))
                    else:
                        word = result["word"]
                        self.assertEqual(result["status"], "WITNESS")
                        self.assertGreater(word, 0)
                        self.assertEqual(direct_syndrome(rows, word), 0)
                        self.assertLessEqual(word.bit_count(), q + 1)
                        self.assertLessEqual(word.bit_length(), q + 1)
                        self.assertLessEqual(result["stats"]["prefix_bit_checks"], m * (q + 1))
                        self.assertLessEqual(result["stats"]["column_xors"], q * (q + 1) // 2)
                    cases += 1
        self.assertEqual(cases, 5058)

    def test_all_small_H_and_projectors_and_strict_distance_claim(self):
        strict_cases = projection_cases = 0
        for n in range(4):
            for m in range(3):
                for H in product(range(1 << n), repeat=m):
                    original = [word for word in range(1, 1 << n) if direct_syndrome(H, word) == 0]
                    distance = min(map(int.bit_count, original), default=float("inf"))
                    for t in range(4):
                        for Q in product(range(1 << m), repeat=t):
                            cert = projection.make_projection_witness(H, Q, n)
                            projection_cases += 1
                            # Independent matrix product by coordinate syndromes.
                            for j in range(n):
                                self.assertEqual(direct_syndrome(cert["projected_rows"], 1 << j),
                                                 direct_syndrome(Q, direct_syndrome(H, 1 << j)))
                            self.assertEqual(cert["rank"], span_rank(cert["projected_rows"]))
                            if n <= cert["rank"]:
                                self.assertEqual(cert["status"], "NO_NONZERO_KERNEL")
                                continue
                            self.assertTrue(projection.verify_projection_witness(H, Q, n, cert)["valid"])
                            if cert["rank"] + 1 < distance:
                                self.assertTrue(cert["spurious_for_original"])
                                self.assertNotEqual(direct_syndrome(H, cert["word"]), 0)
                                projected_words = [word for word in range(1, 1 << n)
                                                   if direct_syndrome(cert["projected_rows"], word) == 0]
                                self.assertLess(min(map(int.bit_count, projected_words)), distance)
                                strict_cases += 1
        self.assertGreater(projection_cases, 7000)
        self.assertGreater(strict_cases, 0)

    def test_actual_rank_differs_from_row_count_and_projector_rank(self):
        cert = projection.make_projection_witness((3, 3), (1, 2), 2)
        self.assertEqual((cert["projector_rank"], cert["rank"], cert["projector_row_count"]), (2, 1, 2))
        self.assertTrue(projection.verify_projection_witness((3, 3), (1, 2), 2, cert)["valid"])
        cert = projection.make_projection_witness((1, 2, 4), (0,) * 17, 3)
        self.assertEqual((cert["rank"], cert["projector_row_count"], cert["weight"]), (0, 17, 1))
        self.assertTrue(cert["spurious_for_original"])

    def test_strict_inequality_and_n_greater_than_q_are_essential(self):
        # Repetition code: d=3 and q+1=3; identity projection preserves distance.
        cert = projection.make_projection_witness((3, 6), (1, 2), 3)
        self.assertEqual((cert["rank"], cert["weight"], cert["word"]), (2, 3, 7))
        self.assertFalse(cert["spurious_for_original"])
        self.assertEqual(projection.dependency_witness((1, 2, 4), 3)["status"], "NO_NONZERO_KERNEL")
        self.assertEqual(projection.dependency_witness((), 0)["status"], "NO_NONZERO_KERNEL")

    def test_affine_statement_only_for_consistent_unrestricted_systems(self):
        for n in range(4):
            for m in range(3):
                for rows in product(range(1 << n), repeat=m):
                    q = span_rank(rows)
                    for target in range(1 << m):
                        solutions = [word for word in range(1 << n) if direct_syndrome(rows, word) == target]
                        if solutions:
                            self.assertLessEqual(min(map(int.bit_count, solutions)), q)

    def test_malformed_inputs_and_forged_witnesses(self):
        for rows, n in [((True,), 1), ((-1,), 1), ((2,), 1), ((), True), ((), -1)]:
            with self.assertRaises(ValueError):
                projection.dependency_witness(rows, n)
        with self.assertRaises(ValueError):
            projection.make_projection_witness((1,), (2,), 1)
        H, Q, n = (3, 6), (1,), 3
        cert = projection.make_projection_witness(H, Q, n)
        changes = [("rank", 99), ("rank", True), ("original_rank", 99),
                   ("projector_rank", 99), ("row_count", 99), ("prefix_length", 99),
                   ("word", 0), ("word", True), ("word", 4), ("weight", True),
                   ("projected_rows", [0]), ("projected_syndrome", 1),
                   ("original_syndrome", 0), ("spurious_for_original", False)]
        for field, value in changes:
            forged = deepcopy(cert)
            forged[field] = value
            self.assertFalse(projection.verify_projection_witness(H, Q, n, forged)["valid"], (field, value))
        for malformed in (None, [], {}, {"status": "NO_NONZERO_KERNEL"}):
            self.assertFalse(projection.verify_projection_witness(H, Q, n, malformed)["valid"])


if __name__ == "__main__":
    unittest.main()
