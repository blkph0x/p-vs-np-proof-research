"""Exact symmetry quotient for the complete RM(2,5) level-eight model.

The model contains every coordinate scope of size at most eight, the exact
projection of the pinned RM(2,5) code on each scope, and every containment
marginal.  The finite quotient is exact: scope representatives are reduced by
GL(5,2) fixing the pin, and each setwise stabilizer is enumerated from the
linear maps induced on the span of the scope.  No floating-point solver is
used by this module; the saved rational primal certificate is checked by the
runner and independent replay.
"""

import itertools
from functools import lru_cache
from collections import Counter
from fractions import Fraction

N = 32
SCOPE_REPRESENTATIVES = {
    1: (1, 2),
    2: (3, 6),
    3: (7, 14, 22),
    4: (15, 23, 30, 150, 278),
    5: (31, 62, 151, 279, 286, 406, 33046, 65814),
    6: (63, 126, 287, 318, 407, 854, 918, 2454, 33047, 65815, 65822, 65942, 98582, 2147549462),
    7: (127, 254, 319, 382, 830, 855, 862, 919, 1942, 2455, 10646, 65823, 65854, 65943, 66390, 66454, 67990, 98583, 213270, 229654, 598294, 622870, 2147549463),
    8: (255, 383, 510, 831, 863, 894, 1910, 1943, 2550, 6038, 10647, 27030, 65855, 65918, 66366, 66391, 66398, 66455, 67478, 67991, 76182, 197462, 197526, 198038, 199062, 213271, 213278, 229655, 491798, 592278, 598295, 598358, 598422, 622871, 2720022),
}
reps = SCOPE_REPRESENTATIVES
def pts(mask): return tuple(i for i in range(N) if mask>>i&1)
def rank(vs):
 b=[]
 for v in vs:
  for x in b:v=min(v,v^x)
  if v:b.append(v);b.sort(reverse=True)
 return len(b)
@lru_cache(maxsize=None)
def canonicalize(mask):
 ps=pts(mask); nz=tuple(x for x in ps if x); r=rank(nz)
 if not r:return mask,{0:0},()
 best=None;bestmap=None
 for comb in itertools.combinations(nz,r):
  if rank(comb)!=r:continue
  for basis in itertools.permutations(comb):
   coords={0:0}
   for j,b in enumerate(basis):
    for v,c in list(coords.items()):coords[v^b]=c|(1<<j)
   mapped={p:coords[p] for p in ps}; image=sum(1<<q for q in mapped.values())
   if best is None or image<best:best=image;bestmap=mapped
 return best,bestmap,()
def affine3_masks():
 out=set()
 for bs in itertools.combinations(range(1,N),3):
  if rank(bs)!=3:continue
  vals={0}
  for b in bs:vals|={x^b for x in tuple(vals)}
  for off in range(N):out.add(sum(1<<(off^x) for x in vals))
 return out


def _affine_scopes(dimension):
    linear = set()
    for basis in itertools.combinations(range(1, N), dimension):
        if rank(basis) != dimension:
            continue
        values = {0}
        for vector in basis:
            values |= {value ^ vector for value in tuple(values)}
        linear.add(frozenset(values))
    scopes = set()
    for subspace in linear:
        for offset in range(N):
            scopes.add(tuple(sorted(offset ^ point for point in subspace)))
    return tuple(sorted(scopes))
def rm_pinned_words():
 masks=[]
 for d in range(3):
  for c in itertools.combinations(range(5),d):masks.append(sum(1<<i for i in c))
 rows=[sum(1<<p for p in range(N) if p&m==m) for m in masks]
 words=[0]
 for row in rows:words += [w^row for w in tuple(words)]
 return tuple(w for w in words if w&1)
def project(mask,w):
 return sum(((w>>p)&1)<<i for i,p in enumerate(pts(mask)))
PINNED=rm_pinned_words()
ALLOWED_REP={m:frozenset(project(m,w) for w in PINNED) for k in reps for m in reps[k]}
@lru_cache(maxsize=None)
def allowed(mask):
 cm,mp,_=canonicalize(mask)
 ac=ALLOWED_REP[cm]; dst=pts(cm); dpos={p:i for i,p in enumerate(dst)}
 src=pts(mask); out=[]
 for a in ac:
  b=0
  for i,p in enumerate(src):
   if a>>dpos[mp[p]]&1:b|=1<<i
  out.append(b)
 return tuple(sorted(out))
def autos(mask):
 ps=pts(mask); nz=tuple(p for p in ps if p); r=rank(nz)
 if not r:return (tuple(range(N)),)
 src=next(c for c in itertools.combinations(nz,r) if rank(c)==r)
 out=[]
 for target in itertools.permutations(nz,r):
  if rank(target)!=r:continue
  coords={0:0}
  for j,b in enumerate(src):
   for v,c in list(coords.items()):coords[v^b]=c|(1<<j)
  vals={0:0}
  for j,b in enumerate(target):
   for v,c in list(vals.items()):vals[v^b]=c|(1<<j)
  amap=list(range(N))
  for p in ps:amap[p]=vals[coords[p]]
  if {amap[p] for p in ps}==set(ps):out.append(tuple(amap))
 return tuple(dict.fromkeys(out))
def inv(g):
 h=[0]*N
 for i,j in enumerate(g):h[j]=i
 return tuple(h)
def comp(f,g):return tuple(f[g[i]] for i in range(N))
def gen_reduce(allg):
 I=tuple(range(N));cl={I};gens=[]
 for g in allg:
  if g in cl:continue
  gens.append(g);gi=inv(g);changed=True
  while changed:
   changed=False
   for h in tuple(cl):
    for z in gens:
     for w in (comp(z,h),comp(gi,h),comp(h,z),comp(h,gi)):
      if w not in cl:cl.add(w);changed=True
  if len(cl)==len(allg):break
 if len(cl)!=len(allg):raise RuntimeError((len(cl),len(allg)))
 return tuple(gens),len(cl)
def move_mask(mask,g):
 return sum(1<<g[p] for p in pts(mask))
def move_atom(mask,a,g):
 src=pts(mask); dst=tuple(sorted(g[p] for p in src)); pos={p:i for i,p in enumerate(dst)}
 return sum(1<<pos[g[p]] for i,p in enumerate(src) if a>>i&1)
def orbit_partition(items,move,gens):
 idx={x:i for i,x in enumerate(items)}; seen=[-1]*len(items);out=[]
 for seed in range(len(items)):
  if seen[seed]>=0:continue
  oid=len(out);q=[seed];seen[seed]=oid;mem=[]
  while q:
   i=q.pop();mem.append(i)
   for g in gens:
    j=idx[move(items[i],g)]
    if seen[j]<0:seen[j]=oid;q.append(j)
  out.append(tuple(mem))
 return seen,tuple(out)
def _group_order(dimension):
    value = 1
    for index in range(dimension):
        value *= (1 << dimension) - (1 << index)
    return value


def build_model():
 stab={};stab_orders={};stab_generators={}
 for k in range(1,9):
  for mask in reps[k]:
   ag=autos(mask);gens,o=gen_reduce(ag);stab[mask]=gens;stab_orders[mask]=o
   stab_generators[mask] = gens
 local_atom_orbits={};var_ids={};variable_orbits=[]
 for k in range(1,9):
  for mask in reps[k]:
   aa=allowed(mask);ao,orbs=orbit_partition(aa,lambda a,g:move_atom(mask,a,g),stab[mask])
   local_atom_orbits[mask]=ao
   for oid,orb in enumerate(orbs):
    var_ids[(mask,oid)]=len(variable_orbits);variable_orbits.append((mask,orb))
 allowed_index={m:{a:i for i,a in enumerate(allowed(m))} for k in range(1,9) for m in reps[k]}
 def gv(mask,a):
  cm,mp,_=canonicalize(mask); cpts=pts(cm); pos={p:i for i,p in enumerate(cpts)}
  ca=0
  for i,p in enumerate(pts(mask)):
   if a>>i&1:ca|=1<<pos[mp[p]]
  return var_ids[(cm,local_atom_orbits[cm][allowed_index[cm][ca]])]
 rows=[];rhs=[];row_reps=[]
 norm_count=sum(len(v) for v in reps.values())
 for k in range(1,9):
  for mask in reps[k]:
   rows.append(("norm",mask));rhs.append(1);row_reps.append(("norm",mask))
 for pk in range(2,9):
  for parent in reps[pk]:
   items=[]
   for q in range(1,pk):
    for cp in itertools.combinations(pts(parent),q):
     child=sum(1<<p for p in cp)
     items.extend((child,a) for a in allowed(child))
   _,orbs=orbit_partition(items,lambda x,g:(move_mask(x[0],g),move_atom(x[0],x[1],g)),stab[parent])
   for orb in orbs:
    child,ca=items[orb[0]];rows.append(("cons",parent,child,ca));rhs.append(0);row_reps.append(("cons",parent,child,ca))
 matrix=[]
 for ri,row in enumerate(rows):
  coeff=Counter()
  if row[0]=="norm":
   p=row[1]
   for a in allowed(p):coeff[var_ids[(p,local_atom_orbits[p][allowed_index[p][a]])]]+=1
  else:
   _,p,c,ca=row;ppts=pts(p);pidx={x:i for i,x in enumerate(ppts)}; child_allowed=allowed(p)
   for pa in child_allowed:
    proj=sum(((pa>>pidx[x])&1)<<j for j,x in enumerate(pts(c)))
    if proj==ca:coeff[var_ids[(p,local_atom_orbits[p][allowed_index[p][pa]])]]+=1
   coeff[gv(c,ca)]-=1
  matrix.append({str(i):int(v) for i,v in sorted(coeff.items()) if v})

 objective=[0]*len(variable_orbits)
 for p in range(1,N):objective[gv(1<<p,1)]+=1
 scope_orbit_sizes={}
 group_order=_group_order(5)
 for values in reps.values():
  for mask in values:
   r=rank(tuple(p for p in pts(mask) if p))
   extension_count=(1 << (r*(5-r))) * _group_order(5-r)
   scope_orbit_sizes[mask]=group_order // (stab_orders[mask] * extension_count)
 affine_rows=tuple(sum(1 << point for point in scope) for scope in _affine_scopes(3))
 return {
  "schema":"rm25_full_level8_quotient_v1","family":"RM(2,5)","pin":0,
  "scope_reps":{str(k):list(v) for k,v in reps.items()},
  "scope_orbit_sizes":{str(m):scope_orbit_sizes[m] for values in reps.values() for m in values},
  "allowed_reps":{str(m):sorted(ALLOWED_REP[m]) for values in reps.values() for m in values},
  "stabilizer_orders":{str(m):stab_orders[m] for values in reps.values() for m in values},
  "stabilizer_generators":{str(m):[list(g) for g in stab_generators[m]] for values in reps.values() for m in values},
  "variable_orbits":[{"scope":m,"atoms":list(o)} for m,o in variable_orbits],
  "rows":[list(r) for r in row_reps],"rhs":rhs,"matrix":matrix,"objective":objective,
  "variable_orbit_count":len(variable_orbits),"row_orbit_count":len(rows),
  "quotient_nonzero_count":sum(len(row) for row in matrix),
  "affine_flat_span_rank":rank(affine_rows),
  "source_claim":"all scopes of sizes 1 through 8; exact pinned RM(2,5) projections; all containment marginals"}


def verify_primal(model, values):
    if len(values) != model["variable_orbit_count"]:
        raise ValueError("primal length mismatch")
    values = tuple(Fraction(value) for value in values)
    if any(value < 0 for value in values):
        raise ValueError("negative primal orbit mass")
    for row, target in zip(model["matrix"], model["rhs"]):
        if sum(Fraction(coefficient) * values[int(index)] for index, coefficient in row.items()) != target:
            raise ValueError("quotient equality failure")
    objective = sum(Fraction(coefficient) * value for coefficient, value in zip(model["objective"], values))
    if objective != Fraction(31, 5):
        raise ValueError("full-level objective mismatch")
    return {"valid": True, "variable_orbits": len(values), "row_orbits": len(model["matrix"]),
            "quotient_nonzero_count": sum(len(row) for row in model["matrix"]),
            "full_level_8_optimum": "31/5"}
