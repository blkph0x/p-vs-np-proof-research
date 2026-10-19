# Response to the peer audit — 20 October 2026

The audit is accepted. It correctly identifies the project's contribution as
an evidence and reproducibility discipline around a collection of finite
experiments, not a new proof system, a new hierarchy theorem, or a solution to
P versus NP. The repository makes no claim that a public search has proved it
is the first project to assemble these ingredients. The current claim is
narrower and checkable: each promoted entry is either an exact certificate for
its declared finite or promised scope, an explicit `UNKNOWN`/`UNKNOWN_CAP`
outcome with its stopping boundary, or it is not presented as a result.

## Disposition of the audit's points

| Audit point | Disposition | Repository evidence |
| --- | --- | --- |
| The component methods already exist in papers, tools, or adjacent projects. | Accepted. The project treats those works as the sources and boundaries of its methods; it does not claim ownership of the underlying proof systems, code families, or width theorems. | [`CITATIONS.md`](CITATIONS.md), [`PUBLIC_SOURCES.md`](PUBLIC_SOURCES.md) |
| The unusual feature is the single rule for promoting a result. | Adopted as the repository's acceptance rule. A producer, independent reconstruction, exact certificate, negative control, and scope statement are required for a promoted finite result. | [`RESOLUTION_STANDARD.md`](RESOLUTION_STANDARD.md), [`CONTRIBUTING.md`](CONTRIBUTING.md) |
| A second program rebuilding the RM quotient is useful evidence but not a proof-assistant trust theorem. | Accepted. Independent replay reduces shared implementation risk; it does not establish formal verification or eliminate a shared definition error. | [`local_marginal_code_lab/REED_MULLER_LEVEL_D_FULL_INDEPENDENT_REVIEW.json`](local_marginal_code_lab/REED_MULLER_LEVEL_D_FULL_INDEPENDENT_REVIEW.json), [`INDEPENDENT_AUDIT.md`](INDEPENDENT_AUDIT.md) |
| The `31/5` RM(2,5) value is a finite exact certificate, not a hierarchy breakthrough. | Accepted and stated that way. The full level-eight quotient has a matching rational primal and dual; the pinned integer optimum is eight. Later SOS cuts close later finite models, each with its own report. | [`local_marginal_code_lab/REED_MULLER_LEVEL_D_FULL_REPORT.md`](local_marginal_code_lab/REED_MULLER_LEVEL_D_FULL_REPORT.md), [`METHOD_INDEX.md`](METHOD_INDEX.md) |
| `UNKNOWN_CAP` and negative moment values must not be promoted into impossibility claims. | Accepted. Capped search, violated cuts, and failed recognizers retain their explicit status and boundary. They are not relabeled as UNSAT, integrality, or general lower bounds. | [`RESOLUTION_STANDARD.md`](RESOLUTION_STANDARD.md), [`proof_motif_candidate_lab/XOR_CLOSURE_REPORT.md`](proof_motif_candidate_lab/XOR_CLOSURE_REPORT.md), [`local_marginal_code_lab/REED_MULLER_SOS_MOMENT_REPORT.md`](local_marginal_code_lab/REED_MULLER_SOS_MOMENT_REPORT.md) |
| The full-model matrix mutation control only checked that a local dictionary changed. | Fixed in this checkpoint. The control now mutates the saved certificate, invokes the complete independent replay, and requires the specific quotient-matrix mismatch. The unmodified certificate is replayed separately and must pass. | [`local_marginal_code_lab/REED_MULLER_LEVEL_D_FULL_INDEPENDENT_REVIEW.py`](local_marginal_code_lab/REED_MULLER_LEVEL_D_FULL_INDEPENDENT_REVIEW.py), [`local_marginal_code_lab/test_reed_muller_level_d_full.py`](local_marginal_code_lab/test_reed_muller_level_d_full.py) |
| The full-model objective was read from the certificate rather than reconstructed. | Fixed in this checkpoint. The independent checker rebuilds the singleton value-one objective from its reconstructed variable map, compares it exactly with the saved vector, and computes the rational objective from the rebuilt vector. A mutated saved objective is rejected. | [`local_marginal_code_lab/REED_MULLER_LEVEL_D_FULL_INDEPENDENT_REVIEW.py`](local_marginal_code_lab/REED_MULLER_LEVEL_D_FULL_INDEPENDENT_REVIEW.py), [`local_marginal_code_lab/REED_MULLER_LEVEL_D_FULL_REPORT.md`](local_marginal_code_lab/REED_MULLER_LEVEL_D_FULL_REPORT.md) |
| The full certificate had not been independently rerun by the audit. | The focused replay is now part of the corrective validation and the focused test suite checks both acceptance of the saved certificate and rejection of matrix/objective mutations. CI remains the final remote rerun record. | [`local_marginal_code_lab/REED_MULLER_LEVEL_D_FULL_INDEPENDENT_REVIEW.json`](local_marginal_code_lab/REED_MULLER_LEVEL_D_FULL_INDEPENDENT_REVIEW.json), [workflow runs](https://github.com/blkph0x/p-vs-np-proof-research/actions) |
| Deterministic small families and symmetry quotients make finite checking meaningful. | Accepted with the stated limit. Exact enumeration supports the saved instances; it does not imply a scalable algorithm or an all-size theorem. | [`local_marginal_code_lab/REED_MULLER_LEVEL_D_FULL_REPORT.md`](local_marginal_code_lab/REED_MULLER_LEVEL_D_FULL_REPORT.md), [`tseitin_expander_lab/REPORT.md`](tseitin_expander_lab/REPORT.md) |
| The project is not stronger than Cutting Planes, Frege, SOS, or the systems in the Proof Complexity Zoo. | Accepted explicitly. The cited literature remains the authority for the broad theorems; this repository supplies finite, replayable records in its declared models. | [`CITATIONS.md`](CITATIONS.md), [Proof Complexity Zoo](https://proofcomplexityzoo.gitlab.io/zoo/) |
| Formula-level proof checkers do not classify a complexity problem. | Accepted. DRAT-trim, cake_lpr, and the SAT competition are cited as neighboring trust and benchmarking tools, not as evidence for a P-versus-NP classification. | [`CITATIONS.md`](CITATIONS.md), [`proof_producing_cdcl_lab/THEOREM.md`](proof_producing_cdcl_lab/THEOREM.md) |
| Two Python programs are weaker than a proof assistant. | Accepted. The trust model and its residual risks are stated in [`INDEPENDENT_AUDIT.md`](INDEPENDENT_AUDIT.md); no formal-verification claim is made. | [`INDEPENDENT_AUDIT.md`](INDEPENDENT_AUDIT.md) |
| A test total is not a result total. | Corrected in this checkpoint. The current full audit reports **55 suites and 546 test methods**. Those are replay checks, not 546 mathematical results; the result ledger is [`METHOD_INDEX.md`](METHOD_INDEX.md). Local counts such as the affine-boundary suite's 46 tests are likewise test counts. | [`TEST_SUMMARY.json`](TEST_SUMMARY.json), [`METHOD_INDEX.md`](METHOD_INDEX.md) |
| Historical dates and scope-specific `UNRESOLVED` fields can confuse the current status. | Corrected in this checkpoint. The landing page and README identify 20 October 2026 as the active checkpoint. Historical reports retain their dates but now identify themselves as historical and link to this current disposition. A scope-specific unresolved marker remains only where that narrower branch is genuinely unresolved; it does not override a later full replay. | [`index.md`](index.md), [`README.md`](README.md), [`REPORT.md`](REPORT.md), [`METHOD_INDEX.md`](METHOD_INDEX.md) |

## Neighboring work and the boundary of comparison

The audit's comparison is useful when each neighbor is described by what it
actually supplies and what this repository does not infer from it:

| Neighbor | What it supplies | Boundary here |
| --- | --- | --- |
| [Proof Complexity Zoo](https://proofcomplexityzoo.gitlab.io/zoo/) | A map of proof systems and simulations. | A literature map is not a certificate or a finite optimum. |
| [SAT Competition](https://satcompetition.github.io/), [DRAT-trim](https://github.com/marijnheule/drat-trim), and [cake_lpr](https://github.com/marijnheule/cake_lpr) | Industrial solving, benchmarking, and formula-level proof checking. | A checked proof of one formula does not classify a relaxation or prove a complexity theorem. |
| [Sherali--Adams](https://doi.org/10.1016/0166-218X(92)00190-W), [Schoenebeck's Lasserre bounds](https://schoeneb.people.si.umich.edu/papers/LasserreNew.pdf), and their exact or numerical tools | Hierarchy definitions, integrality gaps, and stronger all-size results in their stated settings. | The RM(2,5) record is one exact finite rational quotient; it does not replace those theorems. |
| [Reed--Muller literature](https://doi.org/10.1109/TIT.1954.1057465) | Code parameters, distance, and decoding. | The local-marginal relaxation is a separate diagnostic model; its finite certificate is not a new code theorem. |
| [Dantchev's matching-principle notes](https://www.brics.dk/DS/02/2/BRICS-DS-02-2.pdf) | The PHP width construction replayed by the resolution lab. | The replay is a bounded machine-checkable record of a cited construction, not ownership of the all-size theorem. |

Where the cited hierarchy or width theorem applies, it is the stronger result.
The repository's contribution is to preserve a small, exact, independently
replayable instance and to keep its limitations visible.

## What the repository adds, narrowly

The value is epistemic and operational. For the saved models, the repository
keeps the input construction, exact arithmetic, certificate, independent
reconstruction, adversarial mutation, source citation, and scope statement in
one auditable record. This makes it possible to reject a result by changing a
mass, a row, a clause, a role map, or a saved proof step and observing the
checker fail. That is useful public research infrastructure; it is not a new
complexity class or a replacement for the literature's stronger theorems.

The current finite records include the independently replayed RM(2,5)
level-eight value `31/5`, the subsequent seven-cut finite SOS closure, the
uniform ordinary-resolution PHP width construction, and the finite odd-charge
Tseitin campaign. The Tseitin ladder's `16, 32, ..., 2048` conflict counts are
measurements of one fixed deterministic CDCL policy. They are not an all-size
recurrence, a uniform-expander theorem, or a lower bound on arbitrary SAT
algorithms.

Failure is stored data. The capped XOR-chain and role-search branches remain
`UNKNOWN_CAP`; a negative pseudo-expectation remains a violated valid cut; and
a dual-distance or width observation remains scoped to its stated model. The
repository's acceptance standard prevents these observations from being
promoted by implication.

## Finite expansion addendum

To make the Tseitin comparison more concrete without overstating it, the
campaign now includes [`tseitin_expander_lab/EXPANSION_REPORT.md`](tseitin_expander_lab/EXPANSION_REPORT.md).
It enumerates every nonempty vertex subset through half size for all twelve
saved cubic graphs, records both the open and external-neighborhood minima at
each size, and stores a separate replay that reconstructs the graph family
and every witness. The largest row checks 616,665 subsets; the external ratio
on the 20-vertex ladder is `2/5`. This addresses the audit's request for a
reproducible graph property while preserving the correct boundary: these
finite ratios do not prove a uniform standard-expander theorem, a resolution
lower bound for every proof system, or a P-versus-NP result.

## What remains open

The project has not produced a uniform deterministic polynomial-time algorithm
for all SAT instances, nor an unconditional lower bound ruling out every such
algorithm. Therefore P versus NP remains unresolved. The next useful work is
to extend exact certificates or prove uniform bounds while preserving the same
result/`UNKNOWN` boundary, and to record every external theorem as a citation
with its precise hypotheses.

This response supersedes the 19 October addendum for the current status; the
earlier response remains in the history as an audit record.
