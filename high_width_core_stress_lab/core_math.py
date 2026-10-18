"""Explicit graphic-code lower bounds and small exact matroid checks.

All GF(2) ranks are of column sets of an explicitly specified binary generator matrix.
None of these routines asserts polynomial algorithms for general minimum-distance problems.
"""
from __future__ import annotations
from itertools import combinations
from math import comb
import math, random


def rank_vectors(cols: list[int] | tuple[int, ...]) -> int:
    basis={}
    for v in cols:
        x=int(v)
        while x:
            p=x.bit_length()-1
            if p in basis:
                x ^= basis[p]
            else:
                basis[p]=x
                break
    return len(basis)


def graphic_edges(t: int) -> list[tuple[int,int]]:
    return list(combinations(range(t),2))


def graphic_cut_code_columns(t: int) -> tuple[int,...]:
    """Reduced vertex-edge incidence columns. k=t-1, n=C(t,2)."""
    cols=[]
    for u,v in graphic_edges(t):
        w=0
        if u<t-1: w |= 1<<u
        if v<t-1: w |= 1<<v
        cols.append(w)
    return tuple(cols)


def span_rank_of_mask(cols: tuple[int,...], S:int) -> int:
    subset=[]
    while S:
        bit=S&-S; j=bit.bit_length()-1
        subset.append(cols[j]); S ^= bit
    return rank_vectors(subset)


def connectivity(cols:tuple[int,...],S:int)->int:
    n=len(cols); full=(1<<n)-1
    return span_rank_of_mask(cols,S)+span_rank_of_mask(cols,full^S)-rank_vectors(cols)


def min_clique_vertices_for_edges(e:int)->int:
    if e<=0:return 1
    # exact integer computation, avoid float roundoff
    s=(1+math.isqrt(1+8*e))//2
    while comb(s,2)<e:s+=1
    while s>1 and comb(s-1,2)>=e:s-=1
    return s


def balanced_pathwidth_lower_bound(t:int)->dict:
    """Certified universal lower bound for any ordering of edges of K_t.

    Any graph with rank r has at most C(r+1,2) edges. Therefore at prefix
    floor(C(t,2)/2), lambda >= s(A)+s(B)-t-1.
    """
    if t<5:raise ValueError('t must be >=5')
    n=comb(t,2)
    a=n//2;b=n-a
    sa=min_clique_vertices_for_edges(a)
    sb=min_clique_vertices_for_edges(b)
    L=max(0,sa+sb-t-1)
    return {"t":t,"n_edges":n,"incidence_code_dimension":t-1,
            "dual_cycle_code_dimension":n-t+1,"a":a,"b":b,
            "required_vertices_a":sa,"required_vertices_b":sb,
            "certified_trellis_width_lower_bound":L,
            "exact_trellis_width":t-2,
            "exact_min_trellis_states":1<<(t-2),
            "min_trellis_states_at_least":1<<L,
            "cut_code_min_distance":t-1,"cycle_code_min_distance":3,
            "native_graph_solution":"mincut for incidence/cut code; shortest cycle for dual cycle code"}


def graphic_matroid_internal_four_connected_theorem(t:int)->bool:
    """For t>=5, proof is in THEOREMS.md; no exhaustive large-instance search."""
    return t>=5


def graph_cut_rank_from_components(t:int,edge_mask:int)->int:
    """Independent graph-algorithm rank check: r(E')=t-number_of_components(V,E')."""
    par=list(range(t))
    def find(x):
        while par[x]!=x:
            par[x]=par[par[x]];x=par[x]
        return x
    for j,(u,v) in enumerate(graphic_edges(t)):
        if (edge_mask>>j)&1:
            a=find(u);b=find(v)
            if a!=b: par[a]=b
    return t-len({find(v) for v in range(t)})


def exact_graphic_connectivity_audit(t:int)->dict:
    """Only use t<=6: 2^C(t,2) subsets."""
    n=comb(t,2)
    if n>15:raise ValueError('audit is bounded to <=15 edges')
    cols=graphic_cut_code_columns(t); full=(1<<n)-1
    failed=[]; low3=[]
    for S in range(1,full):
        if not (S&1):continue
        a=S.bit_count();b=n-a
        lam=connectivity(cols,S)
        graph_lam=graph_cut_rank_from_components(t,S)+graph_cut_rank_from_components(t,full^S)-(t-1)
        if lam!=graph_lam:
            failed.append(('rank',S,lam,graph_lam))
        if a>=2 and b>=2 and lam<=1:
            failed.append(('3conn',S,lam,a,b))
        if a>=3 and b>=3 and lam==2:
            minor=S if a==3 else (full^S if b==3 else None)
            triangle=False
            if minor is not None:
                arcs=[graphic_edges(t)[j] for j in range(n) if (minor>>j)&1]
                vs={v for pair in arcs for v in pair}
                triangle=len(vs)==3 and len(arcs)==3
            low3.append((S,triangle))
            if not triangle:
                failed.append(('not_internal4',S,lam,a,b))
    return {'t':t,'n_edges':n,'checked_unordered_cuts':2**(n-1)-1,
            'lambda2_3separations':len(low3),'all_small_3seps_triangles':all(x[1] for x in low3),
            'failed_checks':failed,'valid':not failed}


def sampled_order_width(cols:tuple[int,...],order:tuple[int,...])->int:
    S=0;best=0
    for j in order:
        S|=1<<j
        best=max(best,connectivity(cols,S))
    return best


def vertex_star_order(t:int)->tuple[int,...]:
    """A simple reproducible heuristic, all edges grouped by lowest vertex index."""
    return tuple(range(comb(t,2)))


def exact_clique_matroid_pathwidth(t:int)->int:
    """Elementary all-size theorem: pw(M(K_t)) = t-2 for t>=3.

    Lower: immediately before first prefix whose edges connect all t vertices,
    prefix A has precisely two graph components; B is connected because K_t
    has every cross-component edge in B. Thus lambda(A)=t-2.

    Upper: order edges (u,v) lexicographically with u<v; each prefix has
    connectivity at most t-2. See THEOREMS.md for a proof.
    """
    if t<3:raise ValueError('t>=3')
    return t-2
