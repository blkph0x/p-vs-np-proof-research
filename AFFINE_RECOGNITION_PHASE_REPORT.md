# Verified grouping and global affine recognition

**P versus NP remains unresolved.** This increment targets two measured
limitations of the preceding compression phase: sensitivity to clause order,
and greedy pair reductions that stop before a whole sum becomes one piece.
The grouping implementation now verifies 19 of the 22 original stress counts,
up from 11 for unplanned compression and two for the earlier weighted method.
The earlier 58 requests remain at 54 exact counts and four UNKNOWNs.

## Verified clause grouping

The planner scans complete original clause occurrences for four full-support
three-literal clauses excluding exactly one parity class. It groups those
occurrences in a deterministic order, then retains every ungrouped occurrence
in its original order. Duplicate or extra eligible occurrences on a support
conservatively prevent that bucket from being grouped. An independent checker
validates exact integer IDs, signs, complete local truth patterns and a
permutation containing every original occurrence exactly once.

The frozen compressed solver receives the original CNF and only a new checked
clause order. It still derives every clause factor, product, marginal, rewrite
and root count. No parity equation, known graph count or family-specific answer
replaces the original formula in that solver.

| Same complete original requests | Earlier weighted | Unplanned compression | Checked grouping plus compression |
|---|---:|---:|---:|
| 22 stress requests | 2 EXACT / 20 UNKNOWN | 11 EXACT / 11 UNKNOWN | 19 EXACT / 3 UNKNOWN |
| Earlier 58 requests | 54 EXACT / 4 UNKNOWN | 54 EXACT / 4 UNKNOWN | 54 EXACT / 4 UNKNOWN |

All eight previously capped shuffled parity requests now verify, including
both consistent and inconsistent 120-variable, 320-clause inputs. Each grouped
and shuffled pair produces the same canonical ordered clause sequence. The
eight-vertex pair requires 10,018 recorded planning-plus-solving work units;
the 80-vertex pair requires 257,679, for either charge parity. These are
specified operation counters, not timings or asymptotic speed claims.

There are no lost certified answers in these batches. The same three larger
pigeonhole requests remain UNKNOWN. The earlier complete-positive, two planted
and connected mixed requests also remain counting UNKNOWN; detecting 12 parity
blocks in the mixed formula does not suffice to finish its count.

Planning and plan verification are additional measured work. The solver keeps
its original limits, so its 3,000,000-work limit is not claimed as a limit on
the complete pipeline. Proof replay has a separate cost. Also, a contiguous
four-clause group need not become an exact subtree in the solver's balanced
tree: the recorded larger parity controls succeed despite that misalignment.

The independent audit replays all 80 compressed proof artifacts and their
source hashes, checks all 3,559 occurrence-permutation entries, validates
616 complete parity blocks through 4,928 local truth patterns, and verifies
all 73 completed root proofs. It preserves seven UNKNOWNs, rejects the stated
adversarial mutations and checks producer/checker caps. All 11 planner tests
pass. Full originals and proofs are stored in hash-bound gzip files; compression
changes storage only.

## Global recognition beyond pairwise merges

The separate affine-partition recognizer handles a supplied collection of
equal-magnitude pieces with pairwise disjoint affine supports. It proves
coverage of their affine hull using disjointness and exact cardinalities,
then solves a binary linear system for one quadratic phase whose restrictions
match every piece. Its independent checker uses support contradiction
witnesses and quadratic evaluations at coordinate weights zero, one and two,
rather than rerunning the fit.

This recognizes the four nonparallel affine lines left by the saved greedy
trap as one constant piece. It also handles wide symbolic partitions without
enumerating the boundary truth table. Failed disjointness, magnitude, coverage
or phase conditions are UNSUPPORTED for this narrow method, not proof that
another one-piece representation is impossible. Overlapping pieces can cancel.
The recognizer is separate from the frozen SAT solver; no improvement in the
original-CNF table above is attributed to it.

All seven partition tests pass after review moved the unknown-coefficient
limit before monomial-list allocation. The saved 1,349 controls retain
1,210 EXACT, 132 UNSUPPORTED and seven UNKNOWN outcomes. Independent review
replays every exact certificate, classifies 1,338 small cases through full
Boolean phase expansion, and checks 100 additional transformed partitions.
Ten saved equality norms cover 136 closed products. The allocation repair
changes when a limit is checked; the recorded outcomes and work-unit convention
remain unchanged.

The stronger [one-piece design](AFFINE_ONE_PIECE_RECOGNITION_DESIGN.md) removes
that disjointness restriction for an already explicit rational sum. Its key
primitive computes the exact squared norm on any affine restriction using
all pairwise compact contractions. Positive norm permits deterministic search
for a nonzero support point. Repeatedly finding a support point outside the
current affine hull raises its rank, at most once per coordinate. Final zero
norms on all violated hull equations certify the complete support hull.

Values at the hull origin and coordinate weights one and two determine the
only possible quadratic phase and coefficient. A final exact norm of the
difference accepts it precisely when the entire original sum equals that
piece. A zero value at the canonical hull origin must reject a nonzero single
piece; that origin need not be a point found during support discovery. All
these steps have polynomial bit complexity in the **explicit list size and
dimension**, using O(m^2) norm queries, each with O(K^2) pair contractions.

Two mathematical reviewers found this argument sound. The persisted independent
bounded review checks 541 explicit sums, 4,260 original truth words, 7,099
norm queries and 185,061 pair contractions. It includes a gapped full hull
with zero canonical origin, a cubic sign pattern that defeats low-weight
sampling but fails the final norm, and cancellation of overlapping supports.
These bounded checks supplement the proof; they do not replace it or claim
formal verification.

The complete standalone recognizer is now implemented in
[affine_one_piece_lab](affine_one_piece_lab/THEOREM.md). Its saved 494 original
requests contain 276 EXACT outputs, 210 verified one-piece impossibility
certificates and eight UNKNOWNs. Unlike the narrow partition method's
UNSUPPORTED result, each completed rejection here includes a checkable
obstruction to every single affine quadratic representation of that original
explicit sum. UNKNOWN never supplies such an obstruction.

The producer records 3,933 norm queries and 105,786 pair contractions; replay
of the exported proofs uses 22,718 contractions. Discovery performs work that
the final certificate need not repeat, so these totals are intentionally
different. The run also checks 3,230 direct original truth values and rejects
44 proof mutations. Seven author tests include large rational inputs and
derived coefficient-bit limits. These are standalone representation controls,
not additional original-CNF counts.

The completed independent implementation review replays all 494 saved claims,
checks their 3,230 direct truth values, and verifies four wide whole-sum norms
with separately assembled ordered pairs. It classifies 543 additional sums
against an independent full-support and Boolean-polynomial oracle, checking
3,633 original truth words, and rejects 84 adversarial changes to certificates
or sources. Verification also succeeds with producer discovery disabled.
The earlier 109 compression inputs yield 51 EXACT, 53 certified UNSUPPORTED
and five UNKNOWN results under the review's recorded caps. A successful local
compression does not imply that its entire output is one piece.

For wide positive inputs, the implementation first tries a candidate on the
affine hull of the explicit input supports. It accepts only after a full
zero difference norm. A failed candidate falls back to true-support discovery,
because cancellations can shrink that hull; it never directly rejects.
Every failed attempt is charged. Negative proofs certify actual support
witnesses, outside-hull zero norms, and a magnitude, support or phase
obstruction. The checker does not trust the discovery trace or producer stats.

## Keep the decision target and input model explicit

The four earlier counting failures all have direct decision evidence: three
complete original SAT assignments and one original-clause unit contradiction.
An independent mask-based checker verifies those results and 812 additional
small originals. It checks 11,031 unit-proof mutations, distinguishing 2,104
valid alternative refutations from 8,927 rejected variants. The probe still
returns UNKNOWN on limits or when unsuccessful branching has no exported
refutation. It does not prove polynomial SAT search.

The stronger norm-based recognition theorem does not remove the central
obstacle. Expanding an original product of clauses can generate exponentially
many affine pieces. Its unexpanded squared norm is the SAT model count itself;
assuming a cheap oracle for that succinct product would assume the difficult
computation. The theorem supplies the norm only for an explicit list and
charges every pair. Neither recognition nor grouping bounds the number of
pieces needed or found on every original formula.

The [five-to-two control](AFFINE_RECOGNITION_LIMITS_REVIEW.md) makes the remaining
gap concrete. Four nonparallel affine lines partition the three-bit cube, and
an additional pin at 000 gives the function 1 + 1[x_0=x_1=x_2=0]. The greedy
rules retain five pieces. Two pieces suffice by that identity; one is impossible
because the full-support function has two distinct nonzero magnitudes. This
argument and exact equality norms are independently checked at widths 3, 16
and 64. Actual complete-recognizer runs under the stated review caps return
UNSUPPORTED, UNKNOWN and UNKNOWN respectively; the mathematical obstruction
does not turn a capped computation into a completed result.

The [next experiment brief](AFFINE_RECOGNITION_NEXT.md) proposes cheap original-sum
rejection witnesses and an optional, separately measured solver adapter.
Neither is implemented in this phase. Complete recognition of a whole sum
does not search all useful proper subsets, minimize representation size, or
guarantee efficient discovery of a small decomposition.

The [literature scope check](AFFINE_REPRESENTATION_LITERATURE_SCOPE.md) records
the established connection to stabilizer representations, the difference
between full-support phases and affine pins, and the numeric input-size issue
in exponential-rank product-state examples. No novelty claim or unrestricted
complexity lower bound is made.

## Evidence

The combined three-suite run passes **25 tests**, with all recorded source
hashes unchanged during the run. Its transcript and per-suite results are
saved in [the test summary](AFFINE_RECOGNITION_TEST_SUMMARY.json).

The final [artifact audit](AFFINE_RECOGNITION_ARTIFACT_AUDIT.json) passes 180
recorded hash references across 135 bound files, including all 80 compressed
original grouping artifacts. It freshly checks current hashes, input bindings,
status coverage, operation-count arithmetic and consistency with the completed
test run. Mathematical proof replay is attributed to the bound independent
review records; the final audit does not claim to rerun every expensive proof.

- [Previous compression phase](AFFINE_COMPRESSION_PHASE_REPORT.md), including its 54-test run and 300 exact artifact replays.
- [Grouping results](affine_grouping_plan_lab/RESULTS.md) and [independent replay](affine_grouping_plan_lab/INDEPENDENT_REVIEW.md).
- [Partition theorem](affine_partition_compression_lab/THEOREM.md) and saved original controls in that lab.
- [Complete one-piece mathematical review](AFFINE_ONE_PIECE_RECOGNITION_REVIEW.md).
- [Complete one-piece implementation review](affine_one_piece_lab/INDEPENDENT_REVIEW.md).
- [Five-to-two limitation review](AFFINE_RECOGNITION_LIMITS_REVIEW.md).
- [Decision/counting distinction and independent checks](COUNTING_VS_DECISION_REVIEW.md).

The resolution goal remains active. All imported archives and earlier frozen
solver implementations remain intact.
