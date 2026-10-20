"""Coverage, arithmetic, coordinate invariance and forged-certificate controls."""
from copy import deepcopy
from itertools import combinations
import json
from math import comb
import unittest

import explore
import verify


class ScopeExplorationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cases, coverage = explore.enumerate_types()
        cls.certificate = {
            "schema": "d6-ten-point-complete-histogram-certificate-v1",
            "width": 10, "denominator": 651, "rank_numerators": list(explore.NUMERATORS),
            "coverage": coverage, "cases": cases,
        }

    def test_complete_independent_replay(self):
        checked = verify.verify_certificate(json.loads(json.dumps(self.certificate)))
        self.assertTrue(checked["valid"], checked)
        self.assertEqual(checked["tables"], 121)
        self.assertEqual(checked["atom_moment_comparisons"], 123904)
        self.assertEqual(checked["positive_atoms"], 33138)
        self.assertEqual(checked["labelled_simple_relation_subspaces"],
                         {"0": 1, "1": 968, "2": 147466, "3": 4277240})
        self.assertEqual(min(map(int, checked["empty_numerator_histogram"])), 21)

    def test_histogram_coverage_counts_are_exhaustive_compositions(self):
        for d in range(4):
            producer = set(explore.compositions(10, 1 << d))
            independent = set(verify.histograms(10, 1 << d))
            self.assertEqual(producer, independent)
            self.assertEqual(len(independent), comb(10 + (1 << d) - 1, (1 << d) - 1))
            self.assertEqual(set(explore.linear_permutations(d)),
                             set(verify.invertible_actions(d)))
        self.assertEqual([row["orbits"] for row in self.certificate["coverage"]], [1, 8, 32, 80])

    def test_missing_and_duplicated_types_rejected(self):
        missing = deepcopy(self.certificate)
        missing["cases"].pop()
        self.assertFalse(verify.verify_certificate(missing)["valid"])
        doubled = deepcopy(self.certificate)
        doubled["cases"].append(deepcopy(doubled["cases"][0]))
        self.assertFalse(verify.verify_certificate(doubled)["valid"])

    def test_false_tables_and_rebound_coordinates_rejected(self):
        for mutate in (
            lambda value: value.update(denominator=155),
            lambda value: value.update(width=True),
            lambda value: value["cases"][0]["masses"].__setitem__(0, True),
            lambda value: value["cases"][0]["masses"].__setitem__(0, 45),
            lambda value: value["cases"][0]["points"].__setitem__(0, 0),
            lambda value: value["cases"][0]["points"].__setitem__(0, value["cases"][0]["points"][1]),
            lambda value: value["cases"][-1]["relation_basis"].__setitem__(0, 1),
            lambda value: value["cases"][0].update(histogram_orbit_size=2),
            lambda value: value["coverage"][0].update(orbits=2),
        ):
            altered = deepcopy(self.certificate)
            mutate(altered)
            checked = verify.verify_certificate(altered)
            self.assertFalse(checked["valid"], checked)
        altered = deepcopy(self.certificate)
        altered["cases"][0]["masses"][0] -= 1
        altered["cases"][0]["masses"][1] += 1
        self.assertFalse(verify.verify_certificate(altered)["valid"])

    def test_coordinate_basis_change_preserves_the_certificate(self):
        transformed = deepcopy(self.certificate)
        for case in transformed["cases"]:
            case["points"] = [(point & ~3) | ((point & 1) << 1) | ((point & 2) >> 1)
                              for point in case["points"]]
        checked = verify.verify_certificate(transformed)
        self.assertTrue(checked["valid"], checked)

    def test_every_type_marginalizes_to_the_same_rank_moments(self):
        # Complete delete-one marginal checks for every type, not only samples.
        for case in self.certificate["cases"]:
            for removed in range(10):
                points = case["points"][:removed] + case["points"][removed + 1:]
                actual = []
                for atom in range(512):
                    low = atom & ((1 << removed) - 1)
                    high = (atom >> removed) << (removed + 1)
                    original = low | high
                    actual.append(case["masses"][original] +
                                  case["masses"][original | (1 << removed)])
                self.assertEqual(actual, verify.direct_masses(points))

    def test_low_rank_actual_codimension_two_distribution(self):
        # Independent genuine-code control, all651 kernels in F2^6.
        kernels = {
            frozenset(point for point in range(64)
                      if (point & a).bit_count() % 2 == 0 and
                      (point & b).bit_count() % 2 == 0)
            for a, b in combinations(range(1, 64), 2)
        }
        self.assertEqual(len(kernels), 651)
        for scope in ((1, 2, 4, 8, 16, 32), tuple(range(1, 11)),
                      (1, 2, 4, 8, 12, 16, 20, 24, 28, 32)):
            observed = [0] * (1 << len(scope))
            for kernel in kernels:
                atom = sum((point in kernel) << i for i, point in enumerate(scope))
                observed[atom] += 1
            self.assertEqual(observed, verify.direct_masses(scope))

    def test_analytic_coefficients_and_failure_at_next_level(self):
        self.assertEqual(verify.coefficient_controls(),
                         {"0": {"0": 46}, "1": {"3": -7, "5": -1},
                          "2": {"5": 1, "6": 1}, "3": {"6": -4, "7": -1}})
        controls = verify.negative_controls()
        self.assertEqual(controls["D5_ten_points"]["numerator"], -1)
        self.assertEqual(controls["D6_eleven_points"]["numerator"], -1)
        failed = controls["D6_eleven_points"]["points"]
        for index in range(len(failed)):
            self.assertGreaterEqual(min(verify.direct_masses(
                failed[:index] + failed[index + 1:])), 0)


if __name__ == "__main__":
    unittest.main()
