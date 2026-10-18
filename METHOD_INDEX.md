# Method index and research ledger

This ledger maps each implemented direction to its current evidence and
scope. “Proved” means proved for the stated family. It never means that P=NP
or P≠NP has been proved.

| Direction | Status | Evidence and write-up |
| --- | --- | --- |
| Degree-two homogeneous minimum distance | Proved for column weight at most two | [`degree_two_min_distance_lab/REPORT.md`](degree_two_min_distance_lab/REPORT.md), exact shortest-cycle/path reduction, certificate checker, independent brute-force replay. |
| Affine/XOR grouping and partition compression | Proved for the stated explicit representations | `affine_grouping_plan_lab/THEOREM.md`, `affine_partition_compression_lab/THEOREM.md`, and the linked phase reports in the root `README.md`. Discovery caps and UNKNOWN cases are explicit. |
| Complete one-piece affine recognition | Proved as a bounded exact recognizer | [`affine_one_piece_lab/THEOREM.md`](affine_one_piece_lab/THEOREM.md); it recognizes the supplied representation language and does not solve arbitrary SAT. |
| Graph-plus-exception and labelled-join solvers | Proved for supplied structural inputs | [`labelled_join_certified/REPORT.md`](labelled_join_certified/REPORT.md) and the linked certificate checkers. Exponential state/terminal costs remain part of the bound. |
| Degree-three affine/X3C coefficient route | Scoped boundary result | [`ALGEBRAIC_PHASE_REPORT.md`](ALGEBRAIC_PHASE_REPORT.md) and [`COEFFICIENT_COMPLEXITY_REPORT.md`](COEFFICIENT_COMPLEXITY_REPORT.md); coefficient extraction retains the hard part and does not yield a general polynomial algorithm. |
| Randomized isolation and SAT/XOR wiring | Proved hash-isolation moments; unresolved unique-SAT step | [`RANDOMIZED_ISOLATION_REPORT.md`](RANDOMIZED_ISOLATION_REPORT.md). The missing step is recorded rather than inferred. |
| Threshold and algebraic composition | Boundary audit | [`THRESHOLD_PHASE_REPORT.md`](THRESHOLD_PHASE_REPORT.md) and [`ALGEBRAIC_PHASE_REPORT.md`](ALGEBRAIC_PHASE_REPORT.md); exact constructions preserve the representation or certificate costs. |
| Regular LDPC minimum distance | Literature boundary plus finite replay | [`REGULAR_LDPC_MINIMUM_DISTANCE_SCOPE.md`](REGULAR_LDPC_MINIMUM_DISTANCE_SCOPE.md) and [`REGULAR_LDPC_SIZE_BOUND_REPORT.md`](REGULAR_LDPC_SIZE_BOUND_REPORT.md). The cited preprint's all-size theorem remains separate from the local replay. |
| Fourier/Walsh low-dimensional state | Refuted for the specified universal linear representation | [`fourier_spectrum_boundary_lab/REPORT.md`](fourier_spectrum_boundary_lab/REPORT.md); a linear-size distinct-literal family has exponentially many nonzero modes, and the cyclic unique-model family supplies every point mass, spanning the full `2^n`-dimensional function space. |
| Holographic simultaneous basis | Refuted for the tested product-type and common-basis targets | [`simultaneous_basis_lab/THEOREM.md`](simultaneous_basis_lab/THEOREM.md), with independent certificate replay. The result is a scoped tensor obstruction, not a complexity lower bound. |
| Matchgate parity and crossing controls | Proved for the checked identities | [`HOLOGRAPHIC_PHASE_REPORT.md`](HOLOGRAPHIC_PHASE_REPORT.md), exact rational checks and independent mutations. |
| Compact weighted-boundary marginalization | Proved for supplied affine-support/quadratic-phase summaries | [`weighted_boundary_lab/THEOREM.md`](weighted_boundary_lab/THEOREM.md), elimination certificates, direct small-instance oracle, and mutation controls. This does not provide a compact representation for arbitrary CNF sums. |
| Recent public Vohra P=NP claim | Unverified | [`EXTERNAL_STATUS_AUDIT_2026_10_18.md`](EXTERNAL_STATUS_AUDIT_2026_10_18.md) and [`VOHRA_CROSSREF_METADATA.json`](VOHRA_CROSSREF_METADATA.json). Public metadata and abstract were checked; the full proof and bit-complexity argument were not accessible. |
| Adaptive frontier SAT solver | Proved for bounded order discovery | [`typed_merge_planner_lab/ADAPTIVE_FRONTIER_THEOREM.md`](typed_merge_planner_lab/ADAPTIVE_FRONTIER_THEOREM.md), replayable primal-graph/order/frontier certificates, and explicit order/state caps. |
| General proof-producing CDCL | Proved for finite CNF runs | [`proof_producing_cdcl_lab/THEOREM.md`](proof_producing_cdcl_lab/THEOREM.md), independently replayed first-UIP resolution traces, checked SAT models, and explicit resource caps. |
| Proof-complexity scaling campaign | Proved for the stated finite families and solver traces | [`proof_complexity_scaling_lab/THEOREM.md`](proof_complexity_scaling_lab/THEOREM.md) and [`proof_complexity_scaling_lab/SCALING_REPORT.md`](proof_complexity_scaling_lab/SCALING_REPORT.md), with independent family reconstruction, proof replay, and exact all-assignment trace identities. |
| Proof/frontier complexity comparison | Proved for the stated finite rows and supplied order | [`proof_complexity_frontier_lab/THEOREM.md`](proof_complexity_frontier_lab/THEOREM.md) and [`proof_complexity_frontier_lab/FRONTIER_REPORT.md`](proof_complexity_frontier_lab/FRONTIER_REPORT.md), with independent boundary/state replay, exact all-assignment identities, and the pigeonhole h^2 frontier-width check. |
| Bounded-width resolution closure | Proved for the stated width-bounded proof system | [`resolution_width_lab/THEOREM.md`](resolution_width_lab/THEOREM.md), complete weakening/resolution closure with replayable refutations and explicit clause/step caps. |

## Evidence vocabulary

The meanings of proved, finite exhaustive audit, certificate-verified, measured,
unresolved, and refuted are fixed in [`RESOLUTION_STANDARD.md`](RESOLUTION_STANDARD.md).
New entries must use those labels and state the exact input promise, output
certificate, size bound, and independent replay.

## Open next steps

The project still needs either a uniform deterministic polynomial-time algorithm
for all SAT instances with a complete bit-complexity proof, or an unconditional
lower bound ruling out every such algorithm. None of the current scoped results
meets either requirement.
