import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "proof_motif_candidate_lab"))
sys.path.insert(0, str(ROOT / "bounded_language_invention_lab"))

from adaptive_fragment_synthesis import synthesize_fragment, verify_synthesis, result_dict, extract_proof_leaves
import miner
import hard_controls
import engine as broad_engine


class TestAdaptiveFragmentSynthesis(unittest.TestCase):
    def test_direct_xor_relation(self):
        clauses, _, _ = miner.xor3_fixture(1)
        result = synthesize_fragment(clauses, (0, 1, 2))
        self.assertEqual(result.status, "FOUND")
        self.assertEqual(result.candidate["kind"], "XOR")
        self.assertTrue(verify_synthesis(result, clauses))

    def test_existential_local_projection_preserves_xor(self):
        xor, _, _ = miner.xor3_fixture(1)
        clauses = tuple(xor) + ((4,),)
        result = synthesize_fragment(clauses, (0, 1, 2))
        self.assertEqual(result.status, "FOUND")
        self.assertEqual(result.candidate["kind"], "XOR")
        self.assertEqual(result.local, (3,))
        self.assertTrue(verify_synthesis(result, clauses))

    def test_cardinality_relation(self):
        clauses, _ = miner.amo_fixture(3)
        result = synthesize_fragment(clauses, (0, 1, 2))
        self.assertEqual(result.status, "FOUND")
        self.assertEqual(result.candidate["kind"], "PB")
        self.assertEqual(result.candidate["sense"], "<=")
        self.assertEqual(result.candidate["bound"], 1)
        self.assertTrue(verify_synthesis(result, clauses))

    def test_direct_ite_relation(self):
        clauses, _, _ = miner.ite_fixture(1)
        result = synthesize_fragment(clauses, (0, 1, 2, 3))
        self.assertEqual(result.status, "FOUND")
        self.assertEqual(result.candidate["kind"], "ITE")
        self.assertTrue(verify_synthesis(result, clauses))

    def test_permuted_ite_roles_are_checked(self):
        clauses, _, _ = miner.ite_fixture(1)
        remap = {0: 2, 1: 3, 2: 0, 3: 1}
        permuted = tuple(tuple((1 if lit > 0 else -1) * (remap[abs(lit) - 1] + 1) for lit in c)
                         for c in clauses)
        result = synthesize_fragment(permuted, (0, 1, 2, 3))
        self.assertEqual(result.status, "FOUND")
        self.assertEqual(result.candidate["kind"], "ITE")
        self.assertTrue(verify_synthesis(result, permuted))

    def test_resolution_macro_relation(self):
        clauses, heads, _ = miner.hall_groups(1, 5)
        result = synthesize_fragment(clauses, tuple(range(5)))
        self.assertEqual(result.status, "FOUND")
        self.assertEqual(result.candidate["kind"], "UNIT")
        self.assertEqual(result.candidate["var"], heads[0])
        self.assertTrue(verify_synthesis(result, clauses))

    def test_proof_dag_leaf_extraction_is_bounded(self):
        clauses, _, _ = miner.hall_groups(1, 5)
        macro = miner.mine_all(clauses)["OR_COLLAPSE"][0]
        extracted = extract_proof_leaves(macro["proof"]["dag"], macro["proof"]["root"], max_nodes=32)
        self.assertIsNotNone(extracted)
        leaves, visited = extracted
        self.assertEqual(visited, 9)
        result = synthesize_fragment(leaves, tuple(range(5)))
        self.assertEqual(result.candidate["kind"], "UNIT")
        self.assertTrue(verify_synthesis(result, leaves))
        self.assertIsNone(extract_proof_leaves(macro["proof"]["dag"], macro["proof"]["root"], max_nodes=8))

    def test_projection_matches_existing_invention_engine(self):
        cases = [
            (miner.xor3_fixture(1)[0], (0, 1, 2), ()),
            (miner.hall_groups(1, 5)[0], tuple(range(5)), ()),
        ]
        for clauses, boundary, locals_ in cases:
            old_tt, _ = broad_engine.project_relation(clauses, boundary, locals_)
            relation, _ = __import__("adaptive_fragment_synthesis")._relation_projection(
                clauses, boundary, locals_, 1 << 20
            )
            new_tt = sum(int(v) << i for i, v in enumerate(relation))
            self.assertEqual(new_tt, old_tt)

    def test_noncompact_relation_is_explicit(self):
        # x0 OR (x1 AND x2): neither one XOR, threshold, unit nor ITE.
        clauses = ((1, 2), (1, 3))
        result = synthesize_fragment(clauses, (0, 1, 2))
        self.assertEqual(result.status, "NO_COMPACT")
        self.assertEqual(result.candidate["kind"], "TRUTH_TABLE")
        self.assertTrue(verify_synthesis(result, clauses))

    def test_mutated_xor_does_not_keep_xor_certificate(self):
        clauses, _, _ = miner.xor3_fixture(1)
        mutated = clauses[1:]
        result = synthesize_fragment(mutated, (0, 1, 2))
        self.assertNotIn("XOR", [c["kind"] for c in result.all_candidates])
        self.assertTrue(verify_synthesis(result, mutated))

    def test_budget_and_interface_controls_return_unknown(self):
        clauses, _, _ = miner.xor3_fixture(1)
        budget = synthesize_fragment(clauses, (0, 1, 2), max_assignments=1)
        self.assertEqual(budget.status, "UNKNOWN")
        self.assertTrue(verify_synthesis(budget, clauses))

        hard = hard_controls.clique_coloring_cnf(5, 3)
        edges = tuple(sorted(hard["shared"]))
        bounded = synthesize_fragment(hard["A"], edges, max_shared=6)
        self.assertEqual(bounded.status, "UNKNOWN")
        self.assertEqual(bounded.reason, "shared interface exceeds bound")
        self.assertTrue(verify_synthesis(bounded, hard["A"]))


def main():
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(TestAdaptiveFragmentSynthesis)
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    artifact = {
        "tests": result.testsRun,
        "failures": len(result.failures),
        "errors": len(result.errors),
        "all_checks_passed": result.wasSuccessful(),
        "examples": {},
    }
    examples = [
        ("xor", miner.xor3_fixture(1)[0], (0, 1, 2)),
        ("xor_with_local", tuple(miner.xor3_fixture(1)[0]) + ((4,),), (0, 1, 2)),
        ("ite", miner.ite_fixture(1)[0], (0, 1, 2, 3)),
        ("amo", miner.amo_fixture(3)[0], (0, 1, 2)),
        ("hall", miner.hall_groups(1, 5)[0], tuple(range(5))),
        ("noncompact", ((1, 2), (1, 3)), (0, 1, 2)),
        ("mutated_xor", miner.xor3_fixture(1)[0][1:], (0, 1, 2)),
    ]
    for name, clauses, shared in examples:
        row = result_dict(synthesize_fragment(clauses, shared))
        row["clauses"] = [list(c) for c in clauses]
        artifact["examples"][name] = row
    hard = hard_controls.clique_coloring_cnf(5, 3)
    hard_result = synthesize_fragment(hard["A"], tuple(sorted(hard["shared"])), max_shared=6)
    artifact["controls"] = {
        "budget_unknown": result_dict(synthesize_fragment(miner.xor3_fixture(1)[0], (0, 1, 2), max_assignments=1)),
        "clique_coloring_unknown": {
            "status": hard_result.status,
            "reason": hard_result.reason,
            "shared_count": len(hard["shared"]),
            "max_shared": 6,
        },
    }
    (ROOT / "ADAPTIVE_FRAGMENT_SYNTHESIS.json").write_text(json.dumps(artifact, indent=2) + "\n", encoding="utf-8")
    if not result.wasSuccessful():
        raise SystemExit(1)


if __name__ == "__main__":
    main()
