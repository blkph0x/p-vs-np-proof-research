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

The construction also explains the methodological limit of a hidden-structure
experiment. A compact affine representation can be found on one promised
family, while unrestricted affine recognition under existential projection is
already SAT-hard. An algorithm that claims a general discovery theorem must
state its promise, its input encoding, and how it avoids this selector barrier.

## Exact finite replay

`RESULTS.json` contains satisfiable, unsatisfiable, and empty-source controls.
The independent `verify.py` rebuilds the selector lift, enumerates the exact
projection, checks affine closure, and rejects mutations to the projected bits
and source model count. The tests keep the visible width at three and verify
the fixed non-affine truth table `[0,1,0,1,0,1,1,1]`.

The result is a rigorous barrier for general recognition, not a lower bound on
all SAT algorithms and not a P-versus-NP proof. Restricted promised families
such as the XOR chain remain efficiently recognisable by GF(2) elimination.

