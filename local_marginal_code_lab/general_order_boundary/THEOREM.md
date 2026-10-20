# A full dual-distance local witness for every Reed–Muller order

Status: written proof, independently mathematically audited, with exact finite
controls. This is not formal proof verification. Novelty is **UNKNOWN**.
The theorem gives a feasible upper bound, not the exact optimum except where
a separate lower certificate already matches it.

## Model and statement

Let `r>=1`, `m>=r+2`, `d=2^(r+1)`, and `C=RM(r,m)` evaluated on
`V=GF(2)^m`. Fix the coordinate at zero to one. For each scope of total
size at most `d`, the relaxation `L_d(C)` has a nonnegative probability table
supported on the projection of the globally pinned code, with all overlapping
marginals equal. The reduced objective `F` sums the nonpin singleton means;
the total objective is `W=1+F`. This is the same exact-projection model used in
the [formal model note](../REED_MULLER_FORMAL_MODEL.md).

Set `D=r+2` and

\[
 H={D\brack r}_2=\frac{(2d-1)(d-1)}3,
 \qquad M_A=\frac1H {D-\operatorname{rank}A\brack r}_2.
\]

A Gaussian coefficient with upper index below `r` is zero. For each nonpin
scope `S` and proposed set `B` of one-coordinates, define the atom

\[
 \mu_S(B)=\sum_{B\subseteq A\subseteq S}(-1)^{|A\setminus B|}M_A.
 \tag{1}
\]

**Theorem.** All these tables on `|S|<=d` are nonnegative, normalized,
overlap-consistent, and supported on the pinned code projection. They give
a feasible full `L_d` solution, with

\[
 p=\frac3{2d-1},\qquad
 F=\frac{3(2^m-1)}{2d-1},\qquad W=1+F. \tag{2}
\]

For `m>=r+3`, the same construction has an explicit negative atom on a
scope of `d+1` nonpin coordinates. Thus `d` is its exact first failure
boundary over those ambient dimensions. For `m=r+2`, it is an actual
global distribution and has no such failure.

The integer optimum is `I=2^(m-r)`, and

\[
 I-W=\frac{(d-2)(2^m-2d)}{d(2d-1)}. \tag{3}
\]

It is positive for every `m>r+2`. In particular, for `C_s=RM(s,2s+1)`
and `s>=2`, this proves nonintegrality at the **full dual-distance level**
`d=2^(s+1)`. The exhibited total-weight ratio is

\[
 \frac I W=\frac{4d^2-2d}{3d^2+4d-8}\longrightarrow\frac43.
 \tag{4}
\]

This extends the earlier [boundary `d-1` theorem](../REED_MULLER_THEOREM.md)
by one full locality level. It does not improve that earlier level's gap;
the stronger constraints here permit a smaller demonstrated gap. For `r=2`
this recovers the already established virtual-dimension-four witness and
the exact `31/5` reduced value at `m=5`. For higher orders no matching
lower bound is asserted.

## Sparse atom formulas

Call a three-point set `{a,b,a+b}` a line. Write `ell(S)` for the number
of lines contained in `S`, and `ell_a(S)` for those through `a`.
The moment numerators at ranks zero, one, two, and above two are,
respectively, `H`, `d-1`, `1`, and `0`.
Expanding (1) gives all possibly nonzero atoms:

* Empty: `H-(d-1)|S|+binom(|S|,2)-ell(S)`.
* Singleton `{a}`: `d-|S|+ell_a(S)`.
* Rank-two `B`: numerator one if `B=S intersect span(B)`; otherwise zero.
* Rank at least three: zero.

Every numerator is divided by `H`. The rank-two statement follows by
pairwise cancellation over any additional point of `S intersect span(B)`;
a binary rank-two subspace has just three nonzero points. For the singleton
formula, each other point contributes minus one and each contained line
through `a` contributes plus one. The empty formula follows in the same way.

Normalization and all overlap equations hold by subset Möbius inversion,
before checking positivity. The singleton and rank-two atoms are already
nonnegative for `|S|<=d`. It remains to check the empty atom.

## An elementary extremal line lemma

**Lemma.** If `S` is a set of `d=2^a` distinct nonzero binary vectors,
with `a>=2`, then

\[
 \ell(S)\le\frac{(d-1)(d-2)}6. \tag{5}
\]

Work inside the span of `S`, of dimension `R`. Since zero is excluded,
`R>=a+1`. Suppose a linear hyperplane contains `u>=d/2+1` of the points.
It cannot contain all points, so `u<=d-1`. A line either has all three
points inside the hyperplane or one inside and two outside. Counting
pairs bounds these two possibilities by

\[
 f(u)=\frac{u(u-1)}6+\frac{(d-u)(d-u-1)}2.
\]

This quadratic is convex. At `u=d-1` it equals the right-hand side of (5).
At `u=d/2+1` it is smaller by `(d-4)/6`. Thus (5) holds throughout the
permitted interval.

It remains to handle the case where every hyperplane contains at most
`d/2` points. For a binary linear functional `b`, put

\[
 h(b)=\sum_{x\in S}(-1)^{b(x)}.
\]

Then `h(0)=d` and `h(b)<=0` for every nonzero `b`. Character orthogonality,
using `0 notin S`, gives `sum_b h(b)=0`. Parseval gives
`sum_b h(b)^2=2^R d`. Hence, with `a_b=-h(b)>=0` for `b!=0`,

\[
 \sum a_b=d,\qquad
 \sum a_b^2=d(2^R-d)\le\left(\sum a_b\right)^2=d^2.
\]

Therefore `2^R<=2d`, while `R>=a+1` gives the reverse inequality.
Equality forces a single nonzero `a_b=d`, with every other one zero.
For that functional every point of `S` has `b(x)=1`; by cardinality,
`S` is precisely its affine hyperplane. Such a set contains no line,
because the sum of two of its points has `b(x)=0`. This proves the lemma.

At `|S|=d`, the empty numerator is exactly the right-hand side of (5)
minus `ell(S)`, so it is nonnegative. Any smaller scope can be extended
to `d` nonzero points: the ambient space has at least `2d-1` nonzero
points. Consistency expresses its atoms as sums of those of the larger
scope. Thus all table masses are nonnegative.

## Exact pinned projection support

If `rank(S)<=D`, embed its span into `GF(2)^D` and take a uniformly
random two-dimensional linear subspace there. Its codimension is `r`.
The probability that it contains a rank-`t` span is
`[D-t choose r]_2/[D choose r]_2`, which gives exactly the moments above.
The indicator of a codimension-`r` subspace is a product of `r` affine
linear forms, has degree at most `r`, and is one at zero. Extending the
embedding linearly to the ambient space and pulling back this polynomial
shows that each positive atom is supported on a globally pinned codeword.

If `rank(S)>D`, set `Q=S union {0}`. A nonzero dual word supported on `Q`
has weight at least `d`. Dual words have even weight because the constant-one
word belongs to the primal code. Since `|Q|<=d+1`, such a word would have
weight exactly `d`. The minimum-weight dual supports are affine
`(r+1)`-flats. These are the standard Reed–Muller facts recorded in
[Santi, Häger and Pfister, Section II.A](https://arxiv.org/pdf/1804.10319).

If this flat contains zero, its linear span has dimension `r+1`, and at
most one extra nonpin point raises `rank(S)` to at most `r+2=D`.
If it does not contain zero, its `d` points exhaust `S` and have linear
rank at most `r+2=D`. Both contradict the high-rank hypothesis.
No supported dual word exists, so the code projection on `Q` is full.
In particular all assignments on `S` extend with the pin fixed to one.

The same tables may be joined with the deterministic pin. A scope
containing zero uses its nonpin restriction, so all scopes of total size
at most `d` are covered. This completes the feasibility proof.

## Sharp failure and objective

Choose an anchor `a` and `d` distinct nonzero points in a complementary
`(r+2)`-dimensional space. This requires ambient dimension at least `r+3`.
Their union with `a` has `d+1` points and no line through `a`. The singleton
atom at `a` therefore has numerator `d-(d+1)=-1`. The implementation uses
integer labels `a=1` and the even labels `2,4,...,2d` for an explicit scope.

The singleton moment is `(d-1)/H=3/(2d-1)`, proving (2).
Reed–Muller minimum distance is `2^(m-r)`; a codimension-`r` subspace
indicator containing zero attains that pinned weight. Substitution proves
(3) and (4). All assertions concern the specified relaxation. They do not
give a lower bound for arbitrary algorithms or resolve P versus NP.

## Representation cost, evidence and remaining questions

One table has at most `1+|S|+binom(|S|,2)` stored atoms, because a pair
determines its rank-two atom and repeated lines are merged. An atom's one-set
has at most three labels; all other coordinates are zero. This gives a compact
local-table oracle, without enumerating `2^|S|` assignments. Deterministic
sorting and binary lookup give a polynomial construction in `|S|`, `m`, and
`r`, with exact integer numerators and a common `O(r)`-bit denominator.
There are still enormously many scopes. This oracle is not a polynomial-time
algorithm for discovering optimum local tables, checking arbitrary supplied
oracles globally, or solving the original codeword optimization problem.

`witness.py` implements the sparse formulas. `test_witness.py` independently
checks them against subset Möbius inversion, polynomial-evaluation projection
support, and actual subspace enumeration. It exhaustively verifies the line
bound on all 7,800 sets of size four or eight in four dimensions, checks all
delete-one marginals in a fixed finite campaign, and rejects the explicit
first-failure scopes. Source-bound normal and optimized transcripts are
recorded in `VALIDATION.json`. These finite controls supplement the proof;
they do not establish its all-size quantifiers by testing.

```text
python -m unittest -v test_witness
python -O -m unittest -v test_witness
```

The subspace-counting mechanism and code parameters are inherited. The
[novelty ledger](../LOCAL_MARGINAL_NOVELTY_LEDGER.md) identifies the prior
locally explainable non-signaling model. The extremal lemma is proved here
for self-containment, without a priority claim. A theorem-level literature
comparison for this all-order witness and a matching lower bound for orders
above two remain open.
