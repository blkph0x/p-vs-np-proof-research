# Next research decisions

The active goal remains a rigorous answer to P versus NP. A finite solver
improvement is an intermediate result. The current report and acceptance
standard must accompany any claim of progress.

## Completed directions to retain as controls

1. Exact coordinate conditioning, native T-joins, matching-dual certificates,
   and exceptional-syndrome compression are implemented with explicit budgets.
2. The six archived random cores have exact native certificates. Their known
   distances are not new discoveries, and the largest route has exponential
   branching. Do not spend another campaign merely reproducing those distances.
3. Both row-basis heuristics retain all measured attempts. A local optimum and
   a failed escape are not impossibility certificates for a better basis.
4. F7 minors, internal 4-connectivity and large width are insufficient hardness
   criteria, even together, as the explicit near-graphic family shows.
5. Counting rules out universal logarithmic exceptional rank under row changes
   alone. Do not continue searching for a theorem already excluded by that proof.
6. Adding every redundant parity inequality is not exact. On the Golay control,
   exact projections through the proved small sizes do not strengthen it either.

## Completed follow-up: certified labelled joins

The zero/two-terminal primitive, disconnected corrections, nonempty edge pins,
and original-matrix reconstruction are implemented in `labelled_join_certified`.
An arbitrary-terminal subset DP replaces explicit pairing enumeration; it is
still exponential in terminal count. Supplied sparse-U perturbations now have
a checked graph-contraction normalizer using rank(U) label rows. The frozen
solver passes 37 tests and 49 independently replayed benchmark cases.

The coverage proof rules out universal O(log n) label rank on the same
coordinates and even after free linear existential auxiliaries. Arbitrary
linear decoding changes the objective; the new objective audit characterizes
exactly when a map from free inputs preserves nonnegative additive costs.
Do not restart a search for these disproved universal representations.

## Next candidate must specify composition and objective

A nonlinear or restricted-domain encoding is not excluded by the linear
obstruction. It is also not a construction until its full composition is
proved. Matching parity gadgets exist, and some gadgets copy correctly only
on a promised encoded domain. Their extra boundary states can invalidate a
global reduction. Require an explicit domain-enforcement and wiring rule;
testing only the promised local truth table is insufficient.

For a concrete candidate, enumerate every small global assignment, including
invalid encoded states, auxiliary choices, and assignments that decode to
zero. Check exact threshold equivalence in both directions. Count the graph
size, all label rows, target terminals and construction work against the
original input size. Any claim that validity filters compose independently
must come with an actual graph construction and proof.

The matching audit distinguishes feasibility, zero or global-minimum support,
and an arbitrary threshold. Ordinary exchange can fail for threshold support;
a weaker two-sided law still excludes exact paired copy and AND at every
cutoff. The odd-NOT-cycle control exposes invalid half-selected encodings in
naive promised-gadget wiring. Preserve these distinctions rather than upgrading
a restricted obstruction into an impossibility theorem for all reductions.

The threshold-aggregation controls in `NEXT_RESEARCH_BRIEF.md` are now checked
in `THRESHOLD_PHASE_REPORT.md`: flat promised OR is constructible, separate
cost bounds encode SAT exactly but define a hard problem, and numerical
packing produces exact binary-weight matching rather than ordinary minimum
matching. Its 37 new tests and saved evidence pass independent review.

The candidate in `NEXT_ALGEBRAIC_BRIEF.md` is now investigated in
`ALGEBRAIC_PHASE_REPORT.md`. Exact interval and clause-factor compression,
integer-digit extraction, and checked modular filters pass 44 new tests.
The clause method resolves six interval UNKNOWN cases on identical original
SAT encodings. Separate modular witnesses, characteristic cancellation and
exponential numerical sizes remain explicitly bounded in scope.

`NEXT_HOLOGRAPHIC_BRIEF.md` is now investigated in `HOLOGRAPHIC_PHASE_REPORT.md`.
Exact basis invariance, supplied-basis real-affine evaluation and rational
Pfaffian certificates pass 53 tests. Exact algebra excludes common complex
EQ3/OR3 and EQ3/slack matchgate-parity bases, and a new case split excludes the
common product-type target as well. Signed crossing cancellation is explicitly
verified. The 40-formula SAT comparison gives no additional solved
capped cases for the affine method; preserve that negative result.

`AFFINE_DECOMPOSITION_NEXT_REVIEW.md` and `AFFINE_BOUNDARY_DESIGN.md` are now
implemented and tested in `AFFINE_BOUNDARY_PHASE_REPORT.md`. The two compact
boundary implementations, source-bound weighted DAG, and original-count
reference pass 46 tests. All 96 saved production marginals also agree symbolically
with an independent block method. The weighted DAG gives 54/58 exact original
counts and four UNKNOWNs; the separate exponential reference gives 58/58.
Preserve that comparison and the exact planted counts 64/680.

`AFFINE_SUM_COMPRESSION_NEXT.md` is now implemented and independently reviewed
in `AFFINE_COMPRESSION_PHASE_REPORT.md`, with 54 passing tests. The same 58
requests remain at 54 EXACT and four UNKNOWN; compression records more work
on 44 of the 54 shared exact requests. The additional original stress set
improves from two to 11 exact counts, including all eight grouped parity
controls. All eight shuffled counterparts still fail. Preserve both results.

Those experiments are now implemented in `AFFINE_RECOGNITION_PHASE_REPORT.md`.
Checked grouping improves the same stress set to 19/22 exact counts, recovering
all eight shuffled failures without losing a certified answer. The earlier
58 requests remain 54 EXACT and four counting UNKNOWNs. Both the disjoint
partition recognizer and a complete recognizer for arbitrary explicit signed
sums are independently reviewed; the new combined suites pass 25 tests.
The stronger recognizer has 276 exact representations, 210 certified one-piece
rejections and eight UNKNOWNs among 494 saved requests. It is polynomial in
the explicit piece list and dimension, not an unexpanded CNF formula.

`AFFINE_RECOGNITION_NEXT.md` proposes cheap rejection certificates and an
optional, separately measured solver integration. The five-to-two control
proves that even complete whole-sum recognition cannot discover every useful
proper subgroup: the greedy output has five pieces and its exact minimum is
two. A whole-sum rejection is correct but supplies no such regrouping.
Preserve all charged failed attempts and the distinction between mathematical
obstructions and resource-limited UNKNOWNs.

The bounded integration is now implemented in
`globally_compressed_affine_dag_lab`. Its predeclared policy runs the fast
negative probe and complete explicit-sum fallback only after greedy output.
The fixed original-order comparison preserves 11/22 and 54/58 exact coverage,
with no exact recognizer replacements and 3,453 verified rejections across
3,509 attempts. It supplies a reproducible negative result, not a solver
improvement. The adapter's 30 tests, fast wrapper's nine tests and the 80-row
comparison audit all pass. Further work must address representation growth;
tuning this optional stage cannot resolve P versus NP.

`affine_sum_capacity_lab/THEOREM.md` proves that some arbitrary Boolean truth
functions need exponentially many pieces in this language. Its input-length
and succinctness limitation is essential: it does not prove the same for
polynomial-size CNF, every decomposition plan, or every SAT algorithm.

Exact counting is stronger than the SAT decision target. The separate
`COUNTING_VS_DECISION_AUDIT.json` supplies direct original witnesses for three
of the four retained counting failures and a unit contradiction for the fourth.
The bounded witness search is still potentially exponential. Do not use the
counting failures as evidence that these instances are difficult to decide.

The factorized affine-character experiment is now in
`affine_character_factor_lab`. It preserves disjoint original factor ownership
and evaluates affine coupling before assignment expansion. Rank-one global
parity stays exact through 128 blocks. A component-aware replay splits the
independent local-parity case into rank-one components; a connected cumulative
chain exposes the `2^r` character cost and reaches a charged UNKNOWN cap. The
next question is whether a richer quotient can compress high connected affine
rank while charging all character discovery and pre-merge work.
The audited weighted-DAG cross-check gives a complementary control: an
interleaved order solves the same connected chain through 128 blocks with peak
retained terms three, while a poor order reaches its work cap. Future work must
separate order discovery from the cost of using a supplied order.
The new bounded order-discovery certificate makes that separation executable:
it proves width-three chain orders, rejects complete/cycle graphs under narrow
caps, and returns UNKNOWN on a state-limited path search. The next challenge is
to make discovery scale or to prove a broader structural quotient without
silently assuming a favorable order.
The automatic route now composes the bounded discovery certificate with the
weighted solver and its independent replay. It proves exact chain values,
certified width failures, and honest capped UNKNOWNs through one interface.
The unresolved question is still the worst-case discovery/width bound on
arbitrary SAT inputs.

The compact-product coefficient route now has an all-size complexity boundary:
the target coefficient of a product of binary-exponent binomials is NP-complete
to test for positivity, even for `prod_i(1+z^e_i)` encodings from X3C. The
parsimonious proof includes polynomial bit accounting and an independent replay.
Future algebraic work must therefore provide a different exact query or a
general structural promise; storing the product itself is not enough.

The randomized isolation route is also source-bound: affine hashing isolates a
single member of any nonempty solution set with probability at least `3/16` at
the correct rank, but the reduction stops at unique-SAT with XOR constraints.
The exact small-set replay and independent seeded controls pass; finding a
polynomial unique solver remains the unresolved step.

The sparse homogeneous coding gap now has a current literature reference. A
2026 arXiv preprint proves NP-completeness of minimum distance for constant
column weight three and for fully `(3,3)`-regular Tanner graphs, with polynomial
even-cover transformations. This strengthens the unrestricted Vardy reference
for the exact sparse promise. Finite replays cover the local gadgets and two
full `(3,3)` completion cases, but they remain source audits rather than a
formalized independent proof; the result also does not imply `P != NP`. See
`REGULAR_LDPC_MINIMUM_DISTANCE_SCOPE.md`.

The new degree-two solver supplies the complementary positive boundary: every
column-weight-at-most-two homogeneous instance is solved exactly by shortest
cycles and terminal paths, with exhaustive certificate replay. Thus the sparse
parity transition is explicit in the checkpoint: degree two is polynomial,
while degree three is the first hard regime in the cited literature.

The Fourier-spectrum boundary lab audits a separate claimed shortcut. Linear-size
3-CNF families have 2^n nonzero Walsh coefficients, including a
distinct-literal family with a unique satisfying assignment. Signed versions
realize every point mass, so the satisfying indicators span the full 2^n
dimensional function space. Closed forms and independent truth-table replays
over the rationals and odd prime fields make the boundary exact. Any future
Fourier or FWHT route must therefore provide a different compressed invariant;
explicit low-dimensional support or an exact low-dimensional linear state is
not universal.

The connected path-cover theorem supplies a new falsifiable barrier for one
positive affine representation language: the lower bound is exponential even
on a connected linear-size CNF, while the CNF remains recurrence-easy. The next
step is to determine whether a comparably strong statement survives signed
cancellation or richer native factors; no such extension is assumed. The
independent weighted-DAG crosscheck now solves the same path family through
128 variables with peak retained message size four, so the cover lower bound
is explicitly scoped to nonnegative affine supports.

The mixed-information frontier experiment then tests the broader quotient idea
on parity, cardinality and OR bundles. Its exact oracle and independent replay
show both sides of the issue: duplicated or semantically dependent constraints
collapse exponentially many nominal products, while six independent crossing
parities force all 64 residual classes. The next requirement is a polynomially
discoverable quotient certificate for arbitrary mixed bundles; the oracle itself
is deliberately exponential.

The same lab gives a scope theorem for arbitrary CNF: with
`F(z,y)=G(y) AND NOT z`, residual equality at the cut after `z` is equivalent
to unsatisfiability of `G`. Exact complete frontier minimization therefore
contains a coNP-hard subproblem. This does not settle P versus NP, but it
prevents a universal quotient-discovery step from being assumed polynomial.

The affine frontier-order follow-up makes the linear part executable: an exact
subset DP produces cut-rank certificates and an independent replay. A six-pair
crossing system separates width 6 under a bad block order from width 1 under an
interleaving. The DP is a bounded oracle; scalable order discovery and mixed
non-affine width remain open.
The complete-graph incidence follow-up removes the favorable-order escape for
this affine route. At the halfway cut of every edge order on `K_v`, the
component argument gives the exact minimum `lambda=s-1`; the stronger cutwise
formula is now replayed for every cut size through `v=6` and swept through
`v=64`. The system is still solved by Gaussian elimination, so this remains a
representation lower bound rather than a P-versus-NP result.
The graph-order hardness lab formalizes the structural side: mapping each graph
edge to a monotone 2-CNF clause gives an always-satisfiable formula whose active
past boundary is exactly vertex separation. The exact controls and independent
replay show the star's width 7 versus 1 order gap. Known pathwidth/vertex-
separation NP-completeness means a universal minimum-boundary discovery claim
would itself need a new theorem.
The same lab's $K_{4,2}$ replay rejects a local min-boundary greedy rule (width
4 versus exact width 2); the $K_{m,2}$ construction gives an unbounded ratio
for that policy.
The semantic expander-frontier follow-up now charges future-function equality
itself: an almost-induced matching across the balanced cut yields `2^ell`
distinct residual functions for the monotone graph CNF. Exact expansion and
separation replays cover four bounded-degree controls; the asymptotic expander
family remains an external graph-theory input, and the result still scopes
OBDD/frontier compilation rather than arbitrary SAT algorithms.

The variable-boundary SAT lab closes the conditional algorithmic loop: a supplied
order yields an exact DP with at most $2^w$ frontier states per cut, and every
state and transition is independently replayed. It solves 64-variable SAT and
UNSAT chains at width 1. The missing universal step is still order discovery
and mixed-theory compression.
The new primal-order SAT lab composes order discovery with that solver on small
CNFs: exact subset DP finds a minimum-boundary order, the SAT certificate is
then generated, and a separate scope-based implementation replays both. Five
cases are exact while a capped 12-variable search returns `UNKNOWN`, preserving
the exponential cost instead of hiding it behind a success status.
The accompanying redundancy adversary shows why preprocessing must be charged:
tautological clauses raise the raw state count to 766 on the largest control,
whereas removing them leaves the same equality function at 25 states. This is a
representation warning, not a semantic hardness result.
The binary-code row-basis oracle now makes the corresponding discovery cost
executable: all $GL(r,2)$ transforms are checked through rank four, while a
rank-three instance separates the exact objective $(1,1,31)$ from a bounded
local-descent objective $(2,2,33)$. A separate C++ oracle exhausts all
9,999,360 rank-five transforms on four fixed inputs and is independently
replayed; rank six and universal discovery remain open.
The same oracle finds a downstream-parameter tradeoff $(q,p)=(2,2)$ versus
$(4,1)$, showing that exception count is not sufficient to optimize syndrome
state complexity.
The downstream native certificates use four syndrome states for the count-first
basis and two for the rank-first basis, while agreeing on exact distance two.
Rank-aware local descent now recovers the rank-one basis on that control; its
certificate explicitly makes no global-optimality claim.

The exceptional-rank bound is now recorded as an asymptotic route-specific
obstruction. For every `r >= 6`, exact union-bound arithmetic proves existence
of a full-rank matrix with `16r^2+r` columns whose exceptional columns have
rank `r` under every basis, forcing `2^r` native states. The construction is
probabilistic rather than an explicit P-versus-NP lower bound.
The all-nonzero-column projective family supplies a separate exact control at
arbitrary rank: row changes only permute its columns, and rank 12 already
forces 4,096 states on 4,095 columns. Its state count is linear in its input
length, so it validates the formulas without supplying hardness.
The explicit trace/Reed--Solomon family now supplies deterministic instances:
for `k=7,8,9` it forces ranks 14, 32 and 54 and state counts `2^14`, `2^32`
and `2^54`. Its distance and coordinate-distinctness arguments turn the
probabilistic obstruction into an infinite family with
`2^(Omega(sqrt(n)/log n))` state growth for this route.
The new quadratic-length variant sets `t=floor(q/(2k))`, giving
`q/4 <= r <= q/2` and `n=q(q-1)<16r^2`. Its distance exceeds the full
weight-at-most-two budget for every `k>=4`, so it forces
`2^(Omega(sqrt(n)))` states under every row basis. The finite cases `k=4..7`
and formula sweep through `k=12` are independently replayed in
`row_basis_exact_oracle_lab/QUADRATIC_CODE_FAMILY_REPORT.md`. The exponent uses
column count `n`; with an explicit `r`-bit-column encoding of length
`L=Theta(nr)=Theta(r^3)`, the bit-level form is `2^(Omega(L^(1/3)))`, still
superpolynomial.
The natural free-message generator escape is separately rejected on the same
family: three-assignment additivity defects are 8,192, 32,768 and 131,072 for
`k=7,8,9`. Constrained or nonlinear objective preservation remains open.
The linear-weight signature theorem broadens this check to every homogeneous
linear map with nonnegative additive costs when the full objective must be
preserved. Walsh-character independence forces one aggregate signature weight
per nonzero target form; the explicit families therefore require at least
16,256, 65,280 and 261,632 positive cost-bearing rows. Affine, signed,
nonlinear and threshold-only encodings remain outside that homogeneous scope.
The affine extension now allows offsets and signed weights as well: matching
the constant and nonzero Walsh coefficients still forces at least the same
16,256, 65,280 and 261,632 nonzero rows. Nonlinear and threshold-only maps
remain open.
The nonlinear boundary control gives an exact identity showing why they remain
open: binary digits of the source Hamming weight use only 14, 16 or 18
arbitrary nonlinear rows on the saved families. The construction retains the
underlying source-form evaluation cost and supplies no SAT solver.
An explicit XOR/AND ripple circuit now realizes those digit rows with exact
gate counts 553,152; 3,069,184; and 16,223,488. The open problem is therefore
the cost-preserving integration of a polynomial-size nonlinear circuit into a
general decision solver, not the existence of a compact objective map.
The circuit-to-CNF control now checks that transfer directly on 32 assignments:
the proof-producing frontier solver accepts every correct pinned weight and
rejects every wrong one, with width 11 under the saved order. Scaling this
integration while retaining a polynomial search bound remains open.

An independent bounded adaptive-fragment cross-check now exists alongside the
language-invention lab:
project a residual proof fragment onto a shared interface, synthesize exact
unit/XOR/PB/ITE candidates, and replay them with an independent checker. The
implementation records `2^(shared+local)` projection work and returns `UNKNOWN`
past explicit caps. The next extension is to feed actual proof-DAG subfragments
and candidate reuse statistics into the portfolio selector; any unbounded
relation search must remain outside the claimed polynomial work.

The proof-DAG bridge now consumes actual resolution nodes rather than only a
clause fixture: bounded unit sub-DAGs are projected, relation certificates are
replayed independently, and the resulting facts feed the receiver-aware parity
interpolant. The next step is to replace the known unit pattern with arbitrary
repeated sub-DAG proposals while retaining exact implication certificates and
the same hard interpolation controls.

The repeated-sub-DAG follow-up now performs that first label-free proposal scan.
It treats every small derived clause as a possible boundary, canonicalizes
successful candidates by boundary position, and records template reuse with a
separate work ledger. The saved 65-node proof has 42 considered nodes, three
repeated templates, and two explicit `UNKNOWN` cases. This is a bounded
portfolio optimization experiment; it does not establish bounded interfaces
for arbitrary refutations.

The serialized follow-up now includes the 4,097-node scale replay as well. It
considers 2,306 small-boundary nodes and keeps 258 cap failures explicit: two
sub-DAG overflows and 256 local-projection overflows. The scale result is
independently replayed from its full records, so the larger count is not a
producer-only statistic.

A cap sweep at local width 7 recovers the 256 one-variable unit templates that
remain `UNKNOWN` at width 6. This is a measured interface-growth transition:
the experiment makes the extra exponential projection work explicit instead of
silently widening the claimed polynomial boundary.

A structural macro now handles that one family without exhaustive projection:
the Hall-plus-implication clauses are recognized and certified by a linear
resolution chain. It is replayed through width 256 and against an actual
width-eight proof fragment. The macro is intentionally separate from the
generic projector; extending it to arbitrary residuals would reopen the
coNP-hard equivalence problem.

The macro-assisted follow-up now feeds two certified structural rules back
into the 4,097-node scan. The Hall-plus-implication rule recovers the 256
projection-cap unit fragments; a fused-negative-suffix rule checks the final two
ancestry-cap nodes by replaying their reachable chains and an explicit extension
argument. The scoped scan therefore has no UNKNOWN records, while preserving
the 256 projection-cap and two sub-DAG-cap outcomes in its pre-macro audit and
charging every symbolic certificate separately. This is a concrete portfolio
improvement, not unrestricted macro discovery.

The residual-equivalence barrier now supplies the complexity warning for that
extension: exact future-state equality is coNP-hard even with a one-bit
boundary, via `F(z,y)=G(y) AND NOT z`. Quotient discovery must therefore use a
restricted language, a bounded certificate, or an explicit `UNKNOWN` outcome;
universal exact minimization cannot be assumed as polynomial preprocessing.

The certified residual-quotient prototype now supplies the corresponding safe
runtime contract: syntax, bounded truth tables, or replayable bidirectional
resolution proofs may merge states; a separating assignment may split them;
all other cases remain `UNKNOWN`. This keeps the coNP-hard equivalence barrier
visible in the planner's output.

The projection-discovery barrier makes the same limit direct for the macro
pipeline. In `F(z,y)=G(y) AND NOT z`, exact projection onto one boundary bit is
`UNIT_Z_FALSE` exactly when `G` is satisfiable and `EMPTY` exactly when `G` is
unsatisfiable. A universal exact classifier would therefore decide SAT and
UNSAT. The new finite replay keeps this reduction separate from the structural
macros, which remain valid only for recognized proof families.

## Separate general direction: stronger global constraints

Any proposed relaxation must be tested first against the exact Golay witness
and the all-size good-code construction. Explain which new inequality family
excludes the fractional point and why that inequality is valid on every
integer codeword. An inequality based on already knowing the minimum distance
does not supply a useful general optimizer.

Then answer the separate separation question: given a fractional point, how
is a violated inequality found with polynomial bit complexity? Enumeration
of all codewords, all inequalities or all partitions must be included in the
cost. Integrality and efficient separation are separate proof obligations.

## When a proposed breakthrough is ready for serious review

Provide an exact problem statement, all-input algorithm or lower-bound theorem,
complete correctness proof, total fixed-polynomial bound (or unrestricted
machine lower bound), and counterexample search results. Have another reviewer
try to break the central lemma independently. Preserve the failed conjecture
and minimal counterexample when it fails. No finite benchmark, restricted
proof-system lower bound, or successful certificate justifies changing the
overall P-versus-NP status by itself.

## Typed planner checkpoint

The bounded invented-relation bridge now feeds exact Schaefer signatures into
the typed planner. A supplied strong Horn or affine backdoor of size `k` is
also executable: it enumerates `2^k` assignments, checks every restricted
relation, then uses native Horn forward chaining or GF(2) elimination. The
saved `typed_merge_planner_lab/BACKDOOR_RESULTS.json` record and independent
`BACKDOOR_REVIEW.py` replay cover SAT, UNSAT, and conservative `UNKNOWN`
outcomes. This is a parameterized result for an explicitly supplied
backdoor; discovering a small backdoor for arbitrary SAT remains open.

The next hard-pair edge is also executable in
`typed_merge_planner_lab/parameterized_edges.py`: supplied code dimension `k`
gives exact `2^k` message enumeration, while supplied distance `d` gives an
explicit XP support search. The planner preserves the unparameterized
affine/cardinality NP-hard label when no parameter is supplied, and the saved
artifact distinguishes exact witnesses from certified above-bound outcomes.

The Horn/affine backdoor edge now also has a bounded recursive discovery
search. It records every candidate branch and returns `UNKNOWN` when depth or
node caps prevent a complete SAT/UNSAT certificate; a small decision tree is
evidence for that instance, not a universal polynomial discovery theorem.

The typed planner now composes its exact order oracle with frontier dynamic
programming in `typed_merge_planner_lab/adaptive_frontier.py`. The bounded
solver saves primal-graph, order, and every frontier-cut certificate; an
independent replay covers sparse, contradictory, dense, mixed, and capped
controls. The dense and capped cases keep order discovery and state growth
explicit, so this remains a parameterized experiment rather than a general
polynomial SAT solver.

The universal CNF baseline is now also proof-producing in
`proof_producing_cdcl_lab`: every learned clause carries a first-UIP
resolution chain and every finite UNSAT result ends in a replayable empty
clause. The baseline is useful for adversarial scaling comparisons, while its
uncapped search and proof length remain exponential in the worst case.

The bounded-width resolution closure now gives an independent finite barrier:
for each supplied `w`, it exhausts the weakening/resolution universe and
records either a replayable refutation or a fixed-point no-refutation result.
The new width sweep independently certifies the first refutation width on the
small controls (1 for contradictory units, 2 for 3-by-2 pigeonhole, and 3 for
the three-variable all-assignment contradiction). The next comparison is to
correlate these width certificates with CDCL proof length and frontier state
growth, keeping every cap and proof-system scope explicit. The first CDCL
scaling bridge is now saved in `proof_complexity_scaling_lab`; it replays ten
all-assignment and eight pigeonhole traces and records exact deterministic
trace identities where they are proved.
