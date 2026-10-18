"""Run python -m unittest -v test_lab from this directory.

Full n<=26 C++ re-scan: run `python run_lab.py` separately.
"""
import json, pathlib, random, unittest, math
from core_math import (graphic_cut_code_columns,graphic_edges,exact_graphic_connectivity_audit,
                       balanced_pathwidth_lower_bound, exact_clique_matroid_pathwidth,
                       connectivity,rank_vectors,graphic_matroid_internal_four_connected_theorem)
from native_graph_solvers import (stoer_wagner_min_cut,complete_graph_edges,
                                  girth_shortest_cycle,brute_min_cut)
from trellis_solver import trellis_min_nonzero_generator,enumerate_min_distance
from probabilistic_width import existence_bound

ROOT=pathlib.Path(__file__).parent

def gen_from_cols(cols,k):
    return tuple(sum((1<<j) for j,col in enumerate(cols) if (col>>i)&1)
                 for i in range(k))


class LabTest(unittest.TestCase):
    def test_graphic_incidences(self):
        for t in range(5,9):
            cols=graphic_cut_code_columns(t)
            self.assertEqual(rank_vectors(cols),t-1)
            self.assertTrue(graphic_matroid_internal_four_connected_theorem(t))
            self.assertEqual(exact_clique_matroid_pathwidth(t),t-2)

    def test_small_exhaustive_internal4(self):
        for t in [5,6]:
            self.assertTrue(exact_graphic_connectivity_audit(t)['valid'])

    def test_balanced_bound_exact_arithmetic(self):
        for t in [5,6,12,16,32,64,128,256]:
            c=balanced_pathwidth_lower_bound(t)
            self.assertLessEqual(c['certified_trellis_width_lower_bound'],t-2)
            self.assertGreaterEqual(c['required_vertices_a']*(c['required_vertices_a']-1)//2,c['a'])
            self.assertEqual(c['exact_trellis_width'],t-2)

    def test_graph_algorithm_exact_small(self):
        rng=random.Random(5)
        for n in range(4,8):
            for _ in range(5):
                E=[(u,v) for u in range(n) for v in range(u+1,n) if rng.randrange(2)]
                if not E:continue
                d,S=stoer_wagner_min_cut(n,E)
                self.assertEqual(d,brute_min_cut(n,E))
                self.assertEqual(d,sum((u in S)!=(v in S) for u,v in E))

    def test_native_complete_graph_distances(self):
        for t in [5,6,8,16,32]:
            E=complete_graph_edges(t)
            cut,S=stoer_wagner_min_cut(t,E)
            girth,_=girth_shortest_cycle(t,E)
            self.assertEqual(cut,t-1);self.assertEqual(girth,3)

    def test_trellis_matches_brute(self):
        for t in [5,6,7,8]:
            cols=graphic_cut_code_columns(t)
            G=gen_from_cols(cols,t-1)
            d,w,visited=enumerate_min_distance(G)
            out=trellis_min_nonzero_generator(G,len(cols))
            self.assertEqual(d,t-1)
            self.assertEqual(out['distance'],d)
            self.assertEqual(out['max_exact_syndrome_states'],1<<(t-2))

    def test_trellis_dimension_uses_generator_rank(self):
        out=trellis_min_nonzero_generator((3,3,0),2)
        self.assertEqual(out['dimension'],1)
        self.assertEqual(out['dimension']+out['parity_check_rank'],2)
        self.assertEqual(out['distance'],2)
        self.assertEqual(out['word'],3)

    def test_random_cpp_certificate_witnesses(self):
        checks=json.loads((ROOT/'random_code_audits.json').read_text())
        for r in checks:
            n=r['n'];cols=tuple(r['columns']);w=r['central_witness_mask']
            self.assertEqual(rank_vectors(cols),r['k'])
            self.assertEqual(connectivity(cols,w),r['central_min_lambda'])
            self.assertEqual(sum(r['central_lambda_histogram']),r['central_checked'])
            self.assertEqual(r['central_checked'],math.comb(n,n//2)//2)
            if r['mode']=='full':
                self.assertEqual(r['checked_unordered_cuts'],(1<<(n-1))-1)
                self.assertEqual(r['three_conn_violations'],0)
                self.assertEqual(r['internal4_violations'],0)

    def test_probabilistic_existence(self):
        for k in [14,20,40,100,500,1000]:
            x=existence_bound(k)
            self.assertTrue(x['positive_probability_of_full_rank_good_code'])
            self.assertGreaterEqual(x['certified_existence_lambda_lower_bound'],0)
            self.assertLess(x['bad_balanced_cut_probability_upper']+x['full_rank_failure_probability_upper'],1)

if __name__=='__main__':unittest.main()
