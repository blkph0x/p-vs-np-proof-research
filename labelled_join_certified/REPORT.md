# Certified labelled graph solver and limits of universal encodings

The later [threshold-composition report](../THRESHOLD_PHASE_REPORT.md) tests
weighted clause aggregation and exact packed weights. This report preserves
the completed labelled-join checkpoint and its separate test counts.

**P versus NP remains unresolved.** This increment implements an exact solver
for a supplied class, supplies independently checked optimality certificates,
and tests several ways one might try to extend it to general hard problems.
The positive algorithm does not cover every binary code at a small parameter.
The negative results restrict specified representations, not all algorithms.

## What is implemented

For a binary check matrix that, after a supplied invertible row change, has
a graph-incidence block plus p arbitrary parity rows, the solver finds a
minimum nonzero word with nonnegative integer coordinate costs. Its uniform
running time is deterministic 2^{O(p)} times polynomial input size. A supplied
representation with p=O(log N) therefore gives polynomial running time for
homogeneous nonzero optimization. Finding such a representation is a separate
problem, and no universal small-p representation exists in this format.

The graph calculation retains the parity labels on every edge. Lifted
shortest paths handle the labels, and a second closure handles disconnected
Eulerian components. Pinning and deleting each original edge in turn handles
nonemptiness correctly, including zero-cost edges and graph loops.

The independent verifier checks rooted predecessor paths, all Bellman
inequalities, unreachable-state closure, every required dynamic-programming
minimum and every required pinned case. It then checks the answer in the
original matrix, with the original target, costs and nonzero requirement.
The verifier does not rerun the shortest-path search. Resource limits produce
UNKNOWN; a feasible word from an unfinished run is only an upper bound.

Arbitrary affine targets are also supported through a terminal-subset dynamic
program. That fallback is exponential in the number of graph terminals as
well as p. It is not claimed to be polynomial for unrestricted affine inputs.

A checked normalizer accepts H=B+UV when both B and U have incidence columns.
It contracts a forest of U and builds the required row form with p=rank(U).
Dependent U columns do not artificially inflate that parameter. The original
matrix and transformed affine target are both checked. This is a supplied
representation adapter, not a representation-discovery algorithm.

The separate `small_terminal_perturbation.py` extension handles the same-
coordinate form H=B+UV when the graph part has at most two ones per column.
It enumerates every label value z, forms the exact terminal set for
`Bx=s+Uz`, and invokes the certified labelled T-join dynamic program for
`Vx=z`. Its top-level verifier replays every branch and then checks Hx=s in
the original coordinates. A zero-label/zero-boundary branch uses the complete
nonempty edge-pin proof, so zero-cost loops and disconnected cycle corrections
are not silently dropped. The method is deterministic but exponential in p
and in the terminal count; it is a parameterized extension, not a universal
solver.

The saved [small-terminal controls](PERTURBATION_SMALL_RESULTS.json) contain
160 random representation cases and 80 random original-matrix adapter cases
matched against direct exhaustive assignment minima,
plus the one-edge inconsistent branch, wrong-label triangle, disconnected
cycle, zero-rank loop and explicit branch-cap controls. The implementation's
eight-test module is included in the 51-test follow-up suite. A separate replay
in `PERTURBATION_SMALL_AUDIT.json` rechecks all 243 exact controls and rejects
two mutated certificates while confirming the saved source hashes.

The companion [dense-U coverage theorem](PERTURBATION_COVERAGE_THEOREM.md)
counts arbitrary U and V choices directly. Its exact arithmetic artifact
allows every displayed row count up to n and excludes universal
logarithmic-label coverage at (n,r,p) = (128,64,7), (256,128,16) and
(512,256,27); a smaller (16,8,12) control correctly does not exclude
coverage. This is a representation obstruction only.
The saved count is independently replayed by
`verify_perturbation_coverage.py`, including exact integer digests and all
source hashes.

The graph primitive follows known parity-join methods; no algorithmic novelty
is claimed. See the [theory review](THEORY_REVIEW.md),
[coverage proof](COVERAGE_AUDIT.md), and
[independent coverage review](COVERAGE_INDEPENDENT_REVIEW.md). Written proofs
were independently reviewed but have not been formalized in a proof assistant.

## Evidence saved with the implementation

The frozen solver passed **37 tests across four modules**. These include
23,790 terminal/label requests on all 761 one-bit labelled simple graphs
through four vertices, weighted multigraphs, loops, original-code exhaustive
oracles, basis changes, normalization, malformed certificates, and budget
boundaries. See [TEST_SUMMARY.json](TEST_SUMMARY.json) and its transcript.

All **49 saved benchmark requests** completed EXACT, passed independent replay
against their original inputs, and agreed with an independent optimum. Four
requests were correctly certified infeasible, and eleven had valid zero-cost
optima. The bounded controls enumerate 73,920 original words in total.

The larger graph examples go through K10: 45 coordinates and two label rows,
with exact nonzero minimum three. An explicit zero-label triangle supplies
the upper bound; distinct nonzero original columns exclude weights one and
two. This checks the optimum independently without enumerating 2^45 words.
All 49 code certificates and ten sparse-U normalization certificates were
serialized, read back and checked. Source hashes remained unchanged.

The [experiment report](RESULTS.md) records every case and single-run timing;
[RESULTS.json](RESULTS.json) retains original matrices, transformations,
targets, objectives, complete certificates, limits and hashes. These are
correctness experiments, not a measured speedup comparison.

Independent review found a search-versus-verification resource-accounting
defect. It was fixed: sparse reachable search work no longer incorrectly
bounds all-source verification work, and verification exhaustion returns
UNKNOWN rather than rejecting valid mathematical evidence. Regression tests
cover the original failure and both verification limits.

## What prevents the immediate universal leap

The coverage audit proves several distinct restrictions.

- On the same coordinates, counting row spaces rules out representing every
  rank-half binary matrix with only O(log n) arbitrary rows over a graph.
- The class is closed under contraction. Therefore, even arbitrarily many
  free linear auxiliary variables followed by exact coordinate projection
  cannot expand the class at fixed p. This is stronger than an invalid
  attempt to count descriptions after an arbitrary polynomial enlargement.
- General rank-one perturbations, one-row graphic lifts, and disjoint
  exceptional-column rank one are different classes. Explicit small matrices
  separate them; tests must not silently substitute one for another.
- Allowing unbounded p contains every matrix through B=0,U=I,V=H, and restores
  exponential worst-case work. A supplied representation alone does not give
  a polynomial constructor or a small parameter.

Follow-up audits check further candidate shortcuts, with their exact scope:

| Proposed shortcut | Proven restriction | What remains outside the result |
| --- | --- | --- |
| Replace H by a low-rank syndrome projection QH | If q=rank(QH), n>q and q+1<d, every projected minimum is spurious | Procedures retaining or restoring original constraints |
| Decode free graph variables through arbitrary linear T | Nonnegative weighted Hamming cost is additive on all inputs iff positive-cost output rows each depend on at most one input | Restricted domains, affine/nonlinear maps, auxiliary minimization and threshold-only reductions |
| Encode parity as a direct-terminal nonnegative minimum cut | Free auxiliary vertices preserve submodularity; three-bit parity violates it | Matching, labelled joins and externally restricted encodings |
| Compose perfect-matching gadgets as arbitrary logical gates | Feasibility obeys exchange; a weaker two-sided rule persists at every weighted cutoff and excludes exact paired copy and AND | Carefully justified restricted encodings and more general decision reductions |

The corresponding self-contained proofs and controls are in
[projection limits](../projection_limits/THEOREM.md),
[objective pullback limits](../objective_pullback_limits/THEOREM.md),
[cut gadget limits](../gadget_limits/THEOREM.md), and
[matching gadget limits](../matching_gadget_limits/THEOREM.md).
All **41 follow-up tests across five suites** pass with unchanged source hashes.
Their [test summary](../FOLLOWUP_TEST_SUMMARY.json) and transcript are saved
separately; they do not replace or inflate the 37-test solver count. The cut
audit also checks 60,988 bounded graph cases, while the matching audit checks
1,100 graphs, 6,505 boundary relations, 9,000 explicit alternating-path
certificates and 884 weighted threshold supports. These bounded experiments
supplement the all-size proofs.

The [saved-artifact audit](../FOLLOWUP_ARTIFACT_AUDIT.json) checks current source
hashes against the saved experiments and tests, then replays the 49 code
certificates, ten normalizations, twenty projection witnesses, 186 linear
objective certificates and seven composition matchings directly from disk.
All 42 saved source references match. The replay performs no new optimization
searches. All checks pass.

Positive controls prevent overreading the restrictions: matching can realize
parity, and matching gadgets implement copy and AND on a promised encoded
domain while also accepting unwanted boundary states. Exact paired copy and
AND on every physical state remain impossible even with signed costs and an
arbitrary common cutoff: simultaneous path flips preserve total cost, so at
least one of the two exchanged states must remain under the cutoff.

The [composition control](../matching_composition_controls/THEOREM.md) makes
the missing validity condition concrete. Three correctly behaving promised
NOT gadgets form an 18-vertex graph with a valid perfect matching, although
the corresponding odd Boolean NOT cycle is contradictory. The matching uses
one rail of each paired wire and therefore does not decode to a valid Boolean
assignment. Saved larger odd cycles reproduce this specific false positive;
an even cycle is a positive control. This refutes the tested naive wiring,
not all matching reductions or all algorithms.

## The missing result

To conclude P=NP from this work would require a uniformly polynomial-time,
polynomial-size reduction from an NP-complete problem into a proven polynomial
solver, preserving both directions of the decision question. In this route,
that includes the objective threshold, original nonzero semantics, a parameter
bounded relative to the original input size, and any representation-discovery
cost. None of those requirements may be replaced by finite benchmark success.

Same-coordinate and pure linear existential versions of the proposed universal
encoding are ruled out here. Other encodings remain logically possible, but
no correct universal construction has been obtained. The next useful research
step must specify and prove such an encoding or a different general algorithm,
and challenge it on adversarial examples before expanding the implementation.

## Reproduce

From this directory, run `python run_checks.py` and
`python run_lift_experiments.py`. From the parent directory, run
`python run_followup_audits.py` for the separate representation-limit tests.
Run `python verify_followup_artifacts.py` from that parent directory to check
saved-source provenance and replay the stored certificates.
The individual audit folders contain commands for regenerating their stored
examples. All new solver and audit modules use the existing Python standard
library. No installation was needed.
