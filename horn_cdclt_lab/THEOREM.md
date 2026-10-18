# Mixed Horn/affine frontier

This lab gives a checked complexity barrier for the proposed theory-portfolio route. It
does not prove either side of P versus NP.

## Fixed relations

Let

\[
H(x,z_0,z_1)=\{000,110,001\}.
\]

The following three Horn clauses define exactly `H`:

```
(-x OR z0), (x OR -z0), (-x OR -z0 OR -z1).
```

Let `A(y,w,z0,z1)` be defined by the affine equations

```
y XOR z1 = 0
w XOR z0 XOR z1 = 1.
```

The implementation exhaustively evaluates all eight assignments for `H` and all sixteen
assignments for `A`; the accepted sets are exactly the displayed relations.

## Exact-one projection

For every `x,y,w`, exhaustive enumeration of `z0,z1` gives

```
exists z0,z1 . H(x,z0,z1) AND A(y,w,z0,z1)
       iff x+y+w = 1.
```

The witnesses are `(z0,z1)=(0,0)` for `001`, `(0,1)` for `010`, and `(1,0)` for
`100`; the other five target assignments have no witness.

## Reduction consequence

Given a positive 1-in-3-SAT instance with clauses `(a,b,c)`, introduce two fresh bridge
variables per clause and add one renamed copy of the three Horn clauses for `H` plus the
two affine equations for `A`. The projection fact applies independently to every clause,
so the original instance is satisfiable exactly when the resulting mixed Horn/affine
instance is satisfiable. The construction has constant work and two fresh variables per
clause.

Therefore a polynomial-time algorithm for arbitrary conjunctions of Horn constraints and
GF(2) equations with existentially quantified shared variables would yield a polynomial
algorithm for positive 1-in-3-SAT, and hence P=NP. This rules out the hope that simply
combining the two individually polynomial propagators gives a universal polynomial solver.
The conditional statement uses the standard NP-completeness of positive 1-in-3-SAT; the
finite checks in this repository verify the gadget itself and its implementation.

## Certificates and audit

`HornTheory` returns a source-clause index and a partial assignment for every unit or
conflict step. `AffineTheory` returns a row-combination certificate. The independent
replay recomputes both kinds of certificate without calling the solver's verifier.

The audit checked all 16 subsets of the four positive 1-in-3 clauses on four variables,
plus the complete-triple families on 3 through 10 target variables. Direct enumeration
and the encoded solver agreed on satisfiability, every returned solution satisfied every
original exact-one clause, and every recorded certificate replayed independently.

The search engine is deterministic depth-first branching. Its node count is therefore an
explicit record of the remaining search component; the experiment is not presented as a
polynomial algorithm.

## Clause-learning extension

`cdcl.py` adds first-UIP clause learning while keeping Horn clauses and affine equations
opaque. A theory propagation or conflict first emits its source certificate; a learned
clause is then a recorded resolution chain over those checked explanations. The independent
replayer in `review_cdcl.py` recomputes every source explanation and every resolution step.

Three independent 3-coloring controls were translated to positive 1-in-3 instances. Each
vertex gets an exactly-one color clause. For an edge and color, the clause `(u_c,v_c,z)`
has a fresh `z` and is satisfiable exactly when the two endpoint color literals are not
both true. Thus the reduction is satisfiable exactly when the graph is 3-colorable. The
K4, sparse-12, and sparse-14 controls are independently rejected by a separate exhaustive
3-coloring checker; the encoded mixed solver rejects all three and all proof logs replay.

On the saved sparse controls, clause learning reduces deterministic search substantially:

| control | DFS nodes | CDCL decisions | CDCL conflicts | learned clauses | max learned width |
|---|---:|---:|---:|---:|---:|
| K4 | 11 | 6 | 6 | 5 | 3 |
| sparse-12 | 287 | 29 | 9 | 8 | 3 |
| sparse-14 | 491 | 88 | 55 | 54 | 7 |

This is a real algorithmic improvement and a useful proof-compression measurement. It is
not a complexity result: the exact-one projection above still embeds an NP-complete
language, and no polynomial upper bound on the number or size of learned clauses has been
proved. The machine-readable audit is `CDCL_RESULTS.json` with verdicts in
`CDCL_REVIEW.json`.

## Polymorphism audit

The fixed relations were also checked as finite relational structures. Exhaustive
enumeration of all Boolean operations of arity 1, 2, 3, and 4 finds exactly the projections
as operations preserving both `H` and `A` (counts 1, 2, 3, and 4). The named Schaefer
operations separate cleanly: `AND` preserves `H` but not `A`, while ternary minority/XOR
preserves `A` but not `H`; majority preserves `H` but not `A`. The complete tables and an
independent replay are in `POLYMORPHISM_RESULTS.json` and `POLYMORPHISM_REVIEW.json`.

The finite enumeration is independently replayed in the saved artifact. A self-contained
all-arity proof is given in [POLYMORPHISM_THEOREM.md](POLYMORPHISM_THEOREM.md): preservation
of the renamed odd-parity relation forces an arbitrary common operation to be affine, and
preservation of `H` then forces its affine support to have exactly one coordinate. Thus
the common clone is projections, not merely the tested finite fragment.
