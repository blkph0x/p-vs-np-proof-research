# Original-CNF counting reference

This bounded branch/component reference counts satisfying logical assignments of
the external original CNF. It does **not** count slack encodings. Duplicate
clauses/literals and tautologies are normalized only because they preserve this
Boolean function. The producer reuses existing project restriction and component
utilities. Its checker independently reconstructs each restriction and component.
This is an exponential reference algorithm; no new polynomial SAT claim is made.

Let V(F) be the variables actually mentioned by normalized F, and C(F) its
satisfying assignments on V(F). An empty formula has C=1; a formula containing an
empty clause has C=0. For a unit literal on v, its satisfying restriction G has
C(F)=2^(|V(F)|-1-|V(G)|) C(G). For an ordinary branch on v, sum that expression for
both values of v. The factor counts variables that disappear when clauses become
satisfied. Variable-disjoint components multiply. The original n-variable answer
is 2^(n-|V(F)|) C(F). These identities follow by partitioning assignments on v
and by the Cartesian product of independent component assignments.

The certificate is a topologically ordered DAG bound to every original clause
occurrence and original n by a binary hash, and also checked against the full
normalized root. Every child must equal its independently computed restriction;
component variable sets must be disjoint and their clause union must cover the
parent exactly. All supplied nodes must be reachable. Values are recomputed;
supplied counts are never trusted. The original input must be supplied separately.

There can be exponentially many states, and the certificate can be exponentially
large. Each state stores a full residual formula. Counts have at most n+1 bits.
Reported work units include input/residual literal scans and an upper bound on
the clause-pair construction in the legacy component finder; they are not CPU
instruction counts. Sorting, hashing, and Python container overhead remain within
polynomial factors of stored state size. Limits on states, work, dimensions,
depth, and count bits yield UNKNOWN with no count or partial certificate.

The test oracle directly enumerates original logical assignments independently.
Large controls have separate recurrences: disjoint ternary clauses count 7^m;
all positive binary pairs on n variables count n+1; a chain of m ternary clauses
sharing alternate endpoints has C_0=2, C_1=7 and C_m=3 C_(m-1)+2 C_(m-2).
The latter follows from the two-state transfer matrix [[1,2],[2,2]], whose
characteristic polynomial is t^2-3t-2. These controls do not bound general SAT.

The two planted originals also receive a separate complete truth-table count
using bitsets: enumerate the first half of the variables and store every
assignment to the second half in an integer bit vector. Intersect the clause
satisfaction masks and count set bits. This does not prune logical assignments
by the producer's recurrence. Both the bit width and outer iteration count are
exponential, and reported AND counts must be multiplied by bit width when
estimating bit work. A separate four-state transfer checks the signed consecutive
triple chain. These routines are compared against ordinary truth enumeration on
small random formulas before use on the larger original controls.
