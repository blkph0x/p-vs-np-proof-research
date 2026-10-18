# Exact frontier DP for mixed Horn/affine relations

For a finite Boolean relation instance and a supplied variable order, define
the boundary at cut `k` as the processed variables that occur in a constraint
with an unprocessed variable. A state is an assignment to that boundary which
extends to every constraint whose last variable has already been processed.

When the next variable is assigned, only constraints whose last variable is
that variable become decidable. Every other variable in such a constraint is
still on the old boundary. The transition checks the relation tuple, then
restricts the assignment to the new boundary. Merging duplicate boundary
assignments is existential projection. Induction on the cuts proves that the
stored states are exactly the extendable partial assignments.

At the final empty boundary, the sole empty state is present exactly when the
instance is satisfiable. The implementation records each boundary, state and
accepted transition; the independent reviewer recomputes the same objects
without importing the solver.

If the maximum boundary size is `w`, there are at most `2^w` states at every
cut and at most two transitions per state for Boolean variables. Relation tuple
membership is polynomial in the explicitly supplied relation tables. Thus this
is an exact fixed-order algorithm, with proof-producing cost
`O(n 2^w)` up to relation-table factors.

The two-bridge exact-one reduction is an adversarial control: its factors are
locally Horn and affine, but the global frontier still follows the original
clause structure. This theorem supplies a parameterized solver, not a uniform
polynomial algorithm, because discovering an order of bounded width remains a
separate problem.
