# Compact weighted-boundary marginalization

This lab implements and checks one exact symbolic primitive proposed in
`AFFINE_DECOMPOSITION_NEXT_REVIEW.md`. An input summary has ordered boundary
bits followed by ordered internal bits and represents

\[
  H(y,z)=\lambda\,1[A(y,z)=b](-1)^{q(y,z)},
\]

where the equations are binary affine constraints, `lambda` is rational, and
the Boolean phase `q` has degree at most two. The output is the exact marginal
`F(y)=sum_z H(y,z)` in the same representation. The implementation never
constructs a table indexed by all boundary assignments.

## Elimination identities

If a support equation contains an internal bit `t`, row reduction solves it as
`t = a(w)`, where `a` is affine in the other variables. XORing that row out of
the remaining equations preserves the support exactly. Substituting `a` into a
quadratic Boolean phase leaves degree at most two, and each allowed assignment
has exactly one value of `t`, so the scalar is unchanged.

If no support equation contains `t`, write
`q(t,w)=q_0(w)+t L(w)` with `L` affine. Then

\[
  \sum_{t\in\{0,1\}}(-1)^{q(t,w)}
    =2\,1[L(w)=0](-1)^{q_0(w)}.
\]

The producer therefore multiplies the rational scalar by two and appends the
single affine equation `L=0` when it is nonzero. `L=1` is retained as the
explicit inconsistent row `0=1`, which proves a zero marginal. Repeating the
step for every internal bit proves closure and gives a trace of at most one
step per internal variable.

The checker reconstructs the original request, binds its exact hash, validates
the ordered variable IDs, and replays each pivot or free identity. It derives
the final support, phase, and scalar rather than trusting producer snapshots.
All rows and monomials are canonicalized modulo two; quadratic monomials use
Boolean idempotence, so repeated variables are reduced correctly.

## Complexity and limits

For `N` explicit variables, `s` support rows, and `p` phase monomials, the
stored state has `O(sN+p)` bits. Each of the `m` eliminations uses binary row
XOR and affine phase operations, with polynomial arithmetic and rational bit
growth (at most one additional scalar bit per free variable). The code applies
explicit caps to variables, rows, phase terms, work, and integer bits and
returns `UNKNOWN` without a partial certificate when a cap is reached.

This closure result does not imply that a general CNF has a compact affine
summary. A sum of many affine summaries is not closed under this single
representation, and a generic clause expansion can still create exponentially
many terms. The lab proves exact marginalization for a supplied summary only.
