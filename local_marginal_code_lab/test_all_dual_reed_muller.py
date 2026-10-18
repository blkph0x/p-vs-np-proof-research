import copy
import json
from fractions import Fraction
from pathlib import Path
import unittest

from all_dual_reed_muller import (
    gaussian_binomial,
    make_certificate,
    verify_certificate,
)


HERE = Path(__file__).resolve().parent


class AllDualReedMullerTests(unittest.TestCase):
    def test_gaussian_binomials_are_exact(self):
        self.assertEqual(gaussian_binomial(3, 1), 7)
        self.assertEqual(gaussian_binomial(5, 2), 155)
        self.assertEqual(gaussian_binomial(7, 3), 11811)
        self.assertEqual(gaussian_binomial(6, 3), 1395)

    def test_saved_certificates_replay(self):
        saved = json.loads((HERE / "REED_MULLER_ALL_DUAL_RESULTS.json").read_text(encoding="utf-8"))
        self.assertTrue(saved["all_valid"])
        for case in saved["cases"]:
            checked = verify_certificate(case["certificate"])
            self.assertTrue(checked["valid"], case["name"])
            self.assertEqual(checked, case["verification"])

    def test_exact_rm_2_5_has_matching_lp_bound(self):
        certificate = make_certificate(2)["certificate"]
        self.assertEqual(certificate["word_enumeration"]["word_count"], 65536)
        self.assertEqual(certificate["minimum_check_count_through_pin"], 155)
        self.assertEqual(certificate["minimum_check_other_coordinate_incidence"], 35)
        self.assertEqual(certificate["fractional_optimum"], "38/7")
        self.assertEqual(verify_certificate(certificate)["integrality_ratio"], "28/19")

    def test_wrong_uniform_point_is_rejected(self):
        certificate = make_certificate(1)["certificate"]
        certificate["point"][1] = "1/4"
        self.assertFalse(verify_certificate(certificate)["valid"])

    def test_wrong_incidence_and_mixture_are_rejected(self):
        certificate = make_certificate(2)["certificate"]
        mutated_incidence = copy.deepcopy(certificate)
        mutated_incidence["minimum_check_other_coordinate_incidence"] = 36
        self.assertFalse(verify_certificate(mutated_incidence)["valid"])
        mutated_mixture = copy.deepcopy(certificate)
        mutated_mixture["all_dual_mixture_cases"][0]["mixture"][0][0] = "1/2"
        self.assertFalse(verify_certificate(mutated_mixture)["valid"])


if __name__ == "__main__":
    unittest.main()
