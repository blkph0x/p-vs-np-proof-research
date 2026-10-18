import copy
import json
import unittest
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT))
import projection_discovery_barrier as producer
import verify_projection_discovery_barrier as verifier

class ProjectionDiscoveryBarrierTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.artifact=producer.build_artifact()

    def test_exhaustive_small_split(self):
        self.assertEqual(self.artifact["small_formula_count"],256)
        self.assertEqual(self.artifact["satisfiable_count"],95)
        self.assertEqual(self.artifact["unsatisfiable_count"],161)
        self.assertEqual(self.artifact["relation_class_counts"],{"EMPTY":161,"UNIT_Z_FALSE":95,"OTHER":0})

    def test_reduction_relation(self):
        sat=producer.exact_record((),2)
        unsat=producer.exact_record(((1,),(-1,)),1)
        self.assertEqual(sat["projection_bits"],[1,0])
        self.assertEqual(sat["relation_class"],"UNIT_Z_FALSE")
        self.assertEqual(unsat["projection_bits"],[0,0])
        self.assertEqual(unsat["relation_class"],"EMPTY")

    def test_boundary_is_one_bit(self):
        self.assertTrue(all(row["boundary_width"]==1 for row in self.artifact["records"]))
        self.assertTrue(all(len(row["projection_bits"])==2 for row in self.artifact["records"]))

    def test_independent_replay(self):
        self.assertTrue(all(verifier.verify(row) for row in self.artifact["records"]+self.artifact["controls"]))

    def test_forged_record_rejected(self):
        forged=copy.deepcopy(self.artifact["records"][0])
        forged["projection_bits"]=[0,0]
        self.assertFalse(verifier.verify(forged))
        forged=copy.deepcopy(self.artifact["records"][1])
        forged["g_model_count"]+=1
        self.assertFalse(verifier.verify(forged))

    def test_artifact_replay(self):
        saved=json.loads((ROOT/"PROJECTION_DISCOVERY_BARRIER.json").read_text(encoding="utf-8"))
        self.assertTrue(saved["all_checks_passed"])
        self.assertEqual(saved["records"],self.artifact["records"])

if __name__=="__main__": unittest.main()
