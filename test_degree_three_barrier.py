import importlib.util
import sys
import unittest
from fractions import Fraction
from itertools import combinations, product
from pathlib import Path

MODULE = Path(__file__).with_name("degree_three_barrier.py")
SPEC = importlib.util.spec_from_file_location("degree_three_barrier_audit", MODULE)
barrier = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = barrier
SPEC.loader.exec_module(barrier)


class DegreeThreeReductionTests(unittest.TestCase):
    def assert_all_selections(self, instance):
        for selection in range(1 << len(instance.columns)):
            direct = barrier.is_exact_cover(instance, selection)
            encoded = barrier.satisfies_coset_bound(instance, selection)
            self.assertEqual(direct, encoded, (instance.triples, selection))
            cover = barrier.decode_cover(instance, selection)
            self.assertEqual(cover is not None, direct)

    def test_every_two_by_two_by_two_matching_family(self):
        # All 256 allowed-triple families and all 6,561 contained selections.
        possible = tuple((a, 2 + b, 4 + c) for a, b, c in product(range(2), repeat=3))
        checks = yes = 0
        for family in range(1 << len(possible)):
            triples = [triple for i, triple in enumerate(possible) if family >> i & 1]
            instance = barrier.encode_exact_cover(6, triples)
            self.assert_all_selections(instance)
            checks += 1 << len(triples)
            yes += any(barrier.is_exact_cover(instance, selection)
                       for selection in range(1 << len(triples)))
        self.assertEqual(checks, 6561)
        self.assertEqual(yes, 175)

    def test_all_six_element_families_with_at_most_three_sets(self):
        # All 1,351 such families, not only tripartite hypergraphs.
        possible = tuple(combinations(range(6), 3))
        families = 0
        for size in range(4):
            for triples in combinations(possible, size):
                instance = barrier.encode_exact_cover(6, triples)
                self.assertTrue(all(column.bit_count() == 3 for column in instance.columns))
                self.assertEqual(instance.target, 63)
                self.assertEqual(instance.max_weight, 2)
                self.assert_all_selections(instance)
                families += 1
        self.assertEqual(families, 1351)

    def test_weight_bound_is_essential(self):
        # Every vertex occurs an odd number of times, but not exactly once.
        triples = ((0, 1, 2), (0, 1, 3), (0, 2, 4), (0, 3, 5),
                   (1, 2, 5), (1, 3, 4))
        instance = barrier.encode_exact_cover(6, triples)
        near_misses = [selection for selection in range(1 << len(triples))
                       if barrier.syndrome(instance, selection) == instance.target
                       and selection.bit_count() > instance.max_weight]
        self.assertTrue(near_misses)
        for selection in near_misses:
            self.assertFalse(barrier.is_exact_cover(instance, selection))
            self.assertFalse(barrier.satisfies_coset_bound(instance, selection))

    def test_homogeneous_target_would_accept_wrong_zero_witness(self):
        instance = barrier.encode_exact_cover(6, ((0, 1, 2), (0, 1, 3)))
        self.assertEqual(barrier.syndrome(instance, 0), 0)
        self.assertNotEqual(instance.target, 0)
        self.assertFalse(any(barrier.satisfies_coset_bound(instance, selection)
                             for selection in range(4)))

    def test_naive_append_target_homogenization_has_kernel_false_positive(self):
        cert = barrier.naive_homogenization_counterexample()
        self.assertFalse(cert["has_exact_cover"])
        self.assertEqual(cert["kernel_syndrome"], 0)
        self.assertEqual(cert["kernel_weight"], 2)
        self.assertLessEqual(cert["kernel_weight"], cert["naive_homogeneous_threshold"])
        self.assertEqual(cert["appended_target_weight"], 6)

    def test_duplicates_empty_universe_and_permuted_sets(self):
        duplicate = barrier.encode_exact_cover(6, ((2, 1, 0), (0, 1, 2), (5, 4, 3)))
        self.assertEqual(duplicate.triples, ((0, 1, 2), (0, 1, 2), (3, 4, 5)))
        self.assert_all_selections(duplicate)
        empty = barrier.encode_exact_cover(0, ())
        self.assertTrue(barrier.satisfies_coset_bound(empty, 0))
        self.assertEqual(barrier.decode_cover(empty, 0), ())
        self.assert_all_selections(barrier.encode_exact_cover(3, ()))

    def test_malformed_instances_and_selections(self):
        for universe_size in (-3, 1, 4, True, 6.0):
            with self.assertRaises(ValueError):
                barrier.encode_exact_cover(universe_size, ())
        for triples in (((0, 1),), ((0, 1, 1),), ((0, 1, 6),),
                        ((0, 1, -1),), ((0, 1, True),), ((0, 1, 2.0),)):
            with self.assertRaises(ValueError):
                barrier.encode_exact_cover(6, triples)
        instance = barrier.encode_exact_cover(3, ((0, 1, 2),))
        for selection in (-1, 2, True, 1.0):
            for function in (barrier.syndrome, barrier.is_exact_cover,
                             barrier.satisfies_coset_bound, barrier.decode_cover):
                with self.assertRaises(ValueError):
                    function(instance, selection)


class LocalParityRelaxationTests(unittest.TestCase):
    def test_rational_local_convex_mixtures(self):
        cert = barrier.extended_hamming_lp_counterexample()
        point = cert["point"]
        self.assertEqual(point[cert["pinned_one_coordinate"]], 1)
        self.assertEqual(sum(point), Fraction(5, 2))
        self.assertLessEqual(sum(point), cert["decision_upper_bound"])
        self.assertTrue(all(0 <= value <= 1 for value in point))
        for row, mixture in zip(cert["parity_check_rows"], cert["local_even_mixtures"]):
            self.assertEqual(sum(probability for probability, _ in mixture), 1)
            for probability, word in mixture:
                self.assertGreater(probability, 0)
                self.assertEqual(word & ~row, 0)
                self.assertEqual((word & row).bit_count() % 2, 0)
            for coordinate in range(cert["n"]):
                if row >> coordinate & 1:
                    marginal = sum(probability * (word >> coordinate & 1)
                                   for probability, word in mixture)
                    self.assertEqual(marginal, point[coordinate])

    def test_integer_distance_and_pinned_infeasibility(self):
        cert = barrier.extended_hamming_lp_counterexample()
        codewords = [word for word in range(1 << cert["n"])
                     if all((word & row).bit_count() % 2 == 0
                            for row in cert["parity_check_rows"])]
        self.assertEqual(len(codewords), 16)
        self.assertEqual(min(word.bit_count() for word in codewords if word), 4)
        witness = cert["weight_four_witness"]
        self.assertIn(witness, codewords)
        self.assertEqual(witness.bit_count(), 4)
        pinned = [word for word in codewords if word >> cert["pinned_one_coordinate"] & 1]
        self.assertTrue(pinned)
        self.assertEqual(min(word.bit_count() for word in pinned), 4)
        self.assertFalse(any(word.bit_count() <= cert["decision_upper_bound"] for word in pinned))

    def test_redundant_check_repairs_supplied_row_example(self):
        cert = barrier.extended_hamming_lp_counterexample()
        redundant = cert["redundant_check_cut"]
        self.assertEqual(redundant, sum(1 << i for i in (1, 2, 4, 7)))
        point = cert["point"]
        # The odd-set inequality for {7}: x_7 <= x_1+x_2+x_4.
        self.assertGreater(point[7], sum(point[i] for i in (1, 2, 4)))


if __name__ == "__main__":
    unittest.main()
