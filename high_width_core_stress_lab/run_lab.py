#!/usr/bin/env python3
"""Re-run the numerical and exact small audits; compile rank_audit.cpp first.

python run_lab.py, from this directory. The longer exhaustive n=26 scan takes about 15s
on the original host. Set FAST_AUDIT=1 to skip the high-cost re-scan and use stored results.
"""
from __future__ import annotations
import csv, hashlib, json, math, os, pathlib, random, subprocess, time
from core_math import (balanced_pathwidth_lower_bound,graphic_edges, graphic_cut_code_columns,
                       graphic_matroid_internal_four_connected_theorem,exact_clique_matroid_pathwidth,
                       exact_graphic_connectivity_audit,connectivity,rank_vectors,
                       sampled_order_width,vertex_star_order)
from native_graph_solvers import complete_graph_edges,stoer_wagner_min_cut,girth_shortest_cycle,brute_min_cut
from probabilistic_width import existence_bound
from trellis_solver import trellis_min_nonzero_generator,enumerate_min_distance

ROOT=pathlib.Path(__file__).parent

def gen_from_cols(cols,k):
    return tuple(sum((1<<j) for j,c in enumerate(cols) if ((c>>i)&1)) for i in range(k))

def greedy_coordinate_order(cols):
    n=len(cols)
    R=rank_vectors(cols)
    S=0;left=[];remaining=set(range(n));order=[]
    while remaining:
        best=None
        for v in remaining:
            rr=rank_vectors(left+[cols[v]])
            rr_comp=rank_vectors([cols[j] for j in remaining if j!=v])
            score=(rr+rr_comp-R, v)
            if best is None or score<best[0]:best=(score,v)
        v=best[1]
        order.append(v);left.append(cols[v]);remaining.remove(v)
    return tuple(order)

def audit_random():
    audited=[]
    binary=ROOT/'rank_audit'
    if not binary.exists():
        subprocess.run(['g++','-O3','-std=c++17',str(ROOT/'rank_audit.cpp'),'-o',str(binary)],check=True)
    old_path=ROOT/'random_code_audits.json'
    if os.environ.get('FAST_AUDIT') and old_path.exists():
        raw=json.loads(old_path.read_text())
    else:
        raw=[]
        for n,mode in [(18,'full'),(20,'full'),(22,'full'),(24,'full'),(26,'full'),(28,'balanced')]:
            r=json.loads(subprocess.check_output([str(binary),str(n),str(n//2),'20261017',mode],text=True))
            raw.append(r)
        old_path.write_text(json.dumps(raw,indent=2))
    random_rows=[]
    for x in raw:
        n=x['n'];cols=tuple(x['columns']);k=x['k'];S=x['central_witness_mask']
        assert len(cols)==n and rank_vectors(cols)==k
        assert connectivity(cols,S)==x['central_min_lambda']
        assert sum(x['central_lambda_histogram'])==x['central_checked']
        assert x['central_checked']==math.comb(n,n//2)//2
        if x['mode']=='full':
            assert x['checked_unordered_cuts']==(1<<(n-1))-1
            assert x['three_conn_violations']==0
            assert x['internal4_violations']==0
        else:
            assert x['mode']=='balanced'
        G=gen_from_cols(cols,k)
        low,_word,enum=enumerate_min_distance(G)
        natural=trellis_min_nonzero_generator(G,n,order=tuple(range(n)))
        order=greedy_coordinate_order(cols)
        greedy=trellis_min_nonzero_generator(G,n,order=order)
        assert natural['distance']==low==greedy['distance']
        actual_order_width=(greedy['max_exact_syndrome_states']-1).bit_length()
        random_rows.append({
            'n':n,'code_dimension':k,'fully_certified_internal4':x['mode']=='full',
            'exhaustive_cuts_verified':x['checked_unordered_cuts'],
            'certified_min_middle_lambda':x['central_min_lambda'],
            'central_witness':S,
            'min_distance':low,'codewords_enumerated':enum,
            'natural_max_trellis_states':natural['max_exact_syndrome_states'],
            'greedy_max_trellis_states':greedy['max_exact_syndrome_states'],
            'greedy_trellis_width':actual_order_width,
            'greedy_minweight_time_seconds':round(greedy['seconds'],5),
            'natural_minweight_time_seconds':round(natural['seconds'],5),
            'random_generator_columns_sha256':hashlib.sha256(','.join(map(str,cols)).encode()).hexdigest()
        })
        print('random',n,'balanced LB',x['central_min_lambda'],
              'internal4',x['mode']=='full','trellis greedy states',greedy['max_exact_syndrome_states'],flush=True)
    (ROOT/'random_code_results.json').write_text(json.dumps(random_rows,indent=2))
    return random_rows


def audit_graphic():
    rows=[]
    for t in [5,6,8,10,12,16,32,64,128,256]:
        cert=balanced_pathwidth_lower_bound(t)
        assert graphic_matroid_internal_four_connected_theorem(t)
        exact_width=exact_clique_matroid_pathwidth(t)
        assert exact_width==t-2
        assert cert['certified_trellis_width_lower_bound']<=exact_width
        edges=complete_graph_edges(t)
        c,cut=stoer_wagner_min_cut(t,edges)
        girth,_=girth_shortest_cycle(t,edges)
        assert c==t-1 and girth==3
        if t<=6:
            exhaustive=exact_graphic_connectivity_audit(t)
            assert exhaustive['valid']
        trellis_states=None;trellis_secs=None
        if t<=12:
            cols=graphic_cut_code_columns(t)
            G=gen_from_cols(cols,t-1)
            trellis=trellis_min_nonzero_generator(G,len(cols),order=vertex_star_order(t))
            assert trellis['distance']==t-1
            assert trellis['max_exact_syndrome_states']==1<<(t-2)
            trellis_states=trellis['max_exact_syndrome_states']
            trellis_secs=round(trellis['seconds'],6)
        rows.append({
            't_clique_vertices':t,'n_code_coordinates':cert['n_edges'],
            'internally4_proved_all_t_ge5':True,
            'cut_code_dimension':t-1,
            'dual_cycle_code_dimension':cert['dual_cycle_code_dimension'],
            'certified_width_lower_bound':cert['certified_trellis_width_lower_bound'],
            'certified_width_upper_bound':t-2,
            'certified_exact_pathwidth':exact_width,
            'exact_optimal_max_trellis_states_power_of_2':f"2^{exact_width}",
            'at_least_trellis_states_power_of_2':f"2^{cert['certified_trellis_width_lower_bound']}",
            'mincut_minweight':c,'cycle_girth_minweight':girth,
            'trellis_dp_states_if_executed':trellis_states,
            'trellis_dp_seconds_if_executed':trellis_secs,
        })
        print('graphic K',t,'n',cert['n_edges'],'width>=',cert['certified_trellis_width_lower_bound'],
              'width<=',t-2,'native min',c,girth,flush=True)
    (ROOT/'graphic_code_results.json').write_text(json.dumps(rows,indent=2))
    return rows


def check_native_generic_graphs():
    rng=random.Random(20261017)
    out=[]
    for n in range(4,9):
        for case in range(15):
            edges=[(u,v) for u in range(n) for v in range(u+1,n) if rng.random()<.5]
            if not edges:continue
            sw,cut=stoer_wagner_min_cut(n,edges)
            brute=brute_min_cut(n,edges)
            assert sw==brute,(n,case,edges,sw,brute)
            # certificate cut weight recomputed from original graph
            side=set(cut)
            assert sum((u in side)!=(v in side) for u,v in edges)==sw
            out.append({'n':n,'case':case,'mincut':sw,'edges':len(edges)})
    return out


def write_csv(path,rows):
    with path.open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)


def main():
    rand=audit_random()
    graphic=audit_graphic()
    native=check_native_generic_graphs()
    prob=[existence_bound(k) for k in [14,20,40,100,256,500,1000]]
    for p in prob:assert p['positive_probability_of_full_rank_good_code']
    (ROOT/'probabilistic_existence_results.json').write_text(json.dumps(prob,indent=2))
    (ROOT/'native_graph_audits.json').write_text(json.dumps(native,indent=2))
    write_csv(ROOT/'random_code_results.csv',rand)
    write_csv(ROOT/'graphic_code_results.csv',graphic)
    write_csv(ROOT/'probabilistic_existence_results.csv',prob)
    print('Tests: random',len(rand),'graphic',len(graphic),'native mincut crosschecks',len(native),flush=True)

if __name__=='__main__':main()
