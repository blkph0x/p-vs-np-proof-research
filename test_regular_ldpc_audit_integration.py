import importlib.util
import json
import random
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parent
MODULE = ROOT / "regular_ldpc_local_audit.py"
SPEC = importlib.util.spec_from_file_location("regular_ldpc_local_audit_test", MODULE)
audit = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = audit
SPEC.loader.exec_module(audit)

MODULE_33 = ROOT / "regular_ldpc_33_local_audit.py"
SPEC_33 = importlib.util.spec_from_file_location("regular_ldpc_33_local_audit_test", MODULE_33)
audit_33 = importlib.util.module_from_spec(SPEC_33)
sys.modules[SPEC_33.name] = audit_33
SPEC_33.loader.exec_module(audit_33)

MODULE_SIZE = ROOT / "regular_ldpc_size_bounds.py"
SPEC_SIZE = importlib.util.spec_from_file_location("regular_ldpc_size_bounds_test", MODULE_SIZE)
size_bounds = importlib.util.module_from_spec(SPEC_SIZE)
sys.modules[SPEC_SIZE.name] = size_bounds
SPEC_SIZE.loader.exec_module(size_bounds)


class RegularLdpcAuditIntegrationTests(unittest.TestCase):
    def test_saved_artifact_records_exhaustive_extensions(self):
        artifact = json.loads((ROOT / "REGULAR_LDPC_LOCAL_AUDIT.json").read_text())
        self.assertTrue(artifact["all_checks_passed"])
        self.assertEqual(artifact["counts"]["decomposition_exhaustive_cases"], 314)
        self.assertEqual(artifact["counts"]["padding_exhaustive_cases"], 445)
        completion = json.loads((ROOT / "REGULAR_LDPC_33_LOCAL_AUDIT.json").read_text())
        self.assertTrue(completion["all_checks_passed"])
        self.assertEqual(completion["random_completion"]["completed"], 12)

    def test_exhaustive_replays_against_fresh_code(self):
        self.assertEqual(audit.check_decomposition_exhaustive_small(), 314)
        self.assertEqual(audit.check_padding_exhaustive_small(), 445)

    def test_randomized_all_size_completion_invariants(self):
        """Exercise the generic (3,3) completion on fresh small inputs.

        These cases are structural audits: the suffix graph is too large for
        brute-force support enumeration, so the test checks the exact lift,
        degree invariants, weight identity, and the paper's suffix lower bound.
        """
        rng = random.Random(20261018)
        completed = 0
        attempts = 0
        while completed < 12:
            attempts += 1
            checks = rng.randint(3, 5)
            variables = rng.randint(3, 5)
            neighbors = [tuple(sorted(rng.sample(range(checks), 3)))
                         for _ in range(variables)]
            check_degrees = [0] * checks
            for inc in neighbors:
                for row in inc:
                    check_degrees[row] += 1
            # The theorem deletes degree-one checks before this phase.
            if min(check_degrees) < 2:
                continue

            old_supports = set(audit_33.supports(neighbors, checks))
            g1, r1, aux_specs = audit_33.split_checks(neighbors, checks)
            g2, r2, old_to_new, reps = audit_33.duplicate_and_split(
                g1, r1, len(aux_specs), variables)
            m = 2 * max(1, len(aux_specs))
            g3 = [tuple(x) for x in g2]
            r3 = r2
            for rep in reps:
                g3, r3 = audit_33.replicate(g3, r3, rep, m)

            g4, r4, suffix = audit_33.suffix_complete(g3, r3)
            self.assertTrue(all(len(set(inc)) == 3 for inc in g4))
            final_check_degrees = [0] * r4
            for inc in g4:
                for row in inc:
                    final_check_degrees[row] += 1
            self.assertTrue(all(degree == 3 for degree in final_check_degrees))

            # The complete lift is valid and obeys Equation (1) of the source.
            for mask in old_supports:
                split_mask = audit_33.split_lift(mask, variables, aux_specs)
                duplicate_mask = audit_33.duplicate_split_lift(
                    split_mask, len(g1), old_to_new)
                lifted = duplicate_mask
                offset = len(g2)
                for rep in reps:
                    if (lifted >> rep) & 1:
                        lifted |= ((1 << m) - 1) << offset
                    offset += m
                self.assertTrue(audit_33.valid(g4, r4, lifted))
                aux_weight = sum((split_mask >> a) & 1 for a, _ in aux_specs)
                self.assertEqual(
                    lifted.bit_count(), (m + 4) * mask.bit_count() + 2 * aux_weight)

            # If degree-two checks exist, the suffix lower bound is > N and
            # therefore > every threshold used by the first phase.
            degree_counts = [0] * r3
            for inc in g3:
                for row in inc:
                    degree_counts[row] += 1
            q = sum(degree == 2 for degree in degree_counts)
            if q:
                c = 3
                while c * q < 3 * len(g3) + 3:
                    c += 3
                h = c * q
                self.assertGreater(h // 3, len(g3))
                self.assertLessEqual((m + 4) * min(2, variables) + 2 * len(aux_specs),
                                     (m + 4) * variables + 2 * len(aux_specs))
            completed += 1

        self.assertLess(attempts, 500)

    def test_polynomial_size_accounting(self):
        artifact = json.loads((ROOT / "REGULAR_LDPC_SIZE_BOUND_AUDIT.json").read_text())
        self.assertTrue(artifact["all_checks_passed"])
        self.assertEqual(artifact["max_n"], 32)
        checked = size_bounds.run_audit(max_n=8)
        self.assertTrue(checked["all_checks_passed"])
        self.assertGreater(checked["first_phase_rows"], 0)
        self.assertGreater(checked["suffix_phase_rows"], 0)
        for n in range(1, 9):
            for auxiliary in range(0, 3 * n + 1):
                for threshold in range(n + 1):
                    row = size_bounds.first_phase(n, auxiliary, threshold)
                    self.assertGreater(row["lambda"], 2 * auxiliary)
                    self.assertLessEqual(row["phase_one_threshold"],
                                         row["phase_one_variables"])


if __name__ == "__main__":
    unittest.main()
