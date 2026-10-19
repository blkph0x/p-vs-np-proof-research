# Where the projection-marginal LP sits among hierarchy formulations

This note fixes the proof-system terminology for the local-marginal results.
It is a statement about finite polytopes, not a claim that the project has
identified a new standard hierarchy.

## Definition used by the lab

For a finite binary set `C ⊆ {0,1}^n`, let

```text
R_S(C) = { x restricted to S : x in C }.
```

The level-`k` projection-marginal polytope `L_k(C)` contains one nonnegative
table `mu_S(a)` for each `S` with `|S| <= k` and each `a in R_S(C)`. Every
table is normalized, and the tables agree under every containment
`T subseteq S`:

```text
sum over b restricting to a on T of mu_S(b) = mu_T(a).
```

The RM experiments use exactly this definition, with `C` the pinned
codeword set and the objective read from singleton tables.

## Elementary facts proved by the definition

1. Every distribution on `C` gives a feasible point of `L_k(C)` by taking
   its local marginals. Therefore `L_k(C)` is an outer approximation of the
   projections of the global codeword polytope.
2. Restricting a level-`k+1` point to smaller scopes gives a level-`k` point.
   For a minimization objective, the certified lower bound can only increase
   as `k` increases.
3. At `k=n`, `L_n(C)` is exactly the global distribution polytope on `C`:
   the table on the full scope is itself a distribution supported on `C`, and
   all other tables are its marginals.

The first statement is only an inclusion. Local consistency does not in
general produce one distribution on all `n` coordinates; that missing gluing
property is precisely the source of the finite gaps recorded in the lab.

## Why this is not automatically Sherali--Adams

Sherali--Adams is a lift of a specified linear or polynomial formulation.
Its bounded-level polytope depends on that formulation. The projection model
above can be described as exact `k`-local consistency for the relation family
`R_S(C)`, but that relation family already contains the consequences of all
global constraints. This description does not identify it with the
Sherali--Adams lift of a particular parity-check formulation.

A four-variable example shows why the distinction matters. Let

```text
C = {x : x0 xor x1 xor x2 = 0,
          x0 xor x1 xor x3 = 0}.
```

Every word in `C` has `x2 = x3`, so the exact global projection on the pair
`{2,3}` is `{00, 11}`. If one forms a local support rule by inspecting only
parity equations whose entire check scope lies inside a queried pair, then
the same pair sees no check at all and all four assignments are allowed.
Thus global projection support can be strictly tighter than a check-local
support rule at the same locality level.

The accompanying test enumerates this example exactly. It is a warning
against calling the RM certificates “level-`k` Sherali--Adams” without first
specifying the base formulation and proving a map between its moment variables
and the tables above. The primary hierarchy reference used for terminology is
[Sherali and Adams, *A hierarchy of relaxations and convex hull
characterizations*](https://doi.org/10.1016/0166-218X(92)00190-W).

The same caution applies to SOS/Lasserre. The explicit Boolean-square audit is
a moment constraint; the later integer-domain polynomial cuts are not thereby
members of a named SOS degree. Their terminology is fixed in the referee
response and the seven-cut report.

## Consequence for the project claims

The RM family theorem is a theorem about `L_k(C)` as explicitly defined. It
does not claim a lower bound for every Sherali--Adams formulation, every
Lasserre level, or every SAT algorithm. A stronger or weaker relationship can
be asserted only after the relevant formulation and variable map are written
down and checked.

The finite quotient certificate and its compact dual inequality are therefore
valid as scoped local-marginal results while the standard-hierarchy comparison
remains an open research gate.

## Exact check

```text
python -m unittest -v test_local_marginal_hierarchy_note.py
```
