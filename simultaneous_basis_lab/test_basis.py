import copy
from fractions import Fraction
import random
import unittest

import basis as b


def monomial_formula(terms):
    result = {}
    for letters, coefficient in terms.items():
        result[tuple(letters.count(letter) for letter in b.VARIABLES)] = coefficient
    return result


class BasisTests(unittest.TestCase):
    def test_edge_specific_eq3_or3_obstruction_certificate(self):
        certificate = b.edge_specific_or3_certificate()
        self.assertTrue(b.verify_edge_specific_or3_certificate(certificate))
        slack = b.edge_specific_slack_certificate()
        self.assertTrue(b.verify_edge_specific_slack_certificate(slack))
        self.assertNotEqual(certificate["clause_equations"], slack["clause_equations"])
        self.assertEqual(b.edge_eq3_parity_support_patterns(0), [[15, 15, 15]])
        self.assertEqual(b.edge_eq3_parity_support_patterns(1), [[15, 15, 15]])
        for parity in ("even", "odd"):
            changed = copy.deepcopy(certificate)
            changed["identities"][parity][-1] += 1
            self.assertFalse(b.verify_edge_specific_or3_certificate(changed))
        for gate in ("OR3", "SLACK3"):
            global_certificate = b.edge_specific_global_certificate(gate)
            self.assertEqual(len(global_certificate["cases"]), 8)
            self.assertTrue(b.verify_edge_specific_global_certificate(global_certificate))
            changed = copy.deepcopy(global_certificate)
            changed["cases"]["000"]["even"]["identity"][-1] += 1
            self.assertFalse(b.verify_edge_specific_global_certificate(changed))

    def test_eq3_clause_family_classifier(self):
        # The classifier is an exact consequence of the reduced EQ3 family:
        # rho=1 gives palindromic/anti-palindromic clauses, while primitive
        # cube roots leave only EQ3 and its output-complement form.
        self.assertEqual(
            b.common_eq3_parity_branches((0, 1, 1, 0)),
            [{"rho": "one", "eq_support_parity": 0, "clause_support_parity": 0},
             {"rho": "one", "eq_support_parity": 1, "clause_support_parity": 1}],
        )
        self.assertEqual(b.common_eq3_parity_branches(b.EQ3), [
            {"rho": "one", "eq_support_parity": 0, "clause_support_parity": 0},
            {"rho": "one", "eq_support_parity": 1, "clause_support_parity": 1},
            {"rho": "primitive", "eq_support_parity": 0, "clause_support_parity": 0},
            {"rho": "primitive", "eq_support_parity": 1, "clause_support_parity": 1},
        ])
        self.assertEqual(b.common_eq3_parity_branches((0, 1, -1, 0)), [
            {"rho": "one", "eq_support_parity": 0, "clause_support_parity": 1},
            {"rho": "one", "eq_support_parity": 1, "clause_support_parity": 0},
        ])
        self.assertEqual(b.common_eq3_parity_branches(b.OR3), [])
        self.assertEqual(b.common_eq3_parity_branches(b.SLACK3), [])

    def test_classifier_exhaustive_small_integer_signatures(self):
        # Recompute the four reduced parity conditions directly over all
        # signatures in {-1,0,1}^4.  This independently exercises the
        # palindromic and primitive-root branches without a numerical root.
        for f0 in (-1, 0, 1):
            for f1 in (-1, 0, 1):
                for f2 in (-1, 0, 1):
                    for f3 in (-1, 0, 1):
                        f = (f0, f1, f2, f3)
                        branches = b.common_eq3_parity_branches(f)
                        expected = []
                        if f0 == f3 and f1 == f2:
                            expected += [("one", 0, 0), ("one", 1, 1)]
                        if f0 == -f3 and f1 == -f2:
                            expected += [("one", 0, 1), ("one", 1, 0)]
                        if f1 == 0 and f2 == 0 and f0 == f3:
                            expected += [("primitive", 0, 0), ("primitive", 1, 1)]
                        if f1 == 0 and f2 == 0 and f0 == -f3:
                            expected += [("primitive", 0, 1), ("primitive", 1, 0)]
                        actual = [(x["rho"], x["eq_support_parity"],
                                  x["clause_support_parity"]) for x in branches]
                        self.assertEqual(actual, list(dict.fromkeys(expected)), f)

    def test_palindromic_family_direct_hadamard_transform(self):
        # Every palindromic clause is even-supported with the rho=1 basis;
        # its column swap is the corresponding odd branch.
        H = ((1, 1), (1, -1))
        for signature in ((2, -3, -3, 2), (1, 4, 4, 1), (0, 1, 1, 0)):
            transformed = b.transform(signature, b.inverse2(H), "column")
            self.assertEqual(b.support_parities(transformed), [0])
            swapped = ((H[0][1], H[0][0]), (H[1][1], H[1][0]))
            transformed_swapped = b.transform(signature, b.inverse2(swapped), "column")
            self.assertEqual(b.support_parities(transformed_swapped), [1])

    def test_full_polynomial_equations(self):
        # Independently transcribed formulas from THEOREM.md.
        expected = {
            "EQ3": [
                {"aaa": 1, "ccc": 1}, {"aab": 1, "ccd": 1},
                {"abb": 1, "cdd": 1}, {"bbb": 1, "ddd": 1}],
            "OR3": [
                {"bbb": -1, "bbd": 3, "bdd": -3},
                {"abb": 1, "abd": -2, "add": 1, "bbc": -1, "bcd": 2},
                {"aab": -1, "aad": 1, "abc": 2, "acd": -2, "bcc": -1},
                {"aaa": 1, "aac": -3, "acc": 3}],
            "SLACK3": [
                {"bbb": -1, "bbd": 6, "bdd": -3},
                {"abb": 1, "abd": -4, "add": 1, "bbc": -2, "bcd": 2},
                {"aab": -1, "aad": 2, "abc": 4, "acd": -2, "bcc": -1},
                {"aaa": 1, "aac": -6, "acc": 3}],
        }
        for name, signature, orientation in (("EQ3", b.EQ3, "row"),
                                             ("OR3", b.OR3, "adj_column"),
                                             ("SLACK3", b.SLACK3, "adj_column")):
            self.assertEqual(b.symbolic_entries(signature, orientation),
                             [monomial_formula(terms) for terms in expected[name]])

    def test_all_eight_branches(self):
        systems = b.equation_systems()
        self.assertEqual(len(systems), 8)
        self.assertEqual({(s["gate"], s["eq_support_parity"], s["clause_support_parity"])
                          for s in systems},
                         {(g, p, q) for g in ("OR3", "SLACK3") for p in (0, 1) for q in (0, 1)})
        for system in systems:
            self.assertEqual(len(system["equations"]), 5)
            determinant_equation = b.pdeserialize(system["equations"][-1])
            self.assertEqual(determinant_equation, monomial_formula({"adu": 1, "bcu": -1, "": -1}))

    def test_bezout_identities_and_binding(self):
        certificate = b.obstruction_certificate()
        self.assertTrue(b.verify_obstruction(certificate))
        for index in range(4):
            changed = copy.deepcopy(certificate)
            changed["bezout"][index]["A"][0] += 1
            self.assertFalse(b.verify_obstruction(changed))
        changed = copy.deepcopy(certificate)
        changed["bezout"][0]["p"] = [1]
        changed["bezout"][0]["A"] = [1]
        changed["bezout"][0]["B"] = []
        changed["bezout"][0]["K"] = 1
        self.assertFalse(b.verify_obstruction(changed))  # Valid unrelated identity is insufficient.

    def test_certificate_metadata_and_coverage_mutations(self):
        certificate = b.obstruction_certificate()
        mutations = []
        changed = copy.deepcopy(certificate)
        changed["bezout"].pop()
        mutations.append(changed)
        changed = copy.deepcopy(certificate)
        changed["bezout"][0] = changed["bezout"][1]
        mutations.append(changed)
        changed = copy.deepcopy(certificate)
        changed["equation_systems"].pop()
        mutations.append(changed)
        changed = copy.deepcopy(certificate)
        changed["field"] = "all finite fields"
        mutations.append(changed)
        changed = copy.deepcopy(certificate)
        changed["reduced_entries"]["OR3"][0][0] += 1
        mutations.append(changed)
        changed = copy.deepcopy(certificate)
        changed["bezout"][0]["K"] = 0
        mutations.append(changed)
        self.assertTrue(all(not b.verify_obstruction(c) for c in mutations))

    def test_normal_form_reduction(self):
        reduced = b.obstruction_certificate()["reduced_entries"]
        self.assertEqual(reduced["EQ3"], [[2], [], [0, 2], []])
        self.assertEqual(reduced["OR3"], [[-1, -3, -3], [1, 1, -1], [1, 1, -1], [1, 3, -3]])
        self.assertEqual(reduced["SLACK3"], [[-1, -3, -6], [2, 1, -1], [1, 2, -1], [1, 3, -6]])

    def test_symbolic_against_200_exact_rational_transforms(self):
        rng = random.Random(2026101803)
        checked = 0
        while checked < 200:
            a, b_, c, d = [Fraction(rng.randint(-4, 4), rng.randint(1, 4)) for _ in range(4)]
            determinant = a * d - b_ * c
            if not determinant:
                continue
            matrix = ((a, b_), (c, d))
            values = (a, b_, c, d, 1 / determinant)
            for signature, orientation in ((b.EQ3, "row"), (b.OR3, "adj_column"), (b.SLACK3, "adj_column")):
                symbolic = [b.peval(p, values) for p in b.symbolic_entries(signature, orientation)]
                tensor = b.transform(signature, matrix if orientation == "row" else b.inverse2(matrix),
                                     "row" if orientation == "row" else "column")
                numerical = b.symmetric_table(tensor)
                if orientation == "adj_column":
                    numerical = [entry * determinant ** 3 for entry in numerical]
                self.assertEqual(symbolic, numerical)
            checked += 1

    def test_hadamard_genuine_shared_positive_controls(self):
        controls = b.positive_controls()
        expected = ([2, 0, 2, 0], [Fraction(1, 4), 0, Fraction(1, 4), 0],
                    [Fraction(3, 4), 0, Fraction(-1, 4), 0])
        for control, signature in zip(controls[:3], expected):
            self.assertEqual(control["symmetric_transformed"], signature)
            self.assertEqual(control["transformed"], b.matching_signature(control["graph"]))
            self.assertEqual(b.support_parities(control["transformed"]), [0])

    def test_individual_clause_success_does_not_imply_common_success(self):
        controls = b.positive_controls()[3:]
        self.assertEqual(controls[0]["symmetric_transformed"], [0, 1, 0, Fraction(1, 4)])
        self.assertEqual(controls[1]["symmetric_transformed"], [0, 1, 0, -2])
        for control in controls:
            self.assertEqual(b.support_parities(control["transformed"]), [1])
            self.assertEqual(b.support_parities(control["eq3_row_under_same_basis"]), [0, 1])

    def test_column_swap_flips_output_parity(self):
        matrix = ((Fraction(2), Fraction(3)), (Fraction(2), Fraction(-3)))
        swapped = tuple((row[1], row[0]) for row in matrix)
        row = b.transform(b.EQ3, matrix, "row")
        row_swapped = b.transform(b.EQ3, swapped, "row")
        self.assertEqual(row_swapped, list(reversed(row)))
        self.assertEqual(b.support_parities(row), [0])
        self.assertEqual(b.support_parities(row_swapped), [1])
        for signature in (b.OR3, b.SLACK3):
            column = b.transform(signature, b.inverse2(matrix), "column")
            column_swapped = b.transform(signature, b.inverse2(swapped), "column")
            self.assertEqual(column_swapped, list(reversed(column)))
            self.assertEqual(b.support_parities(column), [0, 1])

    def test_nonzero_diagonal_scaling_preserves_support(self):
        matrix = ((1, 1), (1, -1))
        scaled = ((Fraction(2, 3), Fraction(-7, 5)), (Fraction(2, 3), Fraction(7, 5)))
        for signature in (b.EQ3, b.OR3, b.SLACK3):
            for orientation in ("row", "column"):
                original = b.transform(signature, matrix if orientation == "row" else b.inverse2(matrix), orientation)
                changed = b.transform(signature, scaled if orientation == "row" else b.inverse2(scaled), orientation)
                self.assertEqual([bool(x) for x in original], [bool(x) for x in changed])

    def test_inverse_and_singular_rejection(self):
        self.assertEqual(b.inverse2(((1, 1), (1, -1))),
                         ((Fraction(1, 2), Fraction(1, 2)), (Fraction(1, 2), Fraction(-1, 2))))
        with self.assertRaises(ValueError):
            b.inverse2(((1, 2), (2, 4)))
        with self.assertRaises(ValueError):
            b.inverse2(((1,), (2,)))

    def test_saved_symmetric_clause_classification(self):
        import json
        from pathlib import Path
        saved = json.loads((Path(__file__).resolve().parent / "RESULTS.json").read_text())
        classification = saved["symmetric_clause_classification"]
        self.assertEqual(classification["OR3"], [])
        self.assertEqual(classification["SLACK3"], [])
        self.assertEqual(classification["NAE3"], b.common_eq3_parity_branches(b.NAE3))
        self.assertEqual(classification["EQ3"], b.common_eq3_parity_branches(b.EQ3))
        self.assertEqual(saved["counts"]["symmetric_clause_families"], 4)
        self.assertTrue(b.verify_edge_specific_or3_certificate(saved["edge_specific_certificate"]))
        self.assertTrue(b.verify_edge_specific_slack_certificate(saved["edge_specific_slack_certificate"]))
        self.assertEqual(saved["counts"]["edge_specific_surviving_support_triples"], 2)
        self.assertEqual(saved["counts"]["edge_specific_clause_pairs_excluded"], 2)
        self.assertTrue(b.verify_edge_specific_global_certificate(saved["edge_specific_global_certificate"]))
        self.assertTrue(b.verify_edge_specific_global_certificate(saved["edge_specific_global_slack_certificate"]))
        self.assertEqual(saved["counts"]["edge_specific_flip_cases_checked_per_clause"], 16)
        self.assertTrue(b.verify_product_type_obstruction(saved["product_type_certificate"]))
        self.assertTrue(saved["product_type_certificate_replayed"])
        self.assertEqual(saved["counts"]["product_type_common_basis_obstructions"], 1)

    def test_product_type_obstruction_certificate(self):
        certificate = b.product_type_obstruction_certificate()
        self.assertTrue(b.verify_product_type_obstruction(certificate))
        changed = copy.deepcopy(certificate)
        changed["invertible_zero_case_bases"] = ["diagonal"]
        self.assertFalse(b.verify_product_type_obstruction(changed))
        changed = copy.deepcopy(certificate)
        changed["or3_support_diagonal"][1] = 0
        self.assertFalse(b.verify_product_type_obstruction(changed))

    def test_graph_control_mutation_changes_signature(self):
        graph = b.even_graph(2, 2)
        before = b.matching_signature(graph)
        left, right, weight = graph["edges"][0]
        graph["edges"][0] = (left, right, weight + 1)
        self.assertNotEqual(b.matching_signature(graph), before)


if __name__ == "__main__":
    unittest.main()
