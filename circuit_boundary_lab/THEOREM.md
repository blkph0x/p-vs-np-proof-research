# Circuit-to-CNF boundary control

This lab turns the nonlinear Hamming-weight circuit into a standard Tseitin
CNF and measures the exact frontier seen by the proof-producing SAT engine.
Source variable `i+1` denotes bit `i`. Each parity chain uses the four-clause
XOR relation, each accumulator step uses the three-clause AND relation and the
same XOR relation, and constants are pinned by unit clauses.

For every source assignment, the gate values are unique. The XOR and AND
clause tables are exact truth-table definitions, so the CNF has a satisfying
extension with output value `h(u)` and no satisfying extension with a different
output value. Pinning source variables and output bits therefore gives a
correct SAT query for the corresponding Hamming weight.

The circuit is compact, but the CNF is a general constraint system. A supplied
variable order yields an exact frontier DP, whose state count is exponential in
the active boundary width. The saved controls use a small circuit so every
query can be replayed by the existing certificate-producing SAT engine; an
independent checker evaluates the gates directly and recomputes the boundary
scopes. This is a representation-transfer audit, not a universal solver or a
P-versus-NP lower bound.

The order control separates representation from discovery. On the three-form,
three-bit circuit, the saved topological order has width 6, while exact
subset-DP finds width 4 after retaining 262,144 subset states. The independent
replay recomputes both numbers. This is finite evidence that even after
nonlinear compression, finding the best frontier order is a separate
exponential subproblem.

The distance control adds the actual decision query: constrain the output
bits to be at most `t` with exact finite-width clauses and require a nonzero
source assignment. For the seven-form control containing every nonzero
three-bit form, direct enumeration proves minimum nonzero weight four; the
frontier solver returns UNSAT for thresholds 0, 1, 2 and 3 and SAT for 4.
This is a complete bounded optimization certificate, while its state and
order costs remain those of the general SAT instance.

The threshold clauses use a ripple comparator rather than enumerating forbidden
output words. It scans the output bits from most significant to least
significant with equality, less-than, NOT, AND and OR gates, so the comparator
adds O(log n) gates and clauses for an n-form objective. Independent replay
checks every comparator output on all eight source assignments of the distance
control.
