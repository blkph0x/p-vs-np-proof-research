from itertools import product

def T(): return ('T',)
def F(): return ('F',)
def Lit(v,pos=True): return ('L',int(v),bool(pos))
def _key(x): return repr(x)

def Or(*args):
    flat=[]
    for a in args:
        if a==T(): return T()
        if a==F(): continue
        if a[0]=='OR': flat.extend(a[1:])
        else: flat.append(a)
    uniq={}; lits=set()
    for a in flat:
        if a[0]=='L':
            sig=(a[1],a[2]); neg=(a[1],not a[2])
            if neg in lits: return T()
            lits.add(sig)
        uniq[_key(a)]=a
    vals=tuple(sorted(uniq.values(),key=_key))
    if not vals:return F()
    if len(vals)==1:return vals[0]
    return ('OR',)+vals

def And(*args):
    flat=[]
    for a in args:
        if a==F(): return F()
        if a==T(): continue
        if a[0]=='AND': flat.extend(a[1:])
        else: flat.append(a)
    uniq={}; lits=set()
    for a in flat:
        if a[0]=='L':
            sig=(a[1],a[2]); neg=(a[1],not a[2])
            if neg in lits:return F()
            lits.add(sig)
        uniq[_key(a)]=a
    vals=tuple(sorted(uniq.values(),key=_key))
    if not vals:return T()
    if len(vals)==1:return vals[0]
    return ('AND',)+vals

def evalf(f,a):
    op=f[0]
    if op=='T':return True
    if op=='F':return False
    if op=='L':return bool(a[f[1]])==f[2]
    if op=='OR':return any(evalf(x,a) for x in f[1:])
    if op=='AND':return all(evalf(x,a) for x in f[1:])
    raise ValueError(op)

def ast_literal_count(f):
    if f[0]=='L':return 1
    if f[0] in ('T','F'):return 0
    return sum(ast_literal_count(x) for x in f[1:])

def support(f):
    if f[0]=='L':return {f[1]}
    if f[0] in ('T','F'):return set()
    s=set()
    for x in f[1:]: s |= support(x)
    return s

def norm_clause(c):
    s=set(c)
    if any(-x in s for x in s):return None
    return tuple(sorted(s,key=lambda z:(abs(z),z<0)))

def resolve(c1,c2,pivot):
    p=pivot+1;s1=set(c1);s2=set(c2)
    if p in s1 and -p in s2: out=(s1-{p})|(s2-{-p})
    elif -p in s1 and p in s2: out=(s1-{-p})|(s2-{p})
    else: raise ValueError((pivot,c1,c2))
    return norm_clause(out)

def clause_formula_shared(c,shared):
    return Or(*(Lit(abs(l)-1,l>0) for l in c if abs(l)-1 in shared))

class Proof:
    def __init__(self,A,B):
        self.A=[norm_clause(c) for c in A]; self.B=[norm_clause(c) for c in B]
        self.Avars={abs(l)-1 for c in self.A for l in c}
        self.Bvars={abs(l)-1 for c in self.B for l in c}
        self.shared=self.Avars & self.Bvars
        self.nodes=[]
    def leaf(self,part,index):
        c=(self.A if part=='A' else self.B)[index]
        self.nodes.append({'clause':c,'part':part})
        return len(self.nodes)-1
    def res(self,left,right,pivot):
        c=resolve(self.nodes[left]['clause'],self.nodes[right]['clause'],pivot)
        self.nodes.append({'clause':c,'left':left,'right':right,'pivot':pivot})
        return len(self.nodes)-1
    def mcmillan(self,root):
        memo={}
        def go(i):
            if i in memo:return memo[i]
            n=self.nodes[i]
            if 'part' in n:
                out=clause_formula_shared(n['clause'],self.shared) if n['part']=='A' else T()
            else:
                a=go(n['left']); b=go(n['right']); p=n['pivot']
                out=Or(a,b) if (p in self.Avars and p not in self.Bvars) else And(a,b)
            memo[i]=out; return out
        return go(root)

def partition_classes(w,q):
    classes=[[] for _ in range(q)]
    for i in range(w): classes[i%q].append(i)
    return classes

def locality_benchmark(w,q):
    classes=partition_classes(w,q); reps=[c[0] for c in classes]
    A=[tuple(v+1 for v in range(w))]; imp={}
    for cl in classes:
        r=cl[0]
        for x in cl[1:]:
            imp[x]=len(A); A.append(norm_clause((r+1,-(x+1))))
    B=[(-(r+1),) for r in reps]
    P=Proof(A,B); cur=P.leaf('A',0)
    for cl in classes:
        for x in cl[1:]: cur=P.res(cur,P.leaf('A',imp[x]),x)
    for bi,r in enumerate(reps): cur=P.res(cur,P.leaf('B',bi),r)
    assert P.nodes[cur]['clause']==()
    return P,P.mcmillan(cur),reps,classes

def all_shared_raw_benchmark(w,q):
    classes=partition_classes(w,q); reps=[c[0] for c in classes]
    A=[tuple(v+1 for v in range(w))]
    for cl in classes:
        r=cl[0]
        for x in cl[1:]: A.append(norm_clause((r+1,-(x+1))))
    B=[(-(v+1),) for v in range(w)]
    P=Proof(A,B); cur=P.leaf('A',0)
    for bi,v in enumerate(range(w)): cur=P.res(cur,P.leaf('B',bi),v)
    assert P.nodes[cur]['clause']==()
    I=P.mcmillan(cur)
    Q=Or(*(Lit(r,True) for r in reps))
    return P,I,Q,reps,classes

def A_quotient_value(bits,classes):
    if not any(bits):return False
    for cl in classes:
        r=cl[0]
        for x in cl[1:]:
            if bits[x] and not bits[r]:return False
    return True

def verify_quotient_interpolant(w,q,I,all_shared=True):
    classes=partition_classes(w,q); reps=[c[0] for c in classes]
    for bits in product([0,1],repeat=w):
        a={i:bits[i] for i in range(w)}
        if A_quotient_value(bits,classes) and not evalf(I,a): return False
    if all_shared:
        zero={i:0 for i in range(w)}
        return not evalf(I,zero)
    a={r:0 for r in reps}
    return support(I)<=set(reps) and not evalf(I,a)

def parity(bits): return sum(bits)&1
def parity_cnf_clause_count(q): return 1<<(q-1)
def parity_cnf_literal_count(q): return q*(1<<(q-1))
def amo_cnf_clause_count(q): return q*(q-1)//2
def amo_cnf_literal_count(q): return q*(q-1)
def amo(bits): return sum(bits)<=1

def verify_complement(q,A,B,I):
    for bits in product([0,1],repeat=q):
        av=A(bits);bv=B(bits);iv=I(bits)
        if av==bv:return False
        if av and not iv:return False
        if bv and iv:return False
    return True
