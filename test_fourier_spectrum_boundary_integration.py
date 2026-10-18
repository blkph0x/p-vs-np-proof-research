import importlib.util
import json
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parent / "fourier_spectrum_boundary_lab"
SPEC = importlib.util.spec_from_file_location("fourier_boundary_test", ROOT / "fourier_boundary.py")
fourier = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = fourier
SPEC.loader.exec_module(fourier)
VERIFY_SPEC = importlib.util.spec_from_file_location(
    "fourier_boundary_independent_verifier", ROOT / "verify_fourier_boundary.py")
independent = importlib.util.module_from_spec(VERIFY_SPEC)
sys.modules[VERIFY_SPEC.name] = independent
VERIFY_SPEC.loader.exec_module(independent)


class FourierSpectrumBoundaryTests(unittest.TestCase):
    def test_every_clause_has_three_distinct_literals(self):
        for n in range(13):
            variables, clauses = fourier.forced_3cnf(n)
            self.assertEqual(variables, 3 * n)
            self.assertEqual(len(clauses), 4 * n)
            self.assertTrue(all(len(clause) == 3 and
                                len({abs(x) for x in clause}) == 3
                                for clause in clauses))

    def test_saved_artifact_and_analytic_support(self):
        artifact = json.loads((ROOT / "RESULTS.json").read_text())
        self.assertTrue(artifact["all_checks_passed"])
        for row in artifact["analytic_rows"]:
            self.assertEqual(row["analytic_nonzero_coefficients"], 1 << row["n"])

    def test_bruteforce_walsh_transform(self):
        for n in range(5):
            spectrum = fourier.brute_force_spectrum(n)
            self.assertEqual(sum(value != 0 for value in spectrum), 1 << n)
            for subset, value in enumerate(spectrum[:min(64, len(spectrum))]):
                self.assertEqual(value, fourier.spectrum_coefficient(n, subset))

    def test_independent_verifier(self):
        result = independent.verify()
        self.assertTrue(result["independent_checks_passed"])
        self.assertEqual(result["brute_force_rows"], 5)
        self.assertEqual(result["cyclic_brute_force_rows"], 6)

    def test_cyclic_family_is_unique_and_dense(self):
        for n in range(3, 8):
            variables, clauses = fourier.cyclic_unique_3cnf(n)
            self.assertEqual(variables, n)
            self.assertEqual(len(clauses), 4 * n)
            self.assertTrue(all(len(clause) == 3 and
                                len({abs(x) for x in clause}) == 3
                                for clause in clauses))
            models = [assignment for assignment in range(1 << n)
                      if fourier.satisfies(variables, clauses, assignment)]
            self.assertEqual(models, [(1 << n) - 1])
            spectrum = fourier.cyclic_brute_force_spectrum(n)
            self.assertEqual(sum(value != 0 for value in spectrum), 1 << n)
            self.assertTrue(all(value == fourier.cyclic_spectrum_coefficient(n, mask)
                                for mask, value in enumerate(spectrum)))

    def test_cyclic_family_is_dense_over_odd_prime_fields(self):
        for prime in (3, 5, 7):
            for n in range(3, 8):
                spectrum = fourier.cyclic_modular_spectrum(n, prime)
                self.assertEqual(sum(value != 0 for value in spectrum), 1 << n)
                inverse = pow(pow(2, n, prime), -1, prime)
                expected = [(((-1 if mask.bit_count() & 1 else 1) * inverse) % prime)
                            for mask in range(1 << n)]
                self.assertEqual(list(spectrum), expected)

    def test_cyclic_target_family_spans_full_function_space(self):
        # Signed versions of the cyclic forcing gadget realize every point
        # mass delta_t with O(n) distinct-literal 3-CNF clauses.  The point
        # masses are the standard basis, so their exact linear span has
        # dimension 2**n over every field.
        for n in range(3, 6):
            indicators = []
            for target in range(1 << n):
                variables, clauses = fourier.cyclic_unique_target_3cnf(n, target)
                self.assertEqual(variables, n)
                self.assertEqual(len(clauses), 4 * n)
                self.assertTrue(all(len(clause) == 3 and
                                    len({abs(x) for x in clause}) == 3
                                    for clause in clauses))
                models = [assignment for assignment in range(1 << n)
                          if fourier.satisfies(n, clauses, assignment)]
                self.assertEqual(models, [target])
                indicators.append([int(assignment == target)
                                   for assignment in range(1 << n)])
            self.assertEqual(indicators,
                             [[int(i == j) for i in range(1 << n)]
                              for j in range(1 << n)])


if __name__ == "__main__":
    unittest.main()
