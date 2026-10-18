"""Exact minimum-weight nonzero codeword via suffix-syndrome trellis DP.

The input is a binary generator (row integer bitmasks). Output is verified by rechecking
parity constraints; finite instances compare to direct enumeration. The approach is exact
but worst-case exponential in trellis width.
"""
from __future__ import annotations
from typing import Sequence
import time
from core_math import rank_vectors


def kernel_basis(rows:Sequence[int],n:int)->tuple[int,...]:
    A=list(map(int,rows)); piv=[]; row=0
    for col in range(n):
        bit=1<<col
        for idx in range(row,len(A)):
            if A[idx]&bit:
                A[row],A[idx]=A[idx],A[row]
                break
        else:continue
        for idx in range(len(A)):
            if idx!=row and (A[idx]&bit):A[idx]^=A[row]
        piv.append(col);row+=1
        if row==len(A):break
    pset=set(piv)
    basis=[]
    for f in range(n):
        if f in pset:continue
        x=1<<f
        for r,p in reversed(list(zip(A[:row],piv))):
            if (r&~(1<<p)&x).bit_count()&1:x|=1<<p
        basis.append(x)
    assert len(basis)==n-rank_vectors(rows)
    assert all((r&x).bit_count()%2==0 for r in rows for x in basis)
    return tuple(basis)


def column_from_rows(rows:Sequence[int],j:int)->int:
    return sum((1<<i) for i,r in enumerate(rows) if (r>>j)&1)


def add_basis(B:tuple[int,...],x:int)->tuple[int,...]:
    a=list(B)
    while x:
        b=x.bit_length()-1
        if a[b]:x^=a[b]
        else:
            a[b]=x
            break
    return tuple(a)


def is_in_span(B:tuple[int,...],x:int)->bool:
    while x:
        b=x.bit_length()-1
        if B[b]:x^=B[b]
        else:return False
    return True


def trellis_min_nonzero_generator(G:Sequence[int],n:int,order:Sequence[int]|None=None,
                                  reconstruct:bool=True)->dict:
    start=time.perf_counter()
    if order is None:order=list(range(n))
    order=tuple(order)
    if sorted(order)!=list(range(n)):raise ValueError('order must be permutation of n coordinates')
    H=kernel_basis(G,n)
    r=len(H)
    cols=[column_from_rows(H,j) for j in order]
    # suffix_span[i] = linear span of H columns with j>=i
    suffix=[None]*(n+1)
    suffix[n]=tuple([0]*r)
    for i in range(n-1,-1,-1):
        suffix[i]=add_basis(suffix[i+1],cols[i])
    current={(0,False):0}
    history=[]
    state_counts=[1]
    for i,hcol in enumerate(cols):
        nxt={}; parents={}
        for (sy,used),oldcost in current.items():
            for bit in (0,1):
                new_sy=sy^(hcol if bit else 0)
                if not is_in_span(suffix[i+1],new_sy):continue
                key=(new_sy,used or bool(bit))
                cost=oldcost+bit
                if key not in nxt or cost<nxt[key]:
                    nxt[key]=cost
                    if reconstruct:parents[key]=((sy,used),bit)
        current=nxt
        state_counts.append(len({k[0] for k in nxt}))
        if reconstruct:history.append(parents)
    distance=current.get((0,True),None)
    word=None
    if distance is not None and reconstruct:
        key=(0,True); bits=[0]*n
        for i in range(n-1,-1,-1):
            old,bit=history[i][key]
            bits[order[i]]=bit
            key=old
        word=sum((1<<j) for j,b in enumerate(bits) if b)
        assert word.bit_count()==distance
        assert all((h&word).bit_count()%2==0 for h in H)
    return {'n':n,'dimension':rank_vectors(G),'parity_check_rank':r,
            'distance':distance,'word':word,'max_exact_syndrome_states':max(state_counts),
            'state_profile':state_counts,'sum_exact_syndrome_states':sum(state_counts),
            'seconds':time.perf_counter()-start}


def enumerate_min_distance(G:Sequence[int])->tuple[int|None,int|None,int]:
    k=len(G);minw=None;bestword=None
    current=0;last=0
    for i in range(1,1<<k):
        gray=i^(i>>1)
        flip=gray^last
        current^=G[flip.bit_length()-1]
        w=current.bit_count()
        if w and (minw is None or w<minw):
            minw=w;bestword=current
        last=gray
    return minw,bestword,1<<k
