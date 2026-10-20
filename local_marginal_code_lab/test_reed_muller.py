import copy
import json
from fractions import Fraction
from math import comb
from pathlib import Path
import unittest

from reed_muller import (
    affine_minimum_support,
    affine_minimum_witness_masks,
    boundary_nonpin_objective_lower_bound,
    boundary_objective_lower_bound,
    boundary_local_optimum,
    generator_rows,
    gaussian_binomial_2,
    make_certificate,
    monomial_masks,
    parameters,
    verify_certificate,
)
from local_marginal import atom_slot_count, make_certificate as make_local_certificate
from local_marginal import scope_count
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

    def test_symmetric_family_has_exact_boundary_obstruction(self):
        """A minimum dual word through the pin rejects the unit atom at d-1."""
        for s in range(1, 6):
            info = parameters(s)
            for pin in (0, 1, info["n"] - 1):
                support = affine_minimum_support(info["m"], info["r"], pin)
                self.assertEqual(support.bit_count(), info["dual_distance"])
                self.assertTrue(support >> pin & 1)
                row_by_mask = dict(zip(monomial_masks(info["m"], info["r"]),
                                       generator_rows(s)))
                witness = 0
                for mask in affine_minimum_witness_masks(info["m"], info["r"], pin):
                    witness ^= row_by_mask[mask]
                self.assertEqual(witness, support)
                self.assertTrue(all(
                    (support & row).bit_count() % 2 == 0
                    for row in generator_rows(s)
                ))
                boundary_scope = support ^ (1 << pin)
                self.assertEqual(boundary_scope.bit_count(), info["dual_distance"] - 1)

    def test_explicit_all_scope_representation_has_exact_scaling_bounds(self):
        """The unquotiented max-level model is superpolynomial in n."""
        for s in range(1, 7):
            info = parameters(s)
            n = info["n"]
            k = info["dual_distance"] - 2
            top_scope = comb(n, k)
            scopes = scope_count(n, k)
            atoms = atom_slot_count(n, k)
            self.assertLessEqual(top_scope, scopes)
            self.assertLessEqual(scopes, (k + 1) * top_scope)
            top_atoms = (1 << k) * top_scope
            self.assertLessEqual(top_atoms, atoms)
            self.assertLessEqual(atoms, (k + 1) * top_atoms)
            supported_atoms = sum(
                comb(n - 1, size) * (1 << size)
                + (comb(n - 1, size - 1) * (1 << (size - 1)) if size else 0)
                for size in range(k + 1)
            )
            top_supported = (1 << k) * comb(n - 1, k)
            self.assertLessEqual(top_supported, supported_atoms)
            self.assertLessEqual(
                supported_atoms,
                (k + 1) * (1 << (k + 1)) * comb(n - 1, k),
            )

    def test_boundary_level_has_a_general_incidence_lower_bound(self):
        """Minimum affine checks improve the level-d-1 objective bound."""
        for s in range(1, 9):
            info = parameters(s)
            m, r = info["m"], info["r"]
            total = gaussian_binomial_2(m, r + 1)
            through_other = gaussian_binomial_2(m - 1, r)
            self.assertEqual(
                Fraction(total, through_other),
                Fraction((1 << m) - 1, (1 << (r + 1)) - 1),
            )
            expected = Fraction(1) + Fraction((1 << m) - 1,
                                               (1 << (r + 1)) - 1)
            self.assertEqual(boundary_objective_lower_bound(s), expected)
            self.assertEqual(boundary_local_optimum(s), expected)
            self.assertEqual(boundary_nonpin_objective_lower_bound(s), expected - 1)
            self.assertEqual(Fraction(1) - (info["dual_distance"] - 1)
                             * Fraction(1, info["dual_distance"] - 1), 0)
        self.assertEqual(boundary_objective_lower_bound(2), Fraction(38, 7))

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
