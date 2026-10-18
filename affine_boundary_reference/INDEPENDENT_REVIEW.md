# Independent block-reference review

The root reviewer read the support parametrization and quadratic summation proof
and implemented direct sums over original assignments without importing the
reference's algebra helpers. Five hundred held-out requests include sparse and
permuted active/retained coordinates, inconsistent support, duplicate monomials,
negative rational scalars, and unused active variables. Every reported boundary
value agrees with a complete original sum. Saved exact certificates are replayed;
wrong output magnitudes, changed external inputs, summation powers, and pair traces
are rejected. Exact counts and source hashes are saved in INDEPENDENT_REVIEW.json.

The support checker uses the left nullspace of the internal matrix to test all
projected equations. Each designated internal free coordinate equals a distinct
parameter; this proves injectivity. The independently checked matrix nullity
proves surjectivity onto each nonempty fiber. Substitution then preserves the
original phase, and each pair sum and final linear sum has its stated signed
multiplicity. No correctness issue was found in this review. This is ordinary
mathematical and code review, not proof-assistant formalization.
