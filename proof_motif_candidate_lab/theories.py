
from collections import deque

def parity(x):
    return x.bit_count() & 1

class AffineTheory:
    """
    GF(2) equations mask dot x = rhs.
    Every derived row tracks the XOR-combination of original equations.
    """
    def __init__(self, equations):
        self.eq=[(int(mask),int(rhs)&1) for mask,rhs in equations]
        self.n=len(equations)

    def analyze(self,assignment):
        rows=[]
        assigned_mask=0
        assigned_bits=0
        for v,val in assignment.items():
            assigned_mask |= 1<<v
            if val: assigned_bits |= 1<<v

        for i,(mask,rhs) in enumerate(self.eq):
            val=parity(mask & assigned_bits)
            umask=mask & ~assigned_mask
            rows.append([umask,rhs^val,1<<i])

        # Gaussian elimination on unassigned columns.
        basis={}
        derived=[]
        for mask,rhs,combo in rows:
            m=mask;r=rhs;c=combo
            while m:
                p=m.bit_length()-1
                if p in basis:
                    bm,br,bc=basis[p]
                    m^=bm;r^=br;c^=bc
                else:
                    basis[p]=(m,r,c)
                    break
            if m==0:
                if r:
                    cert={"kind":"affine-conflict","combo":c,
                          "assignment":dict(assignment)}
                    return [],cert
            else:
                derived.append((m,r,c))

        props=[]
        # Unit rows in the reduced basis.
        for m,r,c in basis.values():
            if m and (m & (m-1))==0:
                v=m.bit_length()-1
                if v not in assignment:
                    props.append((v,bool(r),{
                        "kind":"affine-prop","combo":c,"var":v,"value":bool(r),
                        "assignment":dict(assignment)
                    }))
        return props,None

    def verify(self,cert):
        combo=cert["combo"]
        mask=0;rhs=0
        for i,(m,r) in enumerate(self.eq):
            if (combo>>i)&1:
                mask ^= m; rhs ^= r
        a=cert["assignment"]
        assigned_mask=sum(1<<v for v in a)
        bits=sum((1<<v) for v,val in a.items() if val)
        reduced_mask=mask & ~assigned_mask
        reduced_rhs=rhs ^ parity(mask & bits)
        if cert["kind"]=="affine-conflict":
            return reduced_mask==0 and reduced_rhs==1
        if cert["kind"]=="affine-prop":
            v=cert["var"];val=int(cert["value"])
            return reduced_mask==(1<<v) and reduced_rhs==val
        return False

class MatchingRegion:
    """
    h left vertices, h rights. Base edges connect every left to rights 0..h-2.
    Optional switch var_j controls edge (left j, special right h-1).
    Perfect matching exists iff at least one switch is not false.
    General matching/Hall code is used anyway so certificates are structural.
    """
    def __init__(self,h,vars_):
        self.h=h;self.vars=list(vars_)
        assert len(self.vars)==h
        self.base={(u,v) for u in range(h) for v in range(h-1)}
        self.optional={var:(j,h-1) for j,var in enumerate(self.vars)}
        self.original=set(self.base)|set(self.optional.values())

    def available_edges(self,assignment,assume_false=None):
        E=set(self.base)
        for var,e in self.optional.items():
            if var==assume_false:
                continue
            if assignment.get(var,True) is not False:
                E.add(e)
        return E

    def max_matching(self,E):
        h=self.h
        adj={u:[] for u in range(h)}
        for u,v in E:adj[u].append(v)
        matchR={};matchL={}
        def dfs(u,seen):
            for v in adj[u]:
                if v in seen:continue
                seen.add(v)
                if v not in matchR or dfs(matchR[v],seen):
                    matchR[v]=u;matchL[u]=v;return True
            return False
        for u in range(h):dfs(u,set())
        return matchL,matchR

    def hall_from_failure(self,E,mL,mR):
        h=self.h
        adj={u:[] for u in range(h)}
        for u,v in E:adj[u].append(v)
        q=deque([u for u in range(h) if u not in mL])
        L=set(q);R=set()
        while q:
            u=q.popleft()
            for v in adj[u]:
                if mL.get(u)==v:continue
                if v in R:continue
                R.add(v)
                if v in mR and mR[v] not in L:
                    L.add(mR[v]);q.append(mR[v])
        return L,R

    def analyze(self,assignment,propagate=True):
        E=self.available_edges(assignment)
        mL,mR=self.max_matching(E)
        if len(mL)<self.h:
            S,N=self.hall_from_failure(E,mL,mR)
            disabled=[]
            for var,e in self.optional.items():
                if e[0] in S and e[1] not in N and assignment.get(var) is False:
                    disabled.append(var)
            cert={"kind":"matching-conflict","S":sorted(S),"N":sorted(N),
                  "disabled":sorted(disabled),"assignment":dict(assignment)}
            return [],cert

        props=[]
        if propagate:
            # A currently unassigned switch is forced true if making it false destroys all perfect matchings.
            for var in self.vars:
                if var in assignment:continue
                Ef=self.available_edges(assignment,assume_false=var)
                fL,fR=self.max_matching(Ef)
                if len(fL)<self.h:
                    S,N=self.hall_from_failure(Ef,fL,fR)
                    false_vars=[x for x in self.vars
                                if assignment.get(x) is False and
                                self.optional[x][0] in S and self.optional[x][1] not in N]
                    cert={"kind":"matching-prop","var":var,"value":True,
                          "S":sorted(S),"N":sorted(N),
                          "disabled":sorted(false_vars+[var]),
                          "assignment":dict(assignment)}
                    props.append((var,True,cert))
        return props,None

    def verify(self,cert):
        S=set(cert["S"]);N=set(cert["N"])
        a=cert["assignment"]
        assume=cert.get("var") if cert["kind"]=="matching-prop" else None
        E=self.available_edges(a,assume_false=assume)
        actual={v for u,v in E if u in S}
        if actual!=N or not (len(N)<len(S)):
            return False
        # every optional repair edge from S outside N must be disabled.
        for var,e in self.optional.items():
            if e[0] in S and e[1] not in N:
                if var==assume:
                    continue
                if a.get(var) is not False:
                    return False
        return True

class PortfolioSolver:
    def __init__(self,nvars,affine=None,matching_regions=()):
        self.nvars=nvars
        self.affine=affine
        self.regions=list(matching_regions)
        self.stats={"nodes":0,"decisions":0,"propagations":0,"conflicts":0,
                    "affine_props":0,"matching_props":0,
                    "affine_conflicts":0,"matching_conflicts":0,
                    "certificates_verified":0}
        self.certs=[]

    def propagate(self,a):
        changed=True
        while changed:
            changed=False
            if self.affine:
                ps,conf=self.affine.analyze(a)
                if conf:
                    assert self.affine.verify(conf)
                    self.stats["certificates_verified"]+=1
                    self.stats["conflicts"]+=1;self.stats["affine_conflicts"]+=1
                    self.certs.append(conf);return False
                for v,val,cert in ps:
                    if v in a:
                        if a[v]!=val:return False
                        continue
                    assert self.affine.verify(cert)
                    self.stats["certificates_verified"]+=1
                    a[v]=val;changed=True
                    self.stats["propagations"]+=1;self.stats["affine_props"]+=1
                    self.certs.append(cert)
            for region in self.regions:
                ps,conf=region.analyze(a,True)
                if conf:
                    assert region.verify(conf)
                    self.stats["certificates_verified"]+=1
                    self.stats["conflicts"]+=1;self.stats["matching_conflicts"]+=1
                    self.certs.append(conf);return False
                for v,val,cert in ps:
                    if v in a:
                        if a[v]!=val:return False
                        continue
                    assert region.verify(cert)
                    self.stats["certificates_verified"]+=1
                    a[v]=val;changed=True
                    self.stats["propagations"]+=1;self.stats["matching_props"]+=1
                    self.certs.append(cert)
        return True

    def solve(self,a=None):
        if a is None:a={}
        self.stats["nodes"]+=1
        a=dict(a)
        if not self.propagate(a):
            return None
        if len(a)==self.nvars:
            return a
        v=next(i for i in range(self.nvars) if i not in a)
        self.stats["decisions"]+=1
        # false-first
        a0=dict(a);a0[v]=False
        r=self.solve(a0)
        if r is not None:return r
        self.stats["decisions"]+=1
        a1=dict(a);a1[v]=True
        return self.solve(a1)

def combined_unsat(groups=6,width=6):
    """
    Group j has width Boolean switches.
    Affine equalities make all switches in a group equal to representative.
    Matching region requires at least one true, therefore every group is forced all true.
    Final parity on representatives is chosen opposite to that forced pattern.
    """
    n=groups*width
    eqs=[]
    reps=[]
    regions=[]
    for g in range(groups):
        vs=list(range(g*width,(g+1)*width));reps.append(vs[0])
        for v in vs[1:]:
            eqs.append(((1<<vs[0])|(1<<v),0))
        regions.append(MatchingRegion(width,vs))
    mask=sum(1<<v for v in reps)
    forced_parity=groups&1
    eqs.append((mask,1-forced_parity))
    return n,AffineTheory(eqs),regions

def matching_only_sat(groups=8,width=8):
    n=groups*width
    regs=[MatchingRegion(width,list(range(g*width,(g+1)*width))) for g in range(groups)]
    return n,regs
