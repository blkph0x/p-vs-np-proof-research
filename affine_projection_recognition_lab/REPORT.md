# Affine representation recognition under existential projection

This lab records a precise hardness barrier for the next proposed discovery
problem. The input is a CNF `F(x,y)`; its visible relation is

```text
R_F(x) = { x : exists y, F(x,y) }.
```

The decision problem `AFFINE-PROJECTION` asks whether `R_F` is a nonempty
affine coset over `F_2`. The complement-style question asks whether it is
non-affine or empty. The reduction below keeps the visible width fixed at
three variables.

## The reduction

Let `G(y)` be any CNF. Let `B(x)` be the fixed non-affine relation

```text
B(x0,x1,x2) = x0 OR (x1 AND x2),
```

encoded by `(x0 OR x1)` and `(x0 OR x2)`. Introduce a selector `s` and form

```text
F_G(x,s,y) =
  AND_{C in G}       (NOT s OR C)
  AND_{D in B}       (s OR D).
```

When `s=1`, the first group enforces `G` and the second group is vacuous.
When `s=0`, the first group is vacuous and the second group enforces `B`.
Therefore

```text
G satisfiable   => R_F = {0,1}^3, which is affine;
G unsatisfiable => R_F = B, which is non-affine.
```

Thus deciding `AFFINE-PROJECTION` would decide SAT, even though the projected
side has exactly three variables. Equivalently, deciding `NON-AFFINE-OR-EMPTY`
would decide UNSAT under the same mapping. This is a polynomial many-one
reduction statement; it is not a claim that the recognition problem has been
classified completely or that P versus NP has been resolved.

## Two-source strengthening

The same lab also records a four-visible-variable reduction from the
SAT--UNSAT pair problem. Start with the non-affine subset `B0` of the affine
plane `x3=0` given by the three clauses used above. Three selector branches add
the missing points of that plane when source `A` is satisfiable. A fifth branch
adds the point `(x0,x1,x2,x3)=(0,0,0,1)` when source `B` is satisfiable. A
one-hot selector makes the projected relation the union of all available
branches.

Consequently, the projection is affine exactly when `A` is satisfiable and
`B` is unsatisfiable. The other three cases are non-affine: the base relation
is non-affine, and an outside-plane point prevents either the completed plane
or the base relation from being affine. This is a direct reduction from the
standard SAT--UNSAT pair language, recorded as hardness evidence rather than
as a complete complexity classification.

## The strongest general upper bound recorded here

For visible width `k`, an exact recognizer can query an existential-CNF SAT
oracle once for each visible assignment, collect the `2^k` membership bits, and
test affine closure on that table. The oracle count is exactly `2^k`; the
post-processing is polynomial in the table size. The saved width-three and
width-four profiles contain 8 and 16 oracle queries respectively. This is an
upper bound in `P^NP` for fixed-width input, not a polynomial-time algorithm
when `k` is part of the input.

The selector reductions show why this accounting matters: even a constant
visible width can encode SAT or SAT--UNSAT through the existential query, while
the query count only becomes an ordinary polynomial bound after the width
promise is fixed.

For the finite witness, `B0` has masks `{1,3,5,6,7}` with `x3=0`; the three
points `1,3,6` have XOR `4`, which is absent, so `B0` is not affine. The
differences of `1` to `3`, `5`, and `6` span all three coordinates, so the
affine hull of `B0` is exactly the plane `x3=0`. Adding masks `0,2,4` completes
that plane. Adding mask `8` instead forces the affine hull to be the full
four-dimensional cube; the resulting six- or nine-point sets are therefore
not affine.

The construction also explains the methodological limit of a hidden-structure
experiment. A compact affine representation can be found on one promised
family, while unrestricted affine recognition under existential projection is
already SAT-hard. An algorithm that claims a general discovery theorem must
state its promise, its input encoding, and how it avoids this selector barrier.

## Exact finite replay

`RESULTS.json` contains satisfiable, unsatisfiable, and empty-source controls.
The independent `verify.py` rebuilds the selector lift, enumerates the exact
projection, checks affine closure, and rejects mutations to the projected bits
and source model count. The tests keep the one-source visible width at three,
the two-source width at four, exhaust all 256 two-variable source CNFs, and
verify the fixed non-affine truth table `[0,1,0,1,0,1,1,1]`.

The result is a rigorous barrier for general recognition, not a lower bound on
all SAT algorithms and not a P-versus-NP proof. Restricted promised families
such as the XOR chain remain efficiently recognisable by GF(2) elimination.
