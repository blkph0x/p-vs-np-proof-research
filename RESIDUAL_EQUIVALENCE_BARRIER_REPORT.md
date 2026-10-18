# Exact future-equivalence barrier

**Status:** source-bound complexity barrier with finite replay. It does not prove
P=NP or P!=NP.

The exact future-equivalence problem asks whether two assignments to a frontier
produce the same residual Boolean function on the remaining variables. The
following reduction is deliberately tiny. Given any CNF `G(y)`, form

    F(z,y) = G(y) AND (NOT z).

At the cut whose boundary is the single variable `z`:

- assigning `z=0` leaves the residual function `G(y)`;
- assigning `z=1` leaves the constant-false function.

The two residuals are equal exactly when `G` is unsatisfiable. Therefore exact
residual-equivalence testing is coNP-hard even when the boundary has width one.
It is also in coNP for the ordinary explicit-CNF representation: a witness for
non-equivalence is one assignment to `y` on which the two residuals differ.
Thus the general equivalence problem is coNP-complete under this representation.

The consequence for the solver architecture is conditional and precise. A
polynomial algorithm that always computed the exact future-equivalence quotient
of arbitrary frontier states would decide this coNP-complete problem in
polynomial time. Consequently, quotient minimization cannot be treated as a
free universal preprocessing step unless the corresponding complexity collapse
is accepted. The obstruction applies even before large interfaces appear; the
boundary is one bit, while the hidden suffix formula is arbitrary.

The finite replay exhaustively checks all 256 subsets of the eight possible
non-tautological clauses over two variables. It finds 95 satisfiable `G`
instances and 161 unsatisfiable instances, with exactly the same split between
non-equivalent and equivalent residuals. Additional empty, contradictory, and
mixed controls are serialized. A separate checker recomputes every model set,
residual truth table, and equivalence decision without importing the producer.

This does not rule out useful quotienting on restricted proof languages. It
supports the stricter design rule already used elsewhere in the project:
discover quotients only with a bounded cap, a structural theorem, or a
proof-carrying certificate; otherwise return `UNKNOWN` or retain the raw states.

Artifacts:

- `residual_equivalence_barrier.py` — reduction replay and finite generator;
- `verify_residual_equivalence_barrier.py` — independent checker;
- `test_residual_equivalence_barrier.py` — exhaustive small controls;
- `RESIDUAL_EQUIVALENCE_BARRIER.json` — serialized evidence.

