
import unittest,importlib.util
from pathlib import Path
def load(name):
 p=Path(__file__).with_name(name);s=importlib.util.spec_from_file_location(name,p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
pe=load("proof_engine.py");po=load("portfolio.py")
class T(unittest.TestCase):
 def test_small_integrated(self):
  for g,w in [(2,3),(3,3),(4,3)]:
   P,I,reps=pe.extract_raw_interpolant(g,w)
   self.assertEqual(pe.ast_literal_count(I),g)
   self.assertTrue(pe.verify_interpolants_exhaustive(g,w,I))
   good=[]
   for c in po.source_candidates(g):
    F=po.source_candidate_semantics(c,g)
    if po.check_interpolant(g,po.alltrue_A,po.B_opposite_parity,F):good.append(c["language"])
   self.assertIn("XOR",good);self.assertIn("PB",good);self.assertIn("CNF-conjunction",good)
 def test_large_selector(self):
  cands=[]
  for c in po.source_candidates(256):
   if c["language"] in ("CNF-conjunction","XOR","PB"):cands.append(c)
  self.assertEqual(po.best_candidate(cands)["language"],"XOR")
if __name__=="__main__":unittest.main()
