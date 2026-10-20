# Trust chain for the RM(2,5) certificate campaign

The finite results are modular. A later checker may reuse an earlier artifact,
but that dependency is recorded explicitly here.

**Virtual-dimension follow-up.** The
[all-D theorem](REED_MULLER_VIRTUAL_DIMENSION_THEOREM.md) proves positivity,
consistency, support, and the sharp failure boundary for its own explicit
moments. Its induction now starts at D=3 and does not import a finite LP dual
or the earlier D4/D5 positivity proofs. It uses classical RM dual distance,
subspace counting, and a fully written relation-space calculation. The
separate [D6 exhaustive replay](level10_scope_exploration/THEOREM.md) reconstructs
all high-rank types and their moments without importing the producer. Neither
the finite replay nor the written proof is proof-assistant verification.

**Stronger level-ten lower bound.** The [selected-model replay](level10_exploration/REPORT.md)
uses the earlier independent base-geometry reconstruction, then independently
enumerates pinned quadratic restrictions and counts the new orbit incidences.
It compares the full matrix and objective before checking the exact certificate
and 14-term identity for singleton lower bound `3843/16627`. Its selected-model
primal is not a full-level-ten witness. The separate D6 virtual construction
gives the full-model singleton upper bound `5/21`.

1. **Mathematical definition.** The pinned code, exact supports, local tables,
   containment equations, and objective are specified in
   [`REED_MULLER_FORMAL_MODEL.md`](REED_MULLER_FORMAL_MODEL.md). This is the
   object being certified.
2. **Code-support replay.** The producer and independent review scripts rebuild
   the degree-at-most-two evaluation rows, enumerate the pinned support, and
   reject support or parameter mutations. The Reed--Muller identities are
   sourced to Reed's paper; the finite enumeration is checked by the scripts.
3. **Quotient equivalence.** Group averaging and stabilizer-orbit lifting are
   proved in [`REED_MULLER_QUOTIENT_EQUIVALENCE.md`](REED_MULLER_QUOTIENT_EQUIVALENCE.md).
   The independent replay reconstructs scope orbits, atom orbits, row orbits,
   and all quotient coefficients. This is the boundary between the written
   theorem and executable enumeration.
4. **Base full-model certificate.** The full checker reconstructs the objective
   and matrix, checks every rational primal equality and nonnegativity, and
   runs adversarial matrix/objective mutations. Its result is the upper bound
   `opt_F(L_full) <= 31/5` (equivalently `opt_W(L_full) <= 36/5`).
5. **Affine-overlap lower bound.** The affine-overlap checker independently
   reconstructs its smaller model and dual reduced costs. The inclusion map
   from the affine-overlap model into the full model gives
   `opt_F(L_affine) <= opt_F(L_full)`. The compact six-slack identity in
   [`REED_MULLER_AFFINE_OVERLAP_DUAL_NOTE.md`](REED_MULLER_AFFINE_OVERLAP_DUAL_NOTE.md)
   explains the exact reduced lower bound `opt_F(L_affine) >= 31/5`.
6. **Exact finite conclusion.** Combining steps 4 and 5 yields
   `opt_F(L_full)=31/5` and `opt_W(L_full)=36/5`. This is a scoped finite theorem. It does not imply a
   uniform SAT algorithm, a hierarchy limit, or a P versus NP result.
7. **Integer-cut extensions.** The square constraint is replayed as an explicit
   Boolean moment identity. The later cuts are checked only for nonnegativity
   on integer weights `0..31` and are labelled integer-domain polynomial cuts.
   Each cut certificate imports the independently audited base matrix; it does
   not silently claim to rebuild a different proof system.
8. **Literature and scope.** The comparison boundary is maintained in
   [`LOCAL_MARGINAL_NOVELTY_LEDGER.md`](LOCAL_MARGINAL_NOVELTY_LEDGER.md) and
   [`REFEREE_RESPONSE_2026_10_20.md`](../REFEREE_RESPONSE_2026_10_20.md).
   The project-wide resolution standard remains in
   [`../RESOLUTION_STANDARD.md`](../RESOLUTION_STANDARD.md).

## Follow-ups recorded on 20 October 2026

**Fresh exact LP discovery.** The workflow in
[`EXACT_LP_DISCOVERY.md`](EXACT_LP_DISCOVERY.md) rebuilds the affine-overlap
equality LP from source, exports exact rational coefficients, and supplies no
saved solution, basis, or expected optimum to SoPlex. The independent checker
accepts arbitrary candidate vectors only after checking `x>=0`, `Ax=b`,
`c-A^T*y>=0`, and `c*x=b*y` exactly. A separate source-binding step reconstructs
the original quotient and compares the complete model, including its objective
offset. Thus a solver status or model hash alone is insufficient. The
[`discovery.json`](EXACT_LP_DISCOVERY/discovery.json) record reproduces reduced
`31/5` and total `36/5`; the historical discovery remains `UNRECORDED`.
This new search does not rediscover the full-model or cut certificates.

**All-dimension quadratic-family theorem.** The
[`RM(2,m)` level-eight proof](REED_MULLER_QUADRATIC_LEVEL8_THEOREM.md) establishes
reduced optimum `(2^m-1)/5` and total optimum `(2^m+4)/5` for every `m>=4`.
Its upper bound uses explicit common moments and exact pinned projection
support. Its lower bound depends on the finite six-term identity in step 5,
transported by `GL(m,2)` averaging and embeddings of selected scope spans of
dimension at most four. The finite identity and quotient-equivalence proof
remain explicit dependencies; neither the new search nor the finite scope
enumeration replaces this argument.

An independent mathematical review checked the eight-point zero-sum-triple
bound, Möbius inversion and nonnegativity, overlap consistency, the
shortened-dual projection argument, and transport of the lower bound including
`m=4`. It also checked the singleton-only scope of the redundant-parity
extension and the proposed level-nine inequality, which excludes the displayed
witness without determining the level-nine optimum. This is a review of the
written proof, not a proof-assistant certificate. Novelty remains `UNKNOWN`.

**Locality-nine follow-up.** The
[new discovery](RM2_NINE_SCOPE_DISCOVERY.md) adds an actual table on nine
coordinates and all 362 selected-flat moment equations. The independent
checker reconstructs its 284 variables and 416 rows, including all 98
cross-boundary closures, and accepts the fresh candidate at reduced seven /
total eight. Tests also derive a compact seven-term dual identity from
original atom incidences and reject changed models even after their hashes
are rebound. Neither test uses the producer to reconstruct the model.

This finite selected model supplies a lower bound for full locality nine.
A genuine pinned weight-eight codeword supplies the matching RM(2,5) upper
bound. The [family theorem](REED_MULLER_QUADRATIC_LEVEL9_THEOREM.md) separately
proves the all-dimension value using common rank moments, nonnegative Möbius
tables and exact projection support. Its proof depends explicitly on the
earlier eight-point lemma. The first single-cut mixture is retained as a
nonextendable control, rather than promoted to a full-L9 witness.

Independent mathematical review checked the lower incidence counts and the
high-rank upper argument. That review corrected the six-point Fano count:
three zero-sum quadruples, and coefficient five in the empty-mass formula.
The correction is covered by a dedicated exact regression test. These
reviews and finite controls are not mechanized proofs or novelty assessments.

The chain is intentionally not described as proof-assistant independence.
Two programs can share a mistaken definition, and a written quotient theorem
can still contain an error. The claim made here is narrower: the saved finite
certificate is replayable from the declared model with exact rational
arithmetic and with the producer's objective and matrix regenerated by the
reviewer.

**Locality-ten strict lower bound.** The
[ten-coordinate inequality](RM2_LEVEL10_CONTROL.md) is pointwise nonnegative
on every Boolean assignment of its stated scope. Symmetrization turns it into
`q-8r+28v>=0`. Combining that row with the already proved level-nine incidence
identities gives `p>=644/2849` for `m>=6`. Seven exact tests check the
1,024 Boolean assignments, rank conditions, original atom-incidence identity
and mutation controls. The written proof transports this finite geometry to
all stated dimensions. Neither a full level-ten primal witness nor its exact
optimum is supplied. The bound and the literature comparison do not establish
novelty.
