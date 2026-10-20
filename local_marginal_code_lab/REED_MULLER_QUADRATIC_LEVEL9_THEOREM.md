# Quadratic Reed–Muller codes at level nine

Status: accepted written proof after independent mathematical audit and bounded
exact controls, including the corrected six-point incidence count below.
This is not proof-assistant verification. Novelty is **UNKNOWN**.
The derivation and finite exact identity below are not a result about P versus NP.

## Statement and conventions

Let \(m\ge5\), \(V=\mathbb F_2^m\), and \(C=RM(2,m)\). Pin coordinate \(0\)
to one. Define \(L_9\) to have normalized nonnegative tables on every
coordinate scope of **total size at most nine**, each supported on the
projection of \(C_1=\{c\in C:c_0=1\}\), and consistent on every overlap.
Set \(p_a=\Pr[x_a=1]\), reduced weight \(F=\sum_{a\ne0}p_a\), and total
weight \(W=1+F\).

**Theorem.**
\[
 \min_{L_9}F={7(2^m-1)\over31},\qquad
 \min_{L_9}W={7\cdot2^m+24\over31}.
\]
The upper construction in fact gives tables on any nine **nonpin**
coordinates jointly with the pin. This includes some scopes of total
size ten, but does not assert a solution for full \(L_{10}\).
The pinned integer optimum is \(2^{m-2}\). At \(m=5\) the displayed total
value is eight, closing the gap; at \(m=6\) it is \(472/31<16\).
The total integer/relaxation ratio tends to \(31/28\).

The proof uses the standard RM duality, minimum-distance, and minimum
dual-support facts stated in Section II and II-A of Santi, Häger and
Pfister, *Decoding Reed–Muller Codes Using Minimum-Weight Parity Checks*
(ISIT 2018):
[primary author manuscript](https://research.chalmers.se/publication/507229/file/507229_Fulltext.pdf),
[published DOI](https://doi.org/10.1109/ISIT.2018.8437637).
In particular, the dual of \(RM(2,m)\) has minimum weight eight, whose
supports are affine three-flats. Every dual word has even weight because
the constant-one word is in the primal code.

We also use the proved eight-point zero-sum-triple lemma and associated
nonnegative moment tables from
`REED_MULLER_QUADRATIC_LEVEL8_THEOREM.md`. These are explicit dependencies.

## Why the first level-nine row is insufficient

After averaging a feasible solution over \(GL(m,2)\), let \(p,q,r\) denote
its common singleton, pair, and linearly independent triple moments.
For nine points in an affine hyperplane excluding zero, their weight \(T\)
satisfies the integer-valid inequality
\[
 {T(T-2)(T-3)\over2}=T-2\binom T2+3\binom T3\ge0.
\]
Taking expectation yields \(p-8q+28r\ge0\).
In the saved selected affine-flat quotient, its row is
\[
 z_{27}-8z_{24}+28z_{18}+28z_{19}\ge0.
\]
The mappings are \(p=z_{27}\), \(q=z_{24}\),
\(r=z_{18}+z_{19}\), the latter being the all-one moment of three points
of the affine plane \(\{1,2,4,7\}\).

The selected model after adding only this row still admits \(p=37/184\):
take the mixture \(735/736\) of the old selected level-eight
witness and \(1/736\) of the constant-one codeword. This is not a full
level-nine witness. Equality in the row forces \(T\in\{0,2,3\}\), whereas
the mixture gives a contained affine plane of four points positive
all-one probability \(1/736\). The following argument enforces an actual
nine-point distribution rather than stopping at that single consequence.
This observation requires only the explicit mixture and its moments,
not an optimizer's claim of selected-model optimality.

## A small complete nine-scope extension and its lower bound

Average any feasible \(L_9\) solution over \(GL(m,2)\). This preserves
feasibility, the pin, and the objective. All following moments and
per-atom masses are therefore invariant under the indicated linear maps.

Choose an affine three-flat \(H\) not containing zero and a point
\(u\notin\operatorname{span}(H)\). This is possible for \(m\ge5\).
The nine-point scope \(S=H\cup\{u\}\) has a table, and the restriction to
\(H\) has even parity. The affine automorphism group of \(H\), extended
to fix \(u\) and zero, splits its even subsets into the following types:

| type | empty | pair | four-point affine plane | other four-set | six-set | full |
|---|---:|---:|---:|---:|---:|---:|
| number of subsets | 1 | 28 | 14 | 56 | 28 | 1 |
| per-atom marginal mass on \(H\) | \(z_5\) | \(z_6\) | \(z_7\) | \(z_8\) | \(z_9\) | \(z_{10}\) |
| per-atom mass jointly with \(x_u=1\) | \(b_0\) | \(b_2\) | \(b_P\) | \(b_N\) | \(b_6\) | \(b_8\) |

Thus \(0\le b_i\le z_i\) in the column-wise correspondence in the table.
Let \(v\) be the common moment of four linearly independent nonzero points.
Counting incidences of one, two, or three specified points of \(H\) gives
\[
\begin{aligned}
 q&=7b_2+7b_P+28b_N+21b_6+b_8,\\
 r&=b_2+3b_P+12b_N+15b_6+b_8,\\
 v&=b_P+4b_N+10b_6+b_8.
\end{aligned} \tag{1}
\]
For example the second equation is the moment of \(u\) and two points of
\(H\); they are linearly independent. The third uses \(u\) and three points
of \(H\), which are linearly independent as well. Full scope consistency
also gives
\[
 p=b_0+28b_2+14b_P+56b_N+28b_6+b_8
\]
and
\[
 3z_9+z_{10}=b_P+6b_6+b_8. \tag{2}
\]
The last equality concerns \(u\) together with a four-point affine plane
in \(H\). Its five points lie in a selected affine three-flat. Neither
the preceding \(p\) identity nor (2) is needed in the compact lower identity, but both are
included in the finite extension model.

For clarity, the only other per-atom mass in the identity is \(z_2\):
on a linear three-flat containing the pin, it is the mass of an assignment
whose nonpin ones are three linearly independent points. In the historical
quotient it is the atom 23 on the ordered scope \([0,1,2,3,4,5,6,7]\).
Here \(z_8\) is a four-set in an unpinned affine three-flat that is not an
affine plane, and \(z_{10}\) is the all-one atom of that flat.

The following exact identity holds:
\[
\begin{split}
279p-63={}&672z_2+1904b_P+8568b_N+4928b_6+216b_8\\
         &+952(z_8-b_N)+328(z_{10}-b_8).
\end{split} \tag{3}
\]
Every term on the right is nonnegative, proving \(p\ge7/31\) and hence the
claimed all-family lower bound.

### Derivation by local counts, without an optimizer

Write \(c\) for the common all-one moment of a four-point affine plane
excluding zero and \(a=z_{10}\). On a pinned linear three-flat the nonpin
ones have odd size. Its five atom types have respective multiplicities
\(7,7,28,21,1\): singleton, zero-sum triple, independent triple, five-set,
and full seven-set. If their per-atom masses are \(z_0,\ldots,z_4\), direct
normalization and incidence counting give
\[
\begin{aligned}
1&=7z_0+7z_1+28z_2+21z_3+z_4,\\
p&=z_0+3z_1+12z_2+15z_3+z_4,\\
q&=z_1+4z_2+10z_3+z_4,\\
r&=z_2+6z_3+z_4,\qquad c=3z_3+z_4.
\end{aligned}
\]
Eliminating \(z_0,z_1,z_3,z_4\) yields
\[
 z_2=r-\tfrac14c-\tfrac{21}{16}q+\tfrac{21}{32}p-\tfrac3{32}.
\]
On an unpinned affine three-flat the six types in the table above give
\[
\begin{aligned}
p&=7z_6+7z_7+28z_8+21z_9+a,\\
q&=z_6+3z_7+12z_8+15z_9+a,\\
r&=z_7+4z_8+10z_9+a,\\
c&=z_7+6z_9+a,\qquad v=z_8+6z_9+a.
\end{aligned}
\]
Consequently
\[
 z_8=\tfrac17a-\tfrac14c+\tfrac18q-\tfrac1{56}p,\qquad
 v=\tfrac27a+\tfrac32r-\tfrac14c-\tfrac58q+\tfrac5{56}p.
\]
Substituting these three identities verifies
\[
279p-63=672z_2+952z_8+328a-252q+1764r-1624v.
\]
Now substitute (1), then separate the nonnegative differences
\(z_8-b_N\) and \(a-b_8\), obtaining (3).

This argument uses only actual scope tables of size at most nine and
symmetry. In particular, it directly proves the all-\(m\) lower bound.
Equivalently the finite selected model plus this nine-scope orbit
transports by embeddings of spans of dimension at most five; it does not
require the full level-nine quotient to stabilize with \(m\).

### Explicit machine-checkable row combination

The compact finite model has 40 nonnegative columns: the historical
28 \(z\) columns, six \(b\) columns in the table order, and six slacks
\(s_i=z_{5+i}-b_i\). Its first 53 rows are the historical selected-model
rows. Rows 53–58 are \(b_i+s_i-z_{5+i}=0\); rows 59–63 are the five
mixed-moment equalities in the order \(p,q,r,v,3z_9+z_{10}\), written
as the expression in \(b\) minus the expression in \(z\).

In this zero-based row ordering, all unlisted \(\lambda_j\) are zero:

```text
{1:1296, 3:-1764, 5:252, 7:279,
 12:-468, 13:-2034, 14:-2160, 15:-762,
 17:-1296, 18:-5022, 19:-8424, 20:-4530,
 24:252, 25:504, 31:279,
 56:-952, 58:-328, 60:252, 61:-1764, 62:1624}
```

They satisfy, for the explicitly specified matrix \(A\) and right side \(b\),
\[
\begin{aligned}
A^\mathsf T\lambda={}&279e_{27}-672e_2-1904e_{30}-8568e_{31}
 -4928e_{32}-216e_{33}-952e_{37}-328e_{39},\\
b^\mathsf T\lambda={}&63.
\end{aligned}
\]
Here \(b\) in \(Ax=b\) is the equality right side, not the six split masses.
The direct counting derivation above grounds the rows; a saved matrix
or matching hash alone is not their mathematical justification.

## Upper construction: moments of a virtual three-subspace

For every finite nonpin set \(A\) of size at most nine, prescribe
\[
 155M_A=
 \begin{cases}
 155,&\operatorname{rank}(A)=0,\\
 35,&\operatorname{rank}(A)=1,\\
 7,&\operatorname{rank}(A)=2,\\
 1,&\operatorname{rank}(A)=3,\\
 0,&\operatorname{rank}(A)\ge4.
 \end{cases} \tag{4}
\]
Rank is binary linear rank, not the size of the set. Define the exact atom
table on \(S\) by Möbius inversion:
\[
 \mu_S(B)=\sum_{A:B\subseteq A\subseteq S}
                    (-1)^{|A\setminus B|}M_A. \tag{5}
\]
The common moments immediately imply normalization and consistency on
every overlap. We prove nonnegativity and exact pinned projection support.

If \(\operatorname{rank}(S)\le5\), embed its span into \(\mathbb F_2^5\).
There are 155 linear three-subspaces there; the numbers containing a
specified subspace of ranks \(0,1,2,3\) are \(155,35,7,1\), respectively.
Thus (4)–(5) are the restriction of their uniform distribution of indicators.
Each indicator is a quadratic polynomial with value one at zero, since
the subspace has codimension two. Extending the embedding linearly to the
ambient \(V\) and composing this polynomial gives an actual word of \(C_1\).
This proves both nonnegativity and support in this case.

For higher rank it suffices to treat \(|S|=9\): any smaller high-rank scope
extends to nine distinct nonzero points, and its table is a marginal by
(4)–(5). Such an extension is available whenever \(m\ge5\); the high-rank
case itself requires \(m\ge6\). Write \(R=\operatorname{rank}(S)\ge6\).
Its relation space
\[
 D=\{w\in\mathbb F_2^S:\sum_{a\in S}w_a a=0\}
\]
has dimension \(9-R\le3\).

### Nonempty atoms

A subset \(B\subseteq S\) is **closed in \(S\)** if
\(B=S\cap\operatorname{span}(B)\). A nonclosed atom has mass zero:
choose \(a\in(S\cap\operatorname{span}(B))\setminus B\) and pair the terms
of (5) according to whether they contain \(a\); their ranks agree.
Atoms of rank at least four have mass zero by (4).

For a closed atom of rank three the numerator \(155\mu_S(B)\) is one.
For a closed rank-two atom, let \(d_B\) be the number of distinct occupied
nonzero cosets of \(\operatorname{span}(B)\) represented by \(S\setminus B\).
Each coset corresponds to exactly one closed rank-three extension of \(B\).
Since the moment of \(B\) is \(7/155\) and each such extension has mass
\(1/155\),
\[
 155\mu_S(B)=7-d_B\ge0.
\]
Indeed \(d_B\le9-|B|\le7\), because a rank-two set has at least two points.

For a rank-one atom \(B=\{a\}\), pass to the quotient by \(\langle a\rangle\).
The remaining points occupy a set \(T\) of at most eight distinct nonzero
quotient points. Repeated cosets are identified, not counted separately.
The formal moments conditional on \(x_a=1\) are
\[
 1,\quad 7/35=1/5,\quad1/35,\quad0,\ldots
\]
according to quotient ranks zero, one, two, and at least three. These are
exactly the common moments in the level-eight construction. Inclusion–
exclusion groups repeated quotient cosets, so
\[
 155\mu_S(\{a\})
 =35-7|T|+\binom{|T|}{2}-t(T)\ge0,
\]
where \(t(T)\) is its number of zero-sum triples. The final inequality is
the independently proved level-eight lemma; no new dimension restriction
is imposed on the quotient.

### Empty atom: incidence identity and relation-space bound

Let \(t\) count the zero-sum triples of \(S\), and let \(Q_4\) count its
zero-sum four-element subsets. Let \(\mathcal F_3\) be its closed rank-three
subsets, and let \(N_s\) count the members of \(\mathcal F_3\) of size \(s\).
Every such subset lies in the seven nonzero points of a binary
three-dimensional space, so \(3\le s\le7\).

Möbius recurrence on the lattice of closed sets gives
\[
 155\mu_S(\varnothing)=155-35k+7W_2-W_3,\qquad k=|S|,
\]
where
\[
 W_2=\binom{k}{2}-t,\qquad
 W_3=\sum_{F\in\mathcal F_3}
       \left(1-|F|+\binom{|F|}{2}-t(F)\right).
\]
These coefficients follow directly from the recurrence: a point has
Möbius value \(-1\), a rank-two flat has value \(|F|-1\), and a rank-three
flat has the negative of one minus its point count plus the rank-two
values below it.
Each independent triple belongs to exactly one rank-three closure, so
\[
 W_3=\binom{k}{3}-t-L,\qquad
 L=\sum_{F\in\mathcal F_3}\binom{|F|-1}{3}.
\]
In particular, for \(k=9\), the empty numerator is \(8-6t+L\).

The following table lists all possibilities inside a rank-three flat.
The two size-four rows distinguish a line plus a point from a quadrangle.

| \(s\) | \(t(F)\) | \(Q_4(F)\) | \(\binom{s-1}{3}\) | \(t(F)(s-3)+Q_4(F)-\binom{s-1}{3}\) |
|---:|---:|---:|---:|---:|
| 3 | 0 | 0 | 0 | 0 |
| 4 | 1 | 0 | 1 | 0 |
| 4 | 0 | 1 | 1 | 0 |
| 5 | 2 | 1 | 4 | 1 |
| 6 | 4 | 3 | 10 | 5 |
| 7 | 7 | 7 | 20 | 15 |

For example, a six-point subset of the Fano configuration has four lines
and **three**, not four, zero-sum quadruples: the complementary lines of
its quadruples are exactly the three lines through the omitted point.
This count was corrected during the independent review before finalization.

Counting pairs of a zero-sum triple and an outside point gives
\(\sum_F t(F)(|F|-3)=t(k-3)\). Each zero-sum quadruple has rank three and
belongs to a unique \(F\), so \(\sum_F Q_4(F)=Q_4\). Summing the table gives
\[
 L=t(k-3)+Q_4-N_5-5N_6-15N_7.
\]
Therefore
\[
 155\mu_S(\varnothing)=8+Q_4-N_5-5N_6-15N_7
 \quad(k=9). \tag{6}
\]

The nullity bound \(\dim D\le3\) implies \(N_7=0\): seven points of rank
three would already supply four independent relations.

If a six-point rank-three flat \(F\) exists, its three-dimensional
relation space equals all of \(D\). Consequently every relation is
supported inside \(F\), and the three remaining columns are independent
over its span. There is exactly one such six-flat. A rank-three flat with
one outside column has inside rank at most two, hence at most three
inside points and four points in total. With two or three outside columns
the inside rank drops to at most one or zero, giving at most three total
points. A rank-three flat wholly inside \(F\) closes to all of \(F\).
Thus \(N_6=1\) and \(N_5=0\).
All zero-sum quadruples are inside \(F\), so \(Q_4=3\); (6) equals six.

If there is no six-flat, each five-point rank-three flat supplies a
two-dimensional subspace of \(D\). Its three nonzero relations have
weights three, three, and four, with union of supports equal to those
five points. Distinct five-flats therefore supply distinct two-dimensional
subspaces of \(D\). A space of dimension at most three has at most seven
such subspaces. Thus \(N_5\le7\), and (6) is at least \(8-7=1\).

This proves the last nonnegativity case in all dimensions. The argument
uses a fixed Fano incidence table and a dimension-three relation-space
bound, not an inference from a bounded computational sample.

### Exact projected-code support in the high-rank case

Set \(Q=S\cup\{0\}\), so \(|Q|\le10\). The annihilator of the projection
of \(C\) onto \(Q\) is the set of dual words supported in \(Q\). Any nonzero
one has even weight at least eight, so its weight is eight or ten.

An eight-check is an affine three-flat \(H\). If \(0\in H\), its seven
nonzero points lie in \(S\), and at most two further points give
\(\operatorname{rank}(S)\le3+2=5\). If \(0\notin H\), its linear span has
dimension four, it is wholly in \(S\), and at most one further point gives
\(\operatorname{rank}(S)\le4+1=5\). Both contradict the high-rank assumption.

A weight-ten check would have support exactly \(Q\). Evaluate the constant
and the coordinate linear functions on these ten points. Their rows are
mutually orthogonal over \(\mathbb F_2\), since all products have degree
at most two and the supposed check is dual to \(RM(2,m)\). Their rowspace
has dimension \(R+1\): the linear evaluation rank is \(R\), and the constant
row is independent because the zero coordinate is present. A self-orthogonal
subspace of the nondegenerate space \(\mathbb F_2^{10}\) has dimension
at most five. This contradicts \(R\ge6\).

Thus there is no nonzero supported dual word, and the projection onto
\(Q\) is full. Every table atom with pin one is admissible. Together with
the genuine-code construction for rank at most five, this proves exact
support for all the tables in (5).

## Consequences, cost, and limits

The tables have nonpin singleton value \(35/155=7/31\), attaining the lower
bound. The same singleton vector also lies in every redundant-check parity
polytope: a check excluding the pin mixes all-zero and all-one words; a
check containing it mixes uniform one-hot and all-one assignments on the
remaining odd number of positions. Its marginal \(7/31\) lies between
\(1/(w-1)\) and one for every check size \(w\ge8\). This is only singleton
parity-polytope membership, not agreement of whole check distributions
with every higher marginal.

For a supplied scope of at most nine explicit \(m\)-bit coordinates,
(4)–(5) use at most 512 subset ranks and a nine-stage Boolean Möbius
transform, all with integer numerators over 155. This is polynomial in
the explicit scope representation. Enumerating all scopes has
\(O((2^m)^9)\) size; it is not polynomial in \(m\), and this witness is
not a general decoder or SAT algorithm.

The finite 40-variable extension is a source-bound lower-bound certificate.
Its optimality alone would not establish full \(L_9\) exactness. The matching
upper proof and the precise pin convention are essential. Likewise, the
first one-row extension's smaller feasible value must not be reported as full
level-nine exactness. No full-\(L_{10}\) optimum, hierarchy-wide limit,
novelty, or general complexity separation is claimed.

## Reproduction and independently checked evidence

The [nine-scope discovery report](RM2_NINE_SCOPE_DISCOVERY.md) records the
fresh exact search, source construction, independent reconstruction, and
primal/dual replay for the expanded 284-variable, 416-row model. That model
uses individual nine-point atoms instead of the six invariant split masses
above. It agrees on the reduced optimum seven and total optimum eight at
\(m=5\). The compact identity (3) is also reconstructed from original atom
incidences and checked by
[the model/certificate tests](test_rm2_nine_scope.py), whose 12 tests passed.
Thus the explicit row multipliers are tested against rebuilt geometry,
not merely a hand-entered matrix with the intended answer.

The separate [upper-bound reviewer](review_rm2_level9_family.py) constructs
tables from the rank moments, independently checks moments and quadratic
projection support, compares low-rank cases with all 155 actual
three-subspaces in five dimensions, and checks the corrected incidence
identity. Its reproducible bounded campaign has 168 scopes; it does not
enumerate every nine-point type. Its
[eight tests](test_rm2_level9_family.py) passed, including malformed-table,
moment, parity, and incidence controls. These finite checks supplement the
all-size proof; they do not replace it.

From this directory:

```text
python run_rm2_nine_scope.py --replay RM2_NINE_SCOPE_DISCOVERY
python review_rm2_level9_family.py
python -m unittest -v test_rm2_nine_scope test_rm2_level9_family
python -O -m unittest -v test_rm2_nine_scope test_rm2_level9_family
```

The discovery report records machine and source provenance and distinguishes
the retained one-row preliminary experiment from the full nine-scope model.
