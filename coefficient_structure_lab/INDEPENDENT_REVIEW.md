# Independent review of clause-structured coefficient counting

Reviewed on 2026-10-18. Verdict: the counting identity, width bound,
certificate checks and stated scope are sound. No producer correction is
required. This review changes only this file; the reviewed source and saved
results remained unchanged during the checks.

## Exact coefficient identity

For a fixed assignment to the original variables, a clause of size k has
false-literal count c and k-1 distinct binary slack choices. The required
digit equation leaves exactly k-1-c slack bits set to one. Its number of
extensions is binomial(k-1,k-1-c), with zero for an out-of-range value. The
base-six no-carry bound is valid because c plus all possible slack bits is
at most 2k-1<=5. Slack sets belonging to different clause occurrences are
disjoint. Multiplying these local extension counts and summing over one
shared original assignment therefore counts precisely the original packed
coefficient, including multiplicity.

This confirms several distinctions that would otherwise change the query:

- A positive ternary clause contributes coefficient 10, not its seven
  satisfying assignments: true-literal counts 1,2,3 have local factors 1,2,1.
- Repeating that same clause gives coefficient 16. Deduplicating a clause
  would change the coefficient even though it preserves satisfiability.
- An unused original variable contributes two distinct choices, even when
  both associated exponents are zero.
- For contradictory unit clauses, local factors depend on the same variable.
  Multiplying separately summed local answers would produce a false result.

The implementation retains all these features. It rejects malformed inputs,
empty clauses and repeated underlying variables within one clause, matching
its stated input contract, while allowing repeated whole clauses, unused
variables and the empty formula/product.

## Elimination, width and arithmetic

The elimination recurrence is a direct application of distributivity: multiply
all active factors involving the current variable, sum that variable, and
retain all other factors. Each factor's scope agrees with the corresponding
filled-graph neighbors. With width defined as the number of live neighbors,
the full bucket has at most w+1 variables and its output table at most 2^w
entries. The implementation verifies this convention explicitly; it does not
assume or discover an optimal-width order.

Every input or generated factor is consumed at most once, so charging a
factor's table lookups and multiplications to that bucket gives
O((n+m)2^(w+1)) arithmetic operations, plus the stated polynomial indexing and
graph bookkeeping. An empty bucket produces scalar two, as required for an
unused variable; final scalar factors are multiplied exactly once. The empty
final product is one.

The q+1 bit bound for partial integer counts is justified by a counting
invariant. Active factors represent disjoint groups of original clause-slack
factors and disjoint groups of eliminated original variables. Variables still
shared between factors are fixed at each bucket assignment. Every partial
product and accumulated nonnegative sum consequently counts at most the 2^q
original binary choices. No numerical-target-sized arithmetic assumption is
needed. The packed exponents themselves have polynomial bit length.

The request checker performs polynomial work to validate the original formula,
reconstruct the required packed digits, compare exponents, and hash the input.
Its scan of logical variables against clauses and its integer-power setup are
additional to the reported factor-arithmetic and graph-fill counters. The
theorem now explicitly distinguishes those setup/bit costs from the named
counters. Thus the counters are not being presented as total CPU cost.

The complexity guarantee is correctly conditional on the supplied order.
The star demonstrates order dependence; the complete primal graph has high
width under every order but is itself an easy instance. UNKNOWN results on
those controls are limitations of this explicit table representation, not
hardness proofs about the instances or all coefficient algorithms.

## Original-request binding and proof replay

The verifier receives the original variable count, clauses, ordered exponent
pairs, target and elimination order externally. It checks the exact base-six
encoding before using the factorization; unrelated products and altered
targets cannot inherit its conclusion. The length-prefixed binary hash binds
all those inputs without decimal integer conversion. Correctness does not
rest on the hash alone.

For every step, the verifier independently reconstructs active factor
ownership, bucket scope and filled-graph neighbors. It enumerates each full
bucket assignment in a different traversal from the producer and checks the
complete multiply-and-sum output table. It then checks all final components,
the coefficient/positivity fields and width/work/count-bit statistics. It
does not merely accept a stored final count or a claimed small width.

Original dimension, state/table, graph-work and arithmetic caps fail closed.
Powers of two are checked before allocations. Producer or verifier exhaustion
returns UNKNOWN; an invalid proof is separate from insufficient verification
resources. No unfinished result claims a coefficient or positivity value.

## Independent validation

All 11 supplied tests passed in 0.543 seconds. Their coverage includes original
coefficient comparisons, slack multiplicity, repeated clauses, unused
variables, contradictory shared variables, width-two families, original
positive/negative controls, order changes, adversarial certificate mutation,
large integer counts and exact resource boundaries.

An additional read-only test used seed 518102026 to generate 300 formulas on
zero through four variables, with zero through four signed clauses and
distinct variables within each clause. It constructed the original packed
pairs directly from the formula, then enumerated all binary choices of those
pairs, with at most 12 factors. It did not use the producer's packing helper,
binomial factors or coefficient oracle for the expected count.

- 8,925 original packed choice words were enumerated across the 300 formulas.
- A shuffled and reversed order were checked for each formula: 600 complete
  coefficient results agreed with direct original-product expansion.
- Positivity also agreed with independent direct evaluation of the original
  Boolean formula.
- The source hash was unchanged and matches the final saved artifact.

The saved named controls were separately replayed:

- All 11 EXACT contraction certificates verified against their external
  original requests.
- All four UNKNOWN results retained null coefficient and positivity fields.
- 2,099 original assignments in the small named controls were checked using
  explicit local slack-bit enumeration, without calling the producer's
  binomial helper.
- All nine saved original positive witnesses passed direct clause evaluation,
  exact sum of original choice weights, and original graph vertex-coverage
  and edge-cost checks.
- Every saved local and prior-encoder source hash was current before and
  after replay.

The large disjoint-clause identity 10^m and the connected-chain transfer
matrix [[1,3],[3,3]] also check algebraically. The latter follows by summing
the one private middle variable for each fixed endpoint pair; its characteristic
polynomial gives C_m=4C_(m-1)+6C_(m-2), with C_0=2 and C_1=10. The disconnected
and connected examples therefore have independent coefficient formulas, not
merely agreement between producer and verifier.

These finite checks validate the implementation and saved evidence. The
all-size guarantee follows from the counting and elimination invariants.
They do not establish small width for arbitrary formulas, infer hidden
structure from arbitrary products, or resolve P versus NP.

## Reviewed frozen sources

| File | SHA-256 |
|------|---------|
| structure.py | 43a3d308e60ec4926b7772b2eaa727ae70745640dbdf54d525334d197a932ab2 |
| test_structure.py | 6a0e48996724533035d65cdde186313d87e8827e29f80c440c7a73c16c2dd983 |
| run_experiments.py | a3f379d51e999150b94325350b524ad84b8c3103da6d9a61a70b174d585d2c91 |
| THEOREM.md | ff267f78963f8f0b3490802abf6be4ee480c989a5bc9707aac500d86c3e6a68a |
| ../packed_cost_exact_matching/packing.py | 1d60ffd5bf25a2cacdb08e5cf0287432135fe8134c6ca531c497e054ede30fbe |
