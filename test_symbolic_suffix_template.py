import copy
import json
import sys
import unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT))
import symbolic_suffix_template as producer
import verify_symbolic_suffix_template as verifier
sys.path.insert(0,str(ROOT.parent / "proof_portfolio_integration_lab"))
import proof_engine
import repeated_subdag_templates as templates

class TestSymbolicSuffixTemplate(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        proof, _, _ = proof_engine.build_fused_partitioned_proof(8,4)
        cls.certificate = templates.serialize_proof(proof)

    def test_two_literal_suffix_is_exact(self):
        result=producer.recognize_suffix_macro(self.certificate,62)
        self.assertEqual(result["status"],"FOUND")
        self.assertEqual(result["candidate"],{"kind":"PB","weights":{"24":1,"28":1},"sense":"<=","bound":1})
        self.assertEqual(result["relation_bits"],[1,1,1,0])
        self.assertTrue(verifier.verify_suffix_result(self.certificate,result))

    def test_one_literal_suffix_is_exact(self):
        result=producer.recognize_suffix_macro(self.certificate,63)
        self.assertEqual(result["status"],"FOUND")
        self.assertEqual(result["candidate"],{"kind":"UNIT","var":28,"value":False})
        self.assertEqual(result["relation_bits"],[1,0])
        self.assertTrue(verifier.verify_suffix_result(self.certificate,result))

    def test_scale_work_is_linear_in_reachable_proof(self):
        proof,_,_=proof_engine.build_fused_partitioned_proof(256,8)
        certificate=templates.serialize_proof(proof)
        result=producer.recognize_suffix_macro(certificate,4094)
        self.assertEqual(result["status"],"FOUND")
        self.assertEqual(result["local_count"],2032)
        self.assertEqual(result["discovery_work"],4065)
        self.assertTrue(verifier.verify_suffix_result(certificate,result))

    def test_parameter_sweep_work_formula(self):
        artifact=json.loads((ROOT/"SYMBOLIC_SUFFIX_TEMPLATE.json").read_text(encoding="utf-8"))
        self.assertEqual(len(artifact["parameter_sweep"]),23)
        for row in artifact["parameter_sweep"]:
            groups,width=row["groups"],row["width"]
            self.assertEqual(row["proof_nodes"],2*groups*width+1)
            self.assertEqual(row["two_boundary_work"],2*width*(groups-2)+1)
            self.assertEqual(row["one_boundary_work"],2*width*(groups-1)+1)
            self.assertEqual(row["two_local_count"],width*(groups-2))
            self.assertEqual(row["one_local_count"],width*(groups-1))

    def test_near_miss_clause_is_rejected(self):
        forged=copy.deepcopy(self.certificate)
        forged["nodes"][62]["clause"]= [-25,-28]
        self.assertEqual(producer.recognize_suffix_macro(forged,62)["status"],"UNKNOWN")

    def test_forged_certificate_is_rejected(self):
        result=producer.recognize_suffix_macro(self.certificate,62)
        forged=copy.deepcopy(result)
        forged["certificate"]["chain_pivots"][0]=4
        self.assertFalse(verifier.verify_suffix_result(self.certificate,forged))
        self.assertTrue(verifier.mutate_and_reject(self.certificate,result))

if __name__=="__main__": unittest.main()
