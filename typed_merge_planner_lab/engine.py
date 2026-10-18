
from itertools import product
from functools import lru_cache
import math

SCHAEFER_TAGS=("ZERO","ONE","AND","OR","MAJ","MIN")
# Boundary messages are queried under arbitrary partial assignments.  Constant
# validity alone does not survive such pins; these four operations do.
EXTENSION_POLYMORPHISMS=frozenset(("AND","OR","MAJ","MIN"))

def tuples(n):
    return list(product([0,1],repeat=n))

def op_and(a,b): return tuple(x&y for x,y in zip(a,b))
def op_or(a,b): return tuple(x|y for x,y in zip(a,b))
def op_maj(a,b,c): return tuple(1 if x+y+z>=2 else 0 for x,y,z in zip(a,b,c))
def op_min(a,b,c): return tuple(x^y^z for x,y,z in zip(a,b,c))

def relation_signature(R,n):
    S=set(tuple(x) for x in R);vals=list(S)
    sig=set()
    z=tuple(0 for _ in range(n));o=tuple(1 for _ in range(n))
    if z in S:sig.add("ZERO")
    if o in S:sig.add("ONE")
    ok=True
    for a in vals:
        for b in vals:
            if op_and(a,b) not in S:ok=False;break
        if not ok:break
    if ok:sig.add("AND")
    ok=True
    for a in vals:
        for b in vals:
            if op_or(a,b) not in S:ok=False;break
        if not ok:break
    if ok:sig.add("OR")
    ok=True
    for a in vals:
        for b in vals:
            for c in vals:
                if op_maj(a,b,c) not in S:ok=False;break
            if not ok:break
        if not ok:break
    if ok:sig.add("MAJ")
    ok=True
    for a in vals:
        for b in vals:
            for c in vals:
                if op_min(a,b,c) not in S:ok=False;break
            if not ok:break
        if not ok:break
    if ok:sig.add("MIN")
    return frozenset(sig)

def implication_relation():
    return [a for a in tuples(2) if (not a[0]) or a[1]]
def equality_relation():
    return [a for a in tuples(2) if a[0]==a[1]]
def parity_relation(n,rhs):
    return [a for a in tuples(n) if sum(a)%2==rhs]
def amo_relation(n):
    return [a for a in tuples(n) if sum(a)<=1]
def exact1_relation(n):
    return [a for a in tuples(n) if sum(a)==1]
def nae_relation(n=3):
    return [a for a in tuples(n) if len(set(a))>1]

def schaefer_pair_status(sig1,sig2,*,allow_pins=False):
    """Classify a fixed finite relation language, with optional unary pins.

    The default is ordinary unpinned SAT, preserving the six Schaefer cases.
    Boundary-extension queries permit both {0} and {1}; only the four
    pin-preserving polymorphisms certify that stronger problem.
    """
    common=set(sig1)&set(sig2)
    if allow_pins:
        common &= EXTENSION_POLYMORPHISMS
        if common:
            return {"status":"POLY_PINNED_SCHAEFER","common":tuple(sorted(common))}
        return {"status":"NP_COMPLETE_PINNED_LANGUAGE","common":()}
    if common:
        return {"status":"POLY_COMMON_SCHAEFER","common":tuple(sorted(common))}
    return {"status":"NP_COMPLETE_FIXED_LANGUAGE","common":()}

# ---------- native theory knowledge base ----------

NATIVE_TYPES={
    "HORN":{"tags":frozenset({"AND"}),"closed":True},
    "DUALHORN":{"tags":frozenset({"OR"}),"closed":True},
    "BIJUNCTIVE":{"tags":frozenset({"MAJ"}),"closed":True},
    "AFFINE":{"tags":frozenset({"MIN"}),"closed":True},
    "CARDINALITY":{"tags":frozenset(),"closed":False},
    "MATCHING":{"tags":frozenset(),"closed":False},
    "GENERIC":{"tags":frozenset(),"closed":False},
}

KNOWN_HARD_PAIRS={
    frozenset(("AFFINE","CARDINALITY")):"MINIMUM_DISTANCE",
    frozenset(("HORN","AFFINE")):"SCHAEFER/HORN_AFFINE",
}

def native_pair_status(a,b):
    A=NATIVE_TYPES[a];B=NATIVE_TYPES[b]
    common=A["tags"]&B["tags"]&EXTENSION_POLYMORPHISMS
    if common:
        return {"status":"POLY_CLOSED","common":tuple(sorted(common))}
    if a==b and A["closed"]:
        return {"status":"POLY_CLOSED","common":tuple(sorted(A["tags"]))}
    hp=KNOWN_HARD_PAIRS.get(frozenset((a,b)))
    if hp:
        return {"status":"KNOWN_NP_HARD","reason":hp}
    return {"status":"UNKNOWN_GENERAL","reason":None}

# ---------- structural typed planner ----------

class Region:
    def __init__(self,name,scope,native_type):
        self.name=name
        self.scope=frozenset(scope)
        self.native_type=native_type
        self.tags=NATIVE_TYPES[native_type]["tags"]

class PlanState:
    def __init__(self,subset,boundary,tags,native_type=None,mode="NATIVE",
                 total_cost=0,max_explicit_width=0,history=None):
        self.subset=frozenset(subset)
        self.boundary=frozenset(boundary)
        self.tags=frozenset(tags)
        self.native_type=native_type
        self.mode=mode
        self.total_cost=total_cost
        self.max_explicit_width=max_explicit_width
        self.history=history

def boundary_for_subset(regions,subset):
    S=set(subset)
    left=set();right=set()
    for i,r in enumerate(regions):
        (left if i in S else right).update(r.scope)
    return frozenset(left&right)

def input_scale(regions):
    # explicit structural input proxy
    return max(2,sum(len(r.scope)+1 for r in regions))

def bridge_allowed(width,N,poly_degree=2):
    return (1<<width) <= N**poly_degree

def leaf_state(regions,i):
    r=regions[i]
    return PlanState({i},boundary_for_subset(regions,{i}),r.tags,
                     native_type=r.native_type,mode="NATIVE",
                     history={"leaf":r.name,"type":r.native_type})

def merge_states(regions,a,b,poly_degree=2):
    subset=a.subset|b.subset
    parent_boundary=boundary_for_subset(regions,subset)
    union_boundary=a.boundary|b.boundary
    width=len(union_boundary)
    N=input_scale(regions)
    options=[]

    common=a.tags & b.tags & EXTENSION_POLYMORPHISMS
    if common:
        # These common polymorphisms survive conjunction, projection and pins.
        hist={"kind":"POLY_COMMON","common":tuple(sorted(common)),
              "left":a.history,"right":b.history,"union_width":width}
        options.append(PlanState(subset,parent_boundary,common,mode="SCHAEFER",
                                 total_cost=a.total_cost+b.total_cost+max(1,width),
                                 max_explicit_width=max(a.max_explicit_width,b.max_explicit_width),
                                 history=hist))

    # Same closed native type also works even if tags metadata was lost.
    if a.native_type and b.native_type and a.native_type==b.native_type:
        info=NATIVE_TYPES[a.native_type]
        if info["closed"]:
            hist={"kind":"POLY_NATIVE","type":a.native_type,
                  "left":a.history,"right":b.history,"union_width":width}
            options.append(PlanState(subset,parent_boundary,info["tags"],
                                     native_type=a.native_type,mode="NATIVE",
                                     total_cost=a.total_cost+b.total_cost+max(1,width),
                                     max_explicit_width=max(a.max_explicit_width,b.max_explicit_width),
                                     history=hist))

    # Generic exact bridge when explicit interface is polynomially bounded.
    if bridge_allowed(width,N,poly_degree):
        c=1<<width
        hist={"kind":"EXPLICIT_TT_BRIDGE","width":width,"states":c,
              "left":a.history,"right":b.history}
        options.append(PlanState(subset,parent_boundary,frozenset(),mode="TT",
                                 total_cost=a.total_cost+b.total_cost+c,
                                 max_explicit_width=max(a.max_explicit_width,b.max_explicit_width,width),
                                 history=hist))
    return options

def compress_states(states):
    # Keep cheapest state by (boundary,tags,native_type,mode,max_explicit_width).
    best={}
    for s in states:
        key=(s.boundary,s.tags,s.native_type,s.mode,s.max_explicit_width)
        if key not in best or s.total_cost<best[key].total_cost:
            best[key]=s
    # Pareto-ish global pruning: same boundary/mode/tag state only above; enough for small audits.
    return list(best.values())

def exact_subset_planner(regions,poly_degree=2,max_regions=10):
    n=len(regions)
    if n>max_regions:
        raise ValueError("audit-only exponential planner")
    dp={}
    for i in range(n):
        dp[frozenset({i})]=[leaf_state(regions,i)]
    for size in range(2,n+1):
        for combo in __import__("itertools").combinations(range(n),size):
            S=frozenset(combo);states=[]
            # unique bipartitions by requiring min(S) in A
            anchor=min(S)
            rest=sorted(S-{anchor})
            for mask in range(1<<(len(rest))):
                A={anchor}
                for j,v in enumerate(rest):
                    if (mask>>j)&1:A.add(v)
                if len(A)==len(S):continue
                B=set(S)-A
                if frozenset(A) not in dp or frozenset(B) not in dp:continue
                for sa in dp[frozenset(A)]:
                    for sb in dp[frozenset(B)]:
                        states.extend(merge_states(regions,sa,sb,poly_degree))
            dp[S]=compress_states(states)
    full=frozenset(range(n))
    if not dp.get(full):return None
    return min(dp[full],key=lambda s:(s.total_cost,s.max_explicit_width))

def greedy_planner(regions,poly_degree=2):
    states=[leaf_state(regions,i) for i in range(len(regions))]
    while len(states)>1:
        best=None
        for i in range(len(states)):
            for j in range(i+1,len(states)):
                opts=merge_states(regions,states[i],states[j],poly_degree)
                for o in opts:
                    score=(o.total_cost,o.max_explicit_width,len(states[i].boundary|states[j].boundary))
                    if best is None or score<best[0]:
                        best=(score,i,j,o)
        if best is None:return None
        _,i,j,o=best
        states=[s for k,s in enumerate(states) if k not in (i,j)]+[o]
    return states[0]

def hard_helper_fixture(w=20,shared=3):
    XH={f"h{i}" for i in range(w)}
    XA={f"a{i}" for i in range(w)}
    S={f"s{i}" for i in range(shared)}
    return [
        Region("H0",XH|S,"HORN"),
        Region("H1",XH,"HORN"),
        Region("A0",XA|S,"AFFINE"),
        Region("A1",XA,"AFFINE"),
    ]

def evaluate_declared_tree(regions,tree,poly_degree=2):
    """
    tree is int leaf or tuple(left,right).
    Return best state for fixed tree.
    """
    if isinstance(tree,int):return leaf_state(regions,tree)
    a=evaluate_declared_tree(regions,tree[0],poly_degree)
    b=evaluate_declared_tree(regions,tree[1],poly_degree)
    if a is None or b is None:return None
    opts=merge_states(regions,a,b,poly_degree)
    if not opts:return None
    return min(opts,key=lambda s:(s.total_cost,s.max_explicit_width))

# ---------- bridge assessor ----------

def assess_hard_merge(type_a,type_b,raw_width,input_size,
                      quotient_states=None,poly_degree=2):
    pair=native_pair_status(type_a,type_b)
    if pair["status"]=="POLY_CLOSED":
        return {"route":"NATIVE_CLOSED","pair_status":pair["status"],"cost":"poly"}
    if quotient_states is not None and quotient_states<=input_size**poly_degree:
        return {"route":"EXTENSION_QUOTIENT","pair_status":pair["status"],
                "states":quotient_states,"cost":"poly"}
    if (1<<raw_width)<=input_size**poly_degree:
        return {"route":"EXPLICIT_TT_BRIDGE","pair_status":pair["status"],
                "states":1<<raw_width,"cost":"poly"}
    if pair["status"]=="KNOWN_NP_HARD":
        return {"route":"HARD_BARRIER","pair_status":pair["status"],
                "reason":pair["reason"],"cost":"superpoly-unless-parameterized"}
    return {"route":"UNKNOWN_OR_LAZY","pair_status":pair["status"],"cost":"unknown"}
