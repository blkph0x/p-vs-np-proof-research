# Certified occurrence-preserving grouping of complete XOR3 clauses

This planner proposes a clause occurrence order. It never returns a SAT answer,
an expected count, a replacement constraint, or a family-specific solver. The
proposed order is passed to the unchanged, frozen
`../compressed_affine_dag_lab/dag.py` using its ordinary original-CNF API and
current documented caps. That solver must still derive and verify every
original factor, marginal, sum rewrite, and complete root count. No polynomial
bound on that solver follows from a polynomial grouping pass.

## Discovery and original binding

The fixed-arity support-bucket discovery idea is adapted from
`../../proof_motif_candidate_lab/miner.py:detect_parity_blocks`. Its old verifier
is not used. The new planner instruments its own scan and has a separate
occurrence-level checker. A source hash identifies the original n and complete
ordered list of original clauses, preserving literal signs, repetitions, and
clause occurrences. Literals and IDs must be exact integers; booleans, floats,
out-of-range literals, and zero literals are rejected.

Only clauses with exactly three literals on three distinct variables are
eligible. A support bucket is grouped only if it contains exactly four eligible
original occurrences, their four forbidden assignments are distinct, and all
four have the same parity. Any extra occurrence on that support, including a
duplicate original clause, makes the entire bucket ungrouped. This deliberately
conservative policy matches the earlier miner's fixed-size bucket restriction;
it does not silently discard duplicates or choose a favorable subset. Tautologies,
empty clauses, incomplete blocks, repeated-variable clauses, mixed-parity
buckets, and all other original occurrences remain in the formula.

Supports are sorted lexicographically in original variable IDs. Within a block,
clauses are sorted by their forbidden assignment word in the support order.
Every ungrouped occurrence is then appended in original occurrence order. With
no detected blocks, the proposal is the original order. Canonical ordering of
the complete blocks can undo an arbitrary shuffle of those occurrences, but it
is not an optimized factor decomposition.

## Local block theorem

A full-support clause on three distinct Boolean variables excludes exactly one
assignment: the assignment setting every positive literal to zero and every
negative literal to one. There are exactly four assignments of each parity on
three bits. Therefore four distinct forbidden assignments of one parity p are
the complete forbidden parity class. Their conjunction equals the parity
equation x+y+z=1-p over F2. This theorem justifies the grouping label, not a
replacement in the solver: all four original clauses remain separate factors.

The independent checker reads every claimed occurrence directly from the
externally supplied original formula. It checks exactly four distinct, unused,
in-range exact integer IDs, exactly three distinct support variables, exactly
one literal per variable, and equality with the complete four-element forbidden
parity set. It also checks the conservative full-bucket condition against all
eligible occurrences in the original formula. Claimed support/parity metadata
alone is never trusted.

## Partition and order theorem

The checker requires disjoint block ownership. The supplied ungrouped IDs must
be exactly the original-order complement of all grouped IDs. Concatenating the
checked block orders and that complement must equal both supplied order fields
and be a permutation of every original clause occurrence ID exactly once. Thus
the proposed ordered product contains precisely the same Boolean clause factors
as the original product. Commutativity proves pointwise equality and hence
equality of counts over the unchanged original variable universe, including
unused variables. This remains true for duplicate clauses, empty clauses, and
contradictory inputs; no logical deduplication is performed.

`verify_plan` independently rebuilds eligible occurrence sets and checks the
proposal. It does not invoke candidate discovery and need not prove that every
discoverable block was found: any checked full-coverage permutation is safe.
An omitted original occurrence, repeated ID, source-swapped certificate, wrong
support, malformed type, wrong parity, or changed order is rejected. UNKNOWN
planning or checking has no accepted order and never triggers a silent solver
fallback in the experiment runner.

## Cost, solver planning, and interpretation

For m clauses with L literal occurrences, the fixed-arity scan uses O(L+m)
dictionary/set operations and sorting uses O(m log(m+1)) comparisons. Only
constant-size truth sets of at most eight assignments are examined; there is
no enumeration of the original assignment space. The checker has comparable
explicit polynomial work. Counters charge input scans, bucket processing,
fixed-size arithmetic, and a stated 2*k*bit_length(k) sorting-work proxy for a
k-item sort. They are reproducible logical-work units, not exact CPU or bit
operation counts; hashing, arbitrary-size integer operations, and I/O have
their ordinary additional input-size costs. Explicit variable, clause, literal,
block, and work caps return UNKNOWN with no partial accepted proposal.

The solver keeps its original caps. Planning and plan verification are additional
work, reported separately and added to solver work in the pipeline totals. A
run with a 3,000,000 solver-work cap is therefore **not** claimed to have a
3,000,000 combined planning-and-solving cap. Solver verification work is also
reported separately and included in the end-to-end replay total. Every failed
solver request remains UNKNOWN.

The frozen solver still separates components and builds its existing balanced
binary factor trees. Contiguous groups of four clauses need not be exact
subtrees, especially when component sizes are not powers of two. For completed
certificates the runner records how many detected groups actually match a
structural node's exact factor ownership and how many do not. A certificate-free
UNKNOWN has no measured completed-tree alignment. Grouping does not assert
successful affine recovery, a minimal-width tree, an optimal merge order, or
completion within the solver caps.

## Reproducible comparison

The runner first uses the same 22 frozen original stress requests, then the
same 58 previously frozen original CNFs. Each request keeps its original n,
clause occurrences, reference count, and solver caps. The only solver option
changed is the independently checked occurrence order. Reference counts are
used only after solving to check results; no label, graph, expected answer, or
parity equation is substituted into the solver. Both newly completed requests
and regressions relative to the frozen unplanned compressed results are saved.

Full original requests, plans, plan checks, solver certificates, and solver
checks are stored in per-case gzip JSON artifacts. Their hashes, source hashes,
reference-file identity, work counters, and statuses are summarized in
`RESULTS.json`; gzip changes storage only, not the proof being checked. The
same small-input tests compare the proposed-order solver with direct original
assignment enumeration. All numeric results remain finite evidence about these
requests. Efficient recognition of a complete small parity block is familiar
preprocessing, not a new general SAT complexity result.
