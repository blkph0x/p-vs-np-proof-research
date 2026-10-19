"""Adversarial and mutation tests for the Tseitin expander campaign."""
import json
from itertools import product
from pathlib import Path
import sys
import unittest

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))

from proof_producing_cdcl_lab.cdcl import CDCL
import tseitin
from INDEPENDENT_REVIEW import expected_cnf, parity_record, replay_result
from review_expansion_profile import exact_profile, expected_controls


def parity_assignment_satisfies(n, edges, charges, assignment):
    incidence = tseitin.incidence(n, edges)
    return all(sum(assignment[variable - 1] for variable in variables) % 2 == charges[vertex]
               for vertex, variables in enumerate(incidence))


class TseitinTests(unittest.TestCase):
    def test_controls_are_connected_cubic_graphs(self):
        controls = tuple(tseitin.graph_controls()) + tuple(tseitin.mobius_ladder_controls())
        self.assertEqual(len(controls), 12)
        for control in controls:
            n, edges = control["n"], control["edges"]
            self.assertTrue(tseitin.connected(n, edges))
            incidence = tseitin.incidence(n, edges)
            self.assertTrue(all(len(row) == 3 for row in incidence))
            self.assertEqual(len(edges), 3 * n // 2)

    def test_mobius_ladder_family_is_exactly_cycle_plus_matching(self):
        controls = tseitin.mobius_ladder_controls()
        self.assertEqual([control["n"] for control in controls], list(range(6, 22, 2)))
        for control in controls:
            n = control["n"]
            expected = {tuple(sorted((i, (i + 1) % n))) for i in range(n)}
            expected |= {tuple(sorted((i, i + n // 2))) for i in range(n // 2)}
            self.assertEqual(set(control["edges"]), expected)

    def test_local_cnf_is_exact_parity_encoding(self):
        control = tseitin.graph_controls()[0]
        charges = [1] + [0] * (control["n"] - 1)
        nvars, clauses = tseitin.tseitin_cnf(control["n"], control["edges"], charges)
        incidence = tseitin.incidence(control["n"], control["edges"])
        self.assertEqual(len(clauses), 4 * control["n"])
        for assignment in product((0, 1), repeat=nvars):
            cnf_satisfied = all(tseitin.clause_satisfied(clause, assignment)
                                for clause in clauses)
            self.assertEqual(cnf_satisfied,
                             parity_assignment_satisfies(control["n"], control["edges"],
                                                         charges, assignment))
        self.assertTrue(all(len(row) == 3 for row in incidence))

    def test_odd_charge_certificate_is_exact(self):
        for control in tseitin.graph_controls():
            charges = [1] + [0] * (control["n"] - 1)
            certificate = tseitin.parity_certificate(control["n"], control["edges"], charges)
            self.assertTrue(certificate["parity_proves_unsat"])
            self.assertEqual(certificate["charge_sum_mod2"], 1)

    def test_even_charge_control_is_satisfiable(self):
        control = tseitin.graph_controls()[0]
        charges = [0] * control["n"]
        nvars, clauses = tseitin.tseitin_cnf(control["n"], control["edges"], charges)
        result = CDCL(nvars, clauses).solve()
        self.assertEqual(result["status"], "SAT")
        model = tuple(int(result["model"][index]) for index in range(nvars))
        self.assertTrue(parity_assignment_satisfies(control["n"], control["edges"], charges, model))

    def test_mutating_charge_removes_unsat_certificate(self):
        control = tseitin.graph_controls()[0]
        charges = [0] * control["n"]
        certificate = tseitin.parity_certificate(control["n"], control["edges"], charges)
        self.assertFalse(certificate["parity_proves_unsat"])
        self.assertFalse(certificate["odd_charge"])

    def test_exact_expansion_profiles_replay_independently(self):
        artifact = json.loads((HERE / "EXPANSION_RESULTS.json").read_text(encoding="utf-8"))
        review = json.loads((HERE / "EXPANSION_REVIEW.json").read_text(encoding="utf-8"))
        self.assertTrue(artifact["all_profiles_exact"])
        self.assertEqual(review["status"], "PASS")
        controls = expected_controls()
        self.assertEqual(len(artifact["rows"]), len(controls))
        for saved, expected in zip(artifact["rows"], controls):
            self.assertEqual(saved["name"], expected["name"])
            self.assertEqual(saved["profile"], exact_profile(saved["vertices"], saved["edges"]))

    def test_expansion_profile_mutation_changes_certificate(self):
        control = expected_controls()[0]
        original = exact_profile(control["n"], control["edges"])
        mutated_edges = list(control["edges"])
        mutated_edges.remove((0, 1))
        mutated_edges.remove((3, 7))
        mutated_edges.extend(((0, 3), (1, 7)))
        mutated = exact_profile(control["n"], mutated_edges)
        self.assertNotEqual(original, mutated)

    def test_saved_artifacts_and_independent_replay(self):
        artifact = json.loads((HERE / "RESULTS.json").read_text(encoding="utf-8"))
        review = json.loads((HERE / "INDEPENDENT_REVIEW.json").read_text(encoding="utf-8"))
        certificates = json.loads((HERE / "CERTIFICATES.json").read_text(encoding="utf-8"))
        self.assertTrue(artifact["all_cases_unsat"])
        self.assertEqual(review["status"], "PASS")
        self.assertTrue(review["parity_certificates_match"])
        self.assertTrue(review["proofs_match"])
        for saved in certificates:
            expected_nvars, expected_clauses = expected_cnf(
                saved["vertices"], saved["edges"], saved["charges"])
            self.assertEqual(expected_nvars, saved["nvars"])
            self.assertEqual([list(clause) for clause in expected_clauses], saved["clauses"])
            self.assertEqual(parity_record(saved["vertices"], saved["edges"], saved["charges"]),
                             saved["parity"])
            self.assertTrue(replay_result(saved["nvars"], saved["clauses"], saved["result"]))


if __name__ == "__main__":
    unittest.main()
