# Public-method review and improvement plan

Reviewed 20 October 2026 against repository base
`914f2e0c283b6440159d3495ececffd83d42dc30`, with the accompanying verifier,
affine-hull and Fourier-precomputation changes identified separately below.

The strongest engineering direction is to reuse established search, planning
and arithmetic implementations, while checking their outputs against the
original request. The repository has useful exact reference implementations
and scoped certificates. It has not demonstrated a general speed advantage
over modern SAT, knowledge-compilation, matching or optimisation software.

This is a capability-level source and literature review, **not a line-by-line
audit of every function**, an exhaustive novelty search, or an external solver
benchmark. The [machine-readable inventory](PUBLIC_METHOD_INVENTORY.json)
maps every Python module in all 65 research directories to a comparison area
and lists its classes/functions and source hashes. Selected implementations,
reports and checker paths were inspected. Function listing is coverage metadata,
not individual correctness certification. The website, dependencies and CI are
included separately. Regenerate and check coverage with:

```text
python build_public_method_inventory.py
python build_public_method_inventory.py --check
```

## Decisions to make first

| Priority | Change | Why it is preferable | Acceptance evidence |
| --- | --- | --- | --- |
| P0 | Harden proof acceptance; benchmark an external proof-producing SAT backend | Older acceptance assertions could disappear under Python optimisation; mature engines have substantially more search machinery | Reject forged proofs under normal Python and `-O`; validate original SAT models and complete UNSAT proofs |
| P1 | Canonical rational LP export and SoPlex discovery adapter | Implemented for affine-overlap and nine-scope discovery; full level-eight/cut regeneration remains | Independently replay the same original model and exact optimal objectives |
| P1 | D4/CPOG certified compilation baseline | Public certification already covers CNF equivalence and projected compilation | Check original CNF/projection semantics, counts, construction and proof costs |
| P1 | CMR pure-graphic recognition and LEMON dual exporter | Complete recognition for a declared class; documented matching dual API | Check row-space/target transformations and every dual inequality |
| P1 | Exact local FWHT precomputation; better contraction/join planning | Removes repeated local arithmetic; targets intermediate-state growth | Equality to direct controls, honest operation counts, paired measurements |
| P2 | GF(2) projection supports and permutation-group quotient construction | Avoids global word enumeration and naive group closure where possible | Reconstruct identical local supports and quotient under certified permutations |
| P2 | Linux benchmark harness and persistent CI evidence | Separates discovery, execution, proof generation, checking and memory | Frozen inputs, pinned binaries, full costs and all capped outcomes |

These are ordered adoption candidates. Except for the explicitly completed
changes below, they are **not installed integrations or measured improvements**.
No universal fastest tool is identified.

## SAT search and certificate checking

| Existing feature | Public method and concrete difference | Adoption and decisive tests |
| --- | --- | --- |
| General CDCL in [cdcl.py](proof_producing_cdcl_lab/cdcl.py) | [CaDiCaL](https://github.com/arminbiere/cadical) and [Kissat](https://github.com/arminbiere/kissat) provide developed native SAT engines. Our engine scans clauses and uses a simple fixed decision policy. | Keep it as a readable proof-producing reference; add a pinned external backend. Compare identical original CNFs, single-thread limits and complete proof cost. SAT needs an original-clause model check; UNSAT needs replay. |
| Repeated SAT calls in affine abstraction and portfolios | CaDiCaL's [incremental interface](https://github.com/arminbiere/cadical/blob/master/src/cadical.hpp) supports assumptions and proof tracing, which must be enabled before adding clauses/solving. | Reuse a base formula with selector-guarded queries. Specify how each assumption-dependent proof discharges its assumptions. Test SAT→UNSAT→SAT sequences; do not accept a proof of a different guarded formula. |
| XOR motifs, Tseitin and mixed Horn/XOR inputs | [CryptoMiniSat](https://github.com/msoos/cryptominisat) has native Gaussian reasoning. [FRAT-XOR](https://github.com/meelgroup/frat-xor) supplies a route to XOR-aware checking with cake_xlrup. | Compare CNF-only and CNF-XOR paths including gadget recognition and CNF translation. Test renamed variables, reordered clauses, redundant equations, unsupported clauses and inconsistent systems. An XOR backend must account for every original clause. |
| Native resolution replay | [DRAT-trim](https://github.com/marijnheule/drat-trim) and [cake_lpr](https://github.com/marijnheule/cake_lpr) have established proof formats/checking infrastructure; cake_lpr offers formal assurance beyond two handwritten Python programs. | Add a verified format bridge or use a supported native proof route. Different proof formats are not interchangeable. Record preprocessing reconstruction and check the original input hash. Keep small explicit-resolution traces as a differential oracle. |
| Horn and typed backdoor selection | [Nishimura–Ragde–Szeider](https://www.satisfiability.org/SAT04/programme/51.pdf) connects strong Horn backdoors to vertex cover; [Dreier–Ordyniak–Szeider](https://doi.org/10.1016/j.jcss.2024.103520) addresses backdoor depth. These complement exhaustive searches, with parameter dependence retained. | Add a declared strong-Horn detector before exact search, then check residual Horn instances. Compare detection plus solving, including failures. Do not confuse backdoor size with recursive depth. |

A concrete defect was reproduced in the old reviewer: under `python -O`,
a forged UNSAT result could pass because acceptance used `assert`.
[Python explicitly removes assertions in this mode](https://docs.python.org/3/reference/simple_stmts.html#the-assert-statement).
The accompanying repair uses explicit checks, validates original models and
resolution parents, and removes exhaustive SAT enumeration from proof
acceptance. Exhaustive controls remain in tests. This improves the verification
architecture; it is not a faster SAT search result.

A separate open resource-contract issue remains: the native terminal
`derive_empty` path can exceed `max_resolution_steps` (contradictory units
with cap zero still derive the empty clause). That does not make the proof
false. Do not advertise that cap as a hard limit until every derivation path
enforces it. The new affine-hull campaign uses a decision budget instead.

## Proof complexity and structural frontiers

The width, PHP, Tseitin, semantic-frontier and graph/circuit-order labs
have different outputs from an ordinary SAT solver. A short SAT proof does
not certify **minimum** resolution width; a small decomposition does not
certify minimum width either.

| Feature | Established comparison | Improvement without changing the claim |
| --- | --- | --- |
| Bounded resolution closure and width games | [Atserias–Dalmau](https://www.cs.upc.edu/~atserias/papers/width/ccc03.pdf) gives the width-game characterization; [Dantchev](https://www.brics.dk/DS/02/2/BRICS-DS-02-2.pdf) supplies the PHP construction already replayed here. | Retain exact small closures as validation. Use proof-producing SAT for finding upper bounds, but require game/closure evidence for lower bounds. Indexing and bit masks are implementation improvements already present, not new proof-system lower bounds. |
| Comparisons beyond resolution | [VeriPB/CakePB](https://veripb.org/) provides pseudo-Boolean proof checking. | Add a separately named proof-system track with a checked CNF translation. A short pseudo-Boolean proof is not evidence of a short resolution proof or of an unrestricted circuit lower bound. |
| Linear orders, boundary tables and typed merge plans | [htd](https://github.com/mabseher/htd) provides tree-decomposition algorithms. [Slivovsky–Szeider](https://pmc.ncbi.nlm.nih.gov/articles/PMC7326555/) gives incidence-treewidth counting using zeta/Möbius transforms. | Check supplied decomposition coverage and running intersection, then implement the corresponding tree-DP consumer. Treewidth is not pathwidth: an htd width number cannot be substituted into the current linear-order bound. |
| Bounded-language, repeated-subDAG and motif synthesis | Established decomposition/compilation planners offer alternative proposals; exhaustive minimum searches currently have explicit caps. | Keep exact tiny optimum searches as comparators. Feed candidate plans to an independent structural validator; count discovery, rejected proposals, memoization and maximum intermediate allocation. |
| Expander/clutter controls | Native XOR reasoning can resolve odd-charge parity systems directly; width or graph expansion alone does not measure general SAT difficulty. | Benchmark representation-sensitive baselines and preprocessing. Preserve the unit-contradiction-with-clique control and named finite graph scope. Do not extrapolate a finite graph sweep to an expander-family theorem. |

The accepted comparison is **same task, same proof system, same original
encoding**. Cross-system comparisons should report the changed task explicitly.

## Affine algebra and compression

These components operate on explicit matrices or explicitly supplied signed
affine atoms. Their favourable complexity does not include discovering such
an expression from an arbitrary succinct CNF.

| Feature | Public method | Improvement and test |
| --- | --- | --- |
| GF(2) elimination, nullspaces, conditioning and row transforms | [M4RI](https://github.com/malb/m4ri) supplies optimized dense binary-matrix kernels. | Benchmark sparse Python masks versus dense arithmetic by dimension/density. Validate proposed row transforms, ranks, kernels, inconsistent targets and original coordinate maps. Include conversion cost. |
| Affine-quadratic atoms and marginalization | [Quadratic-form stabilizer simulation](https://arxiv.org/abs/2109.08629) develops incremental and sparsity-aware operations on closely related objects. | Borrow incremental updates while preserving exact scalar and global sign. Compare signed contractions and all small support/phase tables. Quantum state equivalence up to global phase is too weak for exact signed counts. |
| Pair/partition compression, Gram conditioning and complete one-piece recognition | [Low-rank stabilizer decomposition, §4.3](https://arxiv.org/pdf/1808.00128) uses exact pairwise overlaps for norms. | Cache canonical contractions and symmetric Gram entries; update norms after a rewrite. Retain exact zero testing. Approximate norm estimators may propose a candidate but cannot certify cancellation. |
| Positive covers, capacity and connected-cover obstructions | Representation lower bounds concern their declared language. No public general solver makes those theorems stronger merely by running faster. | Retain as negative controls for new encodings. Test whether an alternative representation escapes the particular obstruction; do not promote it to an arbitrary algorithm lower bound. |

No drop-in public tool with exactly the complete one-piece recognition contract
was established in this review. That is an unresolved comparison, **not a
novelty claim**. Minimum-piece discovery is a different problem. The repository's
previous negative integration comparison must remain in the benchmark set.

## Hidden-affine discovery and projected relations

The cheap baseline is mandatory: recognize complete XOR gadgets and eliminate
over GF(2). Reordered clauses, renamed auxiliaries, redundant equations and
invertible basis changes are useful controls; they do not make linear algebra
intrinsically hard. The symbolic enumeration charges in
[representation_discovery_lab](representation_discovery_lab/REPORT.md) are
neither minimum discovery complexity nor measured runtime.

The accompanying [affine-hull method](affine_projection_recognition_lab/AFFINE_HULL_METHOD.md)
uses the model-outside-current-abstraction loop of
[Reps–Sagiv–Yorsh](https://research.cs.wisc.edu/wpis/papers/vmcai04.BT.pdf).
[Boolean affine-envelope work](https://arxiv.org/pdf/0804.0066) also establishes
projection compatibility. It produces checked basis witnesses plus an
outside-hull UNSAT proof, or UNKNOWN, without using truth-table enumeration
in the checker.

An exact hull can contain points missing from the projected relation. It
cannot replace that relation without a separate equivalence proof. The first
SAT query already decides satisfiability of the input, so this is not a
standalone SAT acceleration. Its useful performance experiment is amortized:
compare preprocessing plus many restricted queries with solving all those
queries directly. Preserve nonconstant hidden multiplicity and non-affine
hole examples. The unrestricted recognition theorem and all associated
conditional hardness statements remain scoped as written.

## Certified knowledge compilation

This is a particularly important correction to the project's competitive
position. Public work already combines rich compiled representations with
independent and formally verified certification.

| Feature | Strong public counterpart | Adoption |
| --- | --- | --- |
| Compressed/weighted affine DAGs and residual quotients | [D4/CPOG, SAT 2023](https://drops.dagstuhl.de/entities/document/10.4230/LIPIcs.SAT.2023.6) certifies compiled CNF equivalence and counting, including a Lean-verified checker/counter. | Benchmark against the same original CNF. Preserve compilation proof, node count, checking cost and follow-on query cost. Certification is not unique to this repository. |
| Existential projection and helper variables | [Projected certified compilation, SAT 2025](https://drops.dagstuhl.de/entities/document/10.4230/LIPIcs.SAT.2025.8) adds projected CNF certificates with HOL4/CakeML verification. | Compare identical visible-variable sets. Test helpers with unequal witness multiplicities. Ordinary model count is not projected model count. |
| Grouping and multiplication/elimination plans | [DPMC/ProCount](https://github.com/vardigroup/DPMC) separates project-join-tree planning from execution. | Accept candidate plans, check original factor occurrences and elimination ownership, then execute exactly. Report generated pieces as well as retained pieces; late compression does not erase a large cross-product allocation. |
| Signed or slack-weighted factors | [Algebraic model counting](https://arxiv.org/abs/1211.4475) specifies conditions for evaluating compiled circuits over semirings. | Prove the adapter preserves the required algebra, smoothing/decomposability/determinism conditions and multiplicities. A Boolean support-only compiler is not automatically a signed-sum evaluator. |

Compilation can be exponentially large. These are stronger engineering and
assurance baselines, not a universal compact-representation theorem.

## Graph decoding, matching and row-basis discovery

| Feature | Public method and advantage | Adoption and acceptance |
| --- | --- | --- |
| Pure-graphic recognition before basis heuristics | [CMR](https://discopt.github.io/cmr/graphic.html) constructively recognizes graphic matrices and exports graph/spanning-tree information. | Reduce independent rows to `[I | A]`, retaining column IDs, and pass the fundamental-cycle part `A`. Reconstruct incidence row space and the affine target independently. Test loops, parallel columns, dependent rows, scrambled incidence matrices, Fano and inconsistent targets. This is a zero-exception fast path, not near-graphic optimization. |
| Matching primal/dual certificates | Current [NetworkX matching](https://networkx.org/documentation/stable/reference/algorithms/generated/networkx.algorithms.matching.max_weight_matching.html) is already a legitimate blossom backend. Our exporter inspects private locals with `sys.setprofile`. [LEMON](https://lemon.cs.elte.hu/pub/doc/1.3/a00254.html) exposes vertex/blossom duals through a documented API. | Export duals and convert their factor-four integer scale exactly. Test odd blossoms, negative/zero weights, nonperfect cases and malformed exports against exhaustive small graphs and the independent checker. No quarter may be silently truncated into a doubled-integer schema. |
| T-joins, degree-two minimum distance and labelled joins | Ordinary graph/matching algorithms already solve the ordinary subproblem. Label rank, exceptional branching and terminal subset DP add different parameters. | Keep NetworkX/LEMON as ordinary-matching comparisons; benchmark full normalization plus all labels/terminals. A better blossom routine does not remove exponential label-state costs. |
| Gadget composition, packed cost and multiple objectives | Ordinary minimum-weight matching does not solve arbitrary exact-weight or simultaneous-bound variants. | Preserve domain/wiring and objective-pullback counterexamples. Require globally valid original-coordinate witnesses before accepting any new gadget method. |
| Nongraphic/regular cores | [Sage matroids](https://doc.sagemath.org/html/en/reference/matroids/sage/matroids/matroid.html) and CMR provide useful external recognition controls. | Verify witnesses/minors in original coordinates; retain exhaustive GL search only for bounded controls. A failed heuristic or capped recognizer remains UNKNOWN. |

CMR is MIT licensed; LEMON's default license is Boost-1.0 with documented
exceptions. These facts favour evaluation, but do not substitute for checking
the chosen release and bundled dependencies. [CMR](https://discopt.github.io/cmr/),
[LEMON licence](https://lemon.cs.elte.hu/trac/lemon/wiki/License).
Blossom V is not a blanket drop-in licence alternative:
its [author distribution](https://pub.ista.ac.at/~vnk/software.html) distinguishes
research and commercial use.

## Coefficient queries, interval support and isolation

| Feature | Public comparison | Concrete improvement and correctness boundary |
| --- | --- | --- |
| Sparse/dense coefficient products and cyclic residues | [FLINT integer polynomials](https://flintlib.org/doc/fmpz_poly.html) and [modular polynomials](https://flintlib.org/doc/nmod_poly.html) provide established exact multiplication engines. | Use sparse/dense crossover and product trees. If coefficients are reconstructed modulo primes, prove a sufficient coefficient bound and CRT modulus product. Coefficient-modulus reconstruction does not repair exponent aliasing modulo `z^M-1`. |
| Interval support for nonnegative binary-encoded weights | [Koiliaris–Xu subset-sum algorithms](https://arxiv.org/abs/1507.02318) give stronger pseudopolynomial algorithms than elementary dense DP in their stated regime. | Subtract each pair's minimum to obtain a nonnegative subset-sum target; compare interval, bitset and divide-and-conquer methods. Preserve witness recovery. Dependence on numerical target can still be exponential in input bits, and interval-compressible examples can favour our method. |
| Structured packed coefficients | [Bucket elimination](https://ics.uci.edu/~dechter/publications/r76A.pdf), join-tree planning and component caching apply to the shared-variable sum-product. | Test the original packed pairs/target. Preserve slack multiplicity: ordinary SAT model counting, coefficient counting and coefficient positivity differ. A width obstruction is not an intrinsic SAT lower bound. |
| Random affine isolation | [ApproxMC](https://github.com/meelgroup/approxmc) uses SAT/XOR queries instead of requiring a pre-enumerated solution set. [Formally certified approximate counting](https://arxiv.org/abs/2406.11414) separates a formal PAC theorem from per-run CNF-XOR certificates. | Use as a separately labelled probabilistic research baseline with explicit tolerance/confidence. It cannot supply an accepted exact count under our current exact-or-UNKNOWN contract. Count all oracle calls and never infer UNSAT from a failed random trial. |

Keep the existing all-size counterexample to separate residue witnesses.
Many individually satisfiable residue constraints need not share one original
choice word. No multiplication library removes that quantifier distinction.
Likewise, polynomial identity testing does not answer whether one specified
coefficient is positive.

## Fourier transforms and character factors

[SymPy's discrete transforms](https://docs.sympy.org/latest/modules/discrete.html)
provide independent FWHT and Möbius reference calculations with exact inputs.
Use them to test ordering, normalization, padding and signed/rational data.
Full transforms on `2^n` entries still have exponential input/output size
in Boolean dimension.

For disjoint factor blocks with sizes `k_j`, constraint rank `r` and
`s` blocks, the character-factor implementation repeatedly evaluated the
same local transforms. Precomputing each local Walsh spectrum changes that
arithmetic contribution from

```text
O(2^r * sum_j 2^k_j)
to O(sum_j k_j * 2^k_j + 2^r * s).
```

This excludes separately charged table construction, mask projection,
multiplication and integer-bit costs. A deterministic cost comparison should
retain direct evaluation when precomputation costs more, and enforce the
same caps. The interpretation is standard
[normal-factor-graph Fourier duality](https://arxiv.org/abs/1102.0316).
The accompanying implementation retains exact normalization and direct replay;
its [method and measurements](affine_character_factor_lab/FWHT_PRECOMPUTATION.md)
are separate from this asymptotic local-work calculation. Inputs remain
integer-only. Verification can need more work than production, and unused
spectrum coefficients can exceed a tight bit cap when the direct requested
sums cancel: equal caps need not preserve completion status. Global `2^r`
dependence remains.

## Holographic signatures, tensors and Pfaffians

| Feature | Public method | Adoption and scope |
| --- | --- | --- |
| Exact contraction and basis-change reference | [cotengra](https://cotengra.readthedocs.io/en/main/basics.html) offers contraction-tree optimization, slicing and reconfiguration. Our reference enumerates edge assignments. | Import a plan only; validate port identities and execute with exact arithmetic. Check inverse basis placement, repeated occurrences, literal polarity and free-variable factors. Numerical contraction is not a certified zero test. |
| Supplied rational affine basis | [Cai–Guo–Williams](https://arxiv.org/pdf/1307.7430) gives transformation discovery for affine/product-type signatures, including broader complex-algebraic classes. | Start with a checked product-type evaluator; later add exact fourth-root phases and published recognition algorithms. A supplied-basis failure does not rule out every basis. State bipartite versus ordinary Holant conventions. |
| Matchgate/parity/crossover controls | [Cai–Gorenstein](https://theoryofcomputing.org/articles/v010a007/) characterizes planar matchgate signatures by their identities. | Check all required identities and composition conditions; retain the existing EQ3/OR3 and crossing-sign obstructions. These are language-specific boundaries. |
| Pfaffian evaluation | [PFAPACK](https://pfapack.readthedocs.io/en/stable/) supplies developed numerical algorithms. | Borrow matrix-algorithm structure or benchmark separately, but retain exact elimination/modular reconstruction for certified answers. Verify orientation and port signs; signed cancellation is not absence of matchings. |

## Code relaxations, symmetry and exact LP discovery

| Feature | Public method | Improvement and acceptance |
| --- | --- | --- |
| RM generators, duality, distance and finite code controls | [Sage coding](https://doc.sagemath.org/html/en/reference/coding/sage/coding/linear_code.html) supplies independent constructors and coding operations. | Optional cross-check of RM/Golay/random cores, weight distributions and row spaces. Distinguish shortening from puncturing. Generic distance computation may remain exponential. |
| Projection-support construction | Gaussian elimination on the pinned affine code obtains an anchor and pin-zero basis; projecting them gives the exact local affine image. | Avoid enumerating all global codewords. Enumerate only required local images and compare every atom against the existing small-code enumeration. This does not remove the all-scope or local-table explosion. |
| Scope, atom and equation orbit construction | [GAP actions](https://gap-system.github.io/gap/doc/ref/chap41.html) and [permutation groups](https://gap-system.github.io/gap/doc/ref/chap43_mj.html) provide stabilizer/orbit machinery; [nauty/Traces](https://pallini.di.uniroma1.it/) is another route via a proved coloured-graph encoding. | Supply the pin-preserving GL action; export generators and transporters. Reproduce orbit counts and the rational matrix up to verified permutations. Arbitrary weight-preserving permutations need not preserve the code. |
| Rational primal/dual discovery | [SoPlex exact mode](https://soplex.zib.de/doc/html/EXACT.php) and [QSopt_ex](https://github.com/sharpbracket/qsopt-ex) solve rational LPs. Our retained runners do not reproduce the historical search. | Export bounds, row/column IDs, rational coefficients and objective offset; store command, version, seed/basis and complete output. Recheck exact feasibility and reduced costs against independently reconstructed matrices. |
| All-redundant-check separation | [Puchert–Tillmann](https://arxiv.org/abs/2004.03387) gives an exact separation IP and general NP-hardness. | Use as a bounded discovery baseline, not a polynomial separator. A finite generated check list cannot replace the analytical witness satisfying every redundant parity check. |

For LP validation, require the existing reduced objectives `31/5`,
`7037/1095` and `35873801083/5129253893` where applicable.
Degenerate optimal solutions may have different vectors. Compare exact
objectives and feasibility, not byte equality of optimizers.
The full base-model benchmark is reduced `31/5` versus integer `7`,
or total `36/5` versus `8`. Never reintroduce the mixed-convention ratio.

SoPlex's default is floating point; exact rational mode and dependencies must
be selected explicitly. Its [current project licence](https://soplex.zib.de/index.php)
is Apache-2.0. The inspected QSopt_ex fork is GPL-3-or-later.
Neither tool's status string constitutes a certificate.

**Implemented follow-up:** the [SoPlex adapter](local_marginal_code_lab/EXACT_LP_DISCOVERY.md)
now performs fresh affine-overlap discovery and independently reconstructs
the model before accepting exact primal/dual optimality at reduced `31/5`.
The original historical search is still unrecorded. Default-tolerance rational
output produced a genuinely rejected candidate; that negative control is
retained. The final search uses zero tolerances. Construction, search and
verification have separate process measurements, with sampled memory clearly
distinguished from a guaranteed peak.

The [nine-scope follow-up](local_marginal_code_lab/RM2_NINE_SCOPE_DISCOVERY.md)
uses the same exact-backend pattern on a new 284-variable, 416-row model.
It discovers reduced optimum seven without a supplied target. Independent
reconstruction checks the projection support and all 362 added moment rows,
including 98 whose affine closure crosses the scope boundary. The full
RM(2,5) locality-nine conclusion uses a separate genuine-codeword upper bound;
the all-dimension statement has its own mathematical proof. This is a concrete
use of the adopted public method, not a speed comparison with another solver.
Regeneration of the original full-level-eight and seven-cut searches remains open.

## Integer cuts versus genuine moment/SOS constraints

The seven-cut campaign adds valid integer-weight polynomial inequalities to
an LP. It is not automatically a degree-bounded SOS hierarchy.

[SumOfSquares.jl](https://github.com/jump-dev/SumOfSquares.jl) supplies polynomial
optimization modelling, including [sparsity and symmetry certificates](https://jump.dev/SumOfSquares.jl/v0.8/reference/certificate/).
[Gatermann–Parrilo](https://arxiv.org/abs/math/0211450) gives the underlying
symmetry-reduction framework. A new experiment must first declare the Boolean
ideal, inequality generators, monomial basis and degree. Export Gram blocks,
then verify the coefficient identity and PSD decomposition exactly.

[Peyrl–Parrilo rational reconstruction](https://www.mit.edu/~parrilo/pubs/files/PeyrlParrilo-ComputingSumOfSquaresDecompositionsWithRationalCoefficients.pdf)
has conditions such as strict feasibility; singular numerical solutions need
separate treatment. A numerical SDP optimum is a candidate, not an exact proof.
The next test is reproducing the stored negative square moment and eliminating
it with a precisely specified standard moment formulation. Finding additional
violated integer cuts alone does not establish convergence or hierarchy level.

## Engineering, evidence and public presentation

| Feature | Public practice | Change |
| --- | --- | --- |
| Benchmarks and runtime chart | [BenchExec](https://github.com/sosy-lab/benchexec/) measures process-tree resources and supports controlled Linux runs. | Use a suitably configured Linux benchmark host; do not pretend Windows stopwatch measurements provide cgroup isolation. Retain frozen observations and add paired-input scatter/quantile views, memory, proof size and censored timeouts. |
| CI scheduling | [GitHub concurrency](https://docs.github.com/en/actions/reference/workflows-and-actions/workflow-syntax#concurrency) allows active runs to finish. | Changed `cancel-in-progress` to false. The default still retains at most one pending run; this is not a guarantee that every intermediate commit runs. Pages success remains distinct from mathematical-check success. |
| Certificates and source binding | Explicit validation and mutation tests; strict original-request binding | The general CDCL reviewer is repaired; normal/`-O` negative tests are in CI. Roll the same audit through other older checkers before claiming project-wide optimisation-mode safety. Verify committed artifacts before regeneration. |
| Source provenance | Generated indexes should derive from source documents, not themselves | Excluded `PUBLIC_SOURCES.md` from its own generator, removing circular provenance. The source inventory uses LF-normalized hashes and rejects new unclassified source modules. |
| Repository manifest | A working-tree file digest is not the same as a Git blob digest | Current manifest reads tracked working files and records the pre-generation HEAD. Treat it as a working snapshot with explicit base revision, not self-authentication of the final commit. Standardizing that format is still open. |
| Runtime chart accessibility | [W3C complex-image guidance](https://www.w3.org/WAI/tutorials/images/complex/) recommends both concise explanation and detailed text/data alternatives. | Existing keyboard focus and accessible data table are useful. Add per-point environment/proof links and repeated-run summaries before drawing stronger comparative conclusions. No replacement chart library is presently justified. |
| Public claims and release evidence | Precise theorem statements, original literature and pinned executable evidence | Keep novelty ledger and trust-chain links beside each result. A source URL establishes provenance, not novelty. Keep the full-suite baseline explicitly historical until a current complete run passes. |

## Benchmark and promotion contract

Every proposed adapter must preserve a record containing the original input
hash, task type, visible/hidden variable mapping, coefficient/objective
convention, tool version and build, settings/seeds, machine and resource
limits, result status, elapsed/CPU time, peak memory, representation size,
certificate size and verifier result. Separate construction, discovery,
execution and checking. Missing measurements remain missing.

Use deterministic families and shuffled/renamed controls already in the
repository, plus public benchmarks with their provenance retained. Include
negative and UNKNOWN cases. Compare a SAT decision tool only with the same
decision request; exact counting, projected counting, minimum width and LP
optimization get separate tables. Repeated measurements must include cold
setup costs where relevant. Timeouts are censored outcomes, never fabricated
runtimes to solution. Charge preprocessing and translation.

Promotion requires all original-input witnesses/certificates to pass, no
unexplained disagreement on exhaustive small cases, and a reproducible
benefit on a declared workload. Retain losing experiments. No improvement
in this plan is evidence that P versus NP is resolved.

## Completed in this increment and remaining work

Completed changes are the optimisation-independent CDCL verifier, source
inventory and provenance repair, non-cancelling active CI replay, integration
of the previously prepared certified affine-hull experiment, and the bounded
local-Fourier improvement with its own evidence. The follow-up also installs
and validates SoPlex as the first optional external discovery backend. Its
nine-coordinate follow-up has now produced a source-bound exact certificate
and a separately reviewed mathematical extension.

Next extend **exact LP discovery** to the larger certificates and build
a **certified SAT/compilation benchmark**. These address remaining
discovery reproducibility and missing external baselines. CMR and LEMON then
target well-defined recognition/export weaknesses. Broader SOS and hierarchy
work remains research requiring its own mathematical specification.

The companion inventory provides the complete module/function navigation.
Unreviewed internals, whole-project formal verification, global performance
superiority and mathematical novelty all remain unestablished.
