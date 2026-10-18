import copy
import json
from pathlib import Path
import unittest

from reed_muller import (
    generator_rows,
    make_certificate,
    monomial_masks,
    parameters,
    verify_certificate,
)
from local_marginal import make_certificate as make_local_certificate
from local_marginal import verify_certificate as verify_local_certificate


HERE = Path(__file__).resolve().parent


class ReedMullerTests(unittest.TestCase):
    def test_symmetric_parameters(self):
        for s in range(1, 6):
            info = parameters(s)
            self.assertEqual(info["m"], 2 * s + 1)
            self.assertEqual(info["n"], 1 << (2 * s + 1))
            self.assertEqual(info["dimension"], info["n"] // 2)
            self.assertEqual(info["distance"], 1 << (s + 1))
            self.assertEqual(info["dual_order"], s)
            self.assertEqual(info["dual_distance"], info["distance"])

    def test_generator_rows_are_the_anf_basis(self):
        for s in (1, 2, 3):
            info = parameters(s)
            self.assertEqual(len(monomial_masks(info["m"], info["r"])), info["dimension"])
            self.assertEqual(len(generator_rows(s)), info["dimension"])
            self.assertTrue(all(row.bit_count() == 1 << (info["m"] - mask.bit_count())
                                for row, mask in zip(
                                    generator_rows(s), monomial_masks(info["m"], info["r"]))))

    def test_saved_certificates_replay(self):
        saved = json.loads((HERE / "REED_MULLER_RESULTS.json").read_text(encoding="utf-8"))
        self.assertTrue(saved["all_valid"])
        for case in saved["cases"]:
            checked = verify_certificate(case["certificate"])
            self.assertTrue(checked["valid"], case["name"])
            self.assertEqual(checked, case["verification"])

    def test_rm_2_5_is_exactly_enumerated(self):
        certificate = make_certificate(2)["certificate"]
        self.assertEqual(certificate["word_enumeration"], {
            "status": "EXACT", "word_count": 65536,
            "minimum_distance": 8, "pinned_minimum": 8,
        })
        self.assertIsNone(certificate["enumerated_support"])

    def test_small_support_replay(self):
        certificate = make_certificate(1, enumerate_scopes=True)["certificate"]
        checked = verify_certificate(certificate)
        self.assertTrue(checked["valid"])
        self.assertTrue(checked["support_replay"])
        self.assertEqual(checked["checked_scopes"], 37)

    def test_rm_1_3_boundary_scope_rejects_unit_point(self):
        boundary = make_local_certificate(generator_rows(1), 8, 0, 3)
        checked = verify_local_certificate(boundary["certificate"])
        self.assertTrue(checked["valid"])
        self.assertFalse(checked["theorem_level_valid"])
        self.assertFalse(checked["support_replay"])

    def test_mutated_rows_are_rejected(self):
        certificate = make_certificate(1)["certificate"]
        mutated = copy.deepcopy(certificate)
        mutated["generator_rows"][0] ^= 1
        self.assertFalse(verify_certificate(mutated)["valid"])

    def test_mutated_theorem_fields_are_rejected(self):
        certificate = make_certificate(1)["certificate"]
        for field, value in (("distance", 2), ("dual_distance", 2),
                             ("pinned_integer_optimum", 2),
                             ("minimum_weight_witness", 1)):
            mutated = copy.deepcopy(certificate)
            mutated[field] = value
            self.assertFalse(verify_certificate(mutated)["valid"], field)

    def test_mutated_dual_and_level_are_rejected(self):
        certificate = make_certificate(1)["certificate"]
        mutated_dual = copy.deepcopy(certificate)
        mutated_dual["dual_basis"][0] ^= 1
        self.assertFalse(verify_certificate(mutated_dual)["valid"])
        mutated_level = copy.deepcopy(certificate)
        mutated_level["level"] = 1
        self.assertFalse(verify_certificate(mutated_level)["valid"])


if __name__ == "__main__":
    unittest.main()
