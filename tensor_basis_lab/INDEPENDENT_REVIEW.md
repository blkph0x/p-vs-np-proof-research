# Independent review of the rational basis-invariance lab

Reviewed the frozen `THEOREM.md`, producer, certificate checker, tests and
saved original requests. No mathematical or correctness defect was found.
No producer or theorem changes were made. This is an independent source and
bounded computational review, not a proof-assistant formalization.

The row action f*T and column action T^-1*g use the same LSB-first ordered
ports. Their edge factors cancel exactly. The code preserves the shared
original variable at every repeated occurrence, each literal's polarity,
whole repeated clauses, and the degree-zero equality scalar two. Empty
clauses are zero. Both input modes match the stated original problem: SAT
counts logical assignments, while slack mode counts logical assignments
together with their local slack-bit extensions. In particular, the ternary
counts 7 versus 10, and the repeated-clause slack count 16, are kept distinct.

The certificate checker binds the external original formula, mode and basis
with a binary integer hash and also reconstructs their mathematical data.
It checks both inverse identities, every intermediate local axis update,
every original/transformed global trace term, and the final equality. Its
inverse verification and traversal differ from the producer. The full
contraction verifier takes the certificate, not the outer result wrapper;
the latter's observational statistics are not proof inputs. Resource
exhaustion has UNKNOWN status and endorses no count.

The scope statement is accurate. Local invariance does not compute a
global contraction, and the reference's 2^E edge expansion can be worse
than enumerating original assignments. Explicit high-degree equality tables
can also be exponential in their degree. The named arithmetic counters do
not subsume parsing, hashing, binomial computation, serialization or all bit
costs; these are separately acknowledged. Exact rational bit lengths stay
polynomial per number, which does not eliminate the exponential number of
reference terms. Neither rational experiments nor the invariance identity
provide a universal tractability or all-complex-bases claim.

Validation performed in this review:

- All 14 supplied tests passed in 1.177 seconds, including rehashed request
  mutations, proof tampering, cap boundaries and large exact inputs.
- An additional 120 seeded raw formulas were tested in both modes under
  identity, Hadamard, nonsymmetric integer and nonsymmetric rational bases:
  240 complete verified requests. The independent original oracle enumerated
  5,040 complete logical/slack choice words, rather than using the producer's
  binomial factors. Repeated literals, signs and empty clauses were retained.
- The same requests were transformed by the separately implemented
  `holographic_tractability_lab` network transformer. All 3,866 final local
  entries and ordered port lists agreed exactly.
- Saved exact certificates, local-only proofs and both wrong-same-basis
  controls were replayed from their external inputs. The wrong actions were
  independently contracted and change the unit-clause count as claimed.
  Original saved counts were checked by explicit logical/slack choices,
  using the closed form 2^n for empty formulas with many unused variables.
- Every saved source hash still matches the frozen source.

The positive conclusion is exact invariance and trustworthy bounded
reference contractions. A general fast evaluator still requires a jointly
tractable transformed family, with the full original network retained.
