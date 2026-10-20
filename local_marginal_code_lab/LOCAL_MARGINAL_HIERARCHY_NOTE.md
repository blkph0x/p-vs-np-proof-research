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

## A precise one-sided comparison that is now proved

There is one standard finite-domain formulation for which the relationship is
exact. Form the extensional CSP `I_k(C)` whose variables are the coordinates
and whose declared relations are

```text
R_S = R_S(C)  for every nonempty S with |S| <= k.
```

Use the usual level-`k` Sherali--Adams/configuration representation: a local
variable is a nonnegative distribution on each allowed assignment to a scope,
each distribution is normalized, and distributions agree on every overlap.
The map

```text
mu_S(a)  <->  the level-k configuration variable for (S,a)
```

is a coordinate-by-coordinate bijection. The normalization and overlap rows
are the same equations, and the singleton objective is unchanged. Therefore

```text
L_k(C) = SA_k(I_k(C))
```

for this explicitly declared finite-domain relation family, at every `k`.
This is a formulation theorem, not a new lower bound: the relations `R_S(C)`
already contain the exact global projections of `C`.

It does **not** identify the RM experiments with Sherali--Adams applied to a
sparse Boolean parity-check CNF. That comparison still depends on the chosen
encoding and on which constraints are visible at each level. The four-variable
control above is a concrete separation between the two support constructions.
The repository now reports both facts: exact configuration-SA equivalence for
`I_k(C)`, and an open formulation-specific comparison for parity encodings.

## A one-sided theorem for check-local parity configurations

Fix a parity-check matrix `H` for `C`, with check scopes `E_a`. For a pinned
model, include the pin as a unary relation in both formulations. Define the
check-local support on a queried scope `S` by

```text
Q_S(H) = { u in {0,1}^S : every check E_a subseteq S
                         has even parity under u }.
```

Let `SA_k^check(H)` be the configuration LP whose table on `S` is supported on
`Q_S(H)` and whose tables agree on all containments, for `|S| <= k`. This is a
fully specified finite-domain parity formulation; it is not being identified
with every polynomial Sherali--Adams encoding of the same equations.

For every scope, `R_S(C) subseteq Q_S(H)`, because a global codeword satisfies
every check, including checks contained in `S`. Extending an `L_k(C)` table by
zero on `Q_S(H) setminus R_S(C)` preserves normalization and every overlap
equation. Hence there is a coordinatewise inclusion

```text
L_k(C) subseteq SA_k^check(H),
opt(SA_k^check(H)) <= opt(L_k(C))
```

for minimization objectives read from the same singleton tables. The inclusion
can be strict at the same locality: in the four-variable control, the scope
`{2,3}` contains no whole parity check, so `Q_{2,3}(H)` is all four pair
assignments, while `R_{2,3}(C) = {00,11}`. This proves a one-sided hierarchy
relationship and a finite strict-support separation for the declared
check-local formulation. It does not compare either configuration LP with a
canonical sparse-CNF Sherali--Adams or Lasserre level without an additional
variable map.

The same four-variable control gives a strict objective separation after
pinning `x_0=1` and minimizing the free weight `F=x_1+x_2+x_3`. The two pinned
codewords are `1100` and `1011`. In every global projection, `x_1+x_2=1` and
`x_2=x_3`, so every `L_2(C)` point has

```text
F = E[x_1] + 2 E[x_2] = 1 + 2 E[x_2] >= 1.
```

At level two, no parity check is wholly contained in a free pair scope. The
check-local configuration LP therefore accepts the point mass with
`(x_1,x_2,x_3)=(0,0,0)` and pinned `x_0=1`, giving `F=0`. Thus
`opt(SA_2^check(H))=0 < 1 <= opt(L_2(C))` for this explicit pinned example.
The separation is exact and finite; it does not assert a separation for every
parity encoding or every level.

## Comparison with the ordinary sparse 3-CNF clause relaxation

The same example also separates the check-local configuration model from the
ordinary clause relaxation of the sparse parity encoding. Encode each ternary
even-parity check by its four clauses forbidding the odd assignments, and add
the pin equality `x_0=1`. Substituting the pin into the two checks leaves the
four binary clauses

```text
(x_1 or x_2),  (not x_1 or not x_2),
(x_1 or x_3),  (not x_1 or not x_3).
```

Their standard 0/1 clause inequalities give
`x_1+x_2 >= 1`, `x_1+x_2 <= 1`, `x_1+x_3 >= 1`, and
`x_1+x_3 <= 1`. Therefore the unlifted clause LP (the first Sherali--Adams
level under the common indexing convention for this 0/1 clause formulation)
has

```text
F = x_1+x_2+x_3 >= 1.
```

The satisfying assignment `(x_0,x_1,x_2,x_3)=(1,1,0,0)` attains `F=1`, so
the clause-LP optimum is exactly one. The check-local level-two configuration
model still has the feasible zero-free point with value zero. Hence, for this
declared encoding,

```text
opt(SA_2^check(H)) = 0 < 1 = opt(clause-LP with x_0=1)
                 <= opt(L_2(C)).
```

This is a finite encoding-specific comparison. It does not identify the full
projection hierarchy with every polynomial Sherali--Adams convention, and it
does not give an all-size sparse-parity hierarchy theorem. The exact clause
simplification and the three objective controls are replayed in
`review_sparse_parity_clause_comparison.py`, with the mutation controls in
`test_sparse_parity_clause_comparison.py`.

## Exact check

```text
python -m unittest -v test_local_marginal_hierarchy_note.py
python review_sparse_parity_clause_comparison.py
python -m unittest -v test_sparse_parity_clause_comparison.py
```
