# Complete ten-point D=6 scope classification

This directory gives an exact, exhaustive certificate for the proposed rank
moments

\[
651M_A=g(\operatorname{rank}A),\qquad g=(651,155,35,7,1,0,\ldots).
\]

It covers every binary configuration of at most ten distinct nonzero points,
in arbitrary ambient dimension, not a random sample. The classification is
finite and independently replayed; it is not proof-assistant verification.
It proves feasibility of this upper witness, not optimality of full level ten,
novelty, an efficient general decoder, or a complexity separation.

The accompanying [analytic draft](GENERAL_DRAFT.md) gives a separate
relation-space proof and the generalized support lemma. The finite
certificate below does not import that draft or any historical moment producer.

## Why the finite list is complete

Low-rank scopes, of rank at most six, embed into \(\mathbb F_2^6\).
Choose uniformly among its 651 codimension-two linear subspaces. The numbers
containing a specified subspace of ranks zero through four are
651, 155, 35, 7, and 1. Their indicator functions are quadratic Boolean
polynomials equal to one at zero. Restriction and linear extension to the
original ambient space prove nonnegativity and pinned-code support.

For the remaining cases it suffices to treat ten points of rank at least
seven. A smaller high-rank scope can be padded with independent points in
a larger vector space; marginalization recovers its original rank moments.
No assumption that the original ambient space has ten independent vectors
is needed.

Write its ordered column matrix as \(A\), and let \(D=\ker A\).
Then \(d=\dim D\le3\). A basis of \(D\) forms a \(d\times10\) matrix.
Its columns belong to \(\mathbb F_2^d\). Up to permutation of the original
ten coordinates, this matrix is described by a histogram of its \(2^d\)
column types. Changing the relation basis acts by \(GL(d,2)\).

Every such histogram is enumerated by weak compositions of ten into
\(2^d\) parts. The generator must have full row rank and every nonzero
relation must have weight at least three: a weight-one relation would mean
a zero original column, and a weight-two relation would mean equal columns.
These conditions are also sufficient for the reconstructed kernel columns
to be distinct and nonzero. Thus the test covers exactly the desired
configurations, up to invertible ambient coordinates and point permutation.

| Relation dimension | All histograms | Admissible histograms | GL order | Types |
| ---: | ---: | ---: | ---: | ---: |
| 0 | 1 | 1 | 1 | 1 |
| 1 | 11 | 8 | 1 | 8 |
| 2 | 286 | 143 | 6 | 32 |
| 3 | 19,448 | 6,413 | 168 | 80 |
| Total | 19,746 | 6,565 | — | 121 |

Accounting also for coordinate labels, these types cover respectively
1, 968, 147,466, and 4,277,240 distinct relation subspaces of
\(\mathbb F_2^{10}\). These are counts of labelled configurations modulo
ambient invertible transformations, not distinct codes in every ambient space.

## What the independent replay checks

The producer computes subset rank from the dimension of relations supported
on that subset and then performs Möbius inversion. `verify.py` imports no
producer code. It:

1. Enumerates all histograms independently by stars and bars, generates
   invertible maps independently as binary matrices, and checks exact orbit
   coverage with no missing or repeated type.
2. Checks each supplied point matrix has the claimed rank and exactly the
   claimed relation kernel.
3. Requires every mass to be a nonnegative integer and total mass 651.
   Its independent zeta transform must recover every rank moment, with
   ranks obtained directly by elimination of the supplied points.
4. Builds the degree-one and degree-two evaluation vectors independently
   and checks rank ten. With constant term one, all ten-bit outputs are
   therefore possible with the pin fixed to one.
5. Checks the separate relation-count formula for the empty atom and both
   next-level negative controls below.

The result is 121 tables, 123,904 atom/moment comparisons, 33,138 positive
atoms, and 121 full quadratic-projection checks. The smallest atom numerator
is zero; the smallest empty-atom numerator is 21.

Common rank moments imply every overlap marginal agrees, because Boolean
moments determine a table uniquely. The tests additionally check all
1,210 delete-one marginal tables of the complete representative list.

## Independent support argument

For \(RM(2,m)\), every nonzero dual word has even weight at least eight.
Suppose a dual word has support \(U\subseteq S\cup\{0\}\), of weight \(w\).
Constant and coordinate-linear evaluations on \(U\) are mutually orthogonal,
since each pairwise product has degree at most two. Their dimension is at
most \(w/2\).

If \(0\in U\), the constant row is independent of all coordinate-linear rows,
so \(\operatorname{rank}(U\setminus\{0\})\le w/2-1\).
The remaining points give
\(\operatorname{rank}(S)\le w/2-1+(|S|-w+1)=|S|-w/2\).
If \(0\notin U\), the same bound follows from
\(\operatorname{rank}(U)\le w/2\) and the \(|S|-w\) remaining points.

Consequently for \(|S|\le D+4\), a scope of rank greater than \(D\) has no
supported nonzero dual word. Its pinned projection is full. In particular,
this applies to \(D=6\), at most ten nonpin points, and ambient \(m\ge6\).
The direct evaluation-rank checks provide an independent finite confirmation.

## Empty-atom identity and exact failure controls

Let \(A_j\) count relation words of weight \(j\), \(B_j\) count two-dimensional
relation subspaces with union support size \(j\), and \(C_j\) count
three-dimensional relation subspaces with union support size \(j\).
For ten points and relation dimension at most three,

\[
651\mu(\varnothing)=46-7A_3-A_5+B_5+B_6-4C_6-C_7.
\]

The verifier independently computes the subspace-lattice coefficients and
checks the identity for every type. There are at most four odd-weight
relations, and at most one three-dimensional subspace. Hence the formula
is at least \(46-28-4=14\); the exhaustive sharp minimum here is 21.

The old D=5 moments fail on the ten-point scope
\(\{1,2,4,8,12,16,20,24,28,32\}\), with the atom \(\{1,2\}\)
having numerator \(-1\) over 155.

The D=6 moments themselves fail at eleven points:

\[
S=\{1,2,4,8,16,24,32,40,48,56,64\},\qquad B=\{1,2,4\}.
\]

The eight outside points occupy distinct nonzero cosets modulo the span
of \(B\). The rank-three moment is \(7/651\), each of the eight rank-four
extensions contributes \(1/651\), and rank-five moments vanish. Thus
\(\mu_S(B)=-1/651\). Direct subset-rank inversion reproduces this value;
all eleven delete-one subscopes remain nonnegative.
This is the first possible scope cardinality at which this fixed D=6
moment witness can fail, not a lower bound on the full level-eleven optimum.

For all \(m\ge6\), feasibility of the ten-point family yields the upper bound
\[
\min_{L_{10}} F\le \frac{5(2^m-1)}{21},\qquad
\min_{L_{10}} W\le 1+\frac{5(2^m-1)}{21}.
\]
No equality with the existing lower bound is claimed.

## Reproduction

From this directory:

```text
python explore.py
python verify.py
python -m unittest -v test_exploration
```

`explore.py` writes the compressed complete certificate and `RESULTS.json`,
including normalized-LF source hashes. `verify.py` only replays the saved
certificate. The Python code uses exact integers and only the standard
library. This fixed-width calculation has no optimizer, external SAT solver,
unbounded ambient enumeration, or boundary truth-table input assumption.
