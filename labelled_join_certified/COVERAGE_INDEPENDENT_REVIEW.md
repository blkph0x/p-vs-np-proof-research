# Independent review of the coverage and auxiliary-variable claims

Reviewed `COVERAGE_AUDIT.md` on 2026-10-18, SHA-256
`3e36a1020f985182c33b98160b77a6561e7e9e900c752978d3c1bab0fe8c89ae`.

**Verdict:** the minor-closure, exact linear existential-projection and
same-coordinate counting claims are sound with the stated scope. No correction
to those conclusions is needed. The details below make the rank, code and
objective qualifications explicit. This review does not certify a general
encoding into the class or a P-versus-NP conclusion.

## 1. Minor closure, including dependent rows

Use a represented matrix K=[A;L], where every column of A has weight at most
two and L has at most p rows. A common ground vertex interprets unit columns;
zero graph columns are loops. Neither block nor K must have independent rows.
Deleting a coordinate merely deletes its column.

To contract a nonzero column e, pivot on a nonzero entry, clear that column in
every other row, then remove the pivot row and column e. This realizes the
quotient by the span of column e even if other rows are dependent.

* If A_e is nonzero, choose a graph endpoint row as pivot. A unit graph column
  merges that endpoint with ground. A two-entry column merges its endpoints:
  add the pivot endpoint row to the other endpoint row and then remove the
  pivot row. Every remaining graph column still has at most two entries.
  Clearing e in L only adds a graph row to some arbitrary rows, so there are
  still at most p arbitrary rows.
* If A_e=0 and L_e is nonzero, pivot in L. No graph row changes, and one label
  row is removed, leaving at most p-1.
* If the whole column is zero, its span is zero; contraction is deletion.

Parallel columns may become loops during this process and must be retained
until their own deletion/contraction. Iterating the same argument handles an
arbitrary auxiliary set, including dependent auxiliary columns. Thus the class
with **at most** p label rows is minor-closed; no independence or density
assumption about the supplied row presentation is required. A dense row change
does not need to preserve the visible graph block: the class asserts existence
of a suitable presentation, and contraction can be performed in that one.

## 2. Existential projection is contraction, not deletion

Write K=[K_X K_Y], with original coordinates x and auxiliary coordinates y.
Let W=span(columns(K_Y)) and let pi be the quotient map onto the ambient
binary vector space modulo W. Then, exactly,

    exists y: K_X x + K_Y y = 0
        iff K_X x belongs to W
        iff (pi K_X) x = 0.

For every original-coordinate subset S, its quotient-column rank is

    rank([K_Y K_S]) - rank(K_Y),

the represented matroid contraction rank. This is the usual quotient-space
description of contraction; see [Victor Reiner, Lectures on Matroids and
Oriented Matroids, section 2.1.3](https://www-users.cse.umn.edu/~reiner/Talks/Vienna05/Lectures.pdf).
The displayed kernel identity additionally proves the exact code claim, rather
than relying only on a matroid name. No duality reversal is required. For
example, projecting ker([1 1]) onto its first coordinate yields the full
one-bit space, as contraction predicts; deleting the second check column would
instead leave the zero kernel.

For a labelled binary matroid, the kernel is its binary cycle space; circuits
generate all binary dependencies. Nevertheless, the direct quotient identity
above is sufficient here and avoids any issue about representation uniqueness.
All original coordinate IDs stay fixed, so the equality is of the actual
codes, not just their unlabelled matroid isomorphism types.

Combining this identity with minor closure shows that **any finite number** of
pure linear existential auxiliary coordinates cannot enlarge the class at
fixed p. Polynomially many are therefore also insufficient. All constraints of
the extension must be included in K and K itself must have the promised
graphic-plus-p-row presentation; adding arbitrary equations outside that
presentation is not covered by the hypothesis.

## 3. Counting row spaces with redundant presentations

Let the target check row space have dimension r on n labelled coordinates.
In any qualifying [A;L] presentation, k=rank(A)<=r. Select k independent
**existing graph rows** and discard the rest. This preserves rowspace(A), and
deleting rows cannot increase any column's weight. Therefore the graphic block
has a representation on k row vertices plus ground even if the original
presentation had arbitrarily many dependent graph rows or isolated vertices.
Retain L, padding with zero rows up to p if necessary.

For fixed k, each coordinate has at most 1+binom(k+1,2) graph column choices,
and the p label rows have 2^(pn) choices. Summing over k<=r gives the valid
upper bound

    (r+1) [1+binom(r+1,2)]^n 2^(pn).

No GL factor is missing: changing a row basis leaves the row space unchanged.
The count already allows every displayed graph-plus-label matrix, and multiple
descriptions only overcount. Permuting coordinates is also already allowed by
choosing the column value separately at each labelled position.

The 2^(r(n-r)) systematic row spaces [I_r|M] are distinct: their left identity
block fixes the unique row-space vector with each prescribed first-r-coordinate
pattern. For r=floor(n/2), this lower bound exceeds the preceding count when
p=O(log n). Thus universal same-coordinate logarithmic-label coverage is
false. Here r means **actual target row-space dimension**, not the number of
possibly redundant rows in an input file.

An extension with M=poly(N) coordinates and p=O(log M) has p=O(log N).
For the rank-half dense input family, N=Theta(n^2) in the standard matrix
encoding, so p=O(log n). Contraction returns a same-coordinate presentation
with that label bound, and the counting obstruction applies. This conclusion
does not use the invalid shortcut of counting enlarged descriptions as though
they still had n columns.

## 4. Objective and nonzero scope

If auxiliary coordinates have zero cost, existential projection preserves the
original additive objective on x. Nonemptiness must still mean x!=0, not merely
(x,y)!=0; the audit correctly requires pins among original coordinates or an
equivalent proof. Charging auxiliary variables can impose additional costs on
fibres, so objective preservation then needs a separate argument even though
the projected feasible code still obeys the class restriction.

An arbitrary output map x=Tz is explicitly outside coordinate projection.
The example T(z1,z2)=(z1,z2,z1+z2) correctly demonstrates the problem: all three
nonzero outputs have weight two, incompatible with fixed additive costs on
z1,z2. Encoding x=Tz as extra linear equations does not evade the theorem
unless the **whole enlarged constraint matrix**, including those equations,
still meets the same p-label bound. Nonlinear encodings, different objective
models and more general decision reductions are not ruled out by this audit.

## 5. Independent finite checks

A separate in-memory contraction implementation checked all 789 presentations
with zero to two graph rows, zero or one label row, and zero to three columns.
All 5,724 choices of auxiliary subsets passed. For each choice it compared the
full projected original kernel against the contracted kernel, checked the
quotient-rank identity, and checked that the graph-column bound and label-row
budget survived every contraction.

Another 500 seeded cases used up to four graph rows, two label rows and seven
coordinates, including zero/dependent rows, loops and parallel columns. Dense
invertible row changes were applied before independently enumerating the
original kernel; all comparisons passed. These finite checks supplement the
proof. No production file or existing audit document was modified.
