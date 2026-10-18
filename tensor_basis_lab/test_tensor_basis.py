from copy import deepcopy
from fractions import Fraction
from hashlib import sha256
from itertools import product, combinations_with_replacement
import json
from pathlib import Path
import random
import unittest

import tensor_basis as tb


BASES = {
    "identity": [[1, 0], [0, 1]],
    "signed": [[1, 0], [0, -1]],
    "Hadamard": [[1, 1], [1, -1]],
    "shear": [[1, 1], [0, 1]],
    "nonorthogonal": [[1, 2], [3, 5]],
    "rational": [[Fraction(1, 2), Fraction(1, 3)], [Fraction(-2, 5), Fraction(3, 7)]],
}


def direct_original_count(n, clauses, mode):
    if n > 10:
        raise ValueError("independent logical enumeration is capped")
    count = 0
    for bits in product((0, 1), repeat=n):
        weight = 1
        for clause in clauses:
            true_count = sum(bool(bits[abs(lit) - 1]) == (lit > 0) for lit in clause)
            if mode == "sat":
                weight *= int(true_count > 0)
            elif not clause:
                weight = 0
            else:
                # Explicitly enumerate the original local slack bits; no comb.
                weight *= sum(sum(slacks) == true_count - 1
                              for slacks in product((0, 1), repeat=len(clause) - 1))
        count += weight
    return count


def direct_kronecker(values, matrix, side):
    degree = len(values).bit_length() - 1
    if degree > 6:
        raise ValueError("independent dense tensor-power control is capped")
    output = []
    for destination in range(len(values)):
        total = Fraction(0)
        for source, entry in enumerate(values):
            term = entry
            for port in range(degree):
                x, y = (source >> port) & 1, (destination >> port) & 1
                term *= matrix[x][y] if side == "row" else matrix[y][x]
            total += term
        output.append(total)
    return output


class TensorBasisTests(unittest.TestCase):
    def check_formula(self, n, clauses, basis, mode):
        result = tb.solve_basis(n, clauses, basis, mode=mode)
        self.assertEqual(result["status"], "EXACT")
        self.assertEqual(tb.decode_rational(result["count"]), direct_original_count(n, clauses, mode))
        verdict = tb.verify_basis(n, clauses, basis, result["certificate"], mode=mode)
        self.assertTrue(verdict["valid"], verdict)
        self.assertEqual(verdict["count"], result["count"])
        return result

    def test_all_clause_polarities_identity_signed_hadamard_and_rational(self):
        cases = 0
        for arity in range(4):
            for signs in product((-1, 1), repeat=arity):
                clauses = [[sign * (i + 1) for i, sign in enumerate(signs)]]
                for basis in BASES.values():
                    for mode in ("sat", "slack"):
                        self.check_formula(arity, clauses, basis, mode)
                        cases += 1
        self.assertEqual(cases, 180)

    def test_every_local_action_against_direct_tensor_power(self):
        n, clauses = 3, [[1, -2, 3], [-1], [2, 1]]
        for basis in BASES.values():
            result = tb.transform_network(n, clauses, basis, mode="slack")
            certificate = result["certificate"]
            inverse = [[tb.decode_rational(v) for v in row] for row in certificate["inverse"]]
            for name, action, side in (("rows", basis, "row"), ("columns", inverse, "column")):
                for node in certificate[name]:
                    before = [tb.decode_rational(v) for v in node["stages"][0]]
                    after = [tb.decode_rational(v) for v in node["stages"][-1]]
                    self.assertEqual(after, direct_kronecker(before, action, side))

    def test_shared_variables_repeated_clauses_and_occurrence_port_order(self):
        n, clauses = 3, [[1, -2], [2, 1], [1, 1, -3]]
        transformed = tb.transform_network(n, clauses, BASES["shear"])["certificate"]
        self.assertEqual(transformed["layout"]["variable_ports"], [[0, 3, 4, 5], [1, 2], [6]])
        self.assertEqual(transformed["layout"]["clause_ports"], [[0, 1], [2, 3], [4, 5, 6]])
        for formula in (clauses, [[1, 2, 3]] * 2, [[1], [-1]], [[1, -1]], [[1, 1, 1]]):
            for mode in ("sat", "slack"):
                self.check_formula(n, formula, BASES["rational"], mode)
        sat = self.check_formula(3, [[1, 2, 3]], BASES["Hadamard"], "sat")
        slack = self.check_formula(3, [[1, 2, 3]], BASES["Hadamard"], "slack")
        self.assertEqual(sat["count"], [7, 1])
        self.assertEqual(slack["count"], [10, 1])
        repeated = self.check_formula(3, [[1, 2, 3]] * 2, BASES["shear"], "slack")
        self.assertEqual(repeated["count"], [16, 1])

    def test_empty_formula_empty_clause_and_unused_variables(self):
        for n, clauses, expected in ((0, [], 1), (0, [[]], 0), (4, [], 16), (4, [[]], 0)):
            for mode in ("sat", "slack"):
                result = self.check_formula(n, clauses, BASES["rational"], mode)
                self.assertEqual(result["count"], [expected, 1])
        unused = tb.solve_basis(256, [], BASES["Hadamard"])
        self.assertEqual(unused["status"], "EXACT")
        self.assertEqual(unused["count"], [1 << 256, 1])
        self.assertTrue(tb.verify_basis(256, [], BASES["Hadamard"], unused["certificate"])["valid"])

    def test_exhaustive_tiny_formula_pairs(self):
        pool = [[], [1], [-1], [2], [-2], [1, 2], [1, -2], [-1, 2], [-1, -2]]
        cases = 0
        for first, second in combinations_with_replacement(pool, 2):
            for mode in ("sat", "slack"):
                self.check_formula(2, [first, second], BASES["nonorthogonal"], mode)
                cases += 1
        self.assertEqual(cases, 90)

    def test_seeded_raw_formulas_with_shared_and_repeated_occurrences(self):
        rng = random.Random(20261018)
        for _ in range(50):
            n = rng.randrange(1, 5)
            clauses = [[rng.choice((-1, 1)) * rng.randrange(1, n + 1) for _ in range(rng.randrange(4))]
                       for _ in range(rng.randrange(4))]
            basis = rng.choice(list(BASES.values()))
            for mode in ("sat", "slack"):
                self.check_formula(n, clauses, basis, mode)

    def test_wrong_transform_both_ends_changes_the_original_count(self):
        for name, expected in (("Hadamard", 2), ("shear", 3)):
            control = tb.wrong_same_basis_control(1, [[1]], BASES[name])
            self.assertEqual(control["status"], "CONTROL")
            self.assertEqual(control["original_count"], [1, 1])
            self.assertEqual(control["wrong_count"], [expected, 1])
            self.assertTrue(control["changes_count"])
            good = tb.solve_basis(1, [[1]], BASES[name])["certificate"]
            good["transformation"]["columns"] = control["network"]["columns"]
            self.assertFalse(tb.verify_basis(1, [[1]], BASES[name], good)["valid"])
        self.assertFalse(tb.wrong_same_basis_control(1, [[1]], BASES["identity"])["changes_count"])

    def test_signed_cancellation_preserves_a_zero_original_count(self):
        result = tb.solve_basis(1, [[1], [-1]], BASES["shear"])
        terms = [tb.decode_rational(v) for v in result["certificate"]["transformed_terms"]]
        self.assertEqual(result["count"], [0, 1])
        self.assertTrue(any(value > 0 for value in terms))
        self.assertTrue(any(value < 0 for value in terms))
        self.assertEqual(sum(terms), 0)

    def test_exact_limits_and_verifier_limits_fail_closed(self):
        n, clauses, basis = 2, [[1, -2], [1]], BASES["shear"]
        baseline = tb.solve_basis(n, clauses, basis)
        limits = {"max_tensor_entries": baseline["stats"]["tensor_entries"],
                  "max_edge_assignments": 8, "max_arithmetic": baseline["stats"]["arithmetic"]}
        self.assertEqual(tb.solve_basis(n, clauses, basis, **limits)["status"], "EXACT")
        for key in limits:
            reduced = {**limits, key: limits[key] - 1}
            result = tb.solve_basis(n, clauses, basis, **reduced)
            self.assertEqual(result["status"], "UNKNOWN")
            self.assertIsNone(result["count"])
            self.assertIsNone(result["certificate"])
        verification = tb.verify_basis(n, clauses, basis, baseline["certificate"])
        exact_work = verification["stats"]["arithmetic"]
        self.assertTrue(tb.verify_basis(n, clauses, basis, baseline["certificate"], max_arithmetic=exact_work)["valid"])
        self.assertEqual(tb.verify_basis(n, clauses, basis, baseline["certificate"], max_arithmetic=exact_work - 1)["status"], "UNKNOWN")
        self.assertEqual(tb.verify_basis(n, clauses, basis, baseline["certificate"], max_edge_assignments=7)["status"], "UNKNOWN")
        self.assertEqual(tb.solve_basis(n, clauses, basis, max_rational_bits=0)["status"], "UNKNOWN")
        self.assertEqual(tb.solve_basis(10**9, [], basis)["status"], "UNKNOWN")

    def test_local_transform_can_finish_without_global_contraction(self):
        n, clauses = 20, [[i, i + 1] for i in range(1, 20)]
        local = tb.transform_network(n, clauses, BASES["Hadamard"], max_edge_assignments=0)
        self.assertEqual(local["status"], "EXACT")
        self.assertTrue(tb.verify_transformation(n, clauses, BASES["Hadamard"], local["certificate"], max_edge_assignments=0)["valid"])
        full = tb.solve_basis(n, clauses, BASES["Hadamard"])
        self.assertEqual(full["status"], "UNKNOWN")
        self.assertIsNone(full["count"])
        high_degree = tb.transform_network(1, [[1]] * 30, BASES["Hadamard"])
        self.assertEqual(high_degree["status"], "UNKNOWN")

    def test_input_binding_rebound_mutation_still_fails(self):
        n, clauses, basis = 2, [[1, -2], [2, 1]], BASES["shear"]
        original = tb.solve_basis(n, clauses, basis)["certificate"]
        changed_clauses = [[-1, -2], [2, 1]]
        for nc, nb, mode in ((changed_clauses, basis, "sat"), (clauses, BASES["Hadamard"], "sat"), (clauses, basis, "slack")):
            self.assertFalse(tb.verify_basis(n, nc, nb, original, mode=mode)["valid"])
        rebound = deepcopy(original)
        actual_changed = tb.transform_network(n, changed_clauses, basis)["certificate"]
        rebound["transformation"]["input_sha256"] = actual_changed["input_sha256"]
        verdict = tb.verify_basis(n, changed_clauses, basis, rebound)
        self.assertEqual(verdict["status"], "INVALID")
        self.assertIn("initial tensor", verdict["reason"])

    def test_tampered_local_tensors_order_inverse_and_trace_rejected(self):
        n, clauses, basis = 2, [[1, -2], [2, 1]], BASES["rational"]
        original = tb.solve_basis(n, clauses, basis)["certificate"]
        modifications = [
            lambda c: c["transformation"]["rows"][0]["ports"].reverse(),
            lambda c: c["transformation"]["rows"][0]["ports"].__setitem__(0, False),
            lambda c: c["transformation"]["rows"][0]["stages"][0].__setitem__(0, [0, 1]),
            lambda c: c["transformation"]["columns"][0]["stages"][-1].__setitem__(0, [99, 1]),
            lambda c: c["transformation"]["inverse"][0].__setitem__(0, [0, 1]),
            lambda c: c["original_terms"].pop(),
            lambda c: c["transformed_terms"].__setitem__(0, [2, 2]),
            lambda c: c["transformed_terms"].__setitem__(0, [1, 0]),
            lambda c: c.__setitem__("count", [99, 1]),
            lambda c: c.__setitem__("extra", True),
        ]
        for modify in modifications:
            forged = deepcopy(original)
            modify(forged)
            self.assertFalse(tb.verify_basis(n, clauses, basis, forged)["valid"])
        for bad in (None, {}):
            self.assertFalse(tb.verify_basis(n, clauses, basis, bad)["valid"])

    def test_validation_json_and_large_exact_matrix_entries(self):
        for n, clauses, basis in ((True, [], BASES["identity"]), (-1, [], BASES["identity"]),
                                 (1, [[0]], BASES["identity"]), (1, [[2]], BASES["identity"]),
                                 (1, [[True]], BASES["identity"]), (1, [[]], [[1, 2], [2, 4]]),
                                 (1, [[1]], [[1.0, 0], [0, 1]]), (1, [[1]], [[True, 0], [0, 1]])):
            with self.assertRaises(ValueError):
                tb.solve_basis(n, clauses, basis)
        for options in ({"mode": "unknown"}, {"max_arithmetic": -1}, {"unrecognized_cap": 1}):
            with self.assertRaises(ValueError):
                tb.solve_basis(0, [], BASES["identity"], **options)
        certificate = tb.solve_basis(2, [[1, -2]], BASES["rational"])["certificate"]
        replay = json.loads(json.dumps(certificate))
        encoded_basis = [[tb.encode_rational(v) for v in row] for row in BASES["rational"]]
        self.assertTrue(tb.verify_basis(2, [[1, -2]], encoded_basis, replay)["valid"])
        large = 1 << 15000
        basis = [[large, 0], [0, Fraction(1, large)]]
        result = tb.solve_basis(1, [[1]], basis)
        self.assertEqual(result["status"], "EXACT")
        self.assertEqual(result["count"], [1, 1])
        self.assertTrue(tb.verify_basis(1, [[1]], basis, result["certificate"])["valid"])

    def test_saved_proofs_and_source_hashes(self):
        here = Path(__file__).resolve().parent
        path = here / "RESULTS.json"
        if not path.exists():
            self.skipTest("saved artifact has not yet been generated")
        saved = json.loads(path.read_text(encoding="utf-8"))
        self.assertTrue(saved["source_unchanged_during_run"])
        for name, digest in saved["source_sha256"].items():
            self.assertEqual(sha256((here / name).read_bytes()).hexdigest(), digest)
        for case in saved["cases"]:
            request, result = case["request"], case["result"]
            if result["status"] == "EXACT":
                check = tb.verify_basis(request["n"], request["clauses"], request["basis"], result["certificate"], mode=request["mode"])
                self.assertTrue(check["valid"])
                self.assertEqual(check["count"], result["count"])
            else:
                self.assertEqual(result["status"], "UNKNOWN")
                self.assertIsNone(result["count"])
        for control in saved["local_transform_controls"]:
            request = control["request"]
            self.assertTrue(tb.verify_transformation(request["n"], request["clauses"], request["basis"],
                                                     control["result"]["certificate"], mode=request["mode"],
                                                     max_edge_assignments=0)["valid"])
        for control in saved["wrong_same_basis_controls"]:
            self.assertEqual(control["control"]["original_count"], [1, 1])
            self.assertTrue(control["control"]["changes_count"])


if __name__ == "__main__":
    unittest.main()
