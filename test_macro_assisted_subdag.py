import copy
import unittest
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT))
import macro_assisted_subdag as macro

class TestMacroAssistedSubdag(unittest.TestCase):
    @classmethod
    def setUpClass(cls): cls.artifact=macro.build_artifact()
    def test_macro_scan_counts(self):
        self.assertEqual(self.artifact["status_counts"],{"FOUND":256,"FOUND_SUFFIX_SYMBOLIC":2,"FOUND_SYMBOLIC":256,"NO_COMPACT":1792})
        self.assertEqual(self.artifact["candidate_kind_counts"],{"PB":257,"TRUTH_TABLE":1792,"UNIT":257})
    def test_all_projection_cap_units_are_recovered(self):
        rows=[r for r in self.artifact["records"] if r["status"]=="FOUND_SYMBOLIC"]
        self.assertEqual(len(rows),256)
        self.assertTrue(all(r["source_unknown_stage"]=="projection_cap" for r in rows))
        self.assertTrue(all(r["symbolic_certificate_nodes"]==17 for r in rows))
    def test_subdag_cap_suffixes_are_recovered_by_structural_macro(self):
        rows=[r for r in self.artifact["records"] if r["status"]=="FOUND_SUFFIX_SYMBOLIC"]
        self.assertEqual(len(rows),2)
        self.assertEqual(self.artifact["source_unknown_subdag_count"],2)
        self.assertTrue(all(r["source_unknown_stage"]=="subdag_cap" for r in rows))
        self.assertEqual(sorted(r["candidate"]["kind"] for r in rows),["PB","UNIT"])
        self.assertEqual(sum(r["status"]=="UNKNOWN" for r in self.artifact["records"]),0)
    def test_symbolic_work_is_not_claimed_as_projection_reuse(self):
        group=next(g for g in self.artifact["template_groups"] if g["status"]=="FOUND_SYMBOLIC")
        self.assertEqual(group["occurrences"],256)
        self.assertEqual(group["saved_work"],0)
    def test_forged_macro_certificate_is_rejected(self):
        row=next(r for r in self.artifact["records"] if r["status"]=="FOUND_SYMBOLIC")
        forged=copy.deepcopy(row["symbolic_result"]); forged["certificate"]["nodes"][-1]["clause"]=[1]
        self.assertFalse(macro.symbolic.verify_unit_certificate(forged))
        suffix_row=next(r for r in self.artifact["records"] if r["status"]=="FOUND_SUFFIX_SYMBOLIC")
        forged_suffix=copy.deepcopy(suffix_row["suffix_result"]); forged_suffix["candidate"]["bound"]=0
        self.assertFalse(macro.suffix.verify_suffix_result(self.artifact["proof_certificate"],forged_suffix))

if __name__=="__main__": unittest.main()
