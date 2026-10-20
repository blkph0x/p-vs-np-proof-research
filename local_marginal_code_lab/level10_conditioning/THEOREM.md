# Level ten closes by conditioning the level-nine identity

For every \(m\ge6\), the full pinned quadratic Reed–Muller locality-ten
relaxation satisfies
\[
 \boxed{\min F=\frac{5(2^m-1)}{21},\qquad
        \min W=\frac{5\cdot2^m+16}{21}.}
\]
Here the pin is \(x_0=1\), \(F=\sum_{a\ne0}\Pr[x_a=1]\), and \(W=1+F\).
The relaxation has normalized, nonnegative, mutually consistent tables on
every coordinate scope of **total size at most ten**, supported on projections
of the globally pinned code \(RM(2,m)_1\).

This report proves the lower bound by an eight-term nonnegative identity.
The matching upper bound is the **separate** \(D=6\) specialization of
[the virtual-dimension theorem](../REED_MULLER_VIRTUAL_DIMENSION_THEOREM.md),
whose locality range is \(D+4\). The selected LP primal below is not being
used as a full-locality upper certificate. At \(m=6\), the total value is16,
also attained by actual quadratic codewords.

These are exact mathematical derivations and independently replayed rational
certificates, not proof-assistant verification. Novelty is unknown.
No conclusion about P versus NP follows.

## The useful recurrence is an identity, not just an inequality

First average a feasible full solution over \(GL(m,2)\). This preserves the
pin, projection supports, overlap consistency and objective. Write \(p\) for
the common nonzero singleton moment and \(q\) for the common moment of two
distinct nonzero coordinates.

Choose an affine five-flat \(A\) that avoids0 and a point \(a\in A\).
For each \(S\subseteq A\), \(|S|\le9\), condition the original table on
\(S\cup\{a\}\) upon \(x_a=1\). This uses at most ten original coordinates.
When \(p>0\), division by \(p\) gives consistent conditional tables.
Each supported atom extends to an original quadratic polynomial with
value1 at \(a\); restriction to \(A\) and translation of \(a\) to zero
therefore gives a pinned \(RM(2,5)\) projection. The conditional tables
constitute a feasible full \(L_9\) solution.

The conditional singleton probability at every point other than \(a\) is
\(q/p\). The proved
[level-nine theorem](../REED_MULLER_QUADRATIC_LEVEL9_THEOREM.md) gives
\[
 1+31q/p\ge8,\qquad\text{hence}\qquad31q\ge7p.                 \tag{1}
\]
There is no division issue for a feasible original solution: on a linear
three-flat through0, the seven nonpin coordinates have odd parity, so
\(7p\ge1\). More generally the scalar consequence at \(p=0\) follows
from nonnegativity.

The simple recurrence is useful but insufficient in the selected model.
Adding only (1) to the59-variable double-outside model gives exact optimum
\(1953/8369<5/21\). Keeping the **complete level-nine identity** instead
gives \(5/21\).

For a general level \(k\), the same argument on an affine \(d\)-flat avoiding
the original pin gives
\[
 (2^d-1)q\ \ge\ \bigl(B_{k-1}(d)-1\bigr)p,
\]
whenever \(B_{k-1}(d)\) is a proved lower bound on total pinned
\(L_{k-1}(RM(2,d))\) weight and \(m\ge d+1\).
This is a necessary consequence, not a general proof that such scalar
recurrences determine higher levels. The successful step here retains
the positive terms of an exact prior identity.

## Original atom quantities and the conditional map

The following definitions agree with the
[earlier source-counted scope model](../level10_exploration/REPORT.md).
All masses are for **one specified assignment of its type**, not total orbit
masses. Let
\[
 H=\{16,\ldots,23\},\qquad a=24,\qquad u=32.
\]
Their linear span has dimension six. They all lie in the affine five-flat
\[
 A=\{x\in\mathbb F_2^6:x_4+x_5=1\}.
\]
For larger \(m\), use this same configuration in a six-dimensional subspace.
Thus \(H\) avoids0, and \(a,u\) are independent modulo
\(\operatorname{span}(H)\). The original scope \(H\cup\{a,u\}\) has size10.

On a linear three-flat through the pin, nonpin ones have odd size. The five
types are singleton, zero-sum triple, independent triple, five-set and
seven-set, with multiplicities \(7,7,28,21,1\); their per-atom masses are
\(z_0,\ldots,z_4\).

The six even-atom types on \(H\) are empty, pair, affine plane \(P\),
nonplane four-set \(N\), six-set and full, with multiplicities
\(1,28,14,56,28,1\); their masses are \(z_5,\ldots,z_{10}\).
For a specified such atom, let \(b_i\) be its joint mass with \(x_a=1\),
and \(\gamma_i\) its joint mass with \(x_a=x_u=1\). Ambient symmetry
interchanges the two outside points, so its four outside-pattern masses are
\[
 11:\gamma_i,\quad 10: d_i=b_i-\gamma_i,\quad
 01:d_i,\quad00:e_i=z_{5+i}-2b_i+\gamma_i.
\]
The subscript \(5+i\) uses the position in the ordered six-type list.
All these quantities are nonnegative.

Any affine automorphism of \(A\) fixing \(a\) extends to a linear ambient
automorphism fixing0 and \(a\): in the decomposition
\(\operatorname{span}(A)=\langle a\rangle\oplus\operatorname{dir}(A)\),
fix \(a\) and use the corresponding invertible linear map on
\(\operatorname{dir}(A)\). Consequently the conditioned solution already
has the symmetry needed by the level-nine identity.

Use primes for the conditional, translated level-nine quantities. Then
\[
 p'=q/p,\qquad z_2'=z_8/p,\qquad
 z_8'=b_N/p,\qquad z_{10}'=b_8/p,\qquad b_i'=\gamma_i/p.       \tag{2}
\]
The only less immediate map is \(z_2'\): the conditioned pinned flat
through \(a\) becomes an original affine three-flat avoiding0.
Its three relatively independent nonpin ones, together with \(a\), form
a four-set whose xor is nonzero, hence a nonplane four-set.
Conversely these are exactly the nonplane four-sets containing \(a\).
There are28 of them. Translation preserves the even-flat type labels
on \(H\); the additional conditioned outside point is \(u\).
Indeed \(H+a=\{8,\ldots,15\}\) spans a four-space, while \(u+a=56\)
is outside that span.

Substitution of (2) into the old level-nine identity, followed by
multiplication by \(p\), proves
\[
\begin{split}
279q-63p={}&672z_8+1904\gamma_P+8568\gamma_N
 +4928\gamma_6+216\gamma_8\\
 &+952d_N+328d_8.                                          \tag{3}
\end{split}
\]
If the same conditional formula is used abstractly at \(p=0\), every
nonempty atom on its right vanishes by singleton consistency: \(q=0\),
\(z_8=0\), and all the displayed joint masses involving \(x_a=1\) are zero.
Thus the unnormalized identity remains valid. In the actual pinned feasible
family, the earlier \(7p\ge1\) already excludes this case.
This equality is the missing higher-order consistency consequence. The
older selected model matched only certain low moments of the double-outside
scope and did not imply (3).

## An eight-term exact lower certificate

The original pin/flat/mixed incidence equations together with (3) imply
\[
\begin{split}
5481p-1305={}&22620z_2+26100z_3+55216\gamma_P
 +214368\gamma_N+4176\gamma_8\\
 &+32480d_6+32480d_8+6496e_N.                              \tag{4}
\end{split}
\]
Every term on the right is a nonnegative atom mass. Since
\(5481=21\cdot261\) and \(1305=5\cdot261\), (4) proves \(p\ge5/21\).
It uses neither the previous inequality \(q-8r+28v\ge0\) nor the additional
twenty-orbit ten-scope. Those remain useful historical controls, but are
not necessary for this proof.

For a direct check without the quotient matrix or any optimizer, let
\(r\) and \(v\) be the moments of three and four linearly independent
nonzero points, and \(h\) the moment of a four-point affine plane avoiding0.
The following expressions are zero, in order:
\[
\begin{array}{rl}
E_1=&7z_0+7z_1+28z_2+21z_3+z_4-1,\\
E_2=&p-z_0-3z_1-12z_2-15z_3-z_4,\\
E_3=&q-z_1-4z_2-10z_3-z_4,\\
E_4=&r-z_2-6z_3-z_4,\qquad E_5=h-3z_3-z_4,\\
E_6=&z_5+28z_6+14z_7+56z_8+28z_9+z_{10}-1,\\
E_7=&p-7z_6-7z_7-28z_8-21z_9-z_{10},\\
E_8=&q-z_6-3z_7-12z_8-15z_9-z_{10},\\
E_9=&r-z_7-4z_8-10z_9-z_{10},\\
E_{10}=&h-z_7-6z_9-z_{10},\quad E_{11}=v-z_8-6z_9-z_{10},\\
E_{12}=&p-b_0-28b_2-14b_P-56b_N-28b_6-b_8,\\
E_{13}=&q-7b_2-7b_P-28b_N-21b_6-b_8,\\
E_{14}=&r-b_2-3b_P-12b_N-15b_6-b_8,\\
E_{15}=&v-b_P-4b_N-10b_6-b_8,\\
E_{16}=&3z_9+z_{10}-b_P-6b_6-b_8,\\
E_{17}=&q-\gamma_0-28\gamma_2-14\gamma_P-56\gamma_N-28\gamma_6-\gamma_8,\\
E_{18}=&r-7\gamma_2-7\gamma_P-28\gamma_N-21\gamma_6-\gamma_8,\\
E_{19}=&v-\gamma_2-3\gamma_P-12\gamma_N-15\gamma_6-\gamma_8,\\
E_{20}=&279q-63p-672z_8-1904\gamma_P-8568\gamma_N-4928\gamma_6
        -216\gamma_8-952(b_N-\gamma_N)-328(b_8-\gamma_8).
\end{array}
\]
The first19 are normalization and direct incidence counts on the displayed
original scopes; \(E_{20}\) is (3). The exact multipliers
```text
[1305,9135,-18270,22620,-12180,0,-126,882,-13944,12180,
 17584,0,1764,-12348,8120,16576,0,3672,-25704,56]
```
sum these expressions to the left side of (4) minus its right side.
`replay.verify_elementary_identity` checks every symbolic coefficient using
integer arithmetic, independently of all saved LP matrices.

## Exact discovery and trust boundary

The two new searches started from the frozen source-built double-outside
model, with no expected answer or initial basis supplied to SoPlex:

| Added consequence | Variables | Equalities | Exact selected minimum \(p\) |
|---|---:|---:|---:|
| \(31q-7p\ge0\), with a nonnegative slack |60|81|\(1953/8369\)|
| Full conditioned identity (3) |59|81|\(5/21\)|

The objective is \(p\), with reporting offset0. SoPlex ran in rational mode
with feasibility and optimality tolerances zero. An independent generic
Fraction verifier checked exact primal feasibility, dual feasibility and
equal objectives. `replay.py` additionally rebuilds the old original scope
incidences through the frozen independent reviewer, reconstructs the new
conditioned row, and rejects a model that differs even if its digest has
been rebound. No discovery producer or optimizer is imported by the checker.

The saved search identity uses the historical variable \(z_{13}\); its
local consistency relation is \(z_{13}=4(z_2+z_3)\). Formula (4) eliminates
that auxiliary variable and has the separate elementary incidence check.
The saved dual multiplier of the old ten-point inequality row64 is zero.

The full-family lower bound follows from actual size-ten tables, symmetry
and the conditional level-nine theorem, not from a claim that a selected
model is the full relaxation. The separate virtual-\(D6\) construction
provides the upper bound. At \(m=6\), an additional positive control directly
enumerates all651 codimension-two subspaces, so the attaining point is an
actual distribution of quadratic codewords.

From this directory:
```text
python -B replay.py
python -B -m unittest test_conditioning -v
python -B -O -m unittest test_conditioning -v
```
Discovery artifacts are under `exact_run`; `REPLAY.json` binds source and
artifact replay. The previous `level10_exploration` artifacts are unchanged.
