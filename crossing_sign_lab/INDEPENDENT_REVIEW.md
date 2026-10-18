# Independent review of crossing signs and exact Pfaffian certificates

Reviewed THEOREM.md, crossing.py, test_crossing.py, run_experiments.py and the
saved RESULTS.json. No correctness correction was required.

The ordered four-port identity is the negative of the matchgate identity
with numeric masks alpha=1 and beta=14, so its ordinary-crossing residual
is exactly 2. This rules out the specified boundary tensor in characteristic
other than two, including complex weights. The cyclic boundary order is an
essential hypothesis. The six-vertex ladder has the stated signed signature;
contracting it against EQ4 changes the ordinary contraction from 2 to 0.
The diagonal-rescaling argument correctly restricts its claim to unary
rescalings, and does not assume that arbitrary basis changes have been ruled
out by that argument.

The necessary identity and deletion-signature convention agree with Cai and
Gorenstein, [Matchgates Revisited, Section 2 and Theorem 1](https://arxiv.org/html/1303.6729#S2).
The independent checks below also establish the particular small graph
signature directly, without requiring a classification theorem.

The skew-elimination congruence has the correct signs. The simultaneous
transposition changes the Pfaffian sign, the triangular congruence has
determinant one, and the resulting block factor is the pivot itself. The
verifier recomputes the full matrix product and binds the proof to the
external original ordered matrix. Its zero-row and odd-size terminations
are valid; these do not convert a resource cap into zero. The theorem's
polynomial rational-operation and bit-complexity bounds are justified:
Schur entries are ratios of bordered subdeterminants after clearing input
denominators, so their bit lengths stay polynomial. This statement does not
claim that the implementation caps bound every temporary allocation.

The efficient output is a signed pairing sum. The report correctly avoids
using its zero value as a general no-matching or SAT-unsatisfiability
certificate, and distinguishes the fixed chord order from graph
nonplanarity. No P-versus-NP or novelty conclusion is inferred.

## Independent execution

- All nine existing unit tests passed.
- An additional 400 seeded rational skew matrices, of dimensions 0 through
  10, agreed with a separate exterior-algebra oracle. That oracle expanded
  the appropriate power of the two-form by subset convolution and divided
  by the factorial; it used neither pivot elimination nor the stored
  recursive pairing expansion. Every exact proof replayed successfully.
- All 38 saved exact certificates replayed from their external original
  matrices. Both saved capped requests remained UNKNOWN, with no value.
- Every one of the 2,676 saved pairing terms was checked for a complete
  vertex pairing, its crossing sign, edge product and signed product.
- All 2,048 boundary/edge-subset combinations of the seven-edge signed
  crossover graph were independently enumerated. The complete matching
  lists, weights and all 16 boundary sums agreed with the saved artifact.
- All four current source hashes match the saved RESULTS.json hashes.

The extra random seed was 2026101831. These finite checks corroborate the
theorem and certificate implementation; the mathematical claims are not
inferred by extrapolation from random examples.

## Reviewed source hashes

- crossing.py: `f12391105a9179dbe7fd09578e87557d3dd4dfc9b1dba8b88e35aacb4fb3ef4b`
- test_crossing.py: `e1b1fce83dbf2188f497aea4ea0dfb64b757aa3f670592d1e8c865c4772cd636`
- run_experiments.py: `effe1238824570e9bf2bf78d5b09550150e10540fac0ec8cf8e7efe0b9a5945c`
- THEOREM.md: `fe5282e8bea770cf508fb4d40e9069c5fb82976ac4ecfa2bfcf45592af80e1a2`
