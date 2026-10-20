# Exact level-eight marginal optimum for quadratic Reed–Muller codes

Status: an elementary proof and reproducible finite checks, with an independent
mathematical review recorded in `TRUST_CHAIN.md`. This is not proof-assistant
verification. Novelty is **UNKNOWN**: this note does not establish that the
result is absent from the literature. The finite enumeration supplements the
proof; it is not the all-size proof.

## Model and statement

Let \(m\geq4\), \(V=\mathbb F_2^m\), and let \(C=RM(2,m)\) be the binary
evaluation code of polynomials of degree at most two. Pin coordinate \(0\)
to one. In \(L_8\), every coordinate set \(Q\subseteq V\) of **total size**
at most eight has a normalized, nonnegative probability table supported
on the projection of \(\{c\in C:c_0=1\}\). These tables agree on all common
marginals. Write \(x_a\) for the singleton probability of one and
\(F=\sum_{a\ne0}x_a\) for the reduced objective; total weight is \(W=1+F\).

**Theorem.** The exact optima are
\[
 \min_{L_8} F={2^m-1\over5},\qquad
 \min_{L_8} W={2^m+4\over5}.
\]
The same values hold if every redundant dual-check parity polytope is
additionally imposed on the singleton vector. They also hold in the stronger
conditioned model supplying joint tables on the pin and **up to eight other
coordinates**. This last statement does not assert feasibility on every
nine-coordinate scope: nine nonpin coordinates are outside its scope.

The pinned integer optimum is \(2^{m-2}\). It is attained by the indicator
of any codimension-two linear subspace, a quadratic polynomial taking value
one at zero. Thus the total integer/relaxation ratio is
\[
 {5\cdot2^{m-2}\over2^m+4}\longrightarrow{5\over4}.
\]
For \(m=4,5,6\), the total relaxation values are respectively \(4,36/5,68/5\);
the first case has no integrality gap.

We use the standard facts that \(RM(r,m)^\perp=RM(m-r-1,m)\), that its minimum
weight is \(2^{m-r}\), and that the minimum-weight dual checks of \(RM(r,m)\)
are the indicators of affine \((r+1)\)-flats. These are stated in Section II
and II-A of Santi, Häger and Pfister, *Decoding Reed–Muller Codes Using
Minimum-Weight Parity Checks* (ISIT 2018),
[author manuscript](https://research.chalmers.se/publication/507229/file/507229_Fulltext.pdf),
[published DOI](https://doi.org/10.1109/ISIT.2018.8437637).
No novelty is claimed for those coding facts.

## A common moment assignment

For every nonpin set \(A\) of size at most eight prescribe
\[
 M_\varnothing=1,\quad M_{\{a\}}={1\over5},\quad
 M_{\{a,b\}}={1\over35},\quad
 M_{\{a,b,c\}}={\mathbf1[a+b+c=0]\over35},
 \quad M_A=0\ (|A|\ge4).
\]
Here the elements in each displayed set are distinct and nonzero. For a
scope \(S\) of \(k\le8\) nonpin points, let \(t\) be the number of zero-sum
triples in \(S\), and \(d_a\) the number of those triples containing \(a\).
Boolean Möbius inversion gives the probability that the ones are exactly
the subset \(A\subseteq S\):
\[
\begin{array}{c|c}
A&35\mu_S(A)\\ \hline
\varnothing&35-7k+\binom{k}{2}-t\\
\{a\}&8-k+d_a\\
\{a,b\}&1-\mathbf1[a+b\in S]\\
\{a,b,c\},\ a+b+c=0&1\\
\text{all other }A&0.
\end{array}
\]
Indeed \(\mu_S(A)=\sum_{B:A\subseteq B\subseteq S}
(-1)^{|B\setminus A|}M_B\). Conversely
\(\sum_{A\supseteq B}\mu_S(A)=M_B\). This proves normalization and agreement
on **every** overlap directly from the common moments, once nonnegativity
is established. Adjoin the pin deterministically at value one.

Singleton, pair, and triple masses are visibly nonnegative. For \(k\le6\),
each unordered pair belongs to at most one zero-sum triple, so
\(t\le\binom{k}{2}/3\). The empty numerator is therefore at least
\(35-7k+(2/3)\binom{k}{2}>0\) for these seven values of \(k\).
For \(k=7\), every point has degree at most three, giving \(t\le7\) and
empty numerator \(7-t\ge0\). The \(k=8\) numerator is also \(7-t\).

**Eight-point lemma.** Eight distinct nonzero vectors in any binary vector
space contain at most seven zero-sum triples.

Every point has degree at most three, since its seven possible partners
are paired by addition of that point. If every degree is at most two,
\(3t\le16\), so \(t\le5\). Otherwise choose a point \(a\) of degree three.
The set is
\[
 \{a,u,b,b+a,c,c+a,d,d+a\}.
\]
In the quotient by \(\langle a\rangle\), the three doubled cosets
\(B,C,D\) are distinct nonzero cosets; the singleton coset \(U\) is distinct
from zero and all three. There are three lines through \(a\).
All remaining triples must use three distinct nonzero cosets.
If \(B+C+D=0\), the three doubled cosets contribute exactly four triples.
No triple uses \(u\), because each doubled-coset pair sum is the third
doubled coset. If \(B+C+D\ne0\), the doubled cosets contribute no triple.
The three pair sums \(B+C,B+D,C+D\) are distinct, so \(U\) equals at most
one of them, contributing at most two triples. Thus \(t\le7\) in both cases.
This proves nonnegativity in all dimensions without enumeration.

## Exact projected-code support

Let \(Q=S\cup\{0\}\), so \(|Q|\le9\). Linear projection onto \(Q\) is
characterized by the dual codewords supported in \(Q\): its annihilator
is precisely that shortened dual space. This follows either by extending
a linear functional on the projected space or from the elementary
rowspace/nullspace orthogonality identity.

Every nonzero dual word has weight at least eight. Every dual word has
even weight because the constant-one word belongs to \(C\). Consequently
a nonzero dual word supported in \(Q\) must have weight eight. There is
at most one: two distinct eight-element supports in a set of size at most
nine intersect in at least seven elements, so their nonzero sum would
have weight at most two, a contradiction. A weight-eight support is an
affine three-flat \(H\).

If no such check exists, the projection onto \(Q\) is full and every
assignment with pin one is admissible. If a check exists, it suffices to
check its even parity.

* If \(0\notin H\), then \(H\subseteq S\), whence \(S=H\) and \(k=8\).
  An affine flat not containing zero has no zero-sum triple, and the sum
  of two distinct members is outside the flat. The table has only empty
  and pair atoms, all even on \(H\).
* If \(0\in H\), put \(H^*=H\setminus\{0\}\). These seven points have seven
  zero-sum triples, and each point lies on three. For \(S=H^*\), the only
  positive atoms have size one or three. If \(S=H^*\cup\{u\}\), then
  \(u\notin H\), there is no triple involving \(u\), and the only positive
  atoms are singletons in \(H^*\), pairs \(\{u,a\}\) with \(a\in H^*\), and
  zero-sum triples in \(H^*\). In either case their restriction to \(H^*\)
  is odd, so adjoining pin one makes the parity on \(H\) even.

The constructed tables are therefore supported on the **exact** pinned
code projections, including when \(m=4\). They prove the upper bound
\(F=(2^m-1)/5\).

## Lower bound transported from a finite exact identity

The existing finite selected-scope model in \(V_5=\mathbb F_2^5\) uses all
affine three-flats, affine two-flats, lines, and singletons, with their
overlap constraints and pin zero equal to one. Its exact independently
reconstructed symmetry quotient has 28 variables and 53 equations.
In the orbit ordering of
`REED_MULLER_LEVEL_D_AFFINE_OVERLAP_RESULTS.json`, its dual identity is
\[
 F_5-\frac{31}{5}
 =\frac{434}{5}z_2+\frac{682}{5}z_3+\frac{124}{5}z_4
  +\frac{496}{5}z_7+\frac{1736}{5}z_8+248z_9\ge0.
\]
The six \(z_i\) are nonnegative quotient atom masses. The identity is
explained in `REED_MULLER_AFFINE_OVERLAP_DUAL_NOTE.md`. The new review script
reconstructs the selected model using its existing independent checker,
then rechecks \(c-A^\mathsf Ty\) and \(b^\mathsf Ty=31/5\) with rational
arithmetic. The finite certificate, orbit convention, and reconstruction
are explicit dependencies of this lower-bound proof; they are not
replaced by an assertion about a numerical optimizer.

Now take any feasible \(L_8\) solution in \(V\) and average it over
\(GL(m,2)\). The code, pin, constraints, and objective are invariant, so
the average is feasible, has the same objective, and has a common nonpin
singleton value \(p\). Every selected scope \(S\) in \(V_5\) has affine
dimension at most three, hence its **linear span** has dimension at most
four. For each such \(S\), embed its linear span injectively into \(V\)
and pull back the averaged local table. This is possible for every \(m\ge4\).

The resulting table does not depend on the embedding: two linear
embeddings of the same span extend to ambient linear automorphisms of
\(V\), and the averaged tables are invariant under those automorphisms.
For a containment \(T\subseteq S\), use the restriction of the embedding
for \(S\), proving consistency. For arbitrary intersections, first
marginalize inside the parent span and use the same invariance argument.
The affine-flat projection constraints are preserved: on a three-flat
the only possible check is its even parity, and smaller flat projections
have no check, apart from the fixed pin when present.
Thus these tables are feasible for the finite selected-scope model in
\(V_5\). Its nonpin objective is \(31p\); the exact identity yields
\(31p\ge31/5\). Hence \(p\ge1/5\) and
\(F=(2^m-1)p\ge(2^m-1)/5\).

This argument transports a selected-scope inequality. It does **not**
assume that the full \(L_8\) symmetry quotient stabilizes with dimension.

## Adding every redundant parity check

The singleton vector of the witness is \(x_0=1,\ x_a=1/5\) otherwise.
A dual check has even size \(w\ge8\).
If it excludes zero, mixing its all-zero and all-one words realizes this
singleton vector. If it includes zero, the remaining \(w-1\) positions
must have odd parity. The uniform one-hot distribution has each marginal
\(1/(w-1)\), and their all-one word has each marginal one. Mixing them
realizes \(1/5\), because \(1/(w-1)\le1/7<1/5\).
These are witnesses for singleton parity-polytope membership, not a
claim that full check tables share every higher marginal with \(\mu\).
Since the lower bound already holds for \(L_8\), the optimum is unchanged.

## Reproducibility and exact costs

`review_rm2_level8_family.py` enumerates all RREF rowspaces in
\(\mathbb F_2^8\). A rank-\(r\) RREF matrix gives eight labelled columns in
\(\mathbb F_2^r\); deleting configurations with zero or repeated columns
enumerates every ordered eight-point nonzero configuration up to
invertible ambient linear coordinates. There are 417,199 rowspaces and
50,864 retained configurations. Their rank histogram is
`{4:12870, 5:31005, 6:6769, 7:219, 8:1}`.
The script checks nonnegative masses, normalization, singleton and pair
moments, the triple bound, and every positive atom against an independent
GF(2) span of constant, linear, and quadratic evaluation rows on the pin
and the eight points. It does not use the dual-flat classification for
that support test. Every smaller scope extends to an eight-point scope
when \(m\ge4\), and restrictions of quadratics to a linear span are all
quadratics on that span, explaining the finite classification's scope.

For one explicitly listed scope of at most eight points, construction
uses at most \(\binom83=56\) XOR triple checks and at most 256 atom slots.
Coordinates have \(m\) bits, so these operations are polynomial in the
explicit scope representation. Enumerating all scope tables takes
\(O((2^m)^8)\) scopes: this is not polynomial in \(m\), nor a general
decoding algorithm. All probabilities use denominator 35; objective
numerators have \(O(m)\) bits. The finite lower-certificate reconstruction
has fixed size independent of \(m\). Runtime, interpreter/platform, exact
check counts, and source/dependency hashes are saved in
`RM2_LEVEL8_FAMILY_REVIEW.json`. Hashes normalize CRLF to LF for Git checkout
portability, and the new result is written with LF line endings. Historical
dependencies are only read, never rewritten by this runner.

Run from this directory:

```text
python -m unittest -v test_rm2_level8_family.py
python review_rm2_level8_family.py
```

## A falsifiable next-level experiment

For \(m\ge5\), choose nine points in an affine hyperplane excluding zero,
for example points 16 through 24 in \(\mathbb F_2^5\). Such a scope has no
zero-sum triple. For every integer \(t\ge0\),
\[
 \frac{t(t-2)(t-3)}2=t-2\binom t2+3\binom t3\ge0.
\]
In a \(GL(m,2)\)-invariant full \(L_9\) solution, let \(p,q,r\) be the
singleton, pair, and linearly independent triple moments. Taking the
expectation on this nine-point scope gives the valid row
\[
 9p-72q+252r\ge0,\quad\text{or}\quad p-8q+28r\ge0.
\]
The present witness has \(p=1/5,q=1/35,r=0\), yielding \(-1/35\) in the
normalized row. It therefore cannot extend to full \(L_9\). These three
moments can already be read from the selected affine-flat model, so
adding this one necessary inequality is a small exact-LP experiment.
This note does not claim the resulting optimum, a strict lower bound
for every alternative \(L_8\)-optimal witness, or the full \(L_9\) optimum.

This is a statement about one explicitly defined local-marginal
relaxation. It is not a general proof-system lower bound, a claim about
all algorithms, or progress establishing either answer to P versus NP.
