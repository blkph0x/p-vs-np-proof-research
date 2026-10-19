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


def parity_assignment_satisfies(n, edges, charges, assignment):
    incidence = tseitin.incidence(n, edges)
    return all(sum(assignment[variable - 1] for variable in variables) % 2 == charges[vertex]
               for vertex, variables in enumerate(incidence))


class TseitinTests(unittest.TestCase):
    def test_controls_are_connected_cubic_graphs(self):
        for control in tseitin.graph_controls():
            n, edges = control["n"], control["edges"]
            self.assertTrue(tseitin.connected(n, edges))
            incidence = tseitin.incidence(n, edges)
            self.assertTrue(all(len(row) == 3 for row in incidence))
            self.assertEqual(len(edges), 3 * n // 2)

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
