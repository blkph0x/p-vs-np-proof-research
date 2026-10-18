
from collections import defaultdict, Counter
from itertools import combinations, product, permutations
import math, time

# ---------------- basic clause/proof utilities ----------------

def norm_clause(c):
    s=set(int(x) for x in c)
    if any(-x in s for x in s):
        return None
    return tuple(sorted(s,key=lambda z:(abs(z),z<0)))

def var(lit): return abs(lit)-1
def lit(v,pos=True): return v+1 if pos else -(v+1)

def resolve(c1,c2,pivot):
    p=pivot+1
    s1=set(c1);s2=set(c2)
    if p in s1 and -p in s2:
        out=(s1-{p})|(s2-{-p})
    elif -p in s1 and p in s2:
        out=(s1-{-p})|(s2-{p})
    else:
        raise ValueError(("bad pivot",pivot,c1,c2))
    return norm_clause(out)

class ProofDAG:
    def __init__(self,clauses):
        self.clauses=[norm_clause(c) for c in clauses]
        self.nodes=[]
    def leaf(self,idx):
        self.nodes.append({"kind":"leaf","clause":self.clauses[idx],"idx":idx})
        return len(self.nodes)-1
    def res(self,a,b,pivot):
        out=resolve(self.nodes[a]["clause"],self.nodes[b]["clause"],pivot)
        self.nodes.append({"kind":"res","left":a,"right":b,"pivot":pivot,"clause":out})
        return len(self.nodes)-1

def ancestor_nodes(P,root):
    seen=set()
    def rec(i):
        if i in seen:return
        seen.add(i)
        n=P.nodes[i]
        if n["kind"]=="res":
            rec(n["left"]);rec(n["right"])
    rec(root)
    return seen

def normalized_subproof_signature(P,root):
    """
    Canonicalize an ancestor proof under variable renaming by assigning canonical
    ids to variables in first structural occurrence. This is a proposal hash only.
    """
    anc=ancestor_nodes(P,root)
    order=[]
    seen=set()
    def walk(i):
        if i in seen:return
        n=P.nodes[i]
        if n["kind"]=="res":
            walk(n["left"]);walk(n["right"])
        seen.add(i);order.append(i)
    walk(root)
    vmap={}
    def cv(v):
        if v not in vmap:vmap[v]=len(vmap)
        return vmap[v]
    enc=[]
    idmap={}
    for i in order:
        n=P.nodes[i]
        if n["kind"]=="leaf":
            cc=[]
            for L in n["clause"]:
                cc.append((cv(var(L)), L>0))
            cc=tuple(sorted(cc))
            enc.append(("L",cc));idmap[i]=len(enc)-1
        else:
            # normalize clause/pivot too, plus parent positions
            p=cv(n["pivot"])
            cc=tuple(sorted((cv(var(L)),L>0) for L in n["clause"]))
            enc.append(("R",idmap[n["left"]],idmap[n["right"]],p,cc))
            idmap[i]=len(enc)-1
    return tuple(enc)

# ---------------- union-find ----------------

class DSU:
    def __init__(self):
        self.p={}
    def find(self,x):
        if x not in self.p:self.p[x]=x
        if self.p[x]!=x:self.p[x]=self.find(self.p[x])
        return self.p[x]
    def union(self,a,b):
        a=self.find(a);b=self.find(b)
        if a!=b:self.p[b]=a
    def classes(self):
        g=defaultdict(list)
        for x in self.p:g[self.find(x)].append(x)
        return [tuple(sorted(v)) for v in g.values() if len(v)>=2]

# ---------------- exact motif validators/miners ----------------

def clause_index(clauses):
    return {c:i for i,c in enumerate(clauses)}

def detect_equivalence_classes(clauses):
    """
    Exact CNF equivalence motif x <-> y requires both:
      (~x or y) and (x or ~y).
    """
    idx=set(clauses)
    d=DSU()
    vars_=sorted({var(L) for c in clauses for L in c})
    # index binary implications by ordered pair a->b
    imps=set()
    for c in clauses:
        if len(c)==2:
            a,b=c
            # (~x or y)
            if a<0 and b>0: imps.add((var(a),var(b)))
            if b<0 and a>0: imps.add((var(b),var(a)))
    for a,b in list(imps):
        if (b,a) in imps:
            d.union(a,b)
    return d.classes()

def verify_equivalence_class(clauses,cl):
    idx=set(clauses)
    r=cl[0]
    for x in cl[1:]:
        if norm_clause((-lit(r,True),lit(x,True))) not in idx:
            return False
        if norm_clause((lit(r,True),-lit(x,True))) not in idx:
            return False
    return True

def detect_amo_cliques(clauses,min_size=3):
    """
    Connected components in all-negative binary graph that are complete.
    """
    edges=set();V=set()
    for c in clauses:
        if len(c)==2 and all(L<0 for L in c):
            a,b=sorted((var(c[0]),var(c[1])))
            edges.add((a,b));V|={a,b}
    adj={v:set() for v in V}
    for a,b in edges:adj[a].add(b);adj[b].add(a)
    seen=set();out=[]
    for v in sorted(V):
        if v in seen:continue
        st=[v];seen.add(v);C=[]
        while st:
            u=st.pop();C.append(u)
            for z in adj[u]:
                if z not in seen:seen.add(z);st.append(z)
        if len(C)>=min_size:
            S=set(C)
            need=len(C)*(len(C)-1)//2
            got=sum(1 for a,b in edges if a in S and b in S)
            if got==need:
                out.append(tuple(sorted(C)))
    return out

def verify_amo(clauses,cl):
    idx=set(clauses)
    for a,b in combinations(cl,2):
        if norm_clause((-lit(a,True),-lit(b,True))) not in idx:
            return False
    return True

def excluded_assignment_from_full_clause(c,support):
    """
    Full-width clause over support excludes exactly the assignment falsifying every literal.
    Return bits in support order.
    """
    mp={var(L):(0 if L>0 else 1) for L in c}
    if set(mp)!=set(support):return None
    return tuple(mp[v] for v in support)

def detect_parity_blocks(clauses,arity=3):
    """
    Exact direct-CNF parity blocks on fixed support. For arity k, parity relation
    has 2^(k-1) full-width clauses excluding one parity class.
    Default k=3 keeps mining fixed-arity polynomial/linear in input.
    """
    groups=defaultdict(list)
    for i,c in enumerate(clauses):
        if len(c)==arity:
            S=tuple(sorted(var(L) for L in c))
            if len(set(S))==arity:
                groups[S].append((i,c))
    out=[]
    expected=1<<(arity-1)
    for S,items in groups.items():
        if len(items)!=expected:continue
        excl=[]
        ok=True
        for _,c in items:
            b=excluded_assignment_from_full_clause(c,S)
            if b is None:ok=False;break
            excl.append(b)
        if not ok or len(set(excl))!=expected:continue
        ps={sum(b)&1 for b in excl}
        if len(ps)==1:
            forbidden=next(iter(ps))
            rhs=1-forbidden
            cand={"kind":"XOR","support":S,"rhs":rhs,
                  "clause_indices":tuple(i for i,_ in items),"arity":arity}
            if verify_parity_block(clauses,cand):
                out.append(cand)
    return out

def verify_parity_block(clauses,cand):
    S=tuple(cand["support"]);rhs=cand["rhs"]
    inds=cand["clause_indices"]
    expected_forbidden=1-rhs
    seen=set()
    for i in inds:
        c=clauses[i]
        if len(c)!=len(S):return False
        b=excluded_assignment_from_full_clause(c,S)
        if b is None or (sum(b)&1)!=expected_forbidden:return False
        seen.add(b)
    return len(seen)==(1<<(len(S)-1))

def ite_truth(c,a,b):
    return a if c else b

def detect_ite_blocks(clauses):
    """
    Detect exact 4-var full-truth-table CNF for z = ite(c,a,b).
    Direct form has one width-4 clause per falsifying assignment => 8 clauses.
    Role search is constant (24 permutations).
    """
    groups=defaultdict(list)
    for i,c in enumerate(clauses):
        if len(c)==4:
            S=tuple(sorted(var(L) for L in c))
            if len(set(S))==4:groups[S].append((i,c))
    out=[]
    for S,items in groups.items():
        if len(items)!=8:continue
        excluded=set()
        ok=True
        for _,cl in items:
            b=excluded_assignment_from_full_clause(cl,S)
            if b is None:ok=False;break
            excluded.add(b)
        if not ok or len(excluded)!=8:continue
        for perm in permutations(S,4):
            z,c,a,b=perm
            spos={v:j for j,v in enumerate(S)}
            bad=set()
            for bits in product([0,1],repeat=4):
                d={S[j]:bits[j] for j in range(4)}
                if d[z] != ite_truth(d[c],d[a],d[b]):
                    bad.add(bits)
            if bad==excluded:
                cand={"kind":"ITE","z":z,"c":c,"a":a,"b":b,
                      "support":S,"clause_indices":tuple(i for i,_ in items)}
                if verify_ite_block(clauses,cand):
                    out.append(cand)
                break
    return out

def verify_ite_block(clauses,cand):
    S=tuple(cand["support"]);z,c,a,b=cand["z"],cand["c"],cand["a"],cand["b"]
    excluded=set()
    for i in cand["clause_indices"]:
        cl=clauses[i]
        bits=excluded_assignment_from_full_clause(cl,S)
        if bits is None:return False
        excluded.add(bits)
    bad=set()
    for bits in product([0,1],repeat=4):
        d={S[j]:bits[j] for j in range(4)}
        if d[z] != ite_truth(d[c],d[a],d[b]):bad.add(bits)
    return excluded==bad

def detect_or_collapse_macros(clauses,min_width=3):
    """
    Exact proof macro:
      C = (r OR x2 OR ... OR xw)
      and for every x!=r, (r OR ~x)
    resolves to unit (r).
    Search every positive literal of a positive wide clause as possible head.
    """
    idx=clause_index(clauses)
    out=[]
    for ci,c in enumerate(clauses):
        if len(c)<min_width or not all(L>0 for L in c):continue
        vs=tuple(var(L) for L in c)
        for r in vs:
            spokes=[]
            ok=True
            for x in vs:
                if x==r:continue
                sc=norm_clause((lit(r,True),lit(x,False)))
                if sc not in idx:
                    ok=False;break
                spokes.append(idx[sc])
            if ok:
                cand={"kind":"OR_COLLAPSE","head":r,"members":vs,
                      "wide_clause":ci,"spokes":tuple(spokes)}
                proof=verify_or_collapse(clauses,cand,build_proof=True)
                if proof is not None:
                    cand["proof"]=proof
                    out.append(cand)
    # Remove duplicate same member/head
    uniq={}
    for x in out:uniq[(x["head"],x["members"])]=x
    return list(uniq.values())

def verify_or_collapse(clauses,cand,build_proof=False):
    r=cand["head"];members=tuple(cand["members"])
    c=clauses[cand["wide_clause"]]
    if c!=norm_clause(lit(v,True) for v in members):return None if build_proof else False
    P=ProofDAG(clauses)
    cur=P.leaf(cand["wide_clause"])
    spoke_map={}
    for si in cand["spokes"]:
        sc=clauses[si]
        # find member x with (r or ~x)
        if len(sc)!=2 or lit(r,True) not in sc:return None if build_proof else False
        neg=[L for L in sc if L<0]
        if len(neg)!=1:return None if build_proof else False
        x=var(neg[0]);spoke_map[x]=si
    for x in members:
        if x==r:continue
        if x not in spoke_map:return None if build_proof else False
        cur=P.res(cur,P.leaf(spoke_map[x]),x)
    if P.nodes[cur]["clause"]!=(lit(r,True),):
        return None if build_proof else False
    if build_proof:
        return {"dag":P,"root":cur,
                "signature":normalized_subproof_signature(P,cur),
                "steps":len(members)-1}
    return True

def macro_recurrence(macros):
    ctr=Counter()
    for m in macros:
        if m["kind"]=="OR_COLLAPSE":
            ctr[m["proof"]["signature"]]+=1
        elif m["kind"]=="XOR":
            ctr[("XOR",m["arity"])]+=1
        elif m["kind"]=="ITE":
            ctr[("ITE",4)]+=1
    return ctr

# ---------------- interface certificates ----------------

def parity(mask_bits,rhs):
    return sum(mask_bits)&1 == rhs

def verify_affine_certificate(cert,trusted_rows):
    """
    cert is accepted only if exactly present in trusted receiver theory rows.
    trusted rows are tuples (support_tuple, rhs).
    """
    if cert.get("kind")!="AFFINE":return False
    S=tuple(sorted(cert["support"]));rhs=int(cert["rhs"])&1
    return (S,rhs) in {(tuple(sorted(s)),int(r)&1) for s,r in trusted_rows}

def verify_pb_certificate(cert,trusted_rows):
    """
    trusted PB rows: (weights_dict, sense, bound), sense in <=,>=.
    """
    if cert.get("kind")!="PB":return False
    w={int(k):int(v) for k,v in cert["weights"].items()}
    s=cert["sense"];b=int(cert["bound"])
    norm=(tuple(sorted(w.items())),s,b)
    tr={(tuple(sorted(dict(x).items())),sense,int(bound)) for x,sense,bound in trusted_rows}
    return norm in tr

def derive_units_from_macros(macros):
    """
    Certified source facts: OR-collapse macros derive head=true.
    """
    units={}
    proofs={}
    for m in macros:
        if m["kind"]=="OR_COLLAPSE":
            units[m["head"]]=True
            proofs[m["head"]]=m["proof"]
    return units,proofs

def propose_from_receiver_certificate(units,cert,trusted_affine=(),trusted_pb=()):
    """
    No benchmark family labels.
    Query shape comes solely from a verified theory certificate.
    Candidate must be entailed by current source units.
    """
    out=[]
    if cert.get("kind")=="AFFINE":
        if not verify_affine_certificate(cert,trusted_affine):return out
        S=tuple(sorted(cert["support"]))
        if all(v in units for v in S):
            val=sum(1 for v in S if units[v])&1
            # If source parity differs from receiver equation, this is an interpolant.
            if val != (cert["rhs"]&1):
                out.append({"kind":"XOR_INTERPOLANT","support":S,"rhs":val,
                            "source":"derived-units","receiver_cert":cert})
    elif cert.get("kind")=="PB":
        if not verify_pb_certificate(cert,trusted_pb):return out
        weights={int(k):int(v) for k,v in cert["weights"].items()}
        if cert["sense"]=="<=" and all(w>=0 for w in weights.values()):
            lb=sum(w for v,w in weights.items() if units.get(v) is True)
            if lb>cert["bound"]:
                # transmit the lower bound induced by fixed true source units
                supp=tuple(sorted(v for v,w in weights.items() if units.get(v) is True and w))
                out.append({"kind":"PB_INTERPOLANT","support":supp,
                            "weights":{v:weights[v] for v in supp},
                            "sense":">=","bound":lb,
                            "source":"derived-units","receiver_cert":cert})
    return out

def verify_interface_candidate(units,cand):
    if cand["kind"]=="XOR_INTERPOLANT":
        S=cand["support"]
        if not all(v in units for v in S):return False
        val=sum(1 for v in S if units[v])&1
        return val==cand["rhs"]
    if cand["kind"]=="PB_INTERPOLANT":
        lhs=sum(w for v,w in cand["weights"].items() if units.get(v) is True)
        return lhs>=cand["bound"]
    return False

# ---------------- fixture generation ----------------

def hall_groups(groups,width,start=0):
    """
    Return clauses only; no group labels used by miner.
    For each group: positive OR plus member->head implication spokes.
    """
    cs=[];heads=[]
    n=start
    for g in range(groups):
        vs=list(range(n,n+width));n+=width
        r=vs[0];heads.append(r)
        cs.append(norm_clause(lit(v,True) for v in vs))
        for x in vs[1:]:
            cs.append(norm_clause((lit(r,True),lit(x,False))))
    return cs,heads,n

def amo_fixture(n,start=0):
    vs=list(range(start,start+n))
    cs=[norm_clause((lit(a,False),lit(b,False))) for a,b in combinations(vs,2)]
    return cs,vs

def xor3_fixture(blocks,start=0):
    cs=[];meta=[];n=start
    for _ in range(blocks):
        S=(n,n+1,n+2);n+=3
        rhs=0
        inds=[]
        for bits in product([0,1],repeat=3):
            if (sum(bits)&1)!=rhs:
                # exclude bits
                cl=tuple(lit(S[j], bits[j]==0) for j in range(3))
                inds.append(len(cs));cs.append(norm_clause(cl))
        meta.append((S,rhs,inds))
    return cs,meta,n

def ite_fixture(blocks,start=0):
    cs=[];meta=[];n=start
    for _ in range(blocks):
        z,c,a,b=n,n+1,n+2,n+3;n+=4
        S=tuple(sorted((z,c,a,b)));inds=[]
        for bits in product([0,1],repeat=4):
            d={S[j]:bits[j] for j in range(4)}
            if d[z]!=ite_truth(d[c],d[a],d[b]):
                cl=tuple(lit(S[j], bits[j]==0) for j in range(4))
                inds.append(len(cs));cs.append(norm_clause(cl))
        meta.append(((z,c,a,b),inds))
    return cs,meta,n

def equivalence_fixture(classes,size,start=0):
    cs=[];cls=[];n=start
    for _ in range(classes):
        vs=list(range(n,n+size));n+=size;cls.append(tuple(vs));r=vs[0]
        for x in vs[1:]:
            cs.append(norm_clause((lit(r,False),lit(x,True))))
            cs.append(norm_clause((lit(r,True),lit(x,False))))
    return cs,cls,n

# ---------------- adversarial mutations ----------------

def mutate_remove_one(clauses,index=0):
    return list(clauses[:index])+list(clauses[index+1:])

def mutate_flip_literal(clauses,ci,li=0):
    out=list(clauses)
    c=list(out[ci]);c[li]=-c[li]
    out[ci]=norm_clause(c)
    return out

def mine_all(clauses):
    eq=detect_equivalence_classes(clauses)
    amo=detect_amo_cliques(clauses)
    xor=detect_parity_blocks(clauses,3)
    ite=detect_ite_blocks(clauses)
    orc=detect_or_collapse_macros(clauses)
    return {"equivalence":eq,"AMO":amo,"XOR":xor,"ITE":ite,"OR_COLLAPSE":orc}


# ---------------- source-driven typed candidate catalog ----------------

def candidate_catalog(mined,clauses):
    out=[]
    # Equality candidates.
    for cl in mined["equivalence"]:
        if verify_equivalence_class(clauses,cl):
            out.append({"kind":"EQUALITY","support":tuple(cl),
                        "certificate":{"type":"binary-equivalence-clauses"}})
    # AMO as PB.
    for cl in mined["AMO"]:
        if verify_amo(clauses,cl):
            out.append({"kind":"PB_AMO","support":tuple(cl),
                        "weights":{v:1 for v in cl},"sense":"<=","bound":1,
                        "certificate":{"type":"complete-negative-clique"}})
    # Affine relations.
    for x in mined["XOR"]:
        if verify_parity_block(clauses,x):
            out.append({"kind":"XOR","support":tuple(x["support"]),"rhs":x["rhs"],
                        "certificate":{"type":"direct-parity-CNF",
                                       "clauses":x["clause_indices"]}})
    # ITE gates.
    for x in mined["ITE"]:
        if verify_ite_block(clauses,x):
            out.append({"kind":"ITE","support":tuple(x["support"]),
                        "z":x["z"],"c":x["c"],"a":x["a"],"b":x["b"],
                        "certificate":{"type":"direct-ITE-CNF",
                                       "clauses":x["clause_indices"]}})
    # Unit facts derived by proof macros.
    for x in mined["OR_COLLAPSE"]:
        if verify_or_collapse(clauses,x,False):
            out.append({"kind":"UNIT","support":(x["head"],),
                        "var":x["head"],"value":True,
                        "certificate":{"type":"resolution-subproof",
                                       "steps":x["proof"]["steps"],
                                       "signature":x["proof"]["signature"]}})
    return out

def candidate_violated_by_assignment(cand,assignment):
    """
    Receiver-side exact check for a complete/partial Boolean assignment.
    Returns True only when assigned variables suffice to falsify the candidate.
    """
    k=cand["kind"]
    if k=="UNIT":
        v=cand["var"]
        return v in assignment and bool(assignment[v]) != bool(cand["value"])
    if k=="EQUALITY":
        vals=[assignment[v] for v in cand["support"] if v in assignment]
        if len(vals)<2:return False
        # A full equality class is falsified as soon as two assigned members differ.
        return len(set(vals))>1
    if k=="PB_AMO":
        # Positive weights, <=1. Partial assignment falsifies once >=2 are true.
        return sum(1 for v in cand["support"] if assignment.get(v) is True)>1
    if k=="XOR":
        S=cand["support"]
        if not all(v in assignment for v in S):return False
        return (sum(1 for v in S if assignment[v])&1) != cand["rhs"]
    if k=="ITE":
        vs=(cand["z"],cand["c"],cand["a"],cand["b"])
        if not all(v in assignment for v in vs):return False
        expected=assignment[cand["a"]] if assignment[cand["c"]] else assignment[cand["b"]]
        return bool(assignment[cand["z"]]) != bool(expected)
    return False

def estimate_candidate_bits(cand,nvars):
    b=max(1,math.ceil(math.log2(max(2,nvars))))
    k=cand["kind"]
    if k=="UNIT": return 8+b+1
    if k=="EQUALITY": return 8+len(cand["support"])*b
    if k=="PB_AMO": return 8+len(cand["support"])*b+b
    if k=="XOR": return 8+len(cand["support"])*b+1
    if k=="ITE": return 8+4*b
    return 10**18

def select_closing_candidate(catalog,assignment,nvars):
    good=[c for c in catalog if candidate_violated_by_assignment(c,assignment)]
    if not good:return None,[]
    best=min(good,key=lambda c:(estimate_candidate_bits(c,nvars),len(c["support"]),c["kind"]))
    return best,good
