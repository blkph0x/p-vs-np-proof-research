"""Independent finite-code and affine-coset checks for the bounded solver."""
from itertools import combinations
from math import comb
import unittest

from deletion_solver import (choose_deletion, conditioned_width_profile,
                             minimum_distance, parity_check)


def all_small_codes(n):
    """Enumerate subspaces by set closure, without GF(2) elimination."""
    spaces = {frozenset({0})}
    for vector in range(1, 1 << n):
        for space in tuple(spaces):
            if vector not in space:
                spaces.add(space | frozenset(word ^ vector for word in space))
    for code in sorted(spaces, key=lambda words: (len(words), sorted(words))):
        rows, span = [], {0}
        for word in sorted(code):
            if word not in span:
                rows.append(word)
                span |= {other ^ word for other in tuple(span)}
        yield tuple(rows), code


def coordinate_subsets(n):
    for size in range(n + 1):
        yield from combinations(range(n), size)


def assignment_number(word, deleted):
    return sum(((word >> coordinate) & 1) << i
               for i, coordinate in enumerate(deleted))


def brute_best(words):
    return min(((word.bit_count(), word) for word in words if word), default=None)


def brute_coset_profiles(code, deleted, order):
    """Count extension-equivalence classes directly from complete codewords."""
    remaining = [j for j in order if j not in deleted]
    cosets = {}
    for word in code:
        cosets.setdefault(assignment_number(word, deleted), []).append(word)
    profiles = []
    for words in cosets.values():
        counts = []
        for split in range(len(remaining) + 1):
            prefix_mask = sum(1 << j for j in remaining[:split])
            suffix_mask = sum(1 << j for j in remaining[split:])
            extensions = {}
            for word in words:
                extensions.setdefault(word & prefix_mask, set()).add(word & suffix_mask)
            counts.append(len({frozenset(values) for values in extensions.values()}))
        profiles.append(counts)
    return profiles


class DeletionSolverTest(unittest.TestCase):
    def assert_exact(self, result, code):
        expected = brute_best(code)
        self.assertEqual(result['status'], 'EXACT')
        self.assertIsNone(result['reason'])
        self.assertEqual(result['distance'], expected[0] if expected else None)
        self.assertEqual(result['upper_bound'], result['distance'])
        if expected is None:
            self.assertIsNone(result['word'])
        else:
            self.assertIn(result['word'], code)
            self.assertNotEqual(result['word'], 0)
            self.assertEqual(result['word'].bit_count(), expected[0])

    def test_every_code_through_four_coordinates_and_every_deletion(self):
        checked = 0
        for n in range(5):
            for rows, code in all_small_codes(n):
                for deleted in coordinate_subsets(n):
                    order = tuple(reversed(range(n)))
                    result = minimum_distance(rows, n, deleted=deleted, order=order)
                    with self.subTest(n=n, rows=rows, deleted=deleted):
                        self.assert_exact(result, code)
                        self.assertEqual(result['dimension'], len(code).bit_length() - 1)
                        self.assertEqual(result['branches_completed'], 1 << len(deleted))
                        self.assertEqual(result['branches_feasible'], len({
                            assignment_number(word, deleted) for word in code}))
                    checked += 1
        self.assertEqual(checked, 1225)

    def test_partial_branch_upper_bounds_match_independent_cosets(self):
        for n in range(4):
            for rows, code in all_small_codes(n):
                for natural_deleted in coordinate_subsets(n):
                    deleted = tuple(reversed(natural_deleted))
                    for limit in range(1 << len(deleted)):
                        result = minimum_distance(rows, n, deleted=deleted,
                                                  max_branches=limit)
                        expected = brute_best(word for word in code
                                              if assignment_number(word, deleted) < limit)
                        with self.subTest(n=n, rows=rows, deleted=deleted, limit=limit):
                            self.assertEqual(result['status'], 'UNKNOWN')
                            self.assertEqual(result['reason'], 'BRANCH_LIMIT')
                            self.assertIsNone(result['distance'])
                            self.assertEqual(result['upper_bound'], expected[0] if expected else None)
                            self.assertEqual(result['branches_completed'], limit)
                            if expected:
                                self.assertIn(result['word'], code)
                                self.assertLess(assignment_number(result['word'], deleted), limit)
                                self.assertEqual(result['word'].bit_count(), expected[0])
                            else:
                                self.assertIsNone(result['word'])

    def test_profile_matches_independent_extension_classes_and_actual_peak(self):
        for rows, code in all_small_codes(4):
            order = (2, 0, 3, 1)
            original_counts = brute_coset_profiles(code, (), order)[0]
            original_peak = max(original_counts)
            original_width = original_peak.bit_length() - 1
            for deleted in coordinate_subsets(4):
                expected = brute_coset_profiles(code, deleted, order)
                profile = conditioned_width_profile(rows, 4, deleted, order)
                result = minimum_distance(rows, 4, deleted=deleted, order=order)
                with self.subTest(rows=rows, deleted=deleted):
                    self.assertTrue(all(counts == expected[0] for counts in expected))
                    self.assertEqual([1 << width for width in profile['profile']], expected[0])
                    self.assertEqual(profile['peak_syndrome_states'], max(expected[0]))
                    self.assertEqual(result['peak_syndrome_states'], max(expected[0]))
                    self.assertLessEqual(result['peak_dp_entries'], 2 * max(expected[0]))
                    self.assertEqual(result['sum_layer_syndrome_states'],
                                     len(expected) * sum(expected[0]))
                    # The feasible fixed assignments form a q-dimensional projection.
                    # Conditioning can reduce this fixed-order width by at most q.
                    projection_dimension = len(expected).bit_length() - 1
                    residual_width = profile['width']
                    self.assertEqual(len(expected), 1 << projection_dimension)
                    self.assertLessEqual(original_width - projection_dimension, residual_width)
                    self.assertLessEqual(residual_width, original_width)
                    self.assertGreaterEqual(len(expected) * max(expected[0]), original_peak)

    def test_zero_code_empty_code_full_space_and_dependent_rows(self):
        cases = [((), 0, {0}), ((0, 0), 0, {0}), ((), 4, {0}),
                 ((0, 0), 4, {0}), ((1, 2, 4), 3, set(range(8))),
                 ((3, 3, 0), 2, {0, 3}), ((3, 5, 6, 0), 3, {0, 3, 5, 6})]
        for rows, n, code in cases:
            for deleted in [(), tuple(range(n))]:
                with self.subTest(rows=rows, n=n, deleted=deleted):
                    self.assert_exact(minimum_distance(rows, n, deleted=deleted), code)

    def test_fixed_coordinate_weight_and_supported_word_are_preserved(self):
        # Freely puncturing coordinate 0 would incorrectly lower distance to 1.
        result = minimum_distance((3,), 2, deleted=(0,))
        self.assert_exact(result, {0, 3})
        self.assertEqual(result['distance'], 2)
        # A nonzero word entirely inside the fixed coordinates must not disappear.
        result = minimum_distance((1, 6), 3, deleted=(0,))
        self.assert_exact(result, {0, 1, 6, 7})
        self.assertEqual(result['word'], 1)

    def test_all_deleted_needs_no_transitions_and_filters_infeasible_assignments(self):
        result = minimum_distance((5,), 3, deleted=(2, 0, 1), max_transitions=0)
        self.assert_exact(result, {0, 5})
        self.assertEqual(result['transitions'], 0)
        self.assertEqual(result['branches_completed'], 8)
        self.assertEqual(result['branches_feasible'], 2)

    def test_exact_transition_budget_boundary(self):
        rows, n, deleted = (3, 12), 4, (0,)
        complete = minimum_distance(rows, n, deleted=deleted)
        used = complete['transitions']
        self.assertGreater(used, 0)
        at_limit = minimum_distance(rows, n, deleted=deleted, max_transitions=used)
        self.assert_exact(at_limit, {0, 3, 12, 15})
        interrupted = minimum_distance(rows, n, deleted=deleted, max_transitions=used - 1)
        self.assertEqual(interrupted['status'], 'UNKNOWN')
        self.assertEqual(interrupted['reason'], 'TRANSITION_LIMIT')
        self.assertIsNone(interrupted['distance'])
        self.assertEqual(interrupted['transitions'], used - 1)

    def test_partial_witness_is_only_an_upper_bound(self):
        # Branch b=0 has minimum 2, while the unvisited b=1 branch has minimum 1.
        limited = minimum_distance((3, 4), 3, deleted=(2,), max_branches=1)
        self.assertEqual(limited['status'], 'UNKNOWN')
        self.assertIsNone(limited['distance'])
        self.assertEqual((limited['upper_bound'], limited['word']), (2, 3))
        interrupted = minimum_distance((3, 4), 3, deleted=(2,),
                                       max_transitions=limited['transitions'])
        self.assertEqual(interrupted['reason'], 'TRANSITION_LIMIT')
        self.assertEqual((interrupted['upper_bound'], interrupted['word']), (2, 3))
        self.assert_exact(minimum_distance((3, 4), 3, deleted=(2,)), {0, 3, 4, 7})

    def test_no_budget_reports_no_completed_witness(self):
        for kwargs, reason in [({'max_branches': 0}, 'BRANCH_LIMIT'),
                               ({'max_transitions': 0}, 'TRANSITION_LIMIT')]:
            result = minimum_distance((3,), 2, **kwargs)
            self.assertEqual(result['status'], 'UNKNOWN')
            self.assertEqual(result['reason'], reason)
            self.assertIsNone(result['distance'])
            self.assertIsNone(result['upper_bound'])
            self.assertIsNone(result['word'])

    def test_chooser_scores_match_independent_profiles(self):
        order = (2, 0, 3, 1)
        for rows, code in all_small_codes(4):
            for count in range(5):
                scores = []
                for deleted in combinations(range(4), count):
                    counts = brute_coset_profiles(code, deleted, order)[0]
                    scores.append((max(counts), sum(counts), deleted))
                expected = min(scores)[2]
                result = choose_deletion(rows, 4, count, order=order)
                with self.subTest(rows=rows, count=count):
                    self.assertEqual(result['status'], 'COMPLETE')
                    self.assertEqual(result['deleted'], list(expected))
                    self.assertEqual(result['candidates_evaluated'], comb(4, count))
                    self.assertEqual(result['rank_evaluations'],
                                     comb(4, count) * (2 * (4 - count + 1) + 1))

    def test_chooser_limits_and_exact_candidate_boundary(self):
        for limit in range(8):
            result = choose_deletion((3, 12), 4, 2, max_candidates=limit)
            self.assertEqual(result['status'], 'COMPLETE' if limit >= 6 else 'CANDIDATE_LIMIT')
            self.assertEqual(result['candidates_evaluated'], min(limit, 6))
            if not limit:
                self.assertIsNone(result['deleted'])
                self.assertIsNone(result['selected_profile'])
            else:
                self.assertIn(tuple(result['deleted']), list(combinations(range(4), 2))[:limit])
        result = choose_deletion((), 0, 0)
        self.assertEqual(result['status'], 'COMPLETE')
        self.assertEqual(result['deleted'], [])

    def test_invalid_inputs_are_rejected(self):
        functions = [minimum_distance, conditioned_width_profile, choose_deletion, parity_check]
        for function in functions:
            for rows, n in [((1,), -1), ((1,), True), ((1,), 1.0),
                            ((-1,), 3), ((8,), 3), ((True,), 3), ((1.5,), 3)]:
                with self.subTest(function=function.__name__, rows=rows, n=n):
                    with self.assertRaises(ValueError):
                        function(rows, n)
        for function in [minimum_distance, conditioned_width_profile]:
            for deleted in [(0, 0), (-1,), (3,), (True,), (1.5,)]:
                with self.assertRaises(ValueError):
                    function((3,), 3, deleted=deleted)
        for function in [minimum_distance, conditioned_width_profile, choose_deletion]:
            for order in [(0, 1), (0, 0, 2), (0, 1, 3), (0, 1, True)]:
                with self.assertRaises(ValueError):
                    function((3,), 3, order=order)
        for key in ['max_transitions', 'max_branches']:
            for value in [-1, True, 1.5]:
                with self.assertRaises(ValueError):
                    minimum_distance((3,), 3, **{key: value})
        for kwargs in [{'delete_count': -1}, {'delete_count': 4},
                       {'delete_count': True}, {'max_candidates': -1},
                       {'max_candidates': True}, {'max_candidates': 1.5}]:
            with self.assertRaises(ValueError):
                choose_deletion((3,), 3, **kwargs)


if __name__ == '__main__':
    unittest.main()
