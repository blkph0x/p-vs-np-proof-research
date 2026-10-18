# Next active investigation after the labelled-join checkpoint

The ultimate goal is still a valid resolution of P versus NP. None has been
obtained. Avoid spending another campaign reproducing the stored distances or
expanding a supplied tractable family without addressing general coverage.

The current implementations and tests are summarized in
`labelled_join_certified/REPORT.md`. The linear auxiliary and objective-map
obstructions rule out specific easy encodings. Matching permits promised-domain
logical behavior, but naive wiring admits invalid half-selected paired states;
the odd-NOT-cycle control records an explicit global false positive.

## A concrete threshold-composition hypothesis to challenge next

Matching threshold signatures can be richer than feasible or global-minimum
signatures. Nevertheless, simultaneous exchange still gives a weaker two-sided
constraint, sufficient to exclude exact paired copy and AND at every threshold.
Do not infer that every threshold signature is a delta-matroid, or that all
threshold encodings have been excluded.

One useful candidate control is a clause-OR threshold gadget. Take k disjoint
edges, one unit-cost edge per 00/11 logical terminal pair. The graph admits
exactly unions of whole deleted pairs. If j pairs are deleted, its optimum
is k-j. The cutoff k-1 accepts exactly the valid nonzero logical tuples, so
an individual OR clause can be realized as a threshold signature in this
precise interface. This follows directly from the disjoint edges; it is not
a construction for arbitrary SAT.

The unresolved issue is aggregation. Summing the clause costs and cutoffs
only requires the *total* number of true literal occurrences to be at least
the number of clauses. It does not require a true literal in every clause.
For the contradictory formula (x) AND (NOT x) AND (x OR y), assignment x=y=1
has clause true-literal counts 1,0,2. Their sum is three, despite the second
clause failing. A full graph reduction would also need consistent negation,
variable copying and valid interfaces, so this logical-level budget example
does not assume those missing constructions.

A stronger exact control avoids depending on a particular choice of clause
weights. The function (a OR b) AND (c OR d) is not a single linear threshold
of these four bits: accepted assignments (1,0,1,0) and (0,1,0,1) have the same
coordinatewise sum as rejected assignments (1,1,0,0) and (0,0,1,1). Any affine
linear cost therefore has equal summed cost on the two pairs. Two accepted
costs <=K cannot have the same sum as two rejected costs >K. This rules out
all real scalar coefficients and an arbitrary constant/cutoff in that simple
aggregation format, not just equal or positive clause weights. It does not
exclude more elaborate matching structures or a different encoding.

Before treating weighted thresholds as a rescue, save and independently test
this clause truth table and aggregation counterexample. Then investigate
whether a proposed objective transformation saturates every satisfied clause
at a common cost while penalizing every unsatisfied clause, with no invalid
states or compensating rewards. Its all-input cost table must respect the
weighted matching exchange inequalities. If it does not, preserve the smallest
violating assignments as a certificate rather than implement the false gadget.

Any proposed general construction still needs a uniform polynomial-time
constructor, polynomial output size, both directions of decision equivalence,
and a polynomial target solver. A necessary invariant or a finite truth-table
match alone is not sufficient. The written proofs here are independently
reviewed mathematical arguments, not proof-assistant formalizations.
