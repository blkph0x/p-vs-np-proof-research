# P versus NP: exact native solvers and audited obstructions

> **Repository status — 18 October 2026.** P versus NP remains unresolved. This
> repository contains exact algorithms for explicitly bounded or promised
> families, finite certificates, reproducible experiments, and scoped barriers
> against proposed generalizations. It does not claim a solver for all SAT and
> it does not claim a P-versus-NP lower bound.

## Start here

- Read [`RESOLUTION_STANDARD.md`](RESOLUTION_STANDARD.md) for the acceptance
  criteria and evidence labels used throughout the project.
- Use [`METHOD_INDEX.md`](METHOD_INDEX.md) to find every current method,
  theorem, boundary result, and its write-up.
- Use [`CITATIONS.md`](CITATIONS.md) and [`PUBLIC_SOURCES.md`](PUBLIC_SOURCES.md)
  for public sources and the reports that use them.
- Follow [`REPRODUCIBILITY.md`](REPRODUCIBILITY.md) to replay the checks from a
  fresh checkout. The current frozen run has 364 passing methods across 35
  suites; the full audit is intentionally separate from the lighter continuous
  integration checks, and all of its suite dependencies are included in this
  repository.
- The latest external status check is
  [`EXTERNAL_STATUS_AUDIT_2026_10_18.md`](EXTERNAL_STATUS_AUDIT_2026_10_18.md).

Changes that alter a result must update the relevant theorem/report, saved
artifact, independent checker, source citation, and the repository manifest in
the same change. A public claim is recorded as unresolved until its full proof
and bit-complexity argument pass the standard above.

This is the active 18 October 2026 research increment. **P versus NP remains
unresolved.** The work delivers exact algorithms for stated structural classes,
finite certificates, and proofs excluding specific proposed generalizations.
It does not provide a polynomial algorithm for all SAT instances or a lower
bound against every polynomial algorithm.

The time-stamped [external status audit](EXTERNAL_STATUS_AUDIT_2026_10_18.md)
checks current public claims against the official problem status and keeps an
unverified recent P=NP claim separate from the project's proof evidence.

Start with the [grouping and global recognition report](AFFINE_RECOGNITION_PHASE_REPORT.md):
verified grouping brings the stress set to 19/22 exact original counts, recovering
all eight shuffled parity failures. The earlier 58 requests still yield 54 exact
counts. The independent grouping audit replays all 80 requests and 73 completed
proofs. Global partition recognition and the implemented complete one-piece
recognizer target the separate greedy-order limitation. The latter's 494 saved
requests retain 276 exact representations, 210 certified rejections and eight
UNKNOWNs, separately from the SAT solver. The
new three-suite run passes 25 tests; independent review adds 543 original sums
and 84 rejected proof/source mutations. The final provenance audit binds
180 recorded references across 135 files. The
[bounded integration report](AFFINE_RECOGNITION_INTEGRATION_REPORT.md) records
the optional fast-recognition adapter inside the affine DAG. Its fixed-policy
run preserves 11/22 and 54/58 exact coverage, makes no one-piece replacements,
and increases work on the 80-formula comparison; the result is independently
audited. The positive-cover and cancellation limits are recorded in
[AFFINE_CANCELLATION_LITERATURE_SCOPE.md](AFFINE_CANCELLATION_LITERATURE_SCOPE.md).
The [affine compression report](AFFINE_COMPRESSION_PHASE_REPORT.md) retains
54 new tests, unchanged 54/58 coverage on earlier original requests, and 11/22
exact additional stress counts versus the baseline's 2/22. Grouped parity gains,
all shuffled failures, greedy nonconfluence, and the restricted scope of a
representation-counting bound remain explicit. The
[decision audit](COUNTING_VS_DECISION_AUDIT.json) separately supplies short
SAT witnesses or a unit contradiction for all four earlier counting failures.
The [compact boundary report](AFFINE_BOUNDARY_PHASE_REPORT.md) retains
46 new tests, independent symbolic boundary checks, and 54/58 exact original-CNF
counts. The four cap failures and the separate reference's 58/58 results remain
explicit. The [holographic report](HOLOGRAPHIC_PHASE_REPORT.md) retains exact
basis changes, a certified affine evaluator, signed crossing controls and
53 new tests. Its simultaneous-basis theorem now also excludes the common
product-type target: EQ3 support forces a diagonal or anti-diagonal basis, and
both OR3 and SLACK3 remain non-product-type. The [algebraic coefficient report](ALGEBRAIC_PHASE_REPORT.md)
retains the preceding exact query algorithms and their 44 tests.
The [coefficient complexity report](COEFFICIENT_COMPLEXITY_REPORT.md) adds a
parsimonious, bit-accounted X3C reduction for the target coefficient of a compact
binomial product, with an independent replay. The [randomized isolation report](RANDOMIZED_ISOLATION_REPORT.md)
adds an all-size second-moment proof for affine hash isolation and exact SAT/XOR wiring controls;
it records the missing unique-SAT step explicitly. The [threshold-composition report](THRESHOLD_PHASE_REPORT.md) preserves
the complete encodings that motivated those queries.
The [regular-LDPC scope audit](REGULAR_LDPC_MINIMUM_DISTANCE_SCOPE.md) records
a current primary preprint's NP-completeness result for homogeneous minimum
distance with every parity-check column of weight three, and for fully (3,3)-regular
Tanner graphs. This closes the sparse homogeneous literature gap while keeping
the source's preprint status and the separate bounded-distance question explicit.
Its local-gadget replay exhausts 490 finite families plus 152 mapped supports,
41 of the composed outputs are enumerated completely, and a separate `(3,3)`
completion replay checks two full small constructions plus 12 fresh seeded
structural completions;
the exact threshold and output-size formulas are independently checked in
[REGULAR_LDPC_SIZE_BOUND_REPORT.md](REGULAR_LDPC_SIZE_BOUND_REPORT.md);
the all-size claim remains tied to the paper's written proof. The replay now
includes 314 exhaustive decomposition families and 445 exhaustive padding
families, in addition to the randomized checks.
The Fourier boundary integration adds seven independently verified tests,
including a separate truth-table/Walsh verifier and a unique-model cyclic
finite fields. Signed versions of the same gadget realize every point-mass
indicator, giving an exact `2^n`-dimensional linear-span barrier.
The new [degree-two minimum-distance report](degree_two_min_distance_lab/REPORT.md)
closes the tractable side constructively: column weight at most two reduces to
shortest cycles and terminal-to-terminal paths, with exact certificates and an
independent brute-force replay.
The [Fourier-spectrum boundary lab](fourier_spectrum_boundary_lab/REPORT.md)
also gives precise counterfamilies to any universal explicit low-dimensional
Walsh/Fourier representation: even a linear-size, distinct-literal 3-CNF with
a unique satisfying assignment can have `2^n` nonzero modes, confirmed by an
independent transform on small instances.
The [labelled-graph report](labelled_join_certified/REPORT.md) records the
previous certified solver and encoding audits. Its new same-coordinate
perturbation extension replays 243 exact small controls for supplied H=B+UV
instances, while retaining explicit 2^p and terminal-width costs. A separate
dense-U count now rules out universal logarithmic-label coverage for that
representation language as well; its integer artifact has an independent
replay and source-hash check.
[REPORT.md](REPORT.md)
retains the first overnight phase. The
[acceptance standard](RESOLUTION_STANDARD.md) specifies what would count as an
actual resolution. Historical matrices and earlier labs are in the parent tree.

## Positive algorithms

- [affine_grouping_plan_lab](affine_grouping_plan_lab/THEOREM.md): verified
  occurrence-preserving XOR3 clause grouping, with every original factor retained.
- [affine_partition_compression_lab](affine_partition_compression_lab/THEOREM.md):
  whole-partition recognition through affine coverage and quadratic phase fitting.
- [affine_one_piece_lab](affine_one_piece_lab/THEOREM.md): complete one-piece
  recognition for explicit rational sums, including overlap and cancellation,
  with exact equality or nonmembership certificates and explicit resource caps.
- [affine_fast_recognition_lab](affine_fast_recognition_lab/INDEPENDENT_REVIEW.md):
  source-bound cheap obstructions followed by the complete recognizer, with
  explicit fallback accounting and UNKNOWN semantics.
- [globally_compressed_affine_dag_lab](AFFINE_RECOGNITION_INTEGRATION_REPORT.md):
  bounded post-greedy integration of recognition, preserving original factors
  and recording its negative 80-formula comparison.
- [affine_sum_compression_lab](affine_sum_compression_lab/THEOREM.md) and
  [compressed_affine_dag_lab](compressed_affine_dag_lab/THEOREM.md): source-bound
  sum identities and original-factor contraction with aggregate discovery caps.
- [affine_compression_review](affine_compression_review/REVIEW.md): independent
  squared-norm equalities, source mutations and an explicit greedy-order trap.
- [affine_compression_stress_lab](affine_compression_stress_lab/THEOREM.md):
  complete original parity/pigeonhole controls with independent count proofs.
- [affine_boundary_lab](affine_boundary_lab/THEOREM.md) and
  [affine_boundary_reference](affine_boundary_reference/THEOREM.md): compact
  signed marginals by independently structured one-bit and block methods.
- [weighted_affine_dag_lab](weighted_affine_dag_lab/THEOREM.md): fully source-bound
  weighted sums of compact pieces, with explicit pre-merge costs and UNKNOWN caps.
- [original_count_reference_lab](original_count_reference_lab/THEOREM.md): an
  explicitly exponential counting reference preserving all original free variables.
- [holographic_tractability_lab](holographic_tractability_lab/THEOREM.md):
  supplied-basis real-affine recognition and exact global signed evaluation.
- [tensor_basis_lab](tensor_basis_lab/THEOREM.md): exact original-formula
  transformations with bounded full-contraction certificates.
- [crossing_sign_lab](crossing_sign_lab/THEOREM.md): rational Pfaffian
  certificates and explicit controls separating signed sums from witness counts.
- [coefficient_structure_lab](coefficient_structure_lab/THEOREM.md): certified
  exact coefficient counting through the original clause interaction structure.
- [interval_coefficient_lab](interval_coefficient_lab/THEOREM.md): exact support
  intervals with independent recurrence proofs and explicit fragmentation controls.
- [coefficient_isolation_lab](coefficient_isolation_lab/THEOREM.md): exact integer
  digits, checked field filters, and coefficient bounds with honest bit costs.
- [coefficient_residue_lab](coefficient_residue_lab/THEOREM.md): counted sparse
  and cyclic layers, original witnesses, and separate/common-residue controls.

- [labelled_join_certified](labelled_join_certified/README.md): independently
  checked labelled shortest-path and Eulerian tables, terminal-subset DP,
  complete original-coordinate pinning, sparse-U normalization, and a
  source-checked small-terminal H=B+UV perturbation extension.

- [native_coset_solver.py](native_coset_solver.py): bounded exceptional-coordinate
  branching followed by exact graph T-joins or shortest nonempty cycles.
- [matching_certificate.py](matching_certificate.py): independent integer
  matching-dual certificate checker, used for each T-join optimum.
- [rank_native_solver.py](rank_native_solver.py): group exceptional assignments
  by syndrome, with exact DP recurrence evidence and original-code witnesses.
- [row_basis_discovery.py](row_basis_discovery.py): bounded heuristic discovery
  of useful representations; every returned transform is independently checked.
- [row_basis_escape.py](row_basis_escape.py): a separately recorded attempt to
  escape local optima; its failed attempts count toward total discovery work.

## Proofs and counterexamples

- [Complete one-piece recognition design](AFFINE_ONE_PIECE_RECOGNITION_DESIGN.md)
  and [independent mathematical review](AFFINE_ONE_PIECE_RECOGNITION_REVIEW.md):
  exact restricted norms recover the true support hull of an explicit signed
  sum and determine its only possible single-piece representation.
- [affine_sum_capacity_lab](affine_sum_capacity_lab/THEOREM.md): exact dictionary
  size and a counting bound for arbitrary Boolean truth functions. It does not
  establish a succinct CNF lower bound or resolve P versus NP.
- [simultaneous_basis_lab](simultaneous_basis_lab/THEOREM.md): exact complex-field
  obstruction for common EQ3/OR3 and EQ3/slack matchgate-parity bases, with
  explicit polynomial identities and genuine positive graph controls. The same
  EQ3 classification now covers every rational symmetric ternary clause: only
  four palindromic/anti-palindromic families can share the parity basis. On
  degree-three equality/OR3 and equality/slack incidence networks, independent
  per-edge 2x2 gauges are also excluded by all eight flip cases, each with a
  finite support-mask proof and Ã‚Â±4 identity.
- [THEORY_REVIEW.md](THEORY_REVIEW.md): native algorithms, a nonregular internally
  4-connected family with growing width, and representation-counting limits.
- [ALL_DUAL_LP_THEOREM.md](ALL_DUAL_LP_THEOREM.md): exact Golay LP gap and a
  probabilistic existence proof of linear integrality gaps.
- [BOUNDED_PROJECTION_BARRIER.md](BOUNDED_PROJECTION_BARRIER.md): limits of exact
  local coordinate projections, including their combination with all dual checks.
- [DEGREE_THREE_REDUCTION_THEOREM.md](DEGREE_THREE_REDUCTION_THEOREM.md): a complete
  X3C reduction to nonzero-syndrome binary decoding with every column of weight three,
  with an independent source-bound replay.
- [INDEPENDENT_AUDIT.md](INDEPENDENT_AUDIT.md): pinning obstruction, Horn projection
  size, and degree-three exact-cover reduction.
- [COEFFICIENT_COMPLEXITY_THEOREM.md](COEFFICIENT_COMPLEXITY_THEOREM.md): parsimonious
  X3C reduction to a compact binary-exponent coefficient query, with bit accounting.
- [RANDOMIZED_ISOLATION_THEOREM.md](RANDOMIZED_ISOLATION_THEOREM.md): a self-contained
  constant-probability affine isolation proof and independent exhaustive replay.
- [VARDY_MINIMUM_DISTANCE_SCOPE.md](VARDY_MINIMUM_DISTANCE_SCOPE.md): primary-source
  scope audit separating homogeneous minimum distance from affine decoding and bounded-distance decoding.
- [REGULAR_LDPC_MINIMUM_DISTANCE_SCOPE.md](REGULAR_LDPC_MINIMUM_DISTANCE_SCOPE.md): current
  primary-preprint scope audit for column-weight-three and (3,3)-regular homogeneous
  minimum-distance NP-completeness.
- [REGULAR_LDPC_LOCAL_AUDIT_REPORT.md](REGULAR_LDPC_LOCAL_AUDIT_REPORT.md): independent
  finite replay of the paper's decomposition, padding, replication and `(3,3)`
  completion gadgets.
- [PERTURBATION_ROUTE_REVIEW.md](PERTURBATION_ROUTE_REVIEW.md): exceptional rank
  versus general graph perturbations and the coupled parity constraints.
- [LABELLED_JOIN_DESIGN.md](LABELLED_JOIN_DESIGN.md): next-stage zero/two-terminal
  prototype, isolated from the core solver pending optimality-certificate work.
- [LABELLED_JOIN_REVIEW.md](LABELLED_JOIN_REVIEW.md): independent proof review,
  including disconnected corrections, loop-aware pinning and bit complexity.
- [REVIEW_ADDENDUM.md](REVIEW_ADDENDUM.md): independent follow-up review.

The labelled-join design's proposed certificates are now implemented in the
new subdirectory. Its 51 tests (37 core plus 14 follow-up) and 49 benchmark
requests are saved separately from this phase's 140-test run. Follow-up proofs and experiments cover
[syndrome projections](projection_limits/THEOREM.md),
[linear objective maps](objective_pullback_limits/THEOREM.md),
[minimum-cut gadgets](gadget_limits/THEOREM.md), and
[matching gadget composition](matching_gadget_limits/THEOREM.md).
The [odd-NOT-cycle control](matching_composition_controls/THEOREM.md) supplies
an explicit global false positive for naive wiring of promised-domain gadgets.

The sibling [typed-merge planner](typed_merge_planner_lab/REPORT.md) now
also exhausts the one-bridge Horn/affine factorization pattern for positive
exact-one and rejects all four finite orientations. Its two-bridge follow-up
finds exact-one witnesses in all four orientations, proving a sharp local
bridge-budget boundary and a fixed mixed Horn+affine NP-hardness reduction.
The companion primal-width audit shows that this local gadget preserves the
original clause-graph pathwidth within two. A proof-producing relation-level
frontier DP and independent certificate replay now cover the same reductions
under supplied orders. An exact subset order oracle reconstructs optimal orders
and preserves its exponential discovery cost in the saved evidence.

The typed planner now also has a supplied strong-backdoor route. For a
backdoor of size `k`, the proof-producing solver enumerates `2^k` assignments,
checks every residual relation, and uses native Horn forward chaining or GF(2)
elimination. Its saved SAT, UNSAT, and conservative `UNKNOWN` cases are
independently replayed in `typed_merge_planner_lab/BACKDOOR_REVIEW.py`; finding
such a backdoor for arbitrary SAT remains outside the claim.

The affine/cardinality planner edge now has two explicit parameterized
routes: exact `2^k` message enumeration for a supplied code dimension and an
XP support search for a supplied distance bound. The unparameterized pair
remains labeled NP-hard; the saved certificates distinguish exact witnesses
from certified above-bound outcomes.

The mixed Horn/affine route now also searches bounded recursive backdoor trees.
It records candidate variables, branch work, and explicit depth/node caps;
failed bounded discovery remains `UNKNOWN` rather than a hardness claim.

The typed planner now also has an adaptive frontier solver that composes exact
primal-graph order discovery with the relation-level dynamic program. Its
bounded controls replay every order and frontier certificate, while dense
scopes and explicit caps retain the exponential discovery/state costs. See
[`typed_merge_planner_lab/ADAPTIVE_FRONTIER_THEOREM.md`](typed_merge_planner_lab/ADAPTIVE_FRONTIER_THEOREM.md).

The repository now also contains a universal proof-producing CNF baseline in
[`proof_producing_cdcl_lab`](proof_producing_cdcl_lab/README.md). It records
first-UIP resolution chains for UNSAT results, checks models for SAT results,
and returns `UNKNOWN` under explicit decision, conflict, or proof-size caps.
Its proof traces establish finite-run correctness but do not supply a
polynomial worst-case bound.

The [bounded-width resolution lab](resolution_width_lab/README.md) separately
closes every weakening and resolution consequence up to width `w`. A fixed
point without the empty clause is a finite certificate that this proof system
has no width-`w` refutation; width and closure caps remain explicit. Its
independent width sweep records the first refutation width on each uncapped
control, rather than treating a single chosen width as a universal claim.

The companion [horn_cdclt_lab](horn_cdclt_lab/REPORT.md) turns that reduction into a
proof-producing Horn-plus-GF(2) portfolio. Its independent replay verifies every emitted
certificate and confirms the exact-one projection on the full truth table. This is a
complexity barrier for the generic portfolio route, not a P=NP result.

Its follow-up CDCL(T) extension adds replayable first-UIP resolution proofs. The saved
3-coloring controls show substantial search compression while retaining the exact-one
hardness barrier; see [CDCL_REVIEW.json](horn_cdclt_lab/CDCL_REVIEW.json).
The same lab's finite polymorphism audit finds only projections common to the fixed
relations through arity four; this is recorded in [POLYMORPHISM_REVIEW.json](horn_cdclt_lab/POLYMORPHISM_REVIEW.json).

The next phase adds [scalar threshold controls](threshold_composition_lab/THEOREM.md),
[promised clause saturation](saturated_clause_limits/THEOREM.md),
[simultaneous-bound matching](multiobjective_matching_limits/THEOREM.md), and
[exact binary-weight packing](packed_cost_exact_matching/THEOREM.md).
Its separate 37-test run is `run_threshold_phase_checks.py`; saved evidence
replays with `verify_threshold_artifacts.py`.
Run `python run_followup_audits.py` for their separate test transcript.

The algebraic phase runs with `python run_algebraic_phase_checks.py` and
`python verify_algebraic_artifacts.py`. The original-input method comparison
is reproduced by `python run_algebraic_crosscheck.py`. Its 34 exact counts
include six cases that exceeded interval limits. This is finite evidence.

The holographic phase runs with `python run_holographic_phase_checks.py`,
`python run_holographic_crosscheck.py` and `python verify_holographic_artifacts.py`.
Its 240 requests retain the same original formulas in both count modes and
three bases; the affine method resolves no additional capped SAT requests in
that batch. The [next review](AFFINE_DECOMPOSITION_NEXT_REVIEW.md) investigates
complete affine decompositions and their full discovery/evaluation cost.
The reuse audit also led to a [historical certificate repair](SEMANTIC_CERTIFICATE_REPAIR.md):
complete original-clause coverage and decomposition ownership are now checked,
with a separate passing 16-test suite and independent adversarial review.

The compact-boundary phase runs with `python run_affine_boundary_phase_checks.py`
and `python verify_affine_boundary_artifacts.py`. The following sum-compression
phase runs with `python run_affine_compression_phase_checks.py` and
`python verify_affine_compression_artifacts.py`. Original comparisons use
`python run_affine_compression_crosscheck.py` and
`python affine_compression_stress_lab/run_experiments.py`. The separate direct
decision probe runs with `python counting_vs_decision_audit.py`; its bounded
witness search remains potentially exponential and its UNSAT evidence is
restricted to unit contradictions.

The grouping and global-recognition phase runs with
`python run_affine_recognition_phase_checks.py` and
`python verify_affine_recognition_artifacts.py`. The latter binds the independent
proof-replay records, source hashes and all grouping artifacts; its scope is
explicitly recorded. [The next brief](AFFINE_RECOGNITION_NEXT.md) proposes cheap
rejection witnesses and a separately measured optional solver integration.

## Reproduction

Python 3.10.10 and the existing NetworkX 3.2.1 installation were used. Existing
SymPy 1.14.0 supports supplementary symbolic checks in the holographic phase;
its principal certificate verifiers use the standard library. No packages were
installed or environment settings changed for this increment. The matching
producer observes private NetworkX return-state details, so another version
may require an adapter; unsupported extraction fails closed. The checker does
not trust that adapter's optimality claim.

From this folder:

```powershell
python run_research_checks.py
python run_native_experiments.py
python row_basis_discovery.py
python row_basis_escape.py
python run_rank_experiments.py
python all_dual_lp_barrier.py
python projection_barrier.py
```

The test runner writes `TEST_OUTPUT.txt` and `TEST_SUMMARY.json`, with source
hashes and independent subprocess results. The experiment scripts write their
named result files and preserve matrices, parameters, costs, and certificates.
The row-basis experiment retains incomplete `UNKNOWN` cases; the separate
escape/full-budget experiment records what changes when more work is allowed.
These scripts do not rerun the historical exponential all-cut audits.

The large-family trellis bounds come from proofs, not actual huge trellis
enumerations. Written mathematical proofs were independently reviewed; they
have not been formalized in a proof assistant. No novelty claims are made.

The next factorized-structure experiment is in
`affine_character_factor_lab`. It applies an exact character expansion to
disjoint original factor blocks coupled by a supplied affine system. The
global-parity controls remain exact through 128 blocks at rank one, and the
component-aware refinement splits 128 independent local parities into rank-one
pieces. A connected cumulative parity chain remains one rank-`m` component and
hits an explicit UNKNOWN cap. Its 23 saved rows, 13 component controls and
independent review preserve the distinction between compact factorization and
a general SAT algorithm. The weighted-DAG cross-check in
`affine_character_factor_lab/ELIMINATION_REPORT.md` solves the connected chain
through 128 blocks under an interleaved order with peak retained terms three;
the same factors in a poor order reach their cap.

The bounded order-discovery controls find and verify width-three chain orders
through 128 blocks, certify NO for complete/cycle graphs at too-small widths,
and preserve UNKNOWN for a deliberately capped search. They do not claim a
polynomial minimum-width algorithm.

The automatic route now composes discovery, weighted solving and independent
replay in one bounded API. It returns exact certificates for the chain,
certified NO for narrow-width controls, and UNKNOWN for capped discovery; no
non-exact status is converted to a SAT value.

The separate `connected_affine_cover_lab` proves an all-size lower bound for
nonnegative affine-support decompositions of a connected path CNF. Exhaustive
coset checks through six variables and independent recurrence checks through
256 variables give a minimum of 1,090,151,200,392,118 pieces at n=256. Signed
cancellation and general SAT algorithms remain outside that theorem. Its
weighted-DAG escape control independently solves the same path family for
n=8,16,32,64,128 with peak retained message size four, making the theorem's
representation scope explicit.

The new `mixed_information_frontier_lab` makes the quotient question explicit
for mixed constraints. It independently replays six exact cut analyses:
duplicate parity collapses 64 nominal states to 2, same-scope cardinality plus
parity collapses 14 to 7, while six independent crossing parities force all 64
future-equivalence classes. A partial-scope cardinality/parity bundle retains
all ten reachable mixed summaries. The oracle is exponential by design and is
a structural control, not a general SAT algorithm.

The same lab records an all-size reduction showing that exact equality of two
arbitrary-CNF residual frontiers is coNP-hard: for
$F(z,y)=G(y)\land\lnot z$, the residuals at $z=0$ and $z=1$ are equal exactly
when $G$ is unsatisfiable. This scopes the quotient program without claiming a
P-versus-NP separation.

The reduction proof and exhaustive selector controls are in
`mixed_information_frontier_lab/EQUIVALENCE_HARDNESS.md`.

The `linear_frontier_order_lab` adds an exact GF(2) rank-width order
certificate. On six crossing parity pairs, the supplied block order has width 6
and the independently replayed interleaving has width 1; repeated-row and
identity controls give widths 1 and 0. The optimizer is explicitly exponential.
The [complete-graph frontier certificate](linear_frontier_order_lab/COMPLETE_GRAPH_FRONTIER_REPORT.md)
proves a stronger all-order statement for the incidence system of `K_v`: every
edge order has a halfway cut with linear residual rank, even though the system
is trivially satisfiable. The saved replay exhausts halfway cuts through `v=7`,
all cut sizes through `v=6`, and checks the exact cutwise formula through
`v=64` (45 halfway bits, 35,184,372,088,832 states).
The `graph_order_hardness_lab` maps a graph to the always-satisfiable monotone
2-CNF consisting of one $(x_u\lor x_v)$ clause per edge. Its active-variable
boundary is vertex separation, so minimum order discovery inherits the known
pathwidth/vertex-separation NP-completeness; the saved star control changes from
width 7 to width 1 under reordering.
Its $K_{4,2}$ control defeats the local min-boundary greedy policy (width 4
versus exact width 2), with the all-size $K_{m,2}$ gap recorded in the theorem.

The `semantic_frontier_expander_lab` upgrades this structural warning to a
semantic residual lower bound. Its almost-induced matching certificate gives
`2^ell` pairwise distinct residual functions for bounded-degree expander graph
CNFs, so exact quotienting cannot merge them. Expansion, productive pairs, and
all finite residual-separation witnesses are independently replayed on four
3-regular controls.

The `variable_boundary_sat_lab` is the corresponding conditional solver: with a
supplied variable order it records and replays every frontier state and
transition. It reaches 64-variable SAT and UNSAT chains at width 1, while a
star order changes width 11 to width 1 without changing the answer.

The `primal_order_sat_lab` now composes the two missing pieces on small inputs:
it builds a CNF primal graph, searches exactly for a minimum-boundary order by
subset DP, and sends that order to the proof-producing SAT solver. Five cases
are exact and an explicitly capped 12-variable complete-graph search returns
`UNKNOWN`; an independent scope-based replay checks both the order certificate
and the SAT answer. This makes the exponential order-discovery cost visible.
The variable-boundary lab also carries a dense-redundancy adversary: six
equality-pair sizes are replayed with and without tautological clauses, with the
largest raw state set growing to 766 while the normalized system stays at 25.

The `row_basis_exact_oracle_lab` attacks the binary-code representation gap
directly. It enumerates every invertible row basis through rank four and
independently compares the result with bounded local descent; the retained
rank-three trap has exact objective $(1,1,31)$ and local objective $(2,2,33)$.
Its rank-tradeoff matrix has a count/rank choice $(2,2)$ versus $(4,1)$, so
exception count is not a proxy for the native solver's state exponent.
The saved native certificates make the consequence concrete: the count-first
basis uses four syndrome states, the rank-first basis two, and both return exact
distance two.
The new rank-aware descent recovers the rank-one representation on this control
and reproduces the two-state native certificate, but remains a bounded heuristic
with no global-optimality claim.

The companion probabilistic bound gives a broader route-specific obstruction:
for every `r >= 6`, a union-bound construction has `n=16r^2+r` columns and
forces exceptional rank `r` for every row basis, so the native syndrome DP must
retain at least `2^r` states. Exact rational replay checks ranks 6, 7, 8, 16
and 32. This is an existence theorem for the representation route, not an
explicit hard family or a P-versus-NP separation.

The projective-family control reaches arbitrary rank by symmetry rather than
enumeration: all nonzero vectors of `F_2^r` are used as columns, so every row
basis merely permutes them. Exact replay through rank 12 gives 4,095 columns
and 4,096 native states at rank 12. This family is polynomial in its encoded
column count and is retained as a high-rank sanity control, not a hardness
claim.

The separate `rank5_exact.cpp` extension goes one rank higher without hiding the
group cost: it exhaustively visits all 9,999,360 elements of `GL(5,2)` on four
fixed inputs, and `rank5_driver.py` replays both objectives with Python
arithmetic. Its first input repeats the downstream tradeoff at rank five: the
count-first basis has two exceptional columns of rank two, the rank-first basis
has four exceptional columns of rank one, and the native certificates use four
versus two states at the same distance two. `RANK5_REVIEW.py` independently
replays the saved native certificates. This remains finite evidence; rank six
and universal basis discovery are open.

The deterministic trace/Reed--Solomon family removes the existence-only
qualification for this route. At `k=7,8,9` it gives ranks 14, 32 and 54 with
16,256; 65,280; and 261,632 distinct columns, while forcing state counts
`2^14`, `2^32` and `2^54` under every row basis. The distance and distinctness
proofs are explicit, and the saved review exhausts all 16,383 degree-one
messages at `k=7`.

The companion [quadratic-length trace-family report](row_basis_exact_oracle_lab/QUADRATIC_CODE_FAMILY_REPORT.md)
uses `t=floor(2^k/(2k))` instead. Its rank satisfies `2^k/4 <= r <= 2^k/2`
and its `n=2^k(2^k-1)` columns obey `n<16r^2`, so the same distance argument
forces `2^r=2^(Omega(sqrt(n)))` syndrome states for this route. Cases `k=4..7`
and a formula sweep through `k=12` are independently replayed. Here `n` is a
column count; an explicit list of `r`-bit columns has bit length
`Theta(nr)=Theta(r^3)`, giving the still-superpolynomial bit-level form
`2^(Omega(L^(1/3)))`. This is a stronger representation-specific obstruction,
not a P-versus-NP result.

The natural generator map from free message bits to these codewords is also
audited. Direct three-assignment additivity defects are 8,192, 32,768 and
131,072 for `k=7,8,9`, so no fixed unary cost on free message variables equals
the codeword Hamming weight. This does not address constrained or nonlinear
objective maps.

The linear-weight signature theorem strengthens the objective audit. Walsh
character independence says exact homogeneous nonnegative additive costs can
agree only when every nonzero linear form has the same aggregate weight. The
explicit families have one distinct form per column, so any exact linear lift
needs at least 16,256; 65,280; or 261,632 positive rows in the three saved
cases. The companion affine signature theorem allows offsets and signed
weights: the constant Fourier term and every nonzero character still have to
match, so the same families require at least 16,256; 65,280; or 261,632
nonzero rows. Nonlinear maps and threshold-only encodings remain separate
questions. The nonlinear compression control makes that boundary concrete:
binary digits of the source Hamming weight reproduce the exact objective with
14, 16 or 18 arbitrary nonlinear rows, while evaluation still contains the
source-form computation. The companion circuit control realizes the same map
with XOR/AND ripple circuits of 553,152; 3,069,184; and 16,223,488 gates.
The circuit-to-CNF audit pins all 32 assignments in a seven-form control,
replays exact SAT certificates for the correct outputs, rejects wrong outputs,
and records frontier width 11 under the topological order.
For a three-form subcase, exact subset-DP order discovery reduces width 6 to 4
after 262,144 subset states, so finding a good order is not free.
The unpinned distance control then proves minimum nonzero weight four for all
seven nonzero three-bit forms, rejecting thresholds 0--3 and accepting 4.
The threshold comparison uses a compact ripple circuit rather than listing all
forbidden output words.

The [circuit-order audit](circuit_order_hardness_lab/THEOREM.md) adds a
structural lower-bound control. For any small graph it emits pinned OR-gate
Tseitin clauses, which are satisfied by the all-ones assignment, while the
source graph is a primal subgraph. Exact subset searches and an independent
replay verify that source pathwidth lower-bounds the complete circuit width;
the constructive extension is within one width unit, and the measured
gate-variable gap is retained as a separate cost.

The [local-marginal code barrier](local_marginal_code_lab/THEOREM.md) adds a
lifted consistency control with exact scope marginals. The dual-distance
argument leaves the unit-vector witness feasible through level `delta-2`; the
even-parity case rejects the boundary level, and the Golay case has level 6
versus pinned optimum 8. This is scoped to the explicit relaxation rather than
being presented as a universal hierarchy or P-versus-NP result.
Its asymptotic probabilistic extension uses exact union bounds to obtain
half-rate random codes with both distances at least `n/16`, leaving a local
witness through level `n/16-2`; lengths 32 through 1024 are replayed. This
does not claim a deterministic family or a general complexity lower bound.

The [adaptive fragment synthesis report](ADAPTIVE_FRAGMENT_SYNTHESIS_REPORT.md)
adds an independent cross-check of the bounded proof-language experiment. A bounded projector existentially
eliminates local variables, discovers exact unit/XOR/PB/ITE relations from a
residual CNF fragment, and keeps an explicit truth-table fallback. Eleven tests
and a separate checker pass; support, assignment, mutation, and clique-coloring
controls return either a finite fallback or `UNKNOWN` when their caps are
exceeded. The result is a finite candidate-discovery step, not a general SAT
algorithm or a P-versus-NP resolution.

The [proof-DAG bridge report](PROOF_PORTFOLIO_BRIDGE_REPORT.md) connects that
independent projector to the actual mixed-theory resolution proof. It extracts
eight positive unit sub-DAGs from a 65-node refutation, invents and certifies each
one-variable relation, and combines them into the receiver-checked parity
interpolant. Four integration tests and a separate replay pass; the same
clique-coloring boundary returns `UNKNOWN`. The same bridge processes the
4,097-node, 256-group proof with 256 certified unit fragments and a passing
symbolic receiver check. The independent replay also reconstructs every node of
the serialized 65-node resolution refutation.
An unlabelled scan of 42 small-boundary proof nodes found eight unit, eight PB,
24 table-only and two `UNKNOWN` relations.

The [residual-equivalence barrier report](RESIDUAL_EQUIVALENCE_BARRIER_REPORT.md)
formalizes the next limitation: for arbitrary `G(y)`, the one-bit-boundary
formula `G(y) AND NOT z` has equivalent `z=0` and `z=1` residuals exactly when
`G` is UNSAT. All 256 two-variable formulas replay independently, while the
source-bound reduction explains why exact quotient discovery cannot be assumed
polynomial in general.

The [certified residual quotient report](CERTIFIED_RESIDUAL_QUOTIENT_REPORT.md)
implements the sound fallback: syntactic, bounded-exact, or replayable-proof
merges; witness-certified distinctions; and explicit `UNKNOWN` otherwise. Six
tests and a separate resolution checker pass, including forged-certificate
rejection and an eight-variable case
that remains `UNKNOWN` past a 16-assignment cap.

The [repeated sub-DAG template report](REPEATED_SUBDAG_TEMPLATES_REPORT.md)
removes the known group labels from the proof scan. It finds 42 small-boundary
nodes, three canonical repeated templates with occurrence counts 24, 8 and 8,
and two explicit `UNKNOWN` nodes. Every occurrence still pays exact projection
work; only fixed candidate-vocabulary search is amortized, and an independent
checker rejects a forged candidate. The same serialized replay at 4,097 proof
nodes considers 2,306 nodes and retains 258 explicit `UNKNOWN` outcomes when
the local or sub-DAG caps are exceeded. Raising the local cap from 6 to 7
recovers all 256 unit templates, leaving only the two sub-DAG-cap `UNKNOWN`
cases; both cap settings are independently replayed.

The [symbolic unit-template report](SYMBOLIC_UNIT_TEMPLATE_REPORT.md) adds a
structural escape for this exact family. A Hall clause plus its implication
clauses is recognized directly and certified by a linear-size resolution proof;
the width-256 instance uses 513 certificate nodes instead of enumerating
`2^256` projections. A near miss and forged proof are rejected, and the rule is
replayed on an actual width-eight proof fragment.

The [symbolic suffix-template report](SYMBOLIC_SUFFIX_TEMPLATE_REPORT.md)
checks the two remaining sub-DAG-cap nodes as the final suffixes of the fused
negative B clause. It replays each reachable resolution node, checks the exact
unit leaf sets, and gives an extension argument for the projected suffix. The
scale instances require 4,065 and 4,081 reachable-node checks and avoid local
truth-table enumeration.

The [macro-assisted scan report](MACRO_ASSISTED_SUBDAG_REPORT.md) feeds both
rules into the real 4,097-node scan. It recovers all 256 unit fragments and
both suffix fragments that the generic caps marked `UNKNOWN`, leaving 1,792
table-only relations and no UNKNOWN records in this scoped scan. Symbolic work
is charged separately for every occurrence and the pre-macro cap outcomes are
retained in the artifact.
