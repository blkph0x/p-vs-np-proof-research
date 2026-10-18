"""Support-enumeration audits for the restricted projection-hull statements."""
from copy import deepcopy
from itertools import combinations, product
from random import Random
import unittest

from projection_barrier import (golay_projection_audit, make_projection_certificate,
                                projection_dimension, verify_projection_certificate)


def independent_words(generator):
    words = set()
    for coefficients in range(1 << len(generator)):
        word = 0
        for j, row in enumerate(generator):
            if coefficients >> j & 1:
                word ^= row
        words.add(word)
    return words


def project(word, coordinates):
    return sum(((word >> coordinate) & 1) << i for i, coordinate in enumerate(coordinates))


class ProjectionBarrierTests(unittest.TestCase):
    def test_all_small_affine_projections_against_supports(self):
        configurations = 0
        for n in range(5):
            subsets = [subset for size in range(n + 1) for subset in combinations(range(n), size)]
            for row_count in range(min(2, n) + 1):
                for generator in product(range(1 << n), repeat=row_count):
                    words = independent_words(generator)
                    for pin in (None, *range(n)):
                        for pin_value in ((1,) if pin is None else (0, 1)):
                            feasible = {word for word in words if pin is None or (word >> pin & 1) == pin_value}
                            for coordinates in subsets:
                                if pin in coordinates:
                                    continue
                                patterns = {project(word, coordinates) for word in feasible}
                                result = projection_dimension(generator, n, coordinates, pin=pin, pin_value=pin_value)
                                self.assertEqual(result["feasible"], bool(patterns))
                                self.assertEqual(result["is_full_cube"], len(patterns) == 1 << len(coordinates))
                                if patterns:
                                    self.assertEqual(1 << result["dimension"], len(patterns))
                                    recovered = {word ^ result["projected_offset"]
                                                 for word in independent_words(result["projected_basis"])}
                                    self.assertEqual(patterns, recovered)
                    configurations += 1
        self.assertEqual(configurations, 371)

    def test_certified_limits_against_every_small_coordinate_set(self):
        for n in range(1, 5):
            for generator in product(range(1 << n), repeat=2):
                made = make_projection_certificate(generator, n, pin=0)
                certificate = made["certificate"]
                result = verify_projection_certificate(generator, n, certificate, pin=0)
                self.assertTrue(result["valid"], result)
                dual_words = [word for word in range(1 << n)
                              if not any((word & row).bit_count() % 2 for row in generator)]
                expected_delta = min((word.bit_count() for word in dual_words if word), default=None)
                self.assertEqual(result["dual_distance"], expected_delta)
                words = independent_words(generator)
                for size in range(result["unconditioned_cube_max_size"] + 1):
                    for subset in combinations(range(n), size):
                        self.assertEqual(len({project(word, subset) for word in words}), 1 << size)
                conditional_limit = result["conditioned_other_cube_max_size"]
                if conditional_limit is not None:
                    for size in range(conditional_limit + 1):
                        for subset in combinations(range(1, n), size):
                            self.assertEqual(len({project(word, subset) for word in words if word & 1}), 1 << size)

    def test_even_parity_boundary_is_not_a_full_cube(self):
        generator = (3, 5, 9)  # Length-four even-parity code; dual distance4.
        certificate = make_projection_certificate(generator, 4, pin=0)["certificate"]
        self.assertEqual(certificate["dual_distance"], 4)
        self.assertEqual(certificate["unconditioned_cube_max_size"], 3)
        self.assertEqual(certificate["conditioned_other_cube_max_size"], 2)
        self.assertEqual(projection_dimension(generator, 4, range(4))["dimension"], 3)
        boundary = projection_dimension(generator, 4, (1, 2, 3), pin=0)
        self.assertEqual(boundary["dimension"], 2)
        self.assertFalse(boundary["is_full_cube"])
        patterns = {project(word, (1, 2, 3)) for word in independent_words(generator) if word & 1}
        self.assertNotIn(0, patterns)
        self.assertTrue(all(pattern.bit_count() % 2 == 1 for pattern in patterns))

    def test_golay_combined_certificate_and_boundary(self):
        audit = golay_projection_audit()
        verified = audit["projection_verification"]
        self.assertTrue(verified["valid"])
        self.assertEqual(verified["dual_distance"], 8)
        self.assertEqual(verified["dual_words_checked"], 4096)
        self.assertEqual(verified["unconditioned_cube_max_size"], 7)
        self.assertEqual(verified["conditioned_other_cube_max_size"], 6)
        self.assertEqual(verified["unconditioned_coordinate_sets_covered"], 536155)
        self.assertEqual(verified["conditioned_coordinate_sets_covered"], 145499)
        self.assertEqual(audit["fractional_feasible_weight"], [30, 7])
        self.assertEqual(audit["combined_exact_lp_optimum"], [30, 7])
        self.assertEqual(audit["lp_lower_certificate"], {"check_count": 253, "other_coordinate_multiplicity": 77})
        self.assertEqual(audit["integer_pinned_optimum"], 8)
        self.assertTrue(audit["combined_all_dual_and_bounded_projection_witness_valid"])
        self.assertEqual(audit["boundary_control"]["unconditioned_projection"]["dimension"], 7)
        self.assertEqual(audit["boundary_control"]["conditioned_projection"]["dimension"], 6)
        # Some actual rank checks complement, but do not replace, the all-subset theorem.
        rng = Random(18026)
        for _ in range(100):
            coordinates = rng.sample(range(1, 24), 6)
            self.assertTrue(projection_dimension(audit["generator_rows"], 24, coordinates, pin=0)["is_full_cube"])
        # The projection-only unit vector is NOT the combined all-dual witness.
        self.assertEqual((audit["boundary_control"]["dual_check"] & 1).bit_count(), 1)

    def test_zero_full_empty_codes_and_budgets(self):
        for generator, n, pin, expected_delta in (((), 0, None, None), ((), 3, 0, 1),
                                                  ((1, 2, 4), 3, 0, None)):
            made = make_projection_certificate(generator, n, pin=pin)
            result = verify_projection_certificate(generator, n, made["certificate"], pin=pin)
            self.assertTrue(result["valid"])
            self.assertEqual(result["dual_distance"], expected_delta)
        unknown = make_projection_certificate((), 5, max_dual_words=16)
        self.assertEqual(unknown["status"], "UNKNOWN")
        certificate = make_projection_certificate((), 5)["certificate"]
        checked = verify_projection_certificate((), 5, certificate, max_dual_words=16)
        self.assertEqual(checked["status"], "UNKNOWN")

    def test_reject_tampered_guarantees_and_dual_basis(self):
        generator = (3, 5, 9)
        certificate = make_projection_certificate(generator, 4, pin=0)["certificate"]
        mutations = [None, {}, []]
        for field in certificate:
            changed = deepcopy(certificate)
            del changed[field]
            mutations.append(changed)
        for field, value in (("dimension", 4), ("n", 5), ("dual_distance", 5),
                             ("dual_distance", True), ("pin", False), ("pin", 1),
                             ("unconditioned_cube_max_size", 4),
                             ("conditioned_other_cube_max_size", 3),
                             ("dual_basis", [15, 15]), ("dual_basis", [14]),
                             ("dual_basis", [True]), ("dual_basis", [-1])):
            changed = deepcopy(certificate)
            changed[field] = value
            mutations.append(changed)
        for mutation in mutations:
            self.assertEqual(verify_projection_certificate(generator, 4, mutation, pin=0)["status"], "INVALID")
        self.assertEqual(verify_projection_certificate(generator, 4, certificate, pin=1)["status"], "INVALID")

    def test_bad_projection_requests(self):
        for coordinates, kwargs in (((0, 0), {}), ((-1,), {}), ((4,), {}), ((True,), {}),
                                    ((0,), {"pin": 0}), ((1,), {"pin": True}),
                                    ((1,), {"pin": 0, "pin_value": True})):
            with self.assertRaises(ValueError):
                projection_dimension((3, 5, 9), 4, coordinates, **kwargs)


if __name__ == "__main__":
    unittest.main()
