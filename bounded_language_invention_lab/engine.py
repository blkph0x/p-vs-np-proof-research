
from itertools import product, permutations, combinations
from collections import defaultdict
import math, random, hashlib, time

def norm_clause(c):
    s=set(int(x) for x in c)
    if any(-x in s for x in s):
        return None
    return tuple(sorted(s,key=lambda z:(abs(z),z<0)))

def var(lit): return abs(lit)-1
def lit(v,pos=True): return v+1 if pos else -(v+1)

def clause_sat(c,a):
    return any(bool(a[var(L)])==(L>0) for L in c)

def cnf_sat(clauses,a):
    return all(clause_sat(c,a) for c in clauses)

# ---------- exact bounded projection ----------

def project_relation(clauses,boundary,locals_):
    """
    Exact relation on boundary:
       R(x_B) = exists x_L . CNF(B,L)
    Return truth-table integer with assignment index in boundary order.
    """
    B=tuple(boundary); L=tuple(locals_)
    k=len(B); ell=len(L)
    tt=0
    witness={}
    allvars=set(B)|set(L)
    if any(var(Lit) not in allvars for c in clauses for Lit in c):
        raise ValueError("clause contains variable outside declared fragment support")
    for bi,bits in enumerate(product([0,1],repeat=k)):
        ok=False; chosen=None
        base={B[i]:bits[i] for i in range(k)}
        for lbits in product([0,1],repeat=ell):
            a=dict(base);a.update({L[i]:lbits[i] for i in range(ell)})
            if cnf_sat(clauses,a):
                ok=True;chosen=lbits;break
        if ok:
            tt |= 1<<bi
            witness[bits]=chosen
    return tt,witness

def eval_tt(tt,k,bits):
    idx=0
    # product order ([0,0,..],[0,..,1],...): binary bits as ordinary number
    for b in bits:
        idx=(idx<<1)|int(b)
    return (tt>>idx)&1

def relation_density(tt,k):
    return tt.bit_count()/(1<<k)

def permute_tt(tt,k,perm):
    """
    New variable order y_i corresponds to old x_{perm[i]}.
    """
    out=0
    for ybits in product([0,1],repeat=k):
        old=[0]*k
        for i,p in enumerate(perm):
            old[p]=ybits[i]
        val=eval_tt(tt,k,tuple(old))
        if val:
            idx=0
            for b in ybits: idx=(idx<<1)|b
            out |= 1<<idx
    return out

def canonical_relation(tt,k):
    """
    Canonicalize under variable permutation only.
    Exact but O(k! 2^k), intended for fixed k.
    Return canonical tt and permutation attaining it.
    """
    best=None;bestp=None
    for p in permutations(range(k)):
        t=permute_tt(tt,k,p)
        if best is None or t<best:
            best=t;bestp=p
    return best,bestp

# ---------- generic exact representations ----------

def anf_coefficients(tt,k):
    """
    Möbius transform: coefficients indexed by monomial subset bitmask.
    Truth-table indexing uses lexicographic bits; convert to mask order first.
    """
    vals=[0]*(1<<k)
    for mask in range(1<<k):
        bits=tuple((mask>>(k-1-i))&1 for i in range(k))
        vals[mask]=eval_tt(tt,k,bits)
    a=vals[:]
    # variable bit convention in mask doesn't matter for count
    for i in range(k):
        bit=1<<i
        for mask in range(1<<k):
            if mask&bit:
                a[mask] ^= a[mask^bit]
    return a

def anf_description(tt,k):
    a=anf_coefficients(tt,k)
    mons=[m for m,c in enumerate(a) if c]
    refs=sum(m.bit_count() for m in mons)
    # explicit subset masks + constant metadata; declared accounting
    bits=8+len(mons)*(k+1)
    return {"kind":"ANF","terms":len(mons),"var_refs":refs,"bits":bits,"monomials":mons}


def affine_description(tt,k):
    a=anf_coefficients(tt,k)
    mons=[m for m,c in enumerate(a) if c]
    if any(m.bit_count()>1 for m in mons):
        return None
    const=1 if 0 in mons else 0
    support=tuple(i for i in range(k) if (1<<(k-1-i)) in mons or (1<<i) in mons)
    # Because monomial mask indexing uses integer bit positions, expose exact masks too.
    linear_masks=tuple(m for m in mons if m)
    bits=8+k+1
    return {"kind":"AFFINE","constant":const,"linear_masks":linear_masks,
            "bits":bits,"terms":len(mons)}

def symmetric_description(tt,k):
    weight_val={}
    for bits in product([0,1],repeat=k):
        w=sum(bits);v=eval_tt(tt,k,bits)
        if w in weight_val and weight_val[w]!=v:
            return None
        weight_val[w]=v
    accepted=tuple(w for w in range(k+1) if weight_val.get(w,0))
    # k+1 membership bits plus tag
    return {"kind":"WEIGHT","accepted_weights":accepted,"bits":8+(k+1),
            "states":k+2}

def residual_table(tt,k,order,prefix):
    assigned={order[i]:prefix[i] for i in range(len(prefix))}
    rem=order[len(prefix):]
    vals=[]
    for sbits in product([0,1],repeat=len(rem)):
        bits=[0]*k
        for v,b in assigned.items():bits[v]=b
        for i,v in enumerate(rem):bits[v]=sbits[i]
        vals.append(eval_tt(tt,k,tuple(bits)))
    return tuple(vals)

def obdd_nodes_for_order(tt,k,order):
    """
    Count reduced nonterminal OBDD nodes as distinct nonconstant residual functions
    at each level.
    """
    total=0;maxwidth=0
    for d in range(k):
        states=set()
        for p in product([0,1],repeat=d):
            r=residual_table(tt,k,order,p)
            if all(x==r[0] for x in r):
                continue
            states.add(r)
        total += len(states)
        maxwidth=max(maxwidth,len(states))
    return total,maxwidth

def best_obdd_description(tt,k,max_k=7):
    if k>max_k:
        return None
    best=None
    for order in permutations(range(k)):
        nodes,width=obdd_nodes_for_order(tt,k,order)
        rec=(nodes,width,order)
        if best is None or rec[:2]<best[:2]:
            best=rec
    nodes,width,order=best
    refbits=max(1,math.ceil(math.log2(nodes+2)))
    bits=8+nodes*(max(1,math.ceil(math.log2(max(2,k))))+2*refbits)
    return {"kind":"OBDD","nodes":nodes,"max_width":width,"order":order,"bits":bits}

# ---------- small circuit synthesis ----------

def tt_mask_all(k):
    return (1<<(1<<k))-1

def var_tt(k,v):
    t=0
    for bits in product([0,1],repeat=k):
        if bits[v]:
            idx=0
            for b in bits:idx=(idx<<1)|b
            t |= 1<<idx
    return t

def synthesize_small_circuit(target,k,max_gates=5,max_k=4):
    """
    Exact enumerative synthesis over {NOT, AND, OR, XOR}.
    Complete only up to max_gates for k<=max_k.
    Gate count is the cost; inputs/constants cost 0.
    """
    if k>max_k:return None
    ALL=tt_mask_all(k)
    best={}
    by=[{} for _ in range(max_gates+1)]
    def add(f,c,expr):
        if f not in best:
            best[f]=(c,expr);by[c][f]=expr
    add(0,0,("0",))
    add(ALL,0,("1",))
    for v in range(k):add(var_tt(k,v),0,("x",v))
    if target in best:
        return {"kind":"CIRCUIT","gates":0,"expr":best[target][1],"bits":8+k}

    for cost in range(1,max_gates+1):
        # NOT
        for f,e in list(by[cost-1].items()):
            add(ALL^f,cost,("NOT",e))
        # binary commutative gates
        for i in range(cost):
            j=cost-1-i
            if i>j:continue
            A=list(by[i].items()); B=list(by[j].items())
            for ai,(fa,ea) in enumerate(A):
                for bi,(fb,eb) in enumerate(B):
                    if i==j and bi<ai:continue
                    add(fa&fb,cost,("AND",ea,eb))
                    add(fa|fb,cost,("OR",ea,eb))
                    add(fa^fb,cost,("XOR",ea,eb))
        if target in best and best[target][0]==cost:
            refbits=max(1,math.ceil(math.log2(k+cost+2)))
            return {"kind":"CIRCUIT","gates":cost,"expr":best[target][1],
                    "bits":8+cost*(2+2*refbits)}
    return None


def essential_positions(tt,k):
    ess=[]
    for v in range(k):
        found=False
        for bits in product([0,1],repeat=k):
            b2=list(bits);b2[v]^=1
            if eval_tt(tt,k,bits)!=eval_tt(tt,k,tuple(b2)):
                found=True;break
        if found:ess.append(v)
    return tuple(ess)

def coordinate_quotient_description(tt,k):
    """
    Exact bounded semantic quotient:
    - ignore inessential coordinates;
    - record coordinates fixed on every satisfying tuple;
    - merge nonfixed coordinates whose XOR is constant on every satisfying tuple;
    - retain an exact quotient truth table over class representatives.
    """
    sat=[bits for bits in product([0,1],repeat=k) if eval_tt(tt,k,bits)]
    if not sat:
        return {"kind":"COORD_QUOTIENT","constant":0,"ignored":tuple(range(k)),
                "fixed":{},"classes":(),"quotient_tt":0,"quotient_arity":0,"bits":9}
    if len(sat)==(1<<k):
        return {"kind":"COORD_QUOTIENT","constant":1,"ignored":tuple(range(k)),
                "fixed":{},"classes":(),"quotient_tt":1,"quotient_arity":0,"bits":9}

    ess=set(essential_positions(tt,k))
    ignored=tuple(i for i in range(k) if i not in ess)
    fixed={}
    remaining=[]
    for i in sorted(ess):
        vals={b[i] for b in sat}
        if len(vals)==1: fixed[i]=next(iter(vals))
        else: remaining.append(i)

    unused=set(remaining);classes=[]
    while unused:
        r=min(unused);unused.remove(r)
        members=[(r,0)]
        take=[]
        for j in sorted(unused):
            xors={b[j]^b[r] for b in sat}
            if len(xors)==1:
                d=next(iter(xors));members.append((j,d));take.append(j)
        for j in take:unused.remove(j)
        classes.append(tuple(members))

    reps=[cl[0][0] for cl in classes]
    q=len(reps)
    qtt=0
    for rbits in product([0,1],repeat=q):
        full=[0]*k
        # arbitrary ignored coordinates set zero; relation is independent of them
        for i,v in fixed.items():full[i]=v
        for ci,cl in enumerate(classes):
            rb=rbits[ci]
            for j,d in cl:full[j]=rb^d
        val=eval_tt(tt,k,tuple(full))
        if val:
            idx=0
            for b in rbits:idx=(idx<<1)|b
            qtt |= 1<<idx

    vb=max(1,math.ceil(math.log2(max(2,k))))
    dep_count=sum(len(cl)-1 for cl in classes)
    bits=(8 + len(fixed)*(vb+1) + dep_count*(2*vb+1)
          + (1<<q))
    return {"kind":"COORD_QUOTIENT","constant":None,"ignored":ignored,
            "fixed":fixed,"classes":tuple(classes),
            "quotient_tt":qtt,"quotient_arity":q,"bits":bits}

def eval_coordinate_quotient(desc,k,bits):
    if desc["constant"] is not None:
        return int(desc["constant"])
    # fixed coordinates
    for i,v in desc["fixed"].items():
        ii=int(i)
        if bits[ii]!=v:return 0
    rbits=[]
    for cl in desc["classes"]:
        r=cl[0][0];rb=bits[r];rbits.append(rb)
        for j,d in cl:
            if bits[j]!=(rb^d):return 0
    q=desc["quotient_arity"]
    idx=0
    for b in rbits:idx=(idx<<1)|b
    return (desc["quotient_tt"]>>idx)&1

def verify_coordinate_quotient(tt,k,desc):
    return all(eval_coordinate_quotient(desc,k,bits)==eval_tt(tt,k,bits)
               for bits in product([0,1],repeat=k))

def truth_table_description(tt,k):
    return {"kind":"TRUTH_TABLE","bits":8+(1<<k),"table":tt}

def choose_representation(tt,k):
    cands=[truth_table_description(tt,k), anf_description(tt,k)]
    cq=coordinate_quotient_description(tt,k)
    useful_cq = (
        cq.get("constant") is not None
        or cq.get("quotient_arity",k) < k
        or bool(cq.get("fixed"))
        or bool(cq.get("ignored"))
        or any(len(cl)>1 for cl in cq.get("classes",()))
    )
    if useful_cq and verify_coordinate_quotient(tt,k,cq):cands.append(cq)
    af=affine_description(tt,k)
    if af:cands.append(af)
    s=symmetric_description(tt,k)
    if s:cands.append(s)
    b=best_obdd_description(tt,k)
    if b:cands.append(b)
    c=synthesize_small_circuit(tt,k)
    if c:cands.append(c)
    return min(cands,key=lambda x:(x["bits"],x["kind"])),cands

# ---------- exact generic relation compiler ----------

def direct_cnf_from_relation(tt,k,var_ids=None):
    """
    Exact no-aux CNF by excluding each falsifying assignment.
    """
    if var_ids is None:var_ids=tuple(range(k))
    cs=[]
    for bits in product([0,1],repeat=k):
        if eval_tt(tt,k,bits):continue
        c=tuple(lit(var_ids[i],bits[i]==0) for i in range(k))
        cs.append(norm_clause(c))
    return cs

def xor3_def(a,b,z):
    """
    z = a xor b, direct four-clause CNF.
    """
    # truth table relation on (a,b,z)
    cs=[]
    for av,bv,zv in product([0,1],repeat=3):
        if zv!=(av^bv):
            cs.append(norm_clause((
                lit(a,av==0),lit(b,bv==0),lit(z,zv==0)
            )))
    return cs

def equality2(a,b):
    return [norm_clause((lit(a,False),lit(b,True))),
            norm_clause((lit(a,True),lit(b,False)))]

def auxiliary_parity4_fragment(base=0):
    """
    Boundary x0..x3. Locals y,z.
      y=x0 xor x1
      z=y xor x2
      z=x3
    => even parity over boundary.
    """
    x=list(range(base,base+4));y=base+4;z=base+5
    cs=[]
    cs+=xor3_def(x[0],x[1],y)
    cs+=xor3_def(y,x[2],z)
    cs+=equality2(z,x[3])
    return {"clauses":cs,"boundary":tuple(x),"locals":(y,z),"name":"aux-parity4"}

def relation_fragment(tt,k,base=0,name="relation"):
    B=tuple(range(base,base+k))
    return {"clauses":direct_cnf_from_relation(tt,k,B),
            "boundary":B,"locals":(),"name":name}

def remap_fragment(fragment,boundary_perm=None,var_offset=0,shuffle_seed=None):
    """
    Produce an isomorphic occurrence with renamed vars and optional boundary-role permutation.
    """
    import random
    B=list(fragment["boundary"]);L=list(fragment["locals"])
    allv=B+L
    newids={v:var_offset+i for i,v in enumerate(allv)}
    if boundary_perm is not None:
        # map original boundary role i onto id allocated for position perm[i]
        ids=[newids[v] for v in B]
        for i,v in enumerate(B):
            newids[v]=ids[boundary_perm[i]]
    cs=[]
    for c in fragment["clauses"]:
        nc=[]
        for LIT in c:
            nv=newids[var(LIT)]
            nc.append(lit(nv,LIT>0))
        cs.append(norm_clause(nc))
    if shuffle_seed is not None:
        rng=random.Random(shuffle_seed);rng.shuffle(cs)
    return {"clauses":cs,
            "boundary":tuple(newids[v] for v in B),
            "locals":tuple(newids[v] for v in L),
            "name":fragment.get("name","occ")}

# ---------- dynamic registry / language invention ----------

class LanguageRegistry:
    def __init__(self,max_boundary=8,max_total=12):
        self.max_boundary=max_boundary;self.max_total=max_total
        self.entries={}
        self.occurrences=[]
        self.next_id=0

    def observe(self,fragment):
        B=tuple(fragment["boundary"]);L=tuple(fragment["locals"])
        k=len(B);ell=len(L)
        if k>self.max_boundary or k+ell>self.max_total:
            return {"accepted":False,"reason":"interface-too-wide","k":k,"local":ell}
        t0=time.perf_counter()
        tt,wit=project_relation(fragment["clauses"],B,L)
        can,perm=canonical_relation(tt,k)
        key=(k,can)
        if key not in self.entries:
            best,cands=choose_representation(can,k)
            self.entries[key]={
                "id":f"REL_{self.next_id:04d}",
                "arity":k,"canonical_tt":can,
                "best_rep":best,"all_reps":cands,
                "count":0,"raw_literals":0,
                "projection_work":0,
            }
            self.next_id+=1
        e=self.entries[key]
        e["count"]+=1
        raw_lits=sum(len(c) for c in fragment["clauses"])
        e["raw_literals"]+=raw_lits
        e["projection_work"] += (1<<(k+ell))*max(1,len(fragment["clauses"]))
        sec=time.perf_counter()-t0
        rec={"accepted":True,"relation_id":e["id"],"arity":k,
             "locals":ell,"canonical_perm":perm,"raw_literals":raw_lits,
             "best_kind":e["best_rep"]["kind"],"best_bits":e["best_rep"]["bits"],
             "seconds":sec}
        self.occurrences.append(rec)
        return rec

    def profitability(self,entry,call_bits=None):
        if call_bits is None:
            call_bits=8+max(1,math.ceil(math.log2(max(2,len(self.entries)+1))))
        # Setup = explicit representation bits + one-time exact projection/certificate work proxy.
        # Recurrence savings compare raw literal-token count to macro call tokens.
        raw=entry["raw_literals"]
        calls=entry["count"]*call_bits
        setup=entry["best_rep"]["bits"]
        saving=raw-calls-setup
        return {"raw_cost":raw,"call_cost":calls,"setup":setup,
                "net_saving":saving,"profitable":saving>0}

    def catalog(self):
        out=[]
        for e in self.entries.values():
            out.append({**e,**self.profitability(e)})
        return sorted(out,key=lambda x:x["id"])


# ---------- independent representation checking against certified truth table ----------

def eval_anf_rep(rep,k,bits):
    mask=0
    # Map tuple bits to monomial integer convention used by transform.
    # anf_coefficients indexes ordinary integer assignment masks.
    assignment_mask=0
    for b in bits:
        assignment_mask=(assignment_mask<<1)|b
    val=0
    for mon in rep["monomials"]:
        if mon==0:
            val ^= 1
        elif (assignment_mask & mon)==mon:
            val ^= 1
    return val

def eval_circuit_expr(expr,bits):
    op=expr[0]
    if op=="0":return 0
    if op=="1":return 1
    if op=="x":return int(bits[expr[1]])
    if op=="NOT":return 1^eval_circuit_expr(expr[1],bits)
    a=eval_circuit_expr(expr[1],bits);b=eval_circuit_expr(expr[2],bits)
    if op=="AND":return a&b
    if op=="OR":return a|b
    if op=="XOR":return a^b
    raise ValueError(op)

def eval_representation(rep,k,bits):
    kind=rep["kind"]
    if kind=="TRUTH_TABLE":
        return eval_tt(rep["table"],k,bits)
    if kind=="ANF":
        return eval_anf_rep(rep,k,bits)
    if kind=="AFFINE":
        # Same monomial-mask convention as ANF.
        assignment_mask=0
        for b in bits:assignment_mask=(assignment_mask<<1)|b
        val=rep["constant"]
        for m in rep["linear_masks"]:
            if assignment_mask&m:val^=1
        return val
    if kind=="WEIGHT":
        return int(sum(bits) in set(rep["accepted_weights"]))
    if kind=="COORD_QUOTIENT":
        return eval_coordinate_quotient(rep,k,bits)
    if kind=="CIRCUIT":
        return eval_circuit_expr(rep["expr"],bits)
    if kind=="OBDD":
        # OBDD entry is currently a size/order diagnostic, not a serialized graph.
        raise ValueError("OBDD metric is diagnostic-only in this prototype")
    raise ValueError(kind)

def verify_representation(tt,k,rep):
    if rep["kind"]=="OBDD":
        return True  # diagnostic only; never logical authority
    return all(eval_representation(rep,k,bits)==eval_tt(tt,k,bits)
               for bits in product([0,1],repeat=k))

def verify_registry_entry(entry):
    tt=entry["canonical_tt"];k=entry["arity"]
    # canonical truth table is the authoritative relation certificate.
    for rep in entry["all_reps"]:
        if rep["kind"]!="OBDD" and not verify_representation(tt,k,rep):
            return False
    return True

def verify_occurrence(fragment,entry):
    B=tuple(fragment["boundary"]);L=tuple(fragment["locals"])
    tt,_=project_relation(fragment["clauses"],B,L)
    can,_=canonical_relation(tt,len(B))
    return can==entry["canonical_tt"] and verify_registry_entry(entry)
