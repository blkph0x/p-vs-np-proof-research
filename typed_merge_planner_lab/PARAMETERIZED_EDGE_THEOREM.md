# Parameterized affine/cardinality edge

The typed planner records `AFFINE + CARDINALITY` as a known hard pair because
it contains binary linear-code minimum-distance decision.  The hard edge does
not disappear when a parameter is small; it gains explicit parameterized
routes.

`engine.assess_hard_merge` exposes these routes when the caller supplies the
corresponding code metadata; without that metadata it retains the hard-barrier
classification.

For a supplied binary generator matrix with row-space dimension `k`, enumerate
the `2^k-1` nonzero messages, evaluate their codewords, and return the minimum
Hamming weight with its message and word certificate.  Row reduction first
normalizes rank-deficient input, so the parameter is the actual code dimension.
The cost is `2^k * poly(n,k)` and is fixed-parameter tractable in `k`.

For a supplied distance bound `d`, enumerate every coordinate support of size at
most `d`.  For a support `S`, solve the homogeneous GF(2) system requiring all
coordinates outside `S` to vanish.  A nonzero null vector gives a codeword
supported in `S`; if no support succeeds, the certificate proves distance
greater than `d`.  The cost is

`sum_{s<=d} binomial(n,s) * poly(n,k)`,

which is an XP bound in `d`, not an FPT claim.  The implementation returns
`UNKNOWN` nowhere inside these supplied finite parameters: it returns an exact
witness or a certified lower bound.  It does not find a useful parameter,
solve arbitrary minimum distance in polynomial time, or resolve P versus NP.

The saved artifact covers exact dimension enumeration, rank-deficient input,
an above-bound certificate, an exact distance witness, and the zero code.  A
separate reviewer checks every result by direct message enumeration and
recomputes the planner route metadata.
