from interp_engine import Proof, norm_clause, ast_literal_count, support, evalf, Lit, And
from itertools import product


def build_fused_partitioned_proof(groups,width):
    """
    A side: for every group, Hall OR plus implications member -> representative.
    B side: one clause excluding the all-true representative assignment.

    This B clause is the clausal theory lemma produced by the final opposite-parity row
    under the all-true A consequence. The proof derives every representative unit from A,
    then resolves them into B's clause.
    """
    A=[]; group_meta=[]; reps=[]
    for g in range(groups):
        vs=list(range(g*width,(g+1)*width)); r=vs[0]; reps.append(r)
        hall_idx=len(A); A.append(tuple(v+1 for v in vs))
        imp=[]
        for x in vs[1:]:
            imp.append((x,len(A)))
            A.append(norm_clause((r+1,-(x+1))))
        group_meta.append((vs,r,hall_idx,imp))
    B=[tuple(-(r+1) for r in reps)]
    P=Proof(A,B)
    unit_nodes=[]
    for vs,r,hidx,imp in group_meta:
        cur=P.leaf('A',hidx)
        for x,aidx in imp:
            cur=P.res(cur,P.leaf('A',aidx),x)
        assert P.nodes[cur]['clause']==(r+1,)
        unit_nodes.append(cur)
    cur=P.leaf('B',0)
    for r,u in zip(reps,unit_nodes):
        cur=P.res(cur,u,r)
    assert P.nodes[cur]['clause']==()
    return P,cur,reps


def extract_raw_interpolant(groups,width):
    P,root,reps=build_fused_partitioned_proof(groups,width)
    I=P.mcmillan(root)
    return P,I,reps


def A_semantics(groups,width,bits):
    # Hall + equalities per group means every member of every group must be true.
    for g in range(groups):
        vs=range(g*width,(g+1)*width)
        vals=[bits[v] for v in vs]
        if not any(vals): return False
        if len(set(vals))!=1: return False
    return True


def B_semantics(groups,width,bits):
    reps=[g*width for g in range(groups)]
    # Opposite parity to all-true reps.
    target=1-(groups&1)
    return (sum(bits[r] for r in reps)&1)==target


def xor_interpolant(groups,width,bits):
    reps=[g*width for g in range(groups)]
    return (sum(bits[r] for r in reps)&1)==(groups&1)


def verify_interpolants_exhaustive(groups,width,I):
    n=groups*width
    if n>18: raise ValueError('audit only')
    for bits in product([0,1],repeat=n):
        a={i:bits[i] for i in range(n)}
        if A_semantics(groups,width,bits) and not evalf(I,a): return False
        if B_semantics(groups,width,bits) and evalf(I,a): return False
        if A_semantics(groups,width,bits) and not xor_interpolant(groups,width,bits): return False
        if B_semantics(groups,width,bits) and xor_interpolant(groups,width,bits): return False
    return True


def raw_interpolant_expected(groups,width):
    return And(*(Lit(g*width,True) for g in range(groups)))
