# Research checkpoint: 18 October 2026

The [latest threshold-composition phase](THRESHOLD_PHASE_REPORT.md) now records
correct SAT encodings, scalar aggregation failures, promised flat clause
gadgets, and the exact-weight query left by numerical packing. It adds 37
separately verified tests. The earlier reports below retain their historical
scope; the overall P-versus-NP question remains unresolved.

The [external status audit](EXTERNAL_STATUS_AUDIT_2026_10_18.md) checks the
official problem listing and records a recent public P=NP claim as unverified.

**Follow-up checkpoint:** the previously proposed labelled-join certificates
are now implemented and tested. The [current follow-up report](labelled_join_certified/REPORT.md)
records 51 total labelled-solver tests (37 core plus 14 follow-up), 49 exact
original-input benchmark replays, a checked sparse-U normalizer, and precise
limits on several universal encoding proposals. The report below preserves the earlier native-solver and
LP-barrier phase. P versus NP remains unresolved in both phases.

The follow-up now also contains a deterministic small-terminal solver for a
supplied same-coordinate perturbation H=B+UV. It enumerates the 2^p label
syndromes, solves each labelled T-join exactly, and replays every branch in
the original coordinates. Its saved controls replay 243 exact cases against
direct exhaustive minima; the explicit parameter and terminal-width costs
remain visible. The dense-U counting audit further excludes universal
O(log n)-label coverage for this representation language while leaving general
SAT algorithms and nonlinear encodings outside its scope.
The dense-U artifact is also replayed with independent integer arithmetic and
source-hash checks; its largest excluded budgets at n=128, 256 and 512 are
p=9, 24 and 55 after allowing every displayed row count.

The typed-merge follow-up exhaustively rejects every one-bridge Horn/affine
factorization of the positive exact-one relation across both scope orientations
and both factor assignments. Its four source-bound searches inspect 1,464,
728, 728 and 1,464 factor pairs with zero exact-one projections; the independent
replay is recorded in [BRIDGE_FACTOR_REVIEW.json](typed_merge_planner_lab/BRIDGE_FACTOR_REVIEW.json).
The subsequent two-bridge search reverses that boundary: all four orientations
contain exact-one witnesses among 37,576, 257,920, 257,920 and 37,576 pairs.
The explicit witness and independent replay are in
[TWO_BRIDGE_FACTOR_THEOREM.md](typed_merge_planner_lab/TWO_BRIDGE_FACTOR_THEOREM.md)
and [TWO_BRIDGE_FACTOR_REVIEW.json](typed_merge_planner_lab/TWO_BRIDGE_FACTOR_REVIEW.json).
The fixed gadget's primal graph preserves the original exact-one clause graph's
pathwidth up to an additive two; all 16 four-variable controls and an
independent replay satisfy the bound in
[MIXED_BRIDGE_WIDTH_THEOREM.md](typed_merge_planner_lab/MIXED_BRIDGE_WIDTH_THEOREM.md).
The relation-level frontier DP now solves those same mixed instances with
proof-producing state/transition certificates under a supplied order; its
independent replay is recorded in
[MIXED_RELATION_DP_REVIEW.json](typed_merge_planner_lab/MIXED_RELATION_DP_REVIEW.json).
The exact subset order oracle now reconstructs minimum-width orders for the
same instances and records its `O(n 2^n)` subset/transition work in
[MIXED_ORDER_DISCOVERY_REVIEW.json](typed_merge_planner_lab/MIXED_ORDER_DISCOVERY_REVIEW.json).

The typed planner now includes a supplied strong-backdoor edge. For a
backdoor of size `k`, every assignment is checked against the requested Horn
or affine closure, then solved by canonical Horn forward chaining or GF(2)
elimination. The four saved cases and direct-enumeration replay in
`typed_merge_planner_lab/BACKDOOR_RESULTS.json` and
`BACKDOOR_REVIEW.py` establish the explicit
`2^k * poly(explicit-table-size)` bound while preserving `UNKNOWN` when the
backdoor condition fails. This is parameterized evidence, not a method for
discovering small backdoors in arbitrary SAT instances.

The affine/cardinality edge now has a separate parameterized audit. A supplied
generator dimension `k` gives an exact `2^k` message enumeration, while a
supplied distance bound `d` gives an explicitly XP support enumeration. The
planner preserves the unparameterized NP-hard classification and records the
route only when its parameter is supplied. Five finite cases, including a
rank-deficient matrix and a certified distance-above-bound result, are replayed
by direct message enumeration in
`typed_merge_planner_lab/PARAMETERIZED_EDGE_REVIEW.py`.

The same planner now searches bounded recursive Horn/affine backdoor trees.
It branches only on variables in a currently non-target relation, charges every
candidate and node, and returns `UNKNOWN` when depth or node caps prevent a
complete certificate. This makes backdoor discovery executable for small
instances without presenting bounded failure as a general lower bound.

The typed planner now also composes exact primal-graph order discovery with
the generic relation frontier DP in
`typed_merge_planner_lab/adaptive_frontier.py`. Its independent replay checks
the graph, reconstructed order, every frontier transition, and direct SAT
status for sparse, contradictory, dense, mixed, and capped controls. The
charged cost is `O(n 2^n)` for order discovery plus `O(n 2^w)` frontier work
up to relation-table factors; dense scopes and cap-triggered `UNKNOWN` results
keep the exponential boundary explicit.

The new [proof-producing CDCL baseline](proof_producing_cdcl_lab/THEOREM.md)
provides an exact solver for arbitrary CNF inputs with independent first-UIP
resolution replay. SAT models are checked against the original clauses, while
UNSAT runs derive the empty clause from the level-zero conflict. Pigeonhole,
all-three-variable assignments, contradictory units, seeded random formulas,
and explicit decision caps are retained as controls. The implementation has no
polynomial bound on decisions, conflicts, learned clauses, or proof steps, so
this is a certified universal baseline rather than a P=NP algorithm.

The [proof-complexity scaling campaign](proof_complexity_scaling_lab/THEOREM.md)
now runs that baseline on ten all-assignment formulas and eight pigeonhole
formulas. Every trace is independently replayed. The all-assignment rows obey
the exact identities `decisions = 2^(n-1)-1`, `conflicts = 2^(n-1)`, and
`resolution_steps = 2^n-1` for this deterministic implementation. Because the
all-assignment input itself has `n*2^n` literal occurrences, this is not a
super-polynomial-in-input-size lower bound. The pigeonhole rows retain the
independent injection-counting proof and expose scaling inside resolution;
they do not lower-bound algorithms outside that proof system.

The [bounded-width resolution lab](resolution_width_lab/THEOREM.md) provides a
second proof-complexity lens. It computes the complete finite closure under
weakening and width-preserving resolution, replaying either an empty-clause
refutation or a no-refutation fixed point. The universe size is bounded by
`sum_{i<=w} 2^i binomial(n,i)`, so this records proof-width growth without
claiming a uniform polynomial algorithm. Its independent width sweep measures
the exact first refutation width on each uncapped control: 1 for contradictory
units, 2 for the 3-by-2 pigeonhole instance, and 3 for the three-variable
all-assignment contradiction; the satisfiable control has no refutation in the
swept range.

The [complete-graph frontier report](linear_frontier_order_lab/COMPLETE_GRAPH_FRONTIER_REPORT.md)
adds an all-order barrier for the affine residual route. The GF(2) incidence
system of `K_v` is trivially satisfiable, but at the halfway cut of every edge
order a component-count argument gives the exact minimum `lambda=s-1`, where
`binomial(s,2) >= floor(binomial(v,2)/2)`. The exact residual DP therefore
needs exponentially many classes for every order; at `v=64` the proved bound
is 35,184,372,088,832 states. The verifier now also checks the exact minimum at
every cut size for `v=4..6`, while the cutwise formula is swept through `v=64`.
The finite halfway-subset replay covers `v=4..7`. This is a
representation barrier for affine frontier enumeration, not a SAT lower bound;
Gaussian elimination still solves the family in polynomial time. Because each
variable is an edge with two endpoints, a sparse edge-list encoding has length
`Theta(v^2 log v)`, giving the same frontier bound as
`2^(Omega(sqrt(L/log L)))` in that encoding; a dense matrix encoding has
length `Theta(v^3)` and gives `2^(Omega(L^(1/3)))`.

The [semantic expander-frontier report](semantic_frontier_expander_lab/REPORT.md)
extends the frontier evidence to ordinary SAT syntax. For a bounded-degree
expander graph `G`, the monotone graph CNF `AND_(u,v) (x_u OR x_v)` has a
balanced-cut almost-induced matching whose assignments leave `2^ell` distinct
future residual functions. The saved controls independently recompute expansion
and every separating suffix witness. This is a lower bound for OBDD/frontier
compilation and semantic quotienting; it is still not a lower bound for all SAT
algorithms.

The new [Horn + affine CDCL(T) audit](horn_cdclt_lab/REPORT.md) implements a
certifying Horn propagator beside GF(2) propagation and independently replays every
certificate. Its fixed two-bridge relation projects to positive exact-one, so arbitrary
positive 1-in-3-SAT reduces to this mixed language with two fresh variables per clause.
This closes the tempting generic-portfolio shortcut; the search engine remains explicitly
exponential in the worst case. The gadget truth table, all 16 four-variable subinstances,
and complete-triple controls through ten target variables are saved in
[REVIEW.json](horn_cdclt_lab/REVIEW.json).

The follow-up CDCL(T) layer keeps those theories opaque, adds first-UIP learning, and
replays every resolution step independently. On sparse non-3-colorable controls it cuts
the deterministic search from 287 to 29 decisions and from 491 DFS nodes to 88 decisions;
the proof logs all replay successfully. These are proof-compression measurements, not a
polynomial bound, because the exact-one projection remains NP-hard. See
[CDCL_REVIEW.json](horn_cdclt_lab/CDCL_REVIEW.json).
An algebraic audit now has an all-arity proof: the affine side forces every common
operation to be affine, and the Horn side forces its support to be a singleton. Thus the
common polymorphism clone is exactly projections. The finite replay and symbolic checks are
in [POLYMORPHISM_REVIEW.json](horn_cdclt_lab/POLYMORPHISM_REVIEW.json), with the proof in
[POLYMORPHISM_THEOREM.md](horn_cdclt_lab/POLYMORPHISM_THEOREM.md).

**Neither P=NP nor P!=NP has been proved.** The strongest positive result is an
exact, certificate-producing optimizer for binary codes that admit a graph
representation after separating a low-rank set of exceptional columns. The
strongest negative result is an all-size linear integrality-gap theorem for
the relaxation containing every redundant parity check. Both have precise
limits; neither establishes a universal complexity result.

## What the solver now does

For a checked parity-check matrix H, an invertible row transform produces a
matrix whose ordinary columns have weight zero, one or two. These are graph
loops, ground edges and ordinary edges. Fixing exceptional coordinates gives
a minimum T-join on that graph. The zero-target, nonzero-word case additionally
requires a shortest nonempty cycle.

Every matching optimum is accompanied by integer vertex and odd-set duals.
The independent verifier checks all edge inequalities and equality of primal
and dual objectives. It independently rebuilds graph distances, verifies cycle
optima, reconstructs the word, and checks the original equations and target.
It therefore checks more than the returned word's feasibility.

There are two exact aggregation methods:

| Method | Parameter | Work before polynomial factors |
| --- | --- | --- |
| Fix every exceptional assignment | q exceptional coordinates | 2^q graph cases |
| Group by exceptional syndrome | p = rank of those q columns | O(q 2^p) DP work and at most 2^p+1 graph cases |

The syndrome DP emits every cost layer and minimum-weight exceptional witnesses.
The checker validates the Bellman recurrence, including a separate nonempty
zero-syndrome possibility. State, transition and graph-call limits are explicit.
An incomplete search returns `UNKNOWN`; an upper-bound witness is not promoted
to an exact answer because it happens to match a reference value.

The matrix transformation and exceptional rank are checkable in polynomial time.
Finding a useful row basis remains a separate cost. These are polynomial
algorithms on families with a supplied or polynomially discovered representation
and logarithmic exceptional rank. The rank can be linear on general inputs.

The [degree-two minimum-distance lab](degree_two_min_distance_lab/REPORT.md)
gives a separate complete boundary case for homogeneous codes: if every column
has weight at most two, the exact nonzero kernel distance is the minimum of a
shortest ordinary cycle and a shortest path joining two weight-one columns.
The solver and independent replay match exhaustive minima on six named controls
plus 96 deterministic random instances, including parallel edges, zero
columns, and a forest with no nonzero kernel.

## Structured cases and stored random cores

The family consisting of the incidence matrix of K_t plus one weight-three
column has an F7 minor, is internally 4-connected, and has pathwidth between
t-2 and t-1. Its code and dual are nongraphic and noncographic. Nevertheless,
every affine coset of the kernel code needs only two native branches.

The saved run reaches t=128, or 8,129 coordinates, with a verified homogeneous
minimum distance of three. The trellis-state lower bound is 2^126 by theorem;
that trellis was not constructed or timed. The simple distance formula and
provided representation make this a structural control, not evidence that a
random instance of comparable size is easy. See [NATIVE_RESULTS.json](NATIVE_RESULTS.json)
and the proofs in [THEORY_REVIEW.md](THEORY_REVIEW.md).

For the six existing random cores, one bounded row-basis search scored at most
30,000 candidates per instance, including initialization and restart costs.
The initial 256-branch budget completed four cases. A separately recorded
larger-budget run completes all six:

| Coordinates | Original q | Discovered q | Complete branches | Exact distance | Discovery, solving and verification |
| --- | --- | --- | --- | --- | --- |
| 18 | 9 | 3 | 8 | 3 | 0.77 s |
| 20 | 9 | 4 | 16 | 3 | 0.47 s |
| 22 | 11 | 6 | 64 | 4 | 1.43 s |
| 24 | 12 | 7 | 128 | 4 | 2.72 s |
| 26 | 13 | 9 | 512 | 4 | 10.45 s |
| 28 | 14 | 12 | 4,096 | 4 | 84.91 s |

Times combine the explicitly identified recorded discovery measurement with
fresh solving, embedded verification and an independent replay. Reference
enumeration is accounted separately in the JSON. These small distances were
already known from enumeration; the new contribution is a different verified
route, not a newly discovered answer or a claim of superior speed.

The exceptional rank equals q in these six discovered representations, so
syndrome compression alone does not improve their branch counts. A separate
equal-budget annealing attempt reduces secondary sparsity scores for n=26 but
does not reduce q or runtime; it performs worse for n=28. Both attempts remain
in [ROW_BASIS_ESCAPE_RESULTS.md](ROW_BASIS_ESCAPE_RESULTS.md), with full cost
and source provenance. No hidden seed search or global-optimality claim is used.

A separate controlled family tests the rank compression directly: complete-graph
incidence on 3p+1 vertices plus all nonzero combinations of p disjoint
weight-three vectors. All eight saved instances p=1 through 8 match a proved
closed-form affine optimum. The largest has 555 coordinates, q=255 exceptional
columns of rank p=8, and uses 256 graph cases plus 43,687 DP transitions. Its
affine optimum is four. It would have 2^255 raw exceptional assignments, a
theoretical count; the exhaustive assignment solver was not run at that size.
The supplied representation and special construction are explicit. All 72
targets for p=1 and p=2 also pass independent checks. See
[RANK_NATIVE_RESULTS.md](RANK_NATIVE_RESULTS.md), including the formula proof,
timings, all eight certificates and source hashes.

Testing all deletions of zero, one or two coordinates also finds no split into
two nontrivial components in these cores. The few splits isolate a coloop and
leave the large component. That finite failure does not establish hardness.
See [STRUCTURAL_PROBE.md](STRUCTURAL_PROBE.md). The conditioned solver's
charged-work replay additionally proves, for all 24 completed cases, that
deleted-assignment attempts plus residual transitions are at least `2^w`,
where `w` is the original supplied-order width; see the
[independent artifact](non_graphic_core_lab/CHARGED_WORK_REVIEW.json).

## Generalizations that failed rigorous checks

**Row changes cannot make the native promise universal.** At length n=2r there
are at least 2^(r^2) distinct rank-r code row spaces. The number having a row
representation with exceptional rank O(log n) is at most 2^{O(n log n)}.
Consequently no universal logarithmic-exceptional-rank theorem of this form
can hold. This excludes that representation scheme; it excludes neither
auxiliary-variable constructions nor other polynomial algorithms.

**All redundant parity checks still leave fractional answers.** A fully checked
self-dual [24,12,8] code has integer pinned optimum eight. Pin one coordinate
to one and set every other coordinate to 1/7. The point belongs to every one
of its 4,095 nonzero dual-check parity polytopes. Its objective is 30/7.
Summing 253 minimum-weight checks through the pin, with each other coordinate
appearing 77 times, proves that 30/7 is also a matching LP lower bound.
Thus the fractional optimum is exact, not a numerical approximation.

More generally, if the dual distance is delta>=3, the same construction with
other coordinates 1/(delta-1) satisfies all dual checks. A random-subspace
argument proves existence of code families with both primal and dual linear
distance, producing an Omega(n) gap. All constants and finite-length bounds
are in [ALL_DUAL_LP_THEOREM.md](ALL_DUAL_LP_THEOREM.md).

**Small exact coordinate projections do not fix this example.** Dual distance
eight makes every unconditioned projection onto at most seven coordinates a
full cube. After a one pin, every projection onto at most six other coordinates
is still a cube. Adding all those exact hulls to the all-dual LP leaves its
optimum at 30/7. This is a theorem about coordinate-hull intersections, with
finite GF(2) certificates; it is not a Sherali-Adams or Lasserre lower bound.
See [BOUNDED_PROJECTION_BARRIER.md](BOUNDED_PROJECTION_BARRIER.md).

**Degree three contains the full obstacle.** For a three-set exact-cover
incidence matrix A, the syndrome equation Ax=1 together with |x|<=|U|/3 is
equivalent to exact cover. Each column has weight three. This is a direct
NP-completeness reduction for affine decoding with a weight threshold; it
does not establish P!=NP or by itself prove homogeneous-distance hardness.

The source-bound proof and independent replay are now consolidated in
[DEGREE_THREE_REDUCTION_THEOREM.md](DEGREE_THREE_REDUCTION_THEOREM.md) and
[DEGREE_THREE_REDUCTION_REVIEW.json](DEGREE_THREE_REDUCTION_REVIEW.json). The replay
covers 256 complete tripartite families, 1,351 six-element families, and malformed-input
controls.

The compact-product algebraic route has the corresponding exact-query boundary:
positivity of one coefficient of a product of binary-exponent binomials is NP-complete.
A parsimonious X3C encoding uses `prod_i(1+z^e_i)` with carry-free base digits, and
the independent replay checks 6,561 small selections, 400 seeded families and malformed
inputs. See [COEFFICIENT_COMPLEXITY_THEOREM.md](COEFFICIENT_COMPLEXITY_THEOREM.md) and
[COEFFICIENT_COMPLEXITY_REVIEW.json](COEFFICIENT_COMPLEXITY_REVIEW.json). This rules out
that coefficient query as a generic polynomial shortcut unless P=NP; it does not prove
P!=NP or exclude other representations.

A targeted [Fourier-spectrum boundary lab](fourier_spectrum_boundary_lab/REPORT.md)
tests the narrow low-dimensional-transform premise in the recent [Vohra
Duality abstract](https://ieeexplore.ieee.org/document/11717448). Two linear-size
3-CNF families have exactly `2^n` nonzero normalized Walsh coefficients, over
the tested odd finite fields as well. The stronger cyclic family uses only `n`
variables, `4n` distinct-literal clauses, and has the unique model `1^n`;
independent truth-table transforms confirm it through `n=8`, with analytic
checks through `n=14`. Signed versions realize every point mass `delta_t` with
the same linear-size clause bound, so the family of satisfying indicators spans
the full `2^n`-dimensional function space over every field. This rules out
explicit polynomial Fourier support and any exact low-dimensional linear
state representation of the full indicators; it does not rule out algorithms
using a different or nonlinear state space and is not a P-versus-NP
separation.

The randomized escape route is now bounded by a separate all-size isolation proof.
For any nonempty solution set, a uniformly random affine hash at rank
`ceil(log2(s))+1` isolates one solution with probability at least `3/16`, by an
exact second-moment argument. The implementation and independent replay exhaust every
nonempty three-variable solution set (273 sets), verify pairwise hash uniformity, and
replay 700 seeded cases. This gives a conditional SAT-to-unique-SAT-with-XOR bridge;
it still requires a polynomial unique solver and is not a P=NP result. See
[RANDOMIZED_ISOLATION_THEOREM.md](RANDOMIZED_ISOLATION_THEOREM.md) and
[RANDOMIZED_ISOLATION_REVIEW.json](RANDOMIZED_ISOLATION_REVIEW.json).

The homogeneous-code branch is now cross-checked against Vardy's primary
minimum-distance theorem. That established result concerns nonzero kernel words
and is separate from the project's nonzero-syndrome, column-weight-three reduction;
it also explicitly leaves bounded-distance decoding open. The scope audit is in
[VARDY_MINIMUM_DISTANCE_SCOPE.md](VARDY_MINIMUM_DISTANCE_SCOPE.md), so the reports
do not silently promote affine hardness into a stronger sparse homogeneous claim.

A new literature audit records a stronger current source for exactly that sparse
homogeneous regime. Jia, Peng, Liu, Wang and Yan's 2026 arXiv preprint states
NP-completeness for `MinDistance_3`, where every variable node (equivalently,
every parity-check column) has degree exactly three, and for
`MinDistance_(3,3)`, where both sides of the Tanner graph are 3-regular. The
scope, lower-degree boundary and preprint status are recorded in
[REGULAR_LDPC_MINIMUM_DISTANCE_SCOPE.md](REGULAR_LDPC_MINIMUM_DISTANCE_SCOPE.md).
An independent finite replay exhausts the three local gadgets on 490 randomized
families, then adds 314 exhaustive decomposition families and 445 exhaustive
padding families; it also checks 152 composed mapped supports. Its limits are explicit in
[REGULAR_LDPC_LOCAL_AUDIT_REPORT.md](REGULAR_LDPC_LOCAL_AUDIT_REPORT.md). The
replay now includes 314 exhaustive decomposition families and 445 exhaustive
padding families, in addition to the randomized and composed checks; it remains
a source audit rather than an independent formalization of the paper's all-size
reduction. A second replay reconstructs the full `(3,3)` completion on two
small inputs and 12 fresh seeded structural cases, including the degree, weight,
and suffix lower-bound invariants. Neither replay separates P from NP.

The companion [size-bound report](REGULAR_LDPC_SIZE_BOUND_REPORT.md) checks the
exact threshold and output-size formulas over 36,464 first-phase rows and
104,544 suffix rows (`1 <= n <= 32`), confirming polynomial resource growth
without treating that accounting as a complexity-class separation.

**Homogeneous and conditioned tractability differ.** Ordinary cut-code minimum
nonzero weight is a graph cut problem, but an all-ones affine shift computes
|E|-MaxCut(G). Even fixing a matching of cut coordinates to one can encode
MaxCut. Likewise, ZERO/ONE-valid Boolean relations need not remain tractable
under arbitrary boundary pins. The typed planner now explicitly uses the
pin-preserving signatures when extension queries are required.

**Symbolic projection size also needs accounting.** An elementary Horn family
has a polynomial representation with auxiliaries but needs 2^m clauses after
eliminating them into an auxiliary-free CNF. This does not make Horn SAT hard;
keeping the auxiliaries preserves its polynomial solving route.

## Evidence and practical limits

The current frozen integration run passes **370 tests across 36 suites**, with
unchanged source hashes throughout. The canonical audit now includes the
51-test labelled-join and perturbation certificate suite in
`labelled_join_certified`. [TEST_SUMMARY.json](TEST_SUMMARY.json) and
[TEST_OUTPUT.txt](TEST_OUTPUT.txt) preserve the counts, timings and full output.
A separate saved-artifact audit confirms all 22 recorded source/input hashes
checked across the four native experiment reports. The tests include independent brute-force optimization,
exhaustive tiny matrices and affine targets, invertible basis changes, malformed
certificates, budget boundaries, disconnected graphs, loops and parallel edges.
The exact LP certificates use integers and fractions, without a floating-point
solver. Saved old all-cut certificates were read, not regenerated.

These tests support implementation correctness on the stated finite sets.
The all-size claims rest on the written arguments, which have received
independent mathematical review but are not proof-assistant formalizations.
The NetworkX matching producer currently uses a version-sensitive observer;
its independent checker is the authority for accepted optimality evidence.

## What remains worth trying

The next constructive class is a **supplied general rank perturbation**
H=B+UV. Setting z=Vx yields Bx=s+Uz together with the mandatory condition Vx=z.
Discarding that second condition is false, and postchecking only the cheapest
ordinary T-join can miss the true optimum. A disconnected cycle can be needed
to correct the parity label. This is a different problem from disjoint
exceptional coordinates.

Known parity-join methods and a deterministic small-terminal route
are scoped in [PERTURBATION_ROUTE_REVIEW.md](PERTURBATION_ROUTE_REVIEW.md).
The isolated [labelled-join design](LABELLED_JOIN_DESIGN.md) now has a direct
proof and eight small exhaustive/adversarial prototype tests: lifted graph
walks plus a separate label-space closure handle disconnected cycle corrections.
It has not been promoted into the certificate-producing solver. Its proposed
optimality certificates still need implementation and independent checking.
An actual implementation must account for every parity state and certify
optimality, not merely produce a valid labelled edge set. Even success would
give another parameterized class; universal polynomial coverage remains a
separate, unproved requirement.

For the polyhedral direction, the demonstrated gap requires constraints
beyond all single parity checks and the small projections proved redundant
above. A useful candidate must have both an integrality argument and a
polynomial-time separation method. Naming the exact convex hull, or adding
exponentially many inequalities without a separator, supplies neither.

The [adaptive fragment synthesis report](ADAPTIVE_FRAGMENT_SYNTHESIS_REPORT.md)
records an independent bounded implementation that cross-checks the existing
proof-language discovery step.
It projects small CNF fragments onto shared variables, discovers exact
unit/XOR/PB/ITE candidates, and includes an explicit table fallback. Its
separate checker replays seven serialized examples, including existential local
projection and a mutated XOR, while budget and clique-coloring controls return
`UNKNOWN` past their caps. The work is charged as `2^(shared+local)` assignment
checks times the fragment size plus the fixed vocabulary's separate `2^shared`
candidate evaluations, so this is a finite research instrument rather than a
hidden general SAT procedure.

The [proof-DAG bridge report](PROOF_PORTFOLIO_BRIDGE_REPORT.md) then wires the
independent bounded projector into the real mixed-theory proof. It extracts
eight positive unit sub-DAGs from a 65-node refutation, projects each onto its
representative, and independently certifies the resulting unit relations before
forming the parity interpolant. Four integration tests and a separate checker
pass; the clique-coloring control remains `UNKNOWN` beyond the boundary cap.
At the larger 256-group, width-eight scale it processes 4,097 proof nodes and
256 unit sub-DAGs, retaining the 256-literal raw interpolant while passing the
symbolic parity check.
The small serialized certificate also replays all 65 resolution nodes to the
empty clause independently.
An unlabelled scan of 42 proof nodes with boundary arity at most two found
eight unit and eight PB relations, 24 table-only relations, and two `UNKNOWN`
cases.

The [residual-equivalence barrier report](RESIDUAL_EQUIVALENCE_BARRIER_REPORT.md)
adds a source-bound coNP-hardness reduction for exact future-state quotienting.
Even a one-bit frontier can hide an arbitrary CNF suffix: the two residuals of
`G(y) AND NOT z` are equal iff `G` is unsatisfiable. This is a conditional
complexity barrier for universal quotient discovery, not a P-versus-NP proof.

The [certified residual quotient report](CERTIFIED_RESIDUAL_QUOTIENT_REPORT.md)
adds the safe operational contract: merge only by syntax, bounded exhaustive
comparison, or bidirectional resolution certificates; accept a one-assignment
separation witness; and return `UNKNOWN` otherwise. Its six tests and separate
proof checker pass, including forged-certificate rejection.

The [repeated sub-DAG template report](REPEATED_SUBDAG_TEMPLATES_REPORT.md)
extends the bridge without using group metadata. A label-free scan of 42
small-boundary nodes finds 16 compact relations, 24 table-only relations, and
two `UNKNOWN` cases. Boundary-position canonicalization exposes three repeated
templates with counts 24, 8 and 8. Projection work remains charged for every
occurrence; only the fixed candidate search is reused, with independent replay
of every serialized record and a forged-candidate rejection control.
The full records also include a 4,097-node scale replay: 2,306 considered
nodes, 256 compact PB relations, 1,792 table-only relations, and 258 explicit
`UNKNOWN` outcomes, including 256 local-projection-cap failures.
The serialized cap sweep at local width 7 recovers 256 unit templates and
reduces the `UNKNOWN` count to the two sub-DAG-cap cases; both scans are
independently replayed.

The [symbolic unit-template report](SYMBOLIC_UNIT_TEMPLATE_REPORT.md) then
adds a structural macro for this specific pattern. It recognizes the
Hall-plus-implication fragment and emits a 513-node resolution certificate at
width 256, avoiding exhaustive `2^256` projection. The separate tests include
the actual width-eight proof fragment, a near miss, and forged-certificate
rejection. This is a scoped rule rather than general macro discovery.

The [symbolic suffix-template report](SYMBOLIC_SUFFIX_TEMPLATE_REPORT.md)
checks the two remaining sub-DAG-cap nodes as the final suffixes of the fused
negative B clause. It replays each reachable resolution node, verifies the
exact Hall-family leaf set for every resolved prefix unit, and supplies an
extension argument for the projected negative suffix. The small and scale
checks reject altered pivots, clauses, and candidate bounds.

The [macro-assisted scan report](MACRO_ASSISTED_SUBDAG_REPORT.md) now combines
both certified rules in the actual 4,097-node scan. It recovers 256 unit
relations and both suffix relations that the generic caps marked `UNKNOWN`,
leaving 1,792 table-only relations and no UNKNOWN records in this scoped scan.
The pre-macro audit still records 256 projection-cap and two sub-DAG-cap
`UNKNOWN` cases, and symbolic work is charged independently per occurrence.

The [projection-discovery barrier report](PROJECTION_DISCOVERY_BARRIER_REPORT.md)
separates the existential step from residual equivalence. For
`F(z,y)=G(y) AND NOT z`, exact projection onto the one-bit boundary is either
`UNIT_Z_FALSE` when `G` is satisfiable or `EMPTY` when `G` is unsatisfiable.
Thus a universal exact projection classifier would decide SAT and UNSAT even
with boundary width one. The 256-formula replay finds 95 versus 161 cases and
rejects forged relation records independently.

The [quadratic-length trace-family report](row_basis_exact_oracle_lab/QUADRATIC_CODE_FAMILY_REPORT.md)
strengthens the separate binary row-basis obstruction. Setting
`q=2^k`, `t=floor(q/(2k))` and `r=kt` gives `n=q(q-1)<16r^2` distinct trace
columns, while the Reed--Solomon root bound gives distance above the complete
weight-at-most-two budget. Therefore the exceptional columns have rank `r` in
every row basis and this route needs at least `2^r=2^(Omega(sqrt(n)))` states.
Here `n` counts columns; an explicit `r`-bit-column encoding has length
`L=Theta(nr)=Theta(r^3)`, so the bit-level statement is
`2^(Omega(L^(1/3)))`, still superpolynomial. The saved cases `k=4..7`, the formula sweep through `k=12`, all sampled basis
replays and a forged-record control pass an independent verifier. This remains
a route-specific state lower bound, not a P-versus-NP separation.

The ultimate goal remains active. These findings sharpen the question and
remove incorrect shortcuts; they do not answer P versus NP.
