# Invented-relation bridge to the typed planner

The bounded language inventor stores a canonical Boolean truth table as the
authoritative certificate for each discovered relation. This bridge decodes
those tables and independently recomputes the six finite Schaefer closure
properties: 0-validity, 1-validity, conjunction, disjunction, majority, and
minority closure.

For a relation (R \subseteq \{0,1\}^k), the replay checks every tuple in
the saved table and applies each operation to every pair or triple of tuples.
It then compares the result with the typed planner's own signature routine.
The comparison is intentionally redundant: a compact ANF, weight, circuit,
OBDD metric, or relation name is never treated as logical authority.

If a relation is closed under AND, OR, MAJ, or MIN, the bridge exposes the
corresponding Horn, dual-Horn, bijunctive, or affine native theory. If no
Schaefer tag is present, the fixed single-relation language is classified as
the NP-complete branch of the planner. The bridge also reports the stronger
pin-preserving classification. 0/1-validity alone is retained for ordinary
unpinned CSPs but is not accepted as a boundary-extension oracle.

The saved inventor catalog contains 32 relation entries. Exhaustive replay of
all (2^{2^k}) relations for (k \le 3) confirms that the independent and
planner implementations agree. The catalog replay binds its result to the
SHA-256 digest of `bounded_language_invention_lab/RESULTS.json` and rejects a
mutated signature record.

This is a classification and composition check, not a universal SAT solver.
The fixed-width invention theorem still pays (2^{K+L}) projection work and
the current permutation-invariant canonicalizer pays (K!2^K). A relation
that is individually affine or Horn does not prove that a growing collection
of invented relations has a polynomial discovery or merge plan.
