# Degree-three affine decoding reduction

This theorem records the exact complexity boundary established by
`degree_three_barrier.py`. It is a reduction for a nonzero syndrome; it is not a proof
about homogeneous minimum distance.

## Decision problem

Input a binary matrix `H`, a target syndrome `s`, and an integer `t`. Decide whether

\[
  \exists x\in\{0,1\}^n:\quad Hx=s\pmod 2,\qquad |x|\le t.
\]

The problem is in NP: a selected-column bit vector is a certificate, and both the syndrome
and the weight are checked in polynomial time.

## Reduction from X3C

Take an instance of Exact Cover by 3-Sets with universe `U`, `|U|=3k`, and triples
`T_1,...,T_n`. Construct one binary column `h_i` for each triple, with ones exactly in
the three rows corresponding to the elements of `T_i`. Set

\[
  s=\mathbf 1_{|U|},\qquad t=k.
\]

Every column has Hamming weight exactly three, so the construction is linear in the input
incidence list and preserves the column-weight-three promise.

For a selected set of columns, let `c_u` be the ordinary integer number of selected
triples containing element `u`. The equation `Hx=s` says every `c_u` is odd, hence
`c_u\ge1`. Since each selected triple contributes to exactly three counts,

\[
  \sum_{u\in U}c_u=3|x|\le3k=|U|.
\]

All `|U|` positive odd counts therefore equal one. The selected triples form an exact
cover. Conversely, an exact cover gives every row count one, hence satisfies the binary
syndrome and has weight `k`. Thus the reduction is iff and proves NP-completeness of the
decision problem even when every column has weight three.

The target is nonzero whenever `U` is nonempty. The reduction does **not** establish
NP-hardness of homogeneous minimum distance (`s=0`): zero-syndrome kernel words remain a
separate issue. Any homogenization must explicitly exclude those words below the threshold;
appending a target column alone does not do so. For a concrete counterexample, take
`U={0,...,5}` and two duplicate triples `{0,1,2}`. There is no exact cover, but selecting
both equal columns is a zero-syndrome word of weight two. The naive appended-target
construction would raise the threshold from `k=2` to three and falsely accept that kernel
word (the appended target column itself has weight six).

## Reproducible audit

The implementation validates the equivalence directly for every family of triples in the
complete `2\times2\times2` tripartite universe (256 families and 6,561 selections), and
for all 1,351 six-element families containing at most three triples. It also checks
duplicate columns, empty universes, malformed inputs, and selections above the threshold.
The independent replay in `degree_three_reduction_review.py` repeats the theorem-specific
checks and records source hashes in `DEGREE_THREE_REDUCTION_REVIEW.json`.
