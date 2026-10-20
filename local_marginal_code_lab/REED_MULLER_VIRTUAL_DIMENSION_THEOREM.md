# Quadratic Reed-Muller local witnesses with a sharp locality boundary

Status: complete written proof, independently mathematically audited.
Executable controls are separate evidence; this is not formal proof
verification. Novelty is **UNKNOWN**.
The conclusion is a feasible upper witness and its exact locality boundary,
not an optimum formula or a result about P versus NP.

## Statement and conventions

For integers \(D\ge3\) and \(m\ge D\), let \(V=\mathbb F_2^m\).
Coordinates of \(RM(2,m)\) are the points of \(V\); pin coordinate zero
to one. For an integer \(t\), define
\[
 G(t)=
 \begin{cases}(2^t-1)(2^t-2)/6,&t\ge2,\\0,&t<2.\end{cases}
\]
Thus \(G(t)={t\brack2}_2\) when \(t\ge0\).
For any set \(A\) of nonzero coordinates set
\[
 M_A=\frac{G(D-\operatorname{rank}A)}{G(D)},\qquad
 \mu_S(B)=\sum_{B\subseteq A\subseteq S}(-1)^{|A\setminus B|}M_A.
 \tag{1}
\]
Here \(B\) specifies exactly the one-coordinates in the atom on \(S\).

**Upper-witness theorem.** For every \(|S|\le D+4\), the table
\(\mu_S\) is nonnegative, normalized, and supported on the projection
of the globally pinned code. The tables are consistent on all overlaps.
They can therefore also be viewed as joint tables on each such \(S\)
and the deterministic pin.

In particular they give a feasible solution of the relaxation \(L_{D+4}\)
defined using scopes of **total size at most \(D+4\)**. The stronger
joint-with-pin statement includes some scopes of total size \(D+5\);
it does not assert full \(L_{D+5}\) feasibility.

The singleton and objective values are
\[
 p_D=\frac{2^{D-2}-1}{2^D-1},\qquad
 F=(2^m-1)p_D,\qquad W=1+F. \tag{2}
\]
These are upper bounds on the corresponding minimum objectives.
Matching lower bounds are already proved for \(D=4,5\) in
[the level-eight theorem](REED_MULLER_QUADRATIC_LEVEL8_THEOREM.md)
and [the level-nine theorem](REED_MULLER_QUADRATIC_LEVEL9_THEOREM.md).
No matching lower bound is claimed here for \(D\ge6\).

**Sharp boundary for this construction.** For each \(D\ge3\) and
\(m\ge D+1\), an explicit scope of \(D+5\) nonpin coordinates has a
negative atom under (1). Thus \(D+4\) is the largest locality guaranteed
uniformly over ambient dimensions by these particular moments.
When \(m=D\), they come from actual global codewords and do not have
that failure.

**Growing-locality corollary.** The integer optimum with the pin fixed
to one is \(I=2^{m-2}\): this is the minimum distance of \(RM(2,m)\),
and a codimension-two subspace indicator attains it with value one at
zero. For \(m>D\ge3\), the exhibited feasible value satisfies
\[
 I-W=
 \frac{3(2^{m-2}-2^{D-2})}{2^D-1}>0. \tag{3}
\]
Consequently the relaxation optimum is strictly below the integer optimum.
Taking \(D=m-1\), for every \(m\ge4\) the full \(L_{m+3}(RM(2,m))\)
relaxation is nonintegral, with an exhibited additive gap
\[
 \frac{3\cdot2^{m-3}}{2^{m-1}-1}.
\]
The ratio \(I/W\) in this growing-locality regime tends to one; this
corollary does not establish a constant-factor asymptotic gap.

## Consistency and the genuine low-rank case

The subset Möbius inversion (1) has moments \(M_A\); summing out a
coordinate cancels exactly its paired terms. Hence all overlap marginals
agree, and normalization follows from \(M_\varnothing=1\).
These are algebraic identities before nonnegativity is established.

If \(\operatorname{rank}S\le D\), embed its span into \(\mathbb F_2^D\)
and choose a uniform codimension-two subspace there. The number containing
a fixed rank-\(r\) subspace is \(G(D-r)\), out of \(G(D)\) choices.
This realizes (1) as an actual distribution. Such a subspace has indicator
\((1+\ell_1)(1+\ell_2)\) over \(\mathbb F_2\), a polynomial of degree
at most two taking value one at zero. Extend the embedding linearly
from the scope's span to \(V\), and pull back this polynomial.
Every resulting atom is therefore a restriction of a pinned RM2 codeword.

The counting/Möbius mechanism is classical; the additional issue addressed
below is nonnegativity when the scope rank exceeds \(D\). See the
[novelty ledger's subspace-counting comparison](LOCAL_MARGINAL_NOVELTY_LEDGER.md).

## A general pinned-support lemma

Suppose \(|S|=k\le D+4\) and \(\operatorname{rank}S>D\). We show that
the projection of \(RM(2,m)\) on \(Q=S\cup\{0\}\) is full.

Any nonzero dual word supported in \(Q\) has a support \(U\) of size
\(w\ge8\), by the standard RM dual minimum distance, valid for every
\(m\ge3\). The duality and minimum-distance facts used here and in
the corollary are stated in
[Santi, Häger, and Pfister, Section II](https://arxiv.org/pdf/1804.10319).
On \(U\), the
evaluation rows of the coordinate linear functions are pairwise
orthogonal over \(\mathbb F_2\): their products have degree at most two
and hence sum to zero against the dual support. The rowspace is
self-orthogonal, so its dimension, which is \(\operatorname{rank}U\),
is at most \(w/2\).

If \(0\notin U\), adding the at most \(k-w\) points of \(S\setminus U\)
gives
\(\operatorname{rank}S\le w/2+k-w=k-w/2\).
If \(0\in U\), the constant-one evaluation row is independent of the
linear rows, since the latter vanish at zero. Adjoining it still gives
a self-orthogonal space. Therefore
\(\operatorname{rank}U+1\le w/2\); adding at most \(k-w+1\) outside
nonpin points again gives \(\operatorname{rank}S\le k-w/2\).

In either case \(\operatorname{rank}S\le k-4\le D\), a contradiction.
There is no supported nonzero dual word. The annihilator characterization
of a linear-code projection now proves that the projection on \(Q\) is
full. In particular every assignment on \(S\) with the pin fixed to one
is admissible. No classification of weight-eight or weight-ten supports
is required for this lemma.

## All nonempty atoms reduce to the preceding D

Assume nonnegativity is known for virtual dimension \(D-1\) on at most
\(D+3\) nonpin points. Fix \(a\in S\), condition on \(x_a=1\), and pass
to the vector-space quotient by \(\langle a\rangle\).
For any \(A\subseteq S\setminus\{a\}\),
\[
 \frac{M_{A\cup\{a\}}}{M_{\{a\}}}
 =
 \frac{G((D-1)-\operatorname{rank}\bar A)}{G(D-1)}. \tag{4}
\]
There are at most \(|S|-1\le D+3\) distinct nonzero quotient points.
Points of \(S\) in the same quotient coset must be assigned the same
conditional bit. To construct the conditional table, take the nonnegative
\((D-1)\)-table on these distinct points and duplicate its bit on each
represented coset. Its moments are exactly (4), including moments using
repeated cosets. Uniqueness of subset Möbius inversion identifies it
with the conditional table from (1).

Every atom with \(x_a=1\) consequently has nonnegative mass. Choosing
an element of any nonempty \(B\) proves nonnegativity of every nonempty
atom. Inconsistent duplicate-coset assignments have mass zero.
This reduces the induction to the empty atom.

For the base \(D=3\), the moment numerators are \(G(3)=7\),
\(G(2)=1\), and zero at all ranks at least two. Distinct nonzero
points have rank two in pairs. Thus on any \(k\le7\) points,
\[
 \mu_S(\varnothing)=(7-k)/7,\qquad
 \mu_S(\{a\})=1/7\quad(a\in S),\qquad
 \mu_S(B)=0\quad(|B|\ge2).
\]
These are nonnegative; the low-rank argument and high-rank support lemma
already establish code-projection support. This gives a self-contained
base without using earlier positivity theorems.

It is enough at each later \(D\ge4\) to prove tables on exactly \(D+4\)
nonpin points: smaller scopes extend to that size, and are their
algebraic marginals. There are enough distinct nonzero ambient points
because \(m\ge D\ge3\) implies \(2^m-1\ge D+4\).
Low-rank scopes were handled above.

## Empty atoms and the relation-subspace lattice

Let \(k=D+4\), \(R=\operatorname{rank}S>D\), and let
\[
 \mathcal R=\{u\in\mathbb F_2^S:\ \sum_{a\in S}u_a a=0\}
\]
be the binary relation code. Its dimension \(d=k-R\) is at most three.
Every nonzero relation has weight at least three, since the scope
points are distinct and nonzero.

Write \(g_D(r)=G(D-r)\), and define
\[
\begin{aligned}
 h_0(s)&=g_D(s),\\
 h_1(s)&=g_D(s-1)-g_D(s),\\
 h_2(s)&=g_D(s-2)-3g_D(s-1)+2g_D(s),\\
 h_3(s)&=g_D(s-3)-7g_D(s-2)+14g_D(s-1)-8g_D(s).
\end{aligned} \tag{5}
\]
For \(A\subseteq S\), put \(\mathcal R_A=\{u\in\mathcal R:
\operatorname{supp}u\subseteq A\}\). Rank-nullity and the subspace
counts in dimensions zero through three give the exact identity
\[
 g_D(\operatorname{rank}A)
   =\sum_{P\le\mathcal R_A}h_{\dim P}(|A|). \tag{6}
\]
Indeed the numbers of subspaces by dimension are
\((1)\), \((1,1)\), \((1,3,1)\), and \((1,7,7,1)\);
substitution into (5) telescopes to
\(g_D(|A|-\dim\mathcal R_A)\).
This is an identity for every subset, not a fitted coefficient model.

For a subspace \(P\le\mathcal R\), let \(w(P)\) be the size of the union
of supports of its words. Exchanging the two finite sums in the empty
atom's inclusion-exclusion yields
\[
 G(D)\mu_S(\varnothing)=
 \sum_{P\le\mathcal R}c_{\dim P}(w(P)),\qquad
 c_j(w)=\sum_{s=w}^{D+4}(-1)^s
             {D+4-w\choose s-w}h_j(s). \tag{7}
\]
Let \(A_w,B_w,C_w\) count the one-, two-, and three-dimensional
subspaces \(P\) with support size \(w\). The one-dimensional ones
correspond to individual nonzero words.
There are at most seven of each of the first two kinds and at most one
of the third:
\[
 \sum_w A_w\le7,\qquad \sum_w B_w\le7,\qquad \sum_w C_w\le1. \tag{8}
\]
Their minimum possible support sizes are respectively \(3,5,6\).
For a two-dimensional subspace, the sum of its three nonzero word
weights equals twice the support size and is at least nine. For a
three-dimensional subspace the corresponding sum equals four times
the support size and is at least 21. These prove the latter two bounds.
Also, weight parity is a linear functional on \(\mathcal R\).
There are either no odd-weight words or exactly \(2^{d-1}\le4\) of them.
In particular \(A_3\le4\) and \(A_3+A_5\le4\).

## Closed coefficient formulas

Define \(t_j=0\) for \(j<0\), and for \(j\ge0\) define
\[
 t_j=\sum_{s=0}^{j+4}(-1)^s{j+4\choose s}G(j-s).
\]
The coefficients in (7) are
\[
\begin{aligned}
 c_0(0)&=t_D,\\
 c_1(w)&=(-1)^w t_{D+1-w},\\
 c_2(w)&=(-1)^w(t_{D+2-w}-t_{D+1-w}),\\
 c_3(w)&=(-1)^{D+1}{D+4-w\choose3}.
\end{aligned} \tag{9}
\]
The last binomial is zero when its upper argument is less than three.

For the first two nontrivial formulas, write the shift of \(G(t)\) by
one as \(E\). Then \(h_1=(E-1)G\), and
\(h_2=(E-1)(E-2)G=(E-1)^2G-(E-1)G\).
Combining each \(E-1\) with the alternating binomial sum by Pascal's
identity produces exactly the shifted \(t\)'s in (9).
For \(h_3=(E-1)(E-2)(E-4)G\), the expression
\((4^t-3\cdot2^t+2)/6\) agrees with \(G(t)\) for all \(t\ge0\).
The three shifts annihilate it. At the truncated boundary, the only
nonzero value is \(h_3(s)=1\) at \(s=D+1\); hence its single contribution
is the last formula in (9).

For completeness, the closed expression for \(t_j\) is
\[
 t_j=\frac{81\cdot3^j-48+(-1)^j
                   (32j^3+120j^2+76j-33)}{1536}. \tag{10}
\]
One exact derivation uses ordinary generating functions:
\[
 \sum_{t\ge0}G(t)z^t=\frac{z^2}{(1-z)(1-2z)(1-4z)},\qquad
 \sum_{j\ge0}t_jz^j=\frac{z^2}{(1-z)(1-3z)(1+z)^4}.
\]
The second identity is the alternating binomial transform of the
sequence \(G(n-4)\), followed by removing the shift by four. Partial
fractions of the displayed rational function give (10).
In particular
\[
 (t_0,\ldots,t_7)=(0,0,1,0,7,8,46,104).
\]

## Dimensions four and five

The general coefficient identity specializes at \(D=4\) to
\[
 G(4)\mu_S(\varnothing)=7-A_3\ge3>0,
\]
using the odd-word bound above. At \(D=5\), it specializes to
\[
 G(5)\mu_S(\varnothing)=8+A_4-B_5+C_6\ge8-7=1>0.
\]
The latter inequality uses at most seven two-dimensional subspaces of
\(\mathcal R\), and drops the positive terms. Together with the explicit
\(D=3\) base and the nonempty-atom reduction, these prove the first two
induction steps. The previously proved level-eight and level-nine
optimality results are background, not dependencies of this positivity
proof.

## Dimension six: a short positive formula

For \(D=6\), (7)--(9) reduce to
\[
 651\mu_S(\varnothing)
   =46-7A_3-A_5+B_5+B_6-4C_6-C_7. \tag{11}
\]
For example the only relevant values of \(h_1(s)\) at \(s\ge3\) are
\((h_1(3),h_1(4),h_1(5))=(28,6,1)\), giving contributions
\(-28+7\cdot6-21=-7\), \(6-6=0\), and \(-1\) at support sizes
three, four, and five. For dimension two, the relevant values
\((h_2(5),h_2(6))=(4,1)\) give contributions one at each size.
For dimension three, \((h_3(6),h_3(7))=(0,1)\) gives \(-4,-1\).
The zero subspace contributes
\(651-10\cdot155+45\cdot35-120\cdot7+210=46\).

The parity bound gives \(A_3+A_5\le4\), while \(C_6+C_7\le1\).
All \(B\) terms are nonnegative, so
\[
 651\mu_S(\varnothing)\ge46-28-4=14>0. \tag{12}
\]
This bound need not be sharp. With the nonempty-atom reduction and
support lemma, it completes the dimension-six upper proof.
Its singleton is \(p_6=5/21\).

## Dimension seven

Here (9) gives
\[
\begin{split}
 G(7)\mu_S(\varnothing)={}&104-8A_3+7A_4+A_6\\
                         &-7B_5-B_6-B_7+10C_6+4C_7+C_8 .
\end{split}
\]
Again \(A_3\le4\), and there are at most seven two-dimensional relation
subspaces. Dropping positive terms proves
\[
 G(7)\mu_S(\varnothing)\ge104-32-49=23>0. \tag{13}
\]
This supplies the next induction step.

## All dimensions at least eight

Put \(\Delta_j=t_j-t_{j-1}\), with \(t_j=0\) for negative indices.
The sequence \(t_j\) is nonnegative and nondecreasing separately on
even and odd indices. The even-index \(\Delta_j\)'s are nondecreasing
from \(\Delta_2=1\); the odd-index ones are nondecreasing from
\(\Delta_3=-1\), with \(\Delta_1=0\), \(\Delta_5=1\).
Thus the only negative \(\Delta_j\) is \(\Delta_3\).

These assertions follow directly from (10):
\[
\begin{aligned}
 t_{j+2}-t_j
 &=\frac{648\cdot3^j+(-1)^j24(8j^2+36j+37)}{1536},\\
 \Delta_{j+2}-\Delta_j
 &=\frac{432\cdot3^j+(-1)^j48(8j^2+28j+23)}{1536}.
\end{aligned}
\]
Even indices have positive summands. At odd indices the needed
inequalities are \(27\cdot3^j\ge P(j)=8j^2+36j+37\) for \(j\ge1\),
and \(9\cdot3^j\ge Q(j)=8j^2+28j+23\) for \(j\ge3\).
The bases are \(81=P(1)\) and \(243>Q(3)=179\). Induction by two follows
from
\[
 9P(j)-P(j+2)=64(j+1)(j+3)>0,\qquad
 9Q(j)-Q(j+2)=32(2j^2+6j+3)>0.
\]
The remaining initial entries were listed above.

It follows from (9), for every admissible support size and \(D\ge8\),
that
\[
\begin{aligned}
 c_1(w)&\ge-t_{D-2},\\
 c_2(w)&\ge-\Delta_{D-3},\\
 c_3(w)&\ge-\boldsymbol1_{D\ {\rm even}}{D-2\choose3}.
\end{aligned}
\]
For \(c_1\), only odd \(w\) gives a negative sign, and its \(t\) index
has the same parity as \(D-2\) and is no larger.
For \(c_2\) with odd \(w\), its difference index is no larger than
\(D-3\) with the same parity. The exceptional initial
\(\Delta_1=0\) is no larger than \(\Delta_{D-3}\), since \(D-3\ge5\).
For even \(w\), a negative value can only be \(\Delta_3=-1\), and
\(\Delta_{D-3}\ge1\). The last bound is immediate from (9) and \(w\ge6\).

Using (8), the empty numerator is at least
\[
 B_D=t_D-7t_{D-2}-7(t_{D-3}-t_{D-4})
                  -\boldsymbol1_{D\ {\rm even}}{D-2\choose3}. \tag{14}
\]
Substituting (10) gives
\[
 B_D=
 \begin{cases}
 3^D/384-D^2/16-7D/32+213/128,&D\text{ even},\\
 3^D/384-D^3/6+25D^2/16-395D/96+347/128,&D\text{ odd}.
 \end{cases}
\]
Both parity subsequences are strictly positive. Their bases are
\(B_8=13\), \(B_9=22\), and direct subtraction gives
\[
\begin{aligned}
 B_{D+2}-9B_D&=(D-4)(D+7)/2 &&(D\text{ even}),\\
 B_{D+2}-9B_D&=(D-6)(D-1)(8D-25)/6 &&(D\text{ odd}).
\end{aligned}
\]
The increments are positive in the stated ranges. This proves empty-atom
nonnegativity for all \(D\ge8\). Together with the explicit \(D=3\) base,
the dimension-four and dimension-five formulas, (12), (13), and
conditional reduction, the induction proves the theorem.

## Exact failure at the next scope size

In \(\mathbb F_2^{D+1}\), take \(B\) to be \(D-3\) independent basis
vectors. In a complementary four-dimensional space take the eight
distinct nonzero vectors with binary labels \(1,2,\ldots,8\), and call
this set \(T\). Set \(S=B\cup T\). It has \(D+5\) points and rank \(D+1\).
The eight quotient points modulo \(\langle B\rangle\) are distinct
and nonzero, and any two are independent.

The moment numerator of \(B\) is \(G(3)=7\).
Adding one point of \(T\) gives rank \(D-2\) and numerator \(G(2)=1\).
Adding two or more points gives rank at least \(D-1\) and numerator zero.
Therefore the atom whose ones are exactly \(B\) has
\[
 G(D)\mu_S(B)=7-8=-1.
\]
For \(D=3\), the anchor \(B\) is empty and the eight-point scope
\(S=\{1,\ldots,8\}\subseteq\mathbb F_2^4\) has empty-atom mass \(-1/7\).
For \(D=6\) an explicit eleven-point example is
\[
 S=(1,2,4,8,16,24,32,40,48,56,64),\qquad B=(1,2,4),
\]
with mass \(-1/651\). It embeds into every \(m\ge D+1\).
This proves the sharp locality boundary for these moments; it is not
an impossibility statement about other local witnesses or algorithms.

## Cost and outstanding scope

For a supplied explicit scope of size \(k\le D+4\), direct construction
uses \(2^k\) binary rank computations and a \(k\)-stage subset Möbius
transform. Denominator \(G(D)\) has \(O(D)\) bits; all subset sums also
have polynomial bit length in \(D+k\). This is a bounded explicit-scope
construction. It is not polynomial in the parameter \(D\) by this
implementation, and producing every local table costs combinatorially
many scopes in the code length.

The theorem supplies feasible objectives (2), generalizes the two proved
rank-moment witnesses, and shows where this family first fails.
It does not determine \(\min L_k\) for \(k\ge10\), certify a general
decoding algorithm, or imply a SAT complexity separation.
The [complete D6 classification](level10_scope_exploration/THEOREM.md)
independently checks every high-rank ten-point type, using a separate
histogram enumerator, direct coordinate elimination, and a zeta-transform
replay. All 121 types pass 123,904 atom/moment comparisons. Its negative
controls retain the D5 ten-point and D6 eleven-point failures.

The [executable construction](rm2_virtual_dimension.py) and
[nine arithmetic tests](test_rm2_virtual_dimension.py) check the coefficient
formulas, induction identities, actual subspace distributions, input guards,
and next-level negative atoms. They are finite controls; the written induction
above proves the all-size statement. The separate eight-test classification
suite checks full coverage, all 1,210 delete-one marginals, and rejection of
corrupted or missing evidence. Both suites pass normally and under `python -O`.

From `local_marginal_code_lab`, reproduce without an optimizer:

```text
python -m unittest -v test_rm2_virtual_dimension
python -O -m unittest -v test_rm2_virtual_dimension
python level10_scope_exploration/verify.py
python -m unittest discover -s level10_scope_exploration -p test_exploration.py -v
```

The [novelty ledger](LOCAL_MARGINAL_NOVELTY_LEDGER.md) also identifies the
exact correspondence with previously defined locally explainable
non-signaling code functions. The model and counting machinery are inherited;
this proof's priority has not been established.
