import importlib.util
import unittest
from fractions import Fraction
from itertools import combinations
from pathlib import Path

SPEC = importlib.util.spec_from_file_location(
    "all_dual_lp_barrier_audit", Path(__file__).with_name("all_dual_lp_barrier.py"))
barrier = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(barrier)


class AllDualLPBarrierTests(unittest.TestCase):
    def test_general_dual_distance_lemma_local_mixtures(self):
        # The all-size proof is analytic. These checks exercise every local
        # weight/pin case in this finite range, including the delta=3 boundary.
        for delta in range(3, 21):
            p = Fraction(1, delta - 1)
            for weight in range(delta, 51):
                for has_pin in (0, 1):
                    free = weight - has_pin
                    mixture = barrier.symmetric_parity_mixture(free, p * free, has_pin)
                    self.assertIsNotNone(mixture, (delta, weight, has_pin))
                    self.assertEqual(sum(prob for prob, _ in mixture), 1)
                    self.assertEqual(sum(prob * k for prob, k in mixture), p * free)
                    self.assertTrue(all(prob >= 0 and 0 <= k <= free and k % 2 == has_pin
                                        for prob, k in mixture))

    def test_complete_rational_certificate(self):
        result = barrier.verify_golay_certificate(barrier.golay_all_dual_certificate())
        self.assertTrue(result["verified"], result)
        self.assertEqual(result["dual_checks_verified"], 4095)
        self.assertEqual(result["weight_distribution"], {0: 1, 8: 759, 12: 2576, 16: 759, 24: 1})
        self.assertEqual(result["distance"], 8)
        self.assertEqual(result["pinned_integer_optimum"], 8)
        self.assertEqual(result["fractional_feasible_weight"], Fraction(30, 7))
        self.assertEqual(result["fractional_optimum"], Fraction(30, 7))
        self.assertEqual(result["dual_bound_check_count"], 253)
        self.assertEqual(result["dual_bound_coordinate_multiplicity"], 77)
        self.assertEqual(result["decision_upper_bound"], 5)

    def test_uniform_subset_mixtures_by_explicit_small_expansion(self):
        # Independent finite expansion verifies the symmetry argument and
        # marginals, instead of only checking expected subset cardinality.
        for length in range(1, 9):
            for parity in (0, 1):
                for numerator in range(2 * length + 1):
                    mean = Fraction(numerator, 2)
                    mixture = barrier.symmetric_parity_mixture(length, mean, parity)
                    allowed = list(range(parity, length + 1, 2))
                    if not allowed or mean < min(allowed) or mean > max(allowed):
                        self.assertIsNone(mixture)
                        continue
                    marginals = [Fraction(0)] * length
                    total = Fraction(0)
                    for probability, weight in mixture:
                        subsets = list(combinations(range(length), weight))
                        for subset in subsets:
                            mass = probability / len(subsets)
                            self.assertEqual(len(subset) % 2, parity)
                            total += mass
                            for i in subset:
                                marginals[i] += mass
                    self.assertEqual(total, 1)
                    self.assertEqual(marginals, [mean / length] * length)

    def test_rejects_fractional_point_cut_by_a_dual_check(self):
        certificate = barrier.golay_all_dual_certificate()
        certificate["point"] = (Fraction(1),) + (Fraction(1, 8),) * 23
        result = barrier.verify_golay_certificate(certificate)
        self.assertFalse(result["verified"])
        self.assertEqual(result["reason"], "a redundant check excludes the point")
        self.assertIn("violated_check", result)

    def test_rejects_wrong_code_claims_and_missing_pin(self):
        changes = (
            {"claimed_distance": 7},
            {"decision_upper_bound": 8},
            {"point": (Fraction(1, 7),) * 24},
            {"parity_check_rows": barrier.golay_all_dual_certificate()["parity_check_rows"][:-1]},
            {"n": 23},
        )
        for change in changes:
            certificate = barrier.golay_all_dual_certificate()
            certificate.update(change)
            self.assertFalse(barrier.verify_golay_certificate(certificate)["verified"])

    def test_same_certificate_works_for_each_pin(self):
        certificate = barrier.golay_all_dual_certificate()
        for pin in range(24):
            certificate["pinned_one_coordinate"] = pin
            certificate["point"] = tuple(Fraction(1) if i == pin else Fraction(1, 7)
                                          for i in range(24))
            result = barrier.verify_golay_certificate(certificate)
            self.assertTrue(result["verified"], (pin, result))
            self.assertEqual(result["pinned_integer_optimum"], 8)
            self.assertEqual(result["fractional_optimum"], Fraction(30, 7))
            self.assertEqual(result["dual_bound_check_count"], 253)
            self.assertEqual(result["dual_bound_coordinate_multiplicity"], 77)


if __name__ == "__main__":
    unittest.main()
