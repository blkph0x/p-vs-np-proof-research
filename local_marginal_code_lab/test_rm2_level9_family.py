"""Independent numerical controls for the all-dimension level-nine proof."""
import importlib.util
from pathlib import Path
import random
import unittest


_SPEC = importlib.util.spec_from_file_location(
    "_independent_level9_review", Path(__file__).with_name("review_rm2_level9_family.py"))
review = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(review)


class LevelNineFamilyTests(unittest.TestCase):
    def test_actual_155_subspace_distribution_on_five_bit_scopes(self):
        self.assertEqual(len(review.three_subspaces_five()), 155)
        rng = random.Random(202610210)
        scopes = [(), tuple(range(1, 8)), tuple(range(16, 25))]
        scopes += [tuple(rng.sample(range(1, 32), rng.randrange(10))) for _ in range(80)]
        for scope in scopes:
            with self.subTest(scope=scope):
                masses = review.mobius_table(scope)
                self.assertEqual(masses, review.actual_five_space_table(scope))
                review.verify_table(scope, masses)

    def test_six_fano_regression_corrects_empty_coefficient(self):
        scope = (1, 2, 3, 4, 5, 6, 8, 16, 32)
        self.assertEqual(review.binary_rank(scope), 6)
        counts = review.empty_atom_counts(scope)
        self.assertEqual(counts["zero_sum_quadruples"], 3)
        self.assertEqual(counts["closed_rank3_flats_by_size"].get(6), 1)
        self.assertEqual(counts["closed_rank3_flats_by_size"].get(5, 0), 0)
        self.assertEqual(counts["empty_numerator_formula"], 6)
        self.assertEqual(review.mobius_table(scope)[0], 6)
        # The draft's -6*N6 coefficient would give5, so this catches that error.
        self.assertNotEqual(review.mobius_table(scope)[0], 8 + 3 - 6)
        review.verify_table(scope, review.mobius_table(scope))

    def test_seven_fano_and_independent_extremes(self):
        seven = (1, 2, 3, 4, 5, 6, 7, 8, 16)
        counts = review.empty_atom_counts(seven)
        self.assertEqual(review.binary_rank(seven), 5)
        self.assertEqual(counts["closed_rank3_flats_by_size"].get(7), 1)
        self.assertEqual(counts["zero_sum_quadruples"], 7)
        self.assertEqual(review.mobius_table(seven)[0], 0)
        independent = tuple(1 << i for i in range(9))
        self.assertEqual(review.mobius_table(independent)[0], 8)
        self.assertEqual(len(review.quadratic_projection_support(independent)), 512)

    def test_every_proper_marginal_of_curated_scopes(self):
        for name, scope in review.named_scopes().items():
            with self.subTest(name=name):
                masses = review.mobius_table(scope)
                review.verify_table(scope, masses)
                self.assertEqual(review.verify_all_marginals(scope, masses), (1 << len(scope)) - 1)

    def test_coordinate_order_and_wide_linear_embedding(self):
        scope = (1, 2, 3, 4, 5, 6, 8, 16, 32)
        embedded = tuple(sum(((point >> bit) & 1) << (17 * bit + 11)
                             for bit in range(6)) for point in scope)
        self.assertEqual(review.mobius_table(scope), review.mobius_table(embedded))
        self.assertEqual(review.quadratic_projection_support(scope),
                         review.quadratic_projection_support(embedded))
        permutation = (8, 0, 6, 2, 1, 7, 3, 5, 4)
        permuted = tuple(scope[i] for i in permutation)
        masses = review.mobius_table(scope)
        other = review.mobius_table(permuted)
        for word, value in enumerate(masses):
            reordered = sum(((word >> old) & 1) << new for new, old in enumerate(permutation))
            self.assertEqual(value, other[reordered])

    def test_nonclosed_atoms_and_rank_two_quotient_formula(self):
        scope = (1, 2, 3, 4, 5, 6, 8, 16, 32)
        masses = review.mobius_table(scope)
        # {1,2} is not closed because its span also contains3.
        self.assertEqual(masses[3], 0)
        # {1,2,3} is a closed rank-two flat; outside points occupy four cosets.
        self.assertEqual(masses[7], 3)
        review.verify_table(scope, masses)

    def test_reject_mutations_and_malformed_inputs(self):
        scope = tuple(range(16, 25))
        masses = review.mobius_table(scope)
        changed = masses[:]
        source = next(i for i, value in enumerate(changed) if value > 0)
        changed[source] -= 1
        changed[source ^ 1] += 1
        with self.assertRaises(ValueError):
            review.verify_table(scope, changed)
        for bad in ([0], [1, 1], [True], [-1], [1.0], list(range(1, 11))):
            with self.subTest(scope=bad), self.assertRaises(ValueError):
                review.mobius_table(bad)
        with self.assertRaises(ValueError):
            review.verify_table(scope, masses[:-1])
        changed = masses[:]
        changed[0] = True
        with self.assertRaises(ValueError):
            review.verify_table(scope, changed)

    def test_reproducible_bounded_review(self):
        result = review.run_review()
        self.assertEqual(result["status"], "PASS")
        self.assertEqual(result["counts"]["scope_cases"], 168)
        self.assertEqual(result["counts"]["high_rank_nine_scopes"], 100)
        self.assertFalse(result["all_nine_point_types_enumerated"])


if __name__ == "__main__":
    unittest.main()
