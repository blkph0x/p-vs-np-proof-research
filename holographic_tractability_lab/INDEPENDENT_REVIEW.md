# Independent review of the supplied-basis real-affine evaluator

Reviewed on 2026-10-18. **Clean verdict within the stated scope.** No source,
test, theorem, or saved result was modified by this review. This document is
the only file added. The executable audits described below ran as bounded
inline checks rather than new production or test modules.

## Mathematical checks

The implementation evaluates explicit rational bipartite tensor networks
after one supplied invertible rational basis. Its local class is exactly
nonzero constant magnitude on affine Boolean support with a quadratic sign
in affine coordinates, together with zero tensors. It does not search bases
or implement the complete complex affine class. This subset and the inverse
bipartite basis convention agree with Definition 2.4 and Theorem 2.2 of
[Cai, Guo and Williams](https://arxiv.org/pdf/1307.7430).

The support recognition argument is valid: differences from one supported
point lie in their computed span, and equality of the support cardinality
with the span cardinality makes that inclusion an equality. Pivot-coordinate
identity proves independence of the certificate's basis and recovers the
unique local coordinates. Testing the proposed phase at every explicit table
entry is necessary and present; agreement at weights zero, one, and two
alone would not reject a cubic phase.

The global construction correctly translates each local support to affine
equations on the original edge variables. Pivot coordinates are affine
linear functions of those edge variables, so the sum of all local phases
remains quadratic. The checker validates consistency by independent rank
and augmented-rank calculations. A checked particular solution and an
independent homogeneous basis of the required nullity establish a bijective
parametrization of all feasible edge assignments, rather than only a subset.

For a present cross term, direct summation gives

\[
\sum_{x,y\in\{0,1\}}(-1)^{xy+xA+yB+C}
=2(-1)^{C+AB}.
\]

Here A and B are affine in the remaining variables. Boolean reduction
\(z_i^2=z_i\) keeps the resulting exponent quadratic. Each recorded step
removes exactly two variables and contributes factor 2. The final affine
phase sums to zero when a nonzero linear coefficient remains, and otherwise
to its constant sign times the number of remaining assignments. Both
negative values and cancellation to zero are therefore retained correctly.
The verifier checks the step identities without calling the producer's
Gauss-sum reducer. It shares some elementary assembly and substitution
helpers, a limitation already stated in the theorem; the independent audits
below provide a separate enumeration check.

The row action \(G T^{\otimes d}\) and column action
\((T^{-1})^{\otimes k}R\) cancel independently on every edge. The formula
builder retains distinct literal occurrences and ties them with variable
equality, including repeated variables, repeated clauses and polarities.
Unused variables have scalar 2; empty clauses have scalar 0. Consequently
the original SAT count and the separate binomial-slack count are preserved
with their different multiplicities. An exact zero implies UNSAT only when
the externally rebuilt original formula has these nonnegative weights.
For a generic signed network, zero may instead be cancellation.

The polynomial conclusion is correctly measured in the explicit table
input length and exact binary arithmetic. Equality tables of large arity
can themselves be exponential in a succinct formula; the theorem explicitly
excludes an unproved polynomial conversion of arbitrary such formulas.
The checked bit statistic does not bound every transient product, and the
theorem explicitly supplies a separate bit-growth argument. UNKNOWN carries
no value or certificate. UNSUPPORTED rejects only the supplied basis for
this local class, not all bases or all polynomial algorithms.

## Independent executable checks

The frozen suite passed all **12 tests in 6.128 seconds** using
`python -m unittest discover -s . -p 'test*.py' -v` in this directory.
Additional bounded checks used the public producer and verifier but did not
use their recognition or summation routines as reference oracles:

- Exhausted all **6,561 ternary tables** over entries {-1,0,1}. An independent
  support-XOR-closure test, explicit span generation, and Boolean Mobius
  transform of the sign truth table classified **481** as real-affine or
  zero and **6,080** as unsupported. Every classification agreed; every
  exact value agreed with direct summation and its certificate verified.
- Checked **560 seeded quadratic phases** through six Boolean variables,
  including constant signs, against direct enumeration. All values and
  certificates agreed.
- Replayed all **15 saved EXACT certificates** from their external original
  requests. Confirmed that all **26 UNSUPPORTED** and **1 UNKNOWN** results
  contain neither a value nor a certificate. All four recorded source
  hashes matched the files reviewed.
- Independently enumerated **1,811 edge assignments** across the saved
  networks of at most nine edges, and **172 original variable assignments**
  across the saved small formula requests. Counts agreed with their saved
  references, including SAT versus slack distinctions.
- Cross-checked **136 transformed formula-node tables** against the separate
  `tensor_basis_lab` implementation. Ports and every exact rational entry
  agreed. Checked all **576 planted clause occurrences** in the six saved
  24-variable requests; this validates the supplied satisfying assignments,
  not any unsupported count.
- Directly expanded the tensor powers for **252 local tables** across the
  five saved equality-family controls. This includes the identity-basis and
  capped controls as well as their successful versions. The intended
  supplied basis transforms their original signed tensors exactly into the
  saved equality tensors. Independent graph traversal verifies connectivity
  of both K3,3 and the 80-node, 120-edge family member. Thus each successful
  original contraction is 2 by basis invariance and connected equality;
  no enumeration of \(2^{120}\) assignments is used or claimed.

These finite checks support the implementation and its stated proof. They
do not extend the class, prove a basis-search theorem, or settle P versus NP.

## Reviewed source identities

| File | SHA-256 |
|---|---|
| affine_holant.py | `85db3e4fdd2d875542d67dd9718eb368b54afe5bd6c1a831adfce6a3cad6afee` |
| test_affine_holant.py | `6e67ab0caf3cdf9747cb2c0419ea2f2fdf7a85ebcfd62d835302dd0983641c6b` |
| run_experiments.py | `7686c4ee65faab9674f7ec06d4e4cf8c9d0244a0f0c38c094d017c1ae97067ac` |
| THEOREM.md | `38cc334540ecf18502961a1bbc7a70d854b226dee6b49c02bf9a038eebd684d8` |
