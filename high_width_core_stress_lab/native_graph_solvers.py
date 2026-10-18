"""Polynomial algorithms for graphic binary codes (not generic affine+weight merge).

- Cut-space code of connected G with at least one edge: minimum nonzero Hamming
  weight = global min cut weight. For disconnected G, global min cut is zero;
  nonzero code minimum weight requires minimizing over nontrivial components.
- Cycle-space code of G: minimum nonzero Hamming weight = girth/shortest cycle.
These are native graph algorithms; the generic minimum-distance problem remains NP-hard.
"""
from collections import deque
from itertools import combinations
import time


def stoer_wagner_min_cut(n:int,edges:list[tuple[int,int]])->tuple[int,tuple[int,...]]:
    """Global undirected unweighted min cut; O(n^3) dense implementation."""
    if n<2: return 0,()
    adj=[[0]*n for _ in range(n)]
    for u,v in edges:
        if u==v:continue
        adj[u][v]+=1;adj[v][u]+=1
    members=[{i} for i in range(n)]
    active=list(range(n))
    best=float('inf');best_side=()
    while len(active)>1:
        used=set();weights=[0]*n;prev=None
        for step in range(len(active)):
            v=max((x for x in active if x not in used),key=lambda x:weights[x])
            used.add(v)
            if step==len(active)-1:
                if weights[v]<best:
                    best=weights[v];best_side=tuple(sorted(members[v]))
                if prev is not None:
                    for w in active:
                        if w!=v and w!=prev:
                            adj[prev][w]+=adj[v][w]
                            adj[w][prev]=adj[prev][w]
                    members[prev] |= members[v]
                    active.remove(v)
                break
            prev=v
            for w in active:
                if w not in used:weights[w]+=adj[v][w]
    return int(best),best_side


def girth_shortest_cycle(n:int,edges:list[tuple[int,int]])->tuple[int|None,tuple[int,...]|None]:
    """BFS from each root; detects the shortest undirected simple cycle."""
    adj=[[] for _ in range(n)]
    for u,v in edges:
        adj[u].append(v);adj[v].append(u)
    best=None;best_edge=None
    for src in range(n):
        dist=[-1]*n;par=[-1]*n
        q=deque([src]);dist[src]=0
        while q:
            u=q.popleft()
            for v in adj[u]:
                if dist[v]==-1:
                    dist[v]=dist[u]+1;par[v]=u;q.append(v)
                elif par[u]!=v:
                    length=dist[u]+dist[v]+1
                    # Overlap of root paths can make naive length an overestimate,
                    # but never underestimate the true cycle. Keeping minimum over
                    # all BFS roots yields exact graph girth.
                    if best is None or length<best:
                        best=length;best_edge=(u,v,src)
    return best,best_edge


def brute_min_cut(n:int,edges:list[tuple[int,int]])->int:
    mn=None
    for mask in range(1,(1<<n)-1):
        c=sum(((mask>>u)&1)!=((mask>>v)&1) for u,v in edges)
        if mn is None or c<mn:mn=c
    return mn


def complete_graph_edges(t:int)->list[tuple[int,int]]:
    return list(combinations(range(t),2))
