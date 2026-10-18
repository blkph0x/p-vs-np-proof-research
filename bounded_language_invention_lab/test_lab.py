
import unittest, importlib.util, itertools, random, sys
from pathlib import Path
spec=importlib.util.spec_from_file_location("e",Path(__file__).with_name("engine.py"))
e=importlib.util.module_from_spec(spec);spec.loader.exec_module(e)
spec2=importlib.util.spec_from_file_location("pm",Path(__file__).with_name("proof_motif_miner.py"))
pm=importlib.util.module_from_spec(spec2);spec2.loader.exec_module(pm)

def tt_from_pred(k,pred):
    t=0
    for bits in itertools.product([0,1],repeat=k):
        if pred(bits):
            idx=0
            for b in bits: idx=(idx<<1)|b
            t|=1<<idx
    return t

class T(unittest.TestCase):
    def test_auxiliary_projection_matches_direct_parity(self):
        parity=tt_from_pred(4,lambda b:sum(b)%2==0)
        d=e.relation_fragment(parity,4)
        a=e.auxiliary_parity4_fragment()
        td,_=e.project_relation(d["clauses"],d["boundary"],d["locals"])
        ta,_=e.project_relation(a["clauses"],a["boundary"],a["locals"])
        cd,_=e.canonical_relation(td,4);ca,_=e.canonical_relation(ta,4)
        self.assertEqual(cd,ca)

    def test_permutation_canonicalization(self):
        tt=tt_from_pred(4,lambda b:(b[0] and b[1]) or b[3])
        can,_=e.canonical_relation(tt,4)
        for p in itertools.permutations(range(4)):
            t=e.permute_tt(tt,4,p)
            c,_=e.canonical_relation(t,4)
            self.assertEqual(c,can)

    def test_unit_coordinate_quotient(self):
        vs=list(range(5));r=vs[0]
        cs=[e.norm_clause(tuple(e.lit(v,True) for v in vs))]
        for x in vs[1:]:
            cs.append(e.norm_clause((e.lit(r,True),e.lit(x,False))))
        tt,_=e.project_relation(cs,tuple(vs),())
        q=e.coordinate_quotient_description(tt,5)
        self.assertTrue(e.verify_coordinate_quotient(tt,5,q))
        self.assertEqual(len(q["ignored"]),4)
        self.assertEqual(len(q["fixed"]),1)

    def test_equality_semantic_quotient(self):
        vs=list(range(5));cs=[]
        for x in vs[1:]:cs+=e.equality2(vs[0],x)
        tt,_=e.project_relation(cs,tuple(vs),())
        q=e.coordinate_quotient_description(tt,5)
        self.assertTrue(e.verify_coordinate_quotient(tt,5,q))
        self.assertEqual(q["quotient_arity"],1)
        self.assertEqual(len(q["classes"][0]),5)

    def test_generic_circuit_synthesis(self):
        tt=tt_from_pred(4,lambda b:b[0]==(b[1] if b[2] else b[3]))
        c=e.synthesize_small_circuit(tt,4,5)
        self.assertIsNotNone(c)
        self.assertLessEqual(c["gates"],5)
        self.assertTrue(e.verify_representation(tt,4,c))

    def test_registry_truth_table_fallback(self):
        tt=18382
        f=e.relation_fragment(tt,4)
        R=e.LanguageRegistry(max_boundary=6,max_total=8)
        for j in range(20):
            occ=e.remap_fragment(f,var_offset=20*j,shuffle_seed=j)
            rr=R.observe(occ);self.assertTrue(rr["accepted"])
        ent=R.catalog()[0]
        self.assertTrue(e.verify_registry_entry(ent))
        self.assertEqual(ent["count"],20)

    def test_width_guard(self):
        tt=0
        f=e.relation_fragment(tt,7)
        R=e.LanguageRegistry(max_boundary=6,max_total=8)
        r=R.observe(f)
        self.assertFalse(r["accepted"])
        self.assertEqual(r["reason"],"interface-too-wide")

    def test_proof_subdag_bridge(self):
        cs,heads,n=pm.hall_groups(16,5)
        mined=pm.mine_all(cs)
        self.assertEqual(len(mined["OR_COLLAPSE"]),16)
        R=e.LanguageRegistry(max_boundary=6,max_total=8)
        ids=[]
        for m in mined["OR_COLLAPSE"]:
            P=m["proof"]["dag"];root=m["proof"]["root"]
            anc=pm.ancestor_nodes(P,root)
            leaves=[];supp=set()
            for i in anc:
                nd=P.nodes[i]
                if nd["kind"]=="leaf":
                    leaves.append(tuple(nd["clause"]))
                    supp.update(pm.var(L) for L in nd["clause"])
            frag={"clauses":leaves,"boundary":tuple(sorted(supp)),"locals":()}
            rr=R.observe(frag);self.assertTrue(rr["accepted"]);ids.append(rr["relation_id"])
        self.assertEqual(len(set(ids)),1)
        ent=R.catalog()[0]
        cq=next(c for c in ent["all_reps"] if c["kind"]=="COORD_QUOTIENT")
        self.assertEqual(len(cq["fixed"]),1)
        self.assertEqual(len(cq["ignored"]),4)

if __name__=="__main__":
    unittest.main()
