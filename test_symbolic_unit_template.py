import copy
import unittest
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT))
import symbolic_unit_template as symbolic

class TestSymbolicUnitTemplate(unittest.TestCase):
    def test_recognizes_and_certifies_large_local_fragment(self):
        clauses,local=symbolic.pattern_for_width(16); result=symbolic.recognize_unit_template(clauses,representative=1)
        self.assertEqual(result["status"],"FOUND"); self.assertEqual(result["local"],list(local)); self.assertTrue(symbolic.verify_unit_certificate(result)); self.assertEqual(result["relation_bits"],[0,1])
    def test_bounded_projector_boundary_is_explicit(self):
        self.assertEqual(symbolic.bounded_projection_status(7,max_local=6),"FOUND"); self.assertEqual(symbolic.bounded_projection_status(8,max_local=6),"UNKNOWN"); self.assertEqual(symbolic.bounded_projection_status(256,max_local=6),"UNKNOWN")
    def test_near_miss_is_rejected(self):
        clauses,_=symbolic.pattern_for_width(8); near=list(clauses[:-1])+[(1,7)]; self.assertEqual(symbolic.recognize_unit_template(near,representative=1)["status"],"UNKNOWN")
    def test_forged_resolution_certificate_is_rejected(self):
        clauses,_=symbolic.pattern_for_width(16); result=symbolic.recognize_unit_template(clauses,representative=1); forged=copy.deepcopy(result); forged["certificate"]["nodes"][-1]["clause"]=[1]; self.assertFalse(symbolic.verify_unit_certificate(forged))
    def test_certificate_size_is_linear(self):
        clauses,_=symbolic.pattern_for_width(256); result=symbolic.recognize_unit_template(clauses,representative=1); self.assertEqual(len(result["certificate"]["nodes"]),513); self.assertEqual(result["discovery_work"],511)

    def test_matches_actual_width_eight_proof_fragment(self):
        proof_dir=ROOT / "proof_portfolio_integration_lab"
        sys.path.insert(0, str(proof_dir))
        import proof_engine
        from adaptive_fragment_synthesis import extract_proof_leaves
        proof, _, _ = proof_engine.build_fused_partitioned_proof(1, 8)
        unit_index = max(i for i, node in enumerate(proof.nodes)
                         if len(node.get("clause", ())) == 1 and node["clause"][0] > 0)
        extracted = extract_proof_leaves(proof, unit_index, max_nodes=32)
        self.assertIsNotNone(extracted)
        leaves, _ = extracted
        result = symbolic.recognize_unit_template(leaves, representative=1)
        self.assertEqual(result["status"], "FOUND")
        self.assertTrue(symbolic.verify_unit_certificate(result))

if __name__ == "__main__": unittest.main()
