# Exact affine-sum compression inside the original-factor DAG

This is a separate experimental adapter. Its structural solver is adapted from
the frozen `../weighted_affine_dag_lab/dag.py`, SHA-256
`5693dfff8bba4b4ec0ba9735698eb209567bc0a4eff1c091bf90e49b70453368`.
That file and its saved results remain unchanged. The adapter invokes the new
`../affine_sum_compression_lab/compression.py` explicitly; it does not monkeypatch
shared modules, silently invoke the baseline as a fallback, or change an
UNKNOWN into an exact count. The algebraic identities and propagation effects
are not claimed as novel. No polynomial bound for general CNF is established.

## Original meaning and retained invariants

`solve_formula(n, clauses)` counts assignments to all n original variables.
`solve_factors(n, factors)` also accepts exact rational affine quadratic factors
and returns a possibly zero or negative rational contraction. The literal,
native-factor, original-coordinate, and complete external-request conventions
are those proved in the frozen weighted solver. In particular, every original
factor occurrence keeps its own ID, repeated literals are locally normalized,
tautologies become one, empty clauses become zero, and no normalization changes
the original n. Variables absent from all normalized scopes contribute the
explicit final factor 2^f. Native scopes preserve their declared universes.

For original factor IDs S, let X_S be their normalized variable union and B_S
the variables in X_S occurring outside S. The node represents

    M_S(b) = sum_{X_S minus B_S} product_{i in S} F_i.

Every original OR is decomposed as 1 minus its affine violation indicator.
A native factor contributes one affine quadratic piece. The producer uses the
same original factor-incidence components, supplied order, and balanced product
trees as the baseline. A product has disjoint child ownership whose union is
the parent. Every ordered pair of child pieces is generated; equations are
stacked, phases XORed, and rational scalars multiplied. Each resulting piece
is marginalized using the independently verified boundary primitive, with
active universe exactly the union of child boundaries and retained universe
exactly the original parent boundary. Shared marginal records require identical
complete requests and do not omit factor occurrences.

The adapter preserves this entire recurrence and the original root coverage,
active-variable, free-variable, and rational arithmetic checks. The sole
functional replacement is the sum-reduction stage **after** generation and
marginalization of all those pieces. The externally bound certificate format is
`compressed-affine-dag-v1`, distinct from the frozen baseline format.

## Pointwise sum rewrites

Each node supplies the compressor with the complete ordered list of derived
canonical marginal messages on that boundary. The compressor may cancel zero
pieces, add coefficients of identical canonical pieces, and perform its checked
addition identities. These include compatible parallel-coset unions,
same-support affine phase-difference restrictions, and codimension-one nested
support subtraction. The exact statements and sign conditions are proved in
`../AFFINE_SUM_COMPRESSION_NEXT.md` and the compressor's theorem.

For example, if B=A intersect [L=b] is a nonempty proper affine hyperplane and
qA+qB is the constant epsilon on B, then the effective cancellation condition
cB=(-1)^(epsilon+1)cA gives

    cA*1_A*(-1)^qA + cB*1_B*(-1)^qB
      = cA*1_{A intersect [L=1+b]}*(-1)^qA.

Thus 1-[literal=false] becomes the one-piece pin [literal=true]. This expresses
ordinary propagation in the weighted representation. A general OR on at least
two unfixed variables does not become a single affine piece by that identity:
its support has 2^k-1 points, not a power of two. A reduction in term count is
therefore conditional, and does not imply a general tractability result.

Every rewrite consumes its named live input IDs exactly once and inserts its
checked output, preserving all other pieces. Such a rewrite preserves the
pointwise sum, even when other pieces have overlapping support. It does not
alter the enclosing original-factor ownership and cannot refund the work of
generating or marginalizing any original pair. The compressor's greedy order
is an implementation choice, not a proof of globally minimum component count.

## Independent source-bound replay

Every structural node now stores its complete `compression` result, including
the trace and final message list, in addition to its original factor ownership,
boundary, active universe, child IDs, and marginal references. The adapter's
verifier derives every local term and every ordered child cross-product from
the externally supplied original factors and previously verified child outputs.
It replays each unique marginal trace and uses the marginal verifier's freshly
derived message, not a saved convenience key or producer statistic.

The ordered list of those freshly derived marginal messages is the external
input to `verify_compression`. Its own checker must bind every incoming piece,
replay every rewrite and recorded pair-attempt observation, and return freshly
derived canonical output messages. Failed-pair observations are semantic no-ops:
the checker meters them but does not rediscover every rejected rule or certify
irreducibility. The complete discovery work is measured in the producer; the
separate checker's work is the work actually needed for its equality proof.
The adapter then compares the saved node output against that
verified list and uses only the fresh list at its parents. A missing, null,
wrong-boundary, or unrelated compression proof does not invoke the producer as
a fallback. Producer statistics are not trusted for verification limits.

The original complete-root and exact free-variable checks still apply. By the
original product recurrence, marginal soundness, and the pointwise sum identity
at each compression step, induction proves every accepted node invariant and
the original count at the root. This is a proof of exactness of accepted
results, not a proof that the bounded producer must finish on every input.

## Resource accounting and the streaming distinction

The original adapter caps remain: `max_terms`, `max_products`, `max_nodes`,
`max_work`, `max_variables`, `max_factors`, and `max_integer_bits`. All child
cross-products are charged before producing or compressing them. The existing
structural/marginal node units remain unchanged; rewrite trace size is governed
by separate compression limits. The old one-per-generated-input merge
bookkeeping unit is still charged, and **all** compressor work is added to the
same global `max_work`. This includes successful and unsuccessful discovery,
identity tests, normalization, and algebra work. As in the baseline, these are
explicit operation counters, not literal bit-operation or wall-clock bounds;
input traversal, hashing, and arbitrary-precision operations have their usual
additional costs in the explicit representations and bit lengths.

`compression_caps` adds the compressor's limits. The adapter passes remaining
budgets across successive nodes, so `max_inputs`, `max_generated`, `max_pairs`,
`max_steps`, and compression `max_work` are **aggregate** limits for the entire
DAG, rather than fresh budgets at every node. Their counters are respectively
incoming pieces, generated rewrite pieces, attempted pairs, trace steps, and
work. Failed pair attempts remain in the attempted total. Per-representation
variable, row, phase-term, scalar-bit, and retained-piece limits remain local
maxima; the adapter bounds scalar bits by its original integer cap and retained
pieces by its original `max_terms`. Verification uses separately metered fresh
checker work and enforces the same aggregate rules; its exact work need not
equal the producer's.

The generated-input list and the retained live list are different objects.
The adapter materializes the complete ordered list of marginal outputs at a
node before calling the internally streaming compressor. Consequently this is
**not** an O(retained-pieces)-memory algorithm: generated inputs, cached
marginals, and certificates also occupy memory. `generated_input_terms` and
`peak_generated_input_terms` record the complete adapter input list, including
zero pieces, separately from all compressor counters.

The streaming compressor permits one arriving piece to be processed and safely
reduced before enforcing its retained-set limit. `peak_terms` reports the
largest retained set after processing an arrival, while
`compression_peak_live_pieces` reports actual simultaneous live proof IDs,
including the arrival. The latter may be one greater than the retained cap.
Pending canonical input/output objects are reported separately; they are not
hidden or asserted to be included in a single exact byte-memory peak.
`peak_output_terms` records completed node output size. This differs from the
baseline's dictionary cap, which can stop before a later cancellation. The
saved comparison must disclose the difference, not call both caps the same
transient-memory bound.

Exhausting any producer cap returns UNKNOWN with no count or completed
certificate. Exhausting a checker cap returns UNKNOWN rather than VERIFIED.
An exact count with a verification UNKNOWN under tighter resources is not
reported as a completed verified case. Separate source hashes and full original
requests support comparison with the frozen baseline, including every failure.

## Required controls and interpretation

The regression tests retain the original-factor and every-boundary-value
oracles, signed/native controls, clause omission and partition mutations,
free-variable checks, and resource exhaustion cases. Added tests require a
compression proof at every node, distinguish input/retained/transient counts,
reject source-swapped proofs, ignore forged producer work statistics, and show
that cumulative caps cannot reset between nodes. Native wide-boundary examples
still use exact algebraic references rather than exponentially large tables.

The parent compares the same 58 frozen original requests, in the same original
clause order, against the unchanged old adapter and the independently certified
original count reference. The additional native controls remain a separate
dataset. No successful example, lower final piece count, or selected benchmark
implies a general performance improvement. Discovery and checking costs, changed
transient-retention semantics, and all UNKNOWN outcomes must remain visible.
