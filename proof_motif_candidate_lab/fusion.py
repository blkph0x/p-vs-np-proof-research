
from theories import combined_unsat
from cdclt import norm_clause,resolve,lit_for,clause_satisfied

def equality_clause_from_equation(affine, eq_index, rep, other):
    mask,rhs=affine.eq[eq_index]
    assert rhs==0 and mask==((1<<rep)|(1<<other))
    # rep OR not other: other -> rep
    return norm_clause((rep+1,-(other+1)))

def hall_clause_for_region(region):
    a={v:False for v in region.vars}
    ps,conf=region.analyze(a,True)
    assert conf is not None and region.verify(conf)
    clause=norm_clause(v+1 for v in conf["disabled"])
    assert set(conf["disabled"])==set(region.vars)
    return clause,conf

def derive_group_unit(affine,region,group_index,width):
    hall,hcert=hall_clause_for_region(region)
    rep=region.vars[0]
    cur=hall; steps=[]; eqclauses=[]
    # combined_unsat stores group equalities in consecutive blocks of width-1
    base=group_index*(width-1)
    for j,other in enumerate(region.vars[1:]):
        ec=equality_clause_from_equation(affine,base+j,rep,other)
        eqclauses.append((ec,base+j))
        out=resolve(cur,ec,other)
        steps.append({"left":cur,"right":ec,"pivot":other,"result":out})
        cur=out
    assert cur==(rep+1,)
    return {"rep":rep,"hall":hall,"hall_cert":hcert,
            "equality_clauses":eqclauses,"steps":steps,"unit":cur}

def final_parity_conflict(affine,reps,groups,width):
    # Last equation is global parity over representatives.
    idx=len(affine.eq)-1
    mask,rhs=affine.eq[idx]
    assert set(reps)=={v for v in range(mask.bit_length()) if (mask>>v)&1}
    # Assignment reps=true violates because combined_unsat chooses opposite parity.
    clause=norm_clause(-(v+1) for v in reps)
    # This clause blocks the all-true violating assignment and is entailed by parity equation.
    return idx,clause

def fused_refutation(groups,width):
    n,A,R=combined_unsat(groups,width)
    units=[];proof=[]
    reps=[]
    for gi,region in enumerate(R):
        d=derive_group_unit(A,region,gi,width)
        reps.append(d["rep"])
        proof.append({"kind":"hall","clause":d["hall"],"cert":d["hall_cert"],"region":gi})
        for c,ei in d["equality_clauses"]:
            proof.append({"kind":"equality","clause":c,"eq_index":ei,
                          "rep":d["rep"],"other":abs(c[1])-1})
        for st in d["steps"]:
            proof.append({"kind":"resolve",**st})
        units.append(d["unit"])

    pidx,pclause=final_parity_conflict(A,reps,groups,width)
    proof.append({"kind":"parity-conflict","eq_index":pidx,"clause":pclause,
                  "reps":reps})
    cur=pclause
    for rep,u in zip(reps,units):
        out=resolve(cur,u,rep)
        proof.append({"kind":"resolve","left":cur,"right":u,"pivot":rep,"result":out})
        cur=out
    assert cur==()
    return {"nvars":n,"affine":A,"regions":R,"units":units,
            "reps":reps,"proof":proof,"empty":cur}

def verify_fused(obj):
    A=obj["affine"]; R=obj["regions"]
    for e in obj["proof"]:
        if e["kind"]=="hall":
            if not R[e["region"]].verify(e["cert"]):return False
            disabled=e["cert"]["disabled"]
            if norm_clause(v+1 for v in disabled)!=tuple(e["clause"]):return False
        elif e["kind"]=="equality":
            mask,rhs=A.eq[e["eq_index"]]
            rep=e["rep"];other=e["other"]
            if rhs!=0 or mask!=((1<<rep)|(1<<other)):return False
            if tuple(e["clause"])!=norm_clause((rep+1,-(other+1))):return False
        elif e["kind"]=="parity-conflict":
            mask,rhs=A.eq[e["eq_index"]]
            reps=e["reps"]
            # all reps true must violate row
            if (len(reps)&1)==rhs:return False
            if tuple(e["clause"])!=norm_clause(-(v+1) for v in reps):return False
        elif e["kind"]=="resolve":
            if resolve(tuple(e["left"]),tuple(e["right"]),e["pivot"])!=tuple(e["result"]):
                return False
    return obj["empty"]==()
