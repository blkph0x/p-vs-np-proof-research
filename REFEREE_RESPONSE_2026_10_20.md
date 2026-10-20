# Response to the independent referee report — 20 October 2026

The report is accepted as a major-revision assessment. It does not identify a
counterexample to the finite Reed–Muller certificates or to the all-dual LP
argument, but it correctly says that mathematical credibility, reproducible
software, novelty, and publication readiness are different claims. The
repository therefore records the report as a revision gate, not as evidence
for P versus NP.

## Disposition

| Referee point | Decision and action |
| --- | --- |
| The `RM(s,2s+1)` family theorem is a credible dual-distance/local-projection theorem. | Retain it as a scoped theorem. The next manuscript must state exactly what is inherited from Reed–Muller dual distance and what, if anything, is new about this local-marginal formulation. No novelty claim is made until that comparison is complete. |
| The exact `31/5` value is a strong finite certificate if the quotient equivalence is established. | Retain the certificate. Add a standalone quotient-equivalence theorem and proof sketch, with the producer/reviewer correspondence and the remaining formalisation boundary recorded in [`REED_MULLER_QUOTIENT_EQUIVALENCE.md`](local_marginal_code_lab/REED_MULLER_QUOTIENT_EQUIVALENCE.md). |
| The certificate's objective convention must be audited independently. | **Addressed.** The producer and reviewer both use the reduced non-pin objective: the exact value is `31/5`, the pinned integer benchmark is `7`, and the equivalent total-weight values are `36/5` and `8`. The independent [normalization audit](local_marginal_code_lab/REED_MULLER_OBJECTIVE_NORMALIZATION_AUDIT.md) enumerates all 32,768 pinned codewords and retires the earlier mixed-convention ratio `40/31`. |
| The seven-cut sequence should not be called a standard SOS hierarchy without degree-bounded SOS proofs. | Adopted. The cuts are now described as **valid integer-domain polynomial cuts** or **integer-cut strengthening**. The degree-two Boolean square is the only item currently described as an SOS/moment constraint. Existing `SOS` filenames are retained as stable artifact paths and are explicitly historical names. |
| The seven-cut value is fractional and the candidate scan is separation only. | Retain the exact primal/dual value `35873801083/5129253893` as a finite integer-cut LP optimum. Retain the 39-candidate scan only as separation evidence; no post-candidate optimum is claimed. |
| The all-redundant-parity LP is a promising focused theorem but overlaps pseudocodeword and fundamental-polytope literature. | Retain the theorem and open a theorem-by-theorem novelty comparison before presenting it as new. |
| X3C reductions and PHP width are correct but largely background or validation infrastructure. | Keep them in the research-software ledger and move them out of any proposed central mathematical paper. |
| The repository is too broad for one paper. | Split the publication plan into: (A) code-based local-marginal gaps, (B) exact finite certificate infrastructure, and (C) structural SAT/proof-complexity experiments. The current repository remains the source record for all three. |
| “Independent reviewer” must not imply proof-assistant independence. | Make the trust chain explicit: definition and code parameters → support replay → symmetry quotient theorem → base primal/dual certificate → integer-cut certificate → scope and literature comparison. A reviewer may import an earlier audited artifact; that dependency is now stated rather than hidden. |
| Machine-readable certificates need a human explanation and cost accounting. | Add the quotient theorem, retain exact rational certificate summaries, and make construction, discovery, and verification costs separate fields in the next paper-oriented report. |

The requested publication-facing artifacts are now separated into three notes:
the [formal model specification](local_marginal_code_lab/REED_MULLER_FORMAL_MODEL.md),
the [explicit trust chain](local_marginal_code_lab/TRUST_CHAIN.md), and the
[theorem-by-theorem novelty ledger](local_marginal_code_lab/LOCAL_MARGINAL_NOVELTY_LEDGER.md).
They are deliberately conservative: they make the finite object and imported
assumptions easier to audit, while leaving new-versus-known status open where
the literature comparison is incomplete.

## Terminology rule adopted here

For a polynomial `P(t)` used only because `P(t) >= 0` for every integer weight
`t` in `0..31`, the repository calls it a **valid integer-domain polynomial
cut**. This does not assert that `P` is nonnegative on the real interval or
that it has a bounded-degree sum-of-squares representation modulo Boolean
constraints. A report may call the degree-two square a Boolean-square/SOS
moment constraint because that representation is explicit. The later cuts
must not inherit that label by filename alone.

## Research gates

The next work is ranked by mathematical value rather than by the number of
additional certificates it can produce:

1. Derive a compact analytical inequality from the 28-orbit affine-overlap
   dual, and test whether it has a parameterised analogue for `RM(s,2s+1)`.
   **Finite-instance gate completed:**
   [`REED_MULLER_AFFINE_OVERLAP_DUAL_NOTE.md`](local_marginal_code_lab/REED_MULLER_AFFINE_OVERLAP_DUAL_NOTE.md)
   records the six-term positive objective-gap identity and an exact replay
   test. A separate exact boundary-level theorem is now recorded in
   [`REED_MULLER_THEOREM.md`](local_marginal_code_lab/REED_MULLER_THEOREM.md):
   plain `L_{d-1}` has reduced value
   `(2^(2s+1)-1)/(2^(s+1)-1)` and total value one larger for the whole
   self-dual family, with an explicit sparse witness and an affine-incidence
   lower bound. This does not provide a parameterised analogue of the compact
   six-term reduced `31/5` identity, which remains open.
2. Compare the local-marginal model and integer-cut sequence with standard
   Sherali–Adams, Lasserre/SOS, pseudocodeword, and orthogonal-array results.
   **Terminology gate partially addressed:**
   [`LOCAL_MARGINAL_HIERARCHY_NOTE.md`](local_marginal_code_lab/LOCAL_MARGINAL_HIERARCHY_NOTE.md)
   defines the exact relation-family local polytope, proves its level-by-level
   equality with configuration Sherali–Adams for the explicitly declared
   finite-domain projection CSP, and gives a four-variable control showing why
   no equivalence to a sparse Boolean parity encoding should be claimed. It
   now also proves the one-sided inclusion `L_k(C) subseteq SA_k^check(H)` for
   an explicitly defined check-local parity configuration LP, with a strict
   four-variable support separation. The relationship to canonical sparse-CNF
   Sherali–Adams and Lasserre levels remains open.
3. Separate construction, discovery, and verification costs for the finite
   `RM(2,5)` certificate, including bit lengths, certificate size, memory, and
   replay time. **Measured for the retained construction and replay paths:**
   [`REED_MULLER_CERTIFICATE_COSTS.md`](local_marginal_code_lab/REED_MULLER_CERTIFICATE_COSTS.md)
   now records exact artifact sizes, rational bit lengths, construction time,
   saved-witness regeneration time, independent replay time, and sampled peak
   RSS. The historical certificate-search/discovery process is not retained
   and remains explicitly `UNRECORDED`.
4. Collect nearby exact instances only when they test a stated scaling
   conjecture. A fitted curve is not a theorem, and a failed conjecture is a
   valid recorded outcome. **A finite scaling theorem is now recorded:** the
   explicit unquotiented all-scope `RM(s,2s+1)` representation has
   `exp(Theta(sqrt(n) log n))` scopes and supported atom slots at the maximum
   unit-witness level. Quotient and implicit-separation scaling remain open.

The short-term success criterion is a publishable theorem with a precise
new-versus-known comparison. Producing more cuts without such a criterion is
not treated as progress toward P versus NP.

## Current scope statement

The repository still has no uniform deterministic polynomial-time SAT solver,
no unconditional lower bound against every polynomial-time SAT solver, and no
resolution of P versus NP. The finite RM(2,5) values, the code-family barrier,
the all-dual LP gap, and the proof-complexity replays remain scoped results.
