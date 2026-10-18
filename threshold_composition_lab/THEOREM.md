# Exact OR thresholds and limits of scalar aggregation

This lab revalidates the concrete controls in `../NEXT_RESEARCH_BRIEF.md`.
It proves an all-size OR signature, gives one false positive for a specified
sum-of-clause-costs rule, and certifies a limitation of affine scores on the
original input bits. It makes no novelty claim and no claim to resolve P
versus NP. In particular, failure to classify every assignment does not by
itself exclude a SAT decision reduction with a different encoding or decoder.

## 1. Boundary convention and exact weighted OR gadget

For a weighted graph with distinguished terminals, a physical boundary state
is a set S of deleted terminals. Its cost f(S) is the minimum total weight of
a perfect matching of the remaining graph; it is infeasible if no such
matching exists. A threshold accepts S exactly when f(S) is finite and at most
K. All remaining vertices must be covered, including any mandatory internal
vertices. Empty remaining graphs have the empty matching of cost zero.

For k >= 1, let G_k consist of k disjoint edges of weight one, with endpoints
(2i, 2i+1), i=0,...,k-1. Every vertex is a terminal. Boolean literal i is
encoded by deleting neither endpoint (0) or both endpoints (1). A state that
deletes exactly one endpoint of a pair is an invalid physical state.

**Theorem.** Every invalid physical state is infeasible. A valid state with j
deleted pairs has exactly one remaining perfect matching and cost k-j.
Consequently cutoff K=k-1 accepts exactly the valid Boolean tuples satisfying
OR, on the entire set of 2^(2k) physical states.

**Proof.** Each edge is a separate connected component. If exactly one endpoint
is deleted, its surviving endpoint is isolated and cannot be matched. In a
valid state each component is either absent or its unique edge must be used.
Exactly k-j components remain. Their edges have total cost k-j, which is at
most k-1 precisely when j >= 1. There are 2^k feasible states, 2^k-1 accepted
states, and 4^k-2^k invalid physical states. This also handles k=1 and the
all-deleted state. QED.

The graph has 2k vertices and k edges and is constructible in linear time.
The executable reference oracle is deliberately finite: this lab saves k=1
through 5, exhausts every physical state, and independently enumerates every
subset of the original graph edges. It checks vertex coverage and total cost
without using the preceding formula. A second test oracle recursively pairs
the first surviving vertex. Neither oracle calls a matching library.

**Relation versus predicate caveat.** The earlier paired AND obstruction in
`../matching_gadget_limits/THEOREM.md` concerns the full gate relation
z = x AND y, including a separately encoded output. It does not exclude the
input-only conjunction predicate. Indeed G_k with cutoff zero accepts exactly
the all-ones input tuple. This clarification is needed when reading the brief's
short phrase "exact paired copy and AND"; it is not a new gate construction.

## 2. Summing clause costs loses per-clause satisfaction

Suppose a clause of length k_c receives the preceding cost k_c-j_c, where
j_c counts its true literal occurrences. Summing its cutoff k_c-1 gives the
single acceptance condition

    sum_c (k_c-j_c) <= sum_c (k_c-1)
    if and only if sum_c j_c >= number_of_clauses.

This allows excess true literals in one clause to compensate for another
clause with none. It is weaker than requiring j_c >= 1 for every clause.

For the unsatisfiable formula (x) AND (NOT x) AND (x OR y), the clause sizes
are (1,1,2) and cutoffs are (0,0,1). All four assignments give:

| x | y | True literal counts | Clause costs | Total | Total <= 1 | Formula |
|---|---|---------------------|--------------|-------|------------|---------|
| 0 | 0 | (0,1,0) | (1,0,2) | 3 | no | false |
| 0 | 1 | (0,1,1) | (1,0,1) | 2 | no | false |
| 1 | 0 | (1,0,1) | (0,1,1) | 2 | no | false |
| 1 | 1 | (1,0,2) | (0,1,0) | 1 | yes | false |

Thus even optimizing over all consistent Boolean assignments and applying
this particular summed cutoff yields a false positive: the minimum is one,
yet the formula is unsatisfiable. This is an arithmetic composition control,
not a claim to have implemented shared-variable, copying, or negation wiring
in a matching graph. It refutes the specified aggregation rule even if
consistent assignment semantics are supplied for free.

## 3. An exact trade excludes every affine score on the four input bits

Let F(a,b,c,d)=(a OR b) AND (c OR d), on all sixteen Boolean tuples in that
coordinate order. Accepted tuples 1010 and 0101 have coordinatewise sum
(1,1,1,1). Rejected tuples 1100 and 0011 have the same sum.

**Theorem.** There are no real coefficients w_1,...,w_4, constant c, and real
cutoff K such that, on all sixteen inputs,

    F(x) is true if and only if c + sum_i w_i*x_i <= K.

**Proof.** Any such affine score s has

    s(1010) + s(0101) = 2c + w_1+w_2+w_3+w_4
                      = s(1100) + s(0011).

The left side is at most 2K because both inputs are accepted. The right side
is strictly greater than 2K because both inputs are rejected. Contradiction.
No sign restriction on coefficients or cutoff was used. Reversing the
threshold direction is covered by negating the score. QED.

The same argument covers any scalar affine combination of the two literal
counts a+b and c+d, including arbitrary clause weights and an offset. It does
not cover nonlinear clause-satisfaction features. For example the features
(1[a OR b],1[c OR d]) admit the exact score minus their sum with cutoff -2.
That positive control changes the feature map; no matching realization of
those features or saturation gadget is claimed here.

## 4. General equal-mass feature-trade certificate

Supply an external finite Boolean truth table t indexed by the original
domain, and an external feature map phi to Q^d. A certificate consists of two
nonempty equal-length lists of row indices, repetitions permitted. The first
list must contain only true rows and the second only false rows. Their summed
feature vectors must agree exactly. Equal list lengths account for the affine
constant. The same summation proof excludes every real affine threshold on
these supplied features, even though the finite executable inputs are exact
integers or rational numbers.

`verify_trade_certificate(truth_table, features, certificate)` independently
checks each of those conditions against the external data. It also checks a
canonical SHA-256 input binding, covering the entire truth table and feature
map. Its versioned binary encoding includes row/column counts, truth labels,
numerator signs, and length-prefixed numerator magnitudes and positive
denominators; it does not convert potentially large integers to decimal text.
The digest is a provenance/integrity check, not the mathematical proof;
labels, equal mass and vector sums are checked independently even when the
caller supplies a recomputed binding. A valid result is `VERIFIED`; malformed
or false certificates are `INVALID` with an error. No floating-point feature
values are accepted. JSON certificates contain row indices and the binding,
so they round-trip without rounding.

Verification uses O(md) exact rational additions for m entries per side after
reading and hashing the input. Its bit complexity is polynomial in the input
and certificate bit lengths: rational denominator products have bit length
at most the sum of input denominator bit lengths. Implementation limits are
4096 truth-table rows, 128 feature coordinates and 4096 entries per side.
These are explicit finite safeguards, not a claim to enumerate large Boolean
truth tables in polynomial time in their number of variables.

## 5. Scope and reproduction

The OR graph proof is valid for every k; saved enumeration covers only k<=5.
The four-point trade proves the stated affine-score impossibility for all
real coefficients, not just coefficients sampled by tests. Neither result
excludes more elaborate weighted matching graphs, minimization over auxiliary
states, nonlinear feature maps, restricted assignment domains, alternate
decoders, multiple objectives, or general SAT decision reductions. A
reduction needs existential decision equivalence; preserving every assignment
label is a stronger requirement and must not be assumed without justification.

The reference matching oracle also tests signed rational costs on small
general graphs. This is only a finite oracle control; the OR gadgets use
positive unit weights. The trade checker handles integer/rational features,
while its mathematical coefficient obstruction allows arbitrary real values.

From this directory, run:

    python threshold_controls.py
    python -m unittest discover -s . -p "test*.py" -v

`RESULTS.json` stores all original OR graphs, every boundary cost and a witness
when feasible, the four aggregation assignments, the complete sixteen-row
trade input and certificate, source hashes and source-stability evidence.
The five graph controls contain 1,364 physical states and 37,448 independently
checked boundary/edge-subset pairs. The tests additionally mutate truth labels,
feature vectors, input bindings and certificate indices, including mutations
with recomputed bindings that must still fail the substantive proof checks.
