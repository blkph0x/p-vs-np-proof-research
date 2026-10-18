"""Independent SAT evaluation, edge-subset oracles and witness mutations."""
from copy import deepcopy
from itertools import combinations, combinations_with_replacement, product
import json
import unittest

import clause_bounds as cb


def edge_subset_matchings(vertices, edges):
    if vertices > 8:
        raise ValueError("edge-subset oracle limited to eight vertices")
    for selected in combinations(range(len(edges)), vertices // 2):
        endpoints = [v for i in selected for v in edges[i]]
        if sorted(endpoints) == list(range(vertices)):
            yield selected


def direct_sat(n, clauses):
    answers = set()
    for bits in product((False, True), repeat=n):
        if all(any(bits[abs(lit) - 1] if lit > 0 else not bits[abs(lit) - 1]
                   for lit in clause) for clause in clauses):
            answers.add(sum(int(bit) << i for i, bit in enumerate(bits)))
    return answers


class ClauseBoundTests(unittest.TestCase):
    def test_single_cycle_has_exactly_two_truth_matchings(self):
        instance = cb.build_instance(1, [])
        self.assertEqual(list(edge_subset_matchings(4, instance["edges"])), [(0, 2), (1, 3)])
        self.assertEqual(cb.assignment_matching(instance, 0), [0, 2])
        self.assertEqual(cb.assignment_matching(instance, 1), [1, 3])

    def test_exhaustive_raw_two_variable_clause_pairs(self):
        # Includes duplicates, opposite literals, empty clauses, and repeated clauses.
        pool = [list(c) for length in range(3) for c in product((1, -1, 2, -2), repeat=length)]
        cases = 0
        for first, second in combinations_with_replacement(pool, 2):
            clauses = [first, second]
            instance = cb.build_instance(2, clauses)
            accepted = set()
            for matching in edge_subset_matchings(8, instance["edges"]):
                actual_costs = [sum(row[i] for i in matching) for row in instance["costs"]]
                if all(value <= cap for value, cap in zip(actual_costs, instance["bounds"])):
                    accepted.add(int(1 in matching) | (int(5 in matching) << 1))
                checked = cb.check_instance_matching(instance, list(matching))
                self.assertEqual(checked["costs"], actual_costs)
            self.assertEqual(accepted, direct_sat(2, clauses))
            cases += 1
        self.assertEqual(cases, 231)

    def test_ternary_unsat_and_scalar_sum_false_positive(self):
        clauses = [list(c) for c in product((1, -1), (2, -2), (3, -3))]
        instance = cb.build_instance(3, clauses)
        self.assertEqual(direct_sat(3, clauses), set())
        for assignment in range(8):
            result = cb.check_instance_matching(instance, cb.assignment_matching(instance, assignment))
            self.assertFalse(result["valid"])
            self.assertEqual(len(result["violated_bounds"]), 1)
            self.assertEqual(sorted(result["costs"]), [0, 1, 1, 1, 2, 2, 2, 3])
            self.assertEqual(sum(result["costs"]), 12)
            self.assertEqual(sum(instance["bounds"]), 16)

    def test_normalization_signs_and_nonnegative_bounded_numbers(self):
        clauses = [[1, 1, 1], [1, -1, 2], [-2, -2], [1, 2, -3]]
        instance = cb.build_instance(3, clauses)
        self.assertEqual(instance["normalization"]["clauses"], [[1], [-2], [1, 2, -3]])
        self.assertEqual(instance["normalization"]["original_indices"], [0, 2, 3])
        self.assertEqual(instance["normalization"]["dropped_tautologies"], [1])
        self.assertTrue(all(weight in (0, 1) for row in instance["costs"] for weight in row))
        self.assertEqual(instance["bounds"], [0, 0, 2])
        self.assertEqual(cb.audit_formula(3, clauses)["accepted_assignments"], sorted(direct_sat(3, clauses)))

    def test_empty_formula_and_empty_clause(self):
        yes = cb.build_instance(0, [])
        self.assertEqual((yes["vertex_count"], yes["edges"], yes["costs"]), (0, [], []))
        self.assertTrue(cb.check_instance_matching(yes, [])["valid"])
        no = cb.build_instance(0, [[]])
        self.assertEqual(no["vertex_count"], 4)
        self.assertEqual(no["costs"], [[1, 1, 1, 1]])
        self.assertEqual(no["bounds"], [1])
        for dummy in (0, 1):
            checked = cb.check_instance_matching(no, cb.assignment_matching(no, 0, dummy_value=dummy))
            self.assertTrue(checked["perfect_matching"])
            self.assertFalse(checked["valid"])
            self.assertEqual(checked["costs"], [2])
        self.assertEqual(cb.audit_formula(0, [[]])["accepted_assignments"], [])

    def test_witness_mutations_and_original_objective_binding(self):
        instance = cb.build_instance(2, [[1], [-2]])
        good = cb.assignment_matching(instance, 1)
        self.assertTrue(cb.check_instance_matching(instance, good)["valid"])
        for bad in (good[:-1], good + [good[0]], [True] + good[1:], [-1] + good[1:], [8] + good[1:]):
            self.assertFalse(cb.check_instance_matching(instance, bad)["valid"])
        wrong_assignment = cb.assignment_matching(instance, 0)
        self.assertFalse(cb.check_instance_matching(instance, wrong_assignment)["valid"])
        relaxed = deepcopy(instance)
        relaxed["bounds"][0] = 1
        self.assertTrue(cb.check_instance_matching(relaxed, wrong_assignment)["valid"])
        self.assertFalse(cb.check_instance_matching(instance, wrong_assignment)["valid"])
        # A verifier verifies its supplied original instance; a modified instance is a different request.

    def test_input_and_budget_rejections(self):
        for n, clauses in ((True, []), (-1, []), (1, [[True]]), (1, [[0]]), (1, [[2]]), (1, [None])):
            with self.assertRaises(ValueError):
                cb.build_instance(n, clauses)
        instance = cb.build_instance(1, [[1]])
        for assignment in (True, -1, 2):
            with self.assertRaises(ValueError):
                cb.assignment_matching(instance, assignment)
        for key, value in (("bounds", [True]), ("bounds", [-1]), ("costs", [[0]]),
                           ("costs", [[0, 0, 0, True]]), ("costs", [[0, 0, 0, -1]])):
            malformed = deepcopy(instance)
            malformed[key] = value
            self.assertFalse(cb.check_instance_matching(malformed, [1, 3])["valid"])
        with self.assertRaises(ValueError):
            cb.audit_formula(1000000, [], max_assignments=4096)
        with self.assertRaises(ValueError):
            cb.oracle_perfect_matchings(4, instance["edges"], max_matchings=1)
        with self.assertRaises(ValueError):
            cb.oracle_perfect_matchings(28, [], max_vertices=24)

    def test_json_roundtrip_exact_costs_and_large_integer_checker(self):
        instance = cb.build_instance(3, [[1, 2, 3], [-1, 2]])
        replay = json.loads(json.dumps(instance))
        for assignment in range(8):
            witness = cb.assignment_matching(instance, assignment)
            self.assertEqual(cb.check_instance_matching(instance, witness), cb.check_instance_matching(replay, witness))
        huge = 1 << 15000
        self.assertTrue(cb.verify_bounded_matching(2, [[0, 1]], [[huge]], [huge], [0])["valid"])
        self.assertFalse(cb.verify_bounded_matching(2, [[0, 1]], [[huge]], [huge - 1], [0])["valid"])


if __name__ == "__main__":
    unittest.main()
