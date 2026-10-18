"""Independent positive, negative and adversarial F7-certificate checks."""
import copy
import json
from pathlib import Path
import unittest

try:
    from .fano_certificate import SCHEMA, find_fano_minor, verify_fano_certificate
except ImportError:
    from fano_certificate import SCHEMA, find_fano_minor, verify_fano_certificate


ROOT = Path(__file__).resolve().parent.parent


class FanoCertificateTests(unittest.TestCase):
    def setUp(self):
        # F7 plus two coloops and a parallel copy of one of those coloops.
        self.columns = tuple(range(1, 8)) + (8, 8, 16)
        self.certificate = {
            "schema": SCHEMA, "n": 10, "matroid_rank": 5,
            "contraction_indices": [7, 9], "retained_indices": list(range(7)),
            "quotient_basis_indices": [0, 1, 3], "quotient_vectors": list(range(1, 8)),
        }

    def test_literal_fano_and_explicit_contraction(self):
        result = find_fano_minor(tuple(range(1, 8)), max_trials=1)
        self.assertEqual(result["status"], "FOUND")
        self.assertEqual(result["certificate"]["contraction_indices"], [])
        check = verify_fano_certificate(self.columns, self.certificate)
        self.assertTrue(check["valid"], check)
        self.assertEqual(check["contraction_rank"], 2)
        self.assertEqual(check["retained_quotient_rank"], 3)

    def test_all_saved_random_cores(self):
        records = json.loads((ROOT / "high_width_core_stress_lab" / "random_code_audits.json").read_text())
        self.assertEqual([r["n"] for r in records], [18, 20, 22, 24, 26, 28])
        for row in records:
            with self.subTest(n=row["n"]):
                result = find_fano_minor(row["columns"])
                self.assertEqual(result["status"], "FOUND")
                self.assertLessEqual(result["search"]["trials"], 15)
                self.assertTrue(verify_fano_certificate(row["columns"], result["certificate"])["valid"])
                self.assertEqual(result, find_fano_minor(row["columns"]))

    def test_graphic_negative_control_is_unknown(self):
        # Reduced incidence columns of K5: a graphic matroid cannot have F7.
        columns = []
        for u in range(5):
            for v in range(u + 1, 5):
                columns.append((1 << u if u < 4 else 0) ^ (1 << v if v < 4 else 0))
        result = find_fano_minor(columns, max_trials=32)
        self.assertEqual(result["status"], "UNKNOWN")
        self.assertIsNone(result["certificate"])
        self.assertEqual(result["search"]["trials"], 32)

    def test_zero_budget_and_small_input_are_unknown(self):
        for columns, budget in ((tuple(range(1, 8)), 0), ((1, 2, 3), 10), ((), 10)):
            result = find_fano_minor(columns, max_trials=budget)
            self.assertEqual(result["status"], "UNKNOWN")
            self.assertEqual(result["search"]["trials"], 0)

    def test_input_validation(self):
        for columns in ([1, -1], [True, 1], [1, "2"], None, "123", {}):
            with self.subTest(columns=columns):
                with self.assertRaises(ValueError):
                    find_fano_minor(columns)
                self.assertFalse(verify_fano_certificate(columns, self.certificate)["valid"])
        for budget in (-1, True, 1.5):
            with self.assertRaises(ValueError):
                find_fano_minor(self.columns, max_trials=budget)
        with self.assertRaises(ValueError):
            find_fano_minor(self.columns, seed=True)

    def test_reject_malformed_certificates(self):
        malformed = [None, [], "certificate", {}]
        for field in self.certificate:
            missing = copy.deepcopy(self.certificate)
            del missing[field]
            malformed.append(missing)
        for field, value in (
            ("schema", "other"), ("n", True), ("matroid_rank", 4),
            ("contraction_indices", None), ("contraction_indices", [-1, 9]),
            ("contraction_indices", [7, 10]), ("contraction_indices", [7, True]),
            ("contraction_indices", [7, 7]), ("contraction_indices", [7, 8]),
            ("contraction_indices", [0, 9]), ("retained_indices", [0, 1, 2, 3, 4, 5]),
            ("retained_indices", [0, 1, 2, 3, 4, 5, 5]),
            ("retained_indices", [0, 1, 2, 3, 4, 5, 8]),
            ("quotient_basis_indices", [0, 1, 2]), ("quotient_basis_indices", [0, 1, 9]),
            ("quotient_vectors", [1, 2, 3, 4, 5, 6, 6]),
            ("quotient_vectors", [2, 1, 3, 4, 5, 6, 7]),
            ("quotient_vectors", [True, 2, 3, 4, 5, 6, 7]),
            ("quotient_vectors", [0, 2, 3, 4, 5, 6, 7]),
        ):
            altered = copy.deepcopy(self.certificate)
            altered[field] = value
            malformed.append(altered)
        for cert in malformed:
            with self.subTest(certificate=cert):
                self.assertFalse(verify_fano_certificate(self.columns, cert)["valid"])

    def test_changed_columns_and_higher_ambient_coordinates(self):
        altered = list(self.columns)
        altered[2] = altered[1]  # Introduce parallel retained columns.
        self.assertFalse(verify_fano_certificate(altered, self.certificate)["valid"])
        # Inserting unused ambient rows does not change the matroid or certificate.
        shifted = [value << 64 for value in self.columns]
        self.assertTrue(verify_fano_certificate(shifted, self.certificate)["valid"])


if __name__ == "__main__":
    unittest.main()
