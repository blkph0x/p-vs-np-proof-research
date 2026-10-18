
import unittest,importlib.util
from itertools import combinations,product
from pathlib import Path
spec=importlib.util.spec_from_file_location("e",Path(__file__).with_name("engine.py"))
e=importlib.util.module_from_spec(spec);spec.loader.exec_module(e)

class T(unittest.TestCase):
 def test_signatures(self):
  self.assertIn("MIN",e.relation_signature(e.parity_relation(3,0),3))
  self.assertEqual(e.relation_signature(e.exact1_relation(3),3),frozenset())
  self.assertIn("MAJ",e.relation_signature(e.amo_relation(3),3))

 def test_schaefer_pair(self):
  p=e.relation_signature(e.parity_relation(3,0),3)
  q=e.relation_signature(e.parity_relation(3,1),3)
  self.assertEqual(e.schaefer_pair_status(p,q)["status"],"POLY_COMMON_SCHAEFER")
  x=e.relation_signature(e.exact1_relation(3),3)
  self.assertEqual(e.schaefer_pair_status(x,x)["status"],"NP_COMPLETE_FIXED_LANGUAGE")

 def test_zero_and_one_valid_are_not_extension_oracles(self):
  zero={(0,0,0),(0,1,1),(1,0,1)}
  one={tuple(1-bit for bit in row) for row in zero}
  for relation,tag in ((zero,"ZERO"),(one,"ONE")):
   sig=e.relation_signature(relation,3)
   self.assertEqual(sig,frozenset({tag}))
   self.assertEqual(e.schaefer_pair_status(sig,sig)["status"],"POLY_COMMON_SCHAEFER")
   self.assertEqual(e.schaefer_pair_status(sig,sig,allow_pins=True)["status"],
                    "NP_COMPLETE_PINNED_LANGUAGE")

 def test_pins_preserve_four_actual_polymorphisms(self):
  for tag in e.EXTENSION_POLYMORPHISMS:
   result=e.schaefer_pair_status({tag,"ZERO"},{tag,"ZERO"},allow_pins=True)
   self.assertEqual(result,{"status":"POLY_PINNED_SCHAEFER","common":(tag,)})
  implication=e.relation_signature(e.implication_relation(),2)
  for rhs,constant_tag in ((0,"ZERO"),(1,"ONE")):
   parity=e.relation_signature(e.parity_relation(3,rhs),3)
   self.assertEqual(e.schaefer_pair_status(implication,parity)["common"],(constant_tag,))
   self.assertEqual(e.schaefer_pair_status(implication,parity,allow_pins=True)["status"],
                    "NP_COMPLETE_PINNED_LANGUAGE")

 def test_minimal_pinning_obstruction(self):
  # Every Boolean relation of arity <=2 is majority-closed.
  for arity in range(3):
   rows=e.tuples(arity)
   for mask in range(1<<len(rows)):
    relation=[row for i,row in enumerate(rows) if mask>>i&1]
    self.assertIn("MAJ",e.relation_signature(relation,arity))
  # A relation with <=2 tuples is minority-closed (any arity).
  for size in range(3):
   for relation in combinations(e.tuples(3),size):
    self.assertIn("MIN",e.relation_signature(relation,3))

 def test_single_pin_exact_one_reduction(self):
  relation={(0,0,0),(0,1,1),(1,0,1)}
  for a,b,c,t in product((0,1),repeat=4):
   actual=any((a,b,s) in relation and (s,c,t) in relation for s in (0,1))
   self.assertEqual(actual,a+b+c==t)
  # Exhaust every positive 1-in-3 formula on the four distinct triples of
  # four variables.  All clauses share just one pinned activation variable.
  triples=list(combinations(range(4),3))
  for mask in range(1<<len(triples)):
   formula=[clause for i,clause in enumerate(triples) if mask>>i&1]
   direct=any(all(sum(bits[i] for i in clause)==1 for clause in formula)
              for bits in product((0,1),repeat=4))
   projected=set()
   for t in (0,1):
    if any(all(any((bits[a],bits[b],s) in relation and (s,bits[c],t) in relation
                   for s in (0,1)) for a,b,c in formula)
           for bits in product((0,1),repeat=4)):
     projected.add(t)
   self.assertEqual(projected,{0,1} if direct else {0})

 def test_boundary_merge_rejects_constant_validity_only(self):
  regs=[e.Region("left",range(40),"GENERIC"),e.Region("right",range(40),"GENERIC")]
  for tag in ("ZERO","ONE"):
   a=e.leaf_state(regs,0);b=e.leaf_state(regs,1)
   a.tags=b.tags=frozenset({tag})
   self.assertEqual(e.merge_states(regs,a,b),[])
  a.tags=b.tags=frozenset({"ZERO","AND"})
  merged=e.merge_states(regs,a,b)
  self.assertEqual(len(merged),1)
  self.assertEqual(merged[0].tags,frozenset({"AND"}))

 def test_horn_projection_fooling_family(self):
  # Independently quantify the hidden Horn variables, then check the explicit
  # projected CNF and the pairwise-meet witness behind its clause lower bound.
  for m in range(1,5):
   def projected(bits):
    return bool(bits[-1] or any(not(bits[2*i] or bits[2*i+1]) for i in range(m)))
   for bits in product((0,1),repeat=2*m+1):
    actual=any(all((not bits[2*i] or local[i]) and (not bits[2*i+1] or local[i])
                   for i in range(m)) and (not all(local) or bits[-1])
               for local in product((0,1),repeat=m))
    clauses=all(bits[-1] or any(not bits[2*i+choice[i]] for i in range(m))
                for choice in product((0,1),repeat=m))
    self.assertEqual(actual,projected(bits))
    self.assertEqual(clauses,projected(bits))
   false_rows=[tuple(v for bit in choice for v in (bit,1-bit))+(0,)
               for choice in product((0,1),repeat=m)]
   self.assertEqual(len(false_rows),1<<m)
   self.assertTrue(all(not projected(row) for row in false_rows))
   for a,b in combinations(false_rows,2):
    self.assertTrue(projected(tuple(x&y for x,y in zip(a,b))))

 def test_helper_fixture(self):
  regs=e.hard_helper_fixture(64,3)
  good=e.evaluate_declared_tree(regs,((0,1),(2,3)),2)
  bad=e.evaluate_declared_tree(regs,((0,2),(1,3)),2)
  self.assertIsNotNone(good);self.assertEqual(good.max_explicit_width,3)
  self.assertIsNone(bad)
  ex=e.exact_subset_planner(regs,2,10)
  self.assertIsNotNone(ex);self.assertEqual(ex.max_explicit_width,3)

 def test_bridge_assessor(self):
  r=e.assess_hard_merge("AFFINE","CARDINALITY",40,1000,None,2)
  self.assertEqual(r["route"],"HARD_BARRIER")
  r=e.assess_hard_merge("HORN","AFFINE",3,1000,None,2)
  self.assertEqual(r["route"],"EXPLICIT_TT_BRIDGE")
  r=e.assess_hard_merge("CARDINALITY","CARDINALITY",2048,10_000_000,2049,2)
  self.assertEqual(r["route"],"EXTENSION_QUOTIENT")

if __name__=="__main__":unittest.main()
