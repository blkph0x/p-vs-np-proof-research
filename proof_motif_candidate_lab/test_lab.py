
import unittest, importlib.util, sys
from pathlib import Path

ROOT=Path(__file__).parent
sys.path.insert(0,str(ROOT))
spec=importlib.util.spec_from_file_location("pm",ROOT/"miner.py")
pm=importlib.util.module_from_spec(spec);spec.loader.exec_module(pm)
import fusion as fu
import hard_controls as hc

class TestMotifMiner(unittest.TestCase):
    def test_or_collapse(self):
        cs,heads,n=pm.hall_groups(16,8)
        m=pm.mine_all(cs)
        self.assertEqual(len(m["OR_COLLAPSE"]),16)
        self.assertEqual(max(pm.macro_recurrence(m["OR_COLLAPSE"]).values()),16)
        units,_=pm.derive_units_from_macros(m["OR_COLLAPSE"])
        self.assertEqual(set(units),set(heads))

    def test_amo_exact_and_near(self):
        cs,vs=pm.amo_fixture(12)
        self.assertEqual(len(pm.mine_all(cs)["AMO"]),1)
        bad=pm.mutate_remove_one(cs,0)
        self.assertEqual(len(pm.mine_all(bad)["AMO"]),0)

    def test_xor_and_ite(self):
        cs,meta,n=pm.xor3_fixture(8)
        self.assertEqual(len(pm.mine_all(cs)["XOR"]),8)
        self.assertEqual(len(pm.mine_all(pm.mutate_remove_one(cs,0))["XOR"]),7)
        cs,meta,n=pm.ite_fixture(8)
        self.assertEqual(len(pm.mine_all(cs)["ITE"]),8)
        self.assertEqual(len(pm.mine_all(pm.mutate_remove_one(cs,0))["ITE"]),7)

    def test_equivalence_requires_both_directions(self):
        cs,cls,n=pm.equivalence_fixture(4,4)
        self.assertEqual(len(pm.mine_all(cs)["equivalence"]),4)
        one=[]
        for cl in cls:
            r=cl[0]
            for x in cl[1:]:
                one.append(pm.norm_clause((pm.lit(r,False),pm.lit(x,True))))
        self.assertEqual(len(pm.mine_all(one)["equivalence"]),0)

    def test_receiver_certificate(self):
        cs,heads,n=pm.hall_groups(16,4)
        m=pm.mine_all(cs);units,_=pm.derive_units_from_macros(m["OR_COLLAPSE"])
        p=sum(1 for h in heads if units[h])&1
        cert={"kind":"AFFINE","support":tuple(heads),"rhs":p^1}
        c=pm.propose_from_receiver_certificate(units,cert,trusted_affine=[(tuple(heads),p^1)])
        self.assertEqual(len(c),1)
        self.assertTrue(pm.verify_interface_candidate(units,c[0]))
        self.assertEqual(pm.propose_from_receiver_certificate(units,cert,trusted_affine=[]),[])

    def test_source_catalog(self):
        cs,vs=pm.amo_fixture(10)
        cat=pm.candidate_catalog(pm.mine_all(cs),cs)
        best,good=pm.select_closing_candidate(cat,{vs[1]:True,vs[8]:True},10)
        self.assertEqual(best["kind"],"PB_AMO")

    def test_actual_fused_proof(self):
        obj=fu.fused_refutation(16,8)
        self.assertTrue(fu.verify_fused(obj))
        cs=[tuple(e["clause"]) for e in obj["proof"] if e["kind"] in ("hall","equality")]
        m=pm.mine_all(cs)
        self.assertEqual(len(m["OR_COLLAPSE"]),16)
        units,_=pm.derive_units_from_macros(m["OR_COLLAPSE"])
        e=[x for x in obj["proof"] if x["kind"]=="parity-conflict"][0]
        mask,rhs=obj["affine"].eq[e["eq_index"]]
        S=tuple(v for v in range(obj["nvars"]) if (mask>>v)&1)
        cert={"kind":"AFFINE","support":S,"rhs":rhs}
        c=pm.propose_from_receiver_certificate(units,cert,trusted_affine=[(S,rhs)])
        self.assertEqual(len(c),1)
        self.assertEqual(c[0]["kind"],"XOR_INTERPOLANT")

    def test_clique_coloring_hard_control(self):
        f=hc.clique_coloring_cnf(5,3)
        self.assertTrue(hc.exhaustive_graph_separation(5,3))
        Ash,Am,Ac=hc.shared_candidates(f["A"],f["shared"])
        Bsh,Bm,Bc=hc.shared_candidates(f["B"],f["shared"])
        self.assertEqual(Ash,[])
        self.assertEqual(Bsh,[])

if __name__=="__main__":
    unittest.main()
