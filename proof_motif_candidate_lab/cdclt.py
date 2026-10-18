
from theories import AffineTheory, MatchingRegion, combined_unsat

def norm_clause(c):
    s=set(c)
    if any(-x in s for x in s):
        return None
    return tuple(sorted(s,key=lambda z:(abs(z),z<0)))

def var_of(lit):
    return abs(lit)-1

def lit_for(v,val):
    return v+1 if val else -(v+1)

def clause_satisfied(c,assign):
    for lit in c:
        v=var_of(lit)
        if v in assign and assign[v]==(lit>0):
            return True
    return False

def unit_or_conflict(c,assign):
    if clause_satisfied(c,assign):
        return ("sat",None)
    un=[lit for lit in c if var_of(lit) not in assign]
    if not un:
        return ("conflict",None)
    if len(un)==1:
        return ("unit",un[0])
    return ("open",None)

def resolve(c1,c2,v):
    p=v+1
    s1=set(c1);s2=set(c2)
    if p in s1 and -p in s2:
        out=(s1-{p})|(s2-{-p})
    elif -p in s1 and p in s2:
        out=(s1-{-p})|(s2-{p})
    else:
        raise ValueError(("bad pivot",v,c1,c2))
    if any(-x in out for x in out):
        return None
    return norm_clause(out)

def affine_combined_equation(theory,combo):
    mask=0;rhs=0
    for i,(m,r) in enumerate(theory.eq):
        if (combo>>i)&1:
            mask ^= m;rhs ^= r
    return mask,rhs

def affine_clause(theory,cert):
    mask,rhs=affine_combined_equation(theory,cert["combo"])
    a=cert["assignment"]
    if cert["kind"]=="affine-conflict":
        lits=[]
        for v in range(max(mask.bit_length(),1)):
            if (mask>>v)&1:
                # complement current assigned literal
                val=a[v]
                lits.append(lit_for(v,not val))
        return norm_clause(lits)
    if cert["kind"]=="affine-prop":
        pv=cert["var"];pval=cert["value"]
        lits=[lit_for(pv,pval)]
        for v in range(max(mask.bit_length(),1)):
            if v==pv or not ((mask>>v)&1):continue
            val=a[v]
            lits.append(lit_for(v,not val))
        return norm_clause(lits)
    raise ValueError

def verify_affine_clause(theory,cert,clause):
    if not theory.verify(cert):return False
    return affine_clause(theory,cert)==tuple(clause)

def matching_clause(region,cert):
    disabled=cert["disabled"]
    # Prop certificate disabled list includes propagated variable.
    return norm_clause([v+1 for v in disabled])

def verify_matching_clause(region,cert,clause):
    return region.verify(cert) and matching_clause(region,cert)==tuple(clause)

class CDCLT:
    def __init__(self,nvars,affine=None,regions=()):
        self.nvars=nvars;self.affine=affine;self.regions=list(regions)
        self.clauses=[]
        self.assign={};self.level={};self.reason={}
        self.trail=[];self.trail_lim=[];self.decision_level=0
        self.proof=[];self.stats={
            "decisions":0,"boolean_props":0,"theory_props":0,
            "conflicts":0,"learned_clauses":0,"learned_literals":0,
            "theory_lemmas":0,"resolution_steps":0,"backjumps":0
        }

    def add_clause(self,c,proof_entry=None):
        c=norm_clause(c)
        if c is None:return None
        idx=len(self.clauses);self.clauses.append(c)
        if proof_entry is not None:
            self.proof.append(proof_entry)
        return idx

    def assign_lit(self,lit,reason_idx):
        v=var_of(lit);val=lit>0
        if v in self.assign:
            return self.assign[v]==val
        self.assign[v]=val;self.level[v]=self.decision_level
        self.reason[v]=reason_idx
        self.trail.append(v)
        return True

    def backtrack(self,level):
        if level>=self.decision_level:return
        while self.trail and self.level[self.trail[-1]]>level:
            v=self.trail.pop()
            del self.assign[v];del self.level[v];del self.reason[v]
        self.decision_level=level
        self.trail_lim=self.trail_lim[:level]

    def boolean_propagate(self):
        changed=True
        while changed:
            changed=False
            for idx,c in enumerate(self.clauses):
                st,lit=unit_or_conflict(c,self.assign)
                if st=="conflict":
                    return idx
                if st=="unit":
                    if not self.assign_lit(lit,idx):
                        return idx
                    self.stats["boolean_props"]+=1
                    changed=True
        return None

    def theory_step(self):
        # affine first
        if self.affine:
            ps,conf=self.affine.analyze(self.assign)
            if conf:
                c=affine_clause(self.affine,conf)
                assert verify_affine_clause(self.affine,conf,c)
                idx=self.add_clause(c,{"kind":"affine-lemma","cert":conf,"clause":c})
                self.stats["theory_lemmas"]+=1
                return ("conflict",idx)
            for v,val,cert in ps:
                if v in self.assign:continue
                c=affine_clause(self.affine,cert)
                assert verify_affine_clause(self.affine,cert,c)
                idx=self.add_clause(c,{"kind":"affine-lemma","cert":cert,"clause":c})
                self.stats["theory_lemmas"]+=1
                lit=lit_for(v,val)
                # Must be unit under current assignment.
                st,u=unit_or_conflict(c,self.assign)
                assert st=="unit" and u==lit
                self.assign_lit(lit,idx)
                self.stats["theory_props"]+=1
                return ("prop",None)
        for ri,region in enumerate(self.regions):
            ps,conf=region.analyze(self.assign,True)
            if conf:
                c=matching_clause(region,conf)
                assert verify_matching_clause(region,conf,c)
                idx=self.add_clause(c,{"kind":"matching-lemma","region":ri,"cert":conf,"clause":c})
                self.stats["theory_lemmas"]+=1
                return ("conflict",idx)
            for v,val,cert in ps:
                if v in self.assign:continue
                c=matching_clause(region,cert)
                assert verify_matching_clause(region,cert,c)
                idx=self.add_clause(c,{"kind":"matching-lemma","region":ri,"cert":cert,"clause":c})
                self.stats["theory_lemmas"]+=1
                lit=lit_for(v,val)
                st,u=unit_or_conflict(c,self.assign)
                assert st=="unit" and u==lit
                self.assign_lit(lit,idx)
                self.stats["theory_props"]+=1
                return ("prop",None)
        return ("none",None)

    def propagate(self):
        while True:
            c=self.boolean_propagate()
            if c is not None:return c
            kind,idx=self.theory_step()
            if kind=="conflict":return idx
            if kind=="prop":continue
            return None

    def analyze(self,conf_idx):
        learned=self.clauses[conf_idx]
        steps=[]
        dl=self.decision_level
        def current_count(c):
            return sum(1 for lit in c if self.level.get(var_of(lit),-1)==dl)

        while current_count(learned)>1:
            pivot=None
            for v in reversed(self.trail):
                if self.level.get(v,-1)!=dl:continue
                if (v+1 in learned or -(v+1) in learned) and self.reason.get(v) is not None:
                    pivot=v;break
            if pivot is None:
                break
            ridx=self.reason[pivot]
            reason=self.clauses[ridx]
            out=resolve(learned,reason,pivot)
            if out is None:
                raise RuntimeError("tautological resolution")
            steps.append({"left":learned,"right":reason,"pivot":pivot,"result":out})
            learned=out

        cur_lits=[lit for lit in learned if self.level.get(var_of(lit),-1)==dl]
        if dl>0 and len(cur_lits)!=1:
            raise RuntimeError(("not asserting",dl,learned,cur_lits))
        other_levels=[self.level.get(var_of(lit),0) for lit in learned
                      if self.level.get(var_of(lit),-1)!=dl]
        back=max(other_levels,default=0)
        return learned,back,steps

    def decide(self):
        for v in range(self.nvars):
            if v not in self.assign:
                self.decision_level+=1
                self.trail_lim.append(len(self.trail))
                self.assign[v]=False;self.level[v]=self.decision_level
                self.reason[v]=None;self.trail.append(v)
                self.stats["decisions"]+=1
                return True
        return False

    def solve(self):
        while True:
            conf=self.propagate()
            if conf is not None:
                self.stats["conflicts"]+=1
                if self.decision_level==0:
                    # log terminal conflict; no need to derive empty clause for solver status
                    self.proof.append({"kind":"terminal-conflict","clause":self.clauses[conf],
                                       "assignment":dict(self.assign)})
                    return None
                learned,back,steps=self.analyze(conf)
                for st in steps:
                    self.proof.append({"kind":"resolve",**st})
                    self.stats["resolution_steps"]+=1
                lidx=self.add_clause(learned,{"kind":"learned","clause":learned,
                                              "from_conflict":self.clauses[conf],
                                              "derivation":steps})
                self.stats["learned_clauses"]+=1
                self.stats["learned_literals"]+=len(learned)
                self.backtrack(back);self.stats["backjumps"]+=1
                # propagation loop will assert learned clause
                continue
            if len(self.assign)==self.nvars:
                return dict(self.assign)
            self.decide()

def final_unit_conflict(clauses):
    assign={}
    changed=True
    while changed:
        changed=False
        for c in clauses:
            st,lit=unit_or_conflict(c,assign)
            if st=="conflict":
                return True
            if st=="unit":
                v=var_of(lit); val=lit>0
                if v in assign:
                    if assign[v]!=val:
                        return True
                else:
                    assign[v]=val; changed=True
    return False

def verify_proof(solver):
    # Every theory lemma is checked against its native theory certificate.
    # Every learned clause is independently replayed from its conflict clause by resolution.
    for e in solver.proof:
        if e["kind"]=="affine-lemma":
            if solver.affine is None or not verify_affine_clause(solver.affine,e["cert"],e["clause"]):
                return False
        elif e["kind"]=="matching-lemma":
            if not verify_matching_clause(solver.regions[e["region"]],e["cert"],e["clause"]):
                return False
        elif e["kind"]=="resolve":
            if resolve(tuple(e["left"]),tuple(e["right"]),e["pivot"])!=tuple(e["result"]):
                return False
        elif e["kind"]=="learned":
            cur=tuple(e["from_conflict"])
            for st in e["derivation"]:
                if tuple(st["left"])!=cur:
                    return False
                out=resolve(tuple(st["left"]),tuple(st["right"]),st["pivot"])
                if out!=tuple(st["result"]):
                    return False
                cur=out
            if cur!=tuple(e["clause"]):
                return False
        elif e["kind"]=="terminal-conflict":
            if clause_satisfied(e["clause"],e["assignment"]):
                return False

    # For an UNSAT run, the final verified clause database should itself unit-refute.
    # This is stronger than trusting the final solver assignment.
    return final_unit_conflict(solver.clauses)
