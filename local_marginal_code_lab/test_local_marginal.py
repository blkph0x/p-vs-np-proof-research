import itertools
import unittest

from local_marginal import (basis, make_certificate, orthogonal_basis,
                            random_code_union_bound, span, verify_certificate)


def even_parity_generator(n):
    return tuple((1 << i) | (1 << (n - 1)) for i in range(n - 1))


class LocalMarginalTests(unittest.TestCase):
    def test_even_parity_is_exact_through_level_n_minus_two(self):
        rows = even_parity_generator(5)
        made = make_certificate(rows, 5, 0, 3)
        self.assertEqual(made["status"], "FOUND")
        checked = verify_certificate(made["certificate"])
        self.assertTrue(checked["valid"])
        self.assertTrue(checked["theorem_level_valid"])
        self.assertTrue(checked["support_replay"])
        self.assertEqual(checked["pinned_integer_optimum"], 2)

    def test_parity_boundary_fails_at_full_scope(self):
        rows = even_parity_generator(5)
        made = make_certificate(rows, 5, 0, 4)
        checked = verify_certificate(made["certificate"])
        self.assertTrue(checked["valid"])
        self.assertFalse(checked["theorem_level_valid"])
        self.assertFalse(checked["support_replay"])
        self.assertEqual(checked["counterexample"], [1, 2, 3, 4])

    def test_linear_algebra_helpers(self):
        rows = even_parity_generator(5)
        self.assertEqual(len(basis(rows)), 4)
        dual = orthogonal_basis(rows, 5)
        self.assertEqual(len(dual), 1)
        self.assertEqual(span(dual), (0, 31))

    def test_malformed_certificate_is_rejected(self):
        rows = even_parity_generator(5)
        certificate = make_certificate(rows, 5, 0, 4)["certificate"]
        certificate["dual_distance"] = 4
        self.assertFalse(verify_certificate(certificate)["valid"])

    def test_all_small_even_parity_scopes_replay(self):
        for n in range(2, 7):
            rows = even_parity_generator(n)
            for pin in range(n):
                for level in range(n + 1):
                    made = make_certificate(rows, n, pin, level)
                    checked = verify_certificate(made["certificate"])
                    self.assertTrue(checked["valid"])
                    expected = level < n - 1
                    self.assertEqual(checked["support_replay"], expected)

    def test_random_code_union_bound_is_strict(self):
        for n in (32, 64, 128, 256):
            bound = random_code_union_bound(n)
            self.assertTrue(bound["strictly_positive_good_probability"])
            self.assertEqual(bound["rank"], n // 2)
            self.assertEqual(bound["distance_lower_bound"], n // 16)
            self.assertEqual(bound["local_level_lower_bound"], n // 16 - 2)


if __name__ == "__main__":
    unittest.main()
