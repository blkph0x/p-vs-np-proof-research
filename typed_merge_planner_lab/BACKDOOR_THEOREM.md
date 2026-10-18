# Strong Schaefer backdoor solver

This lab makes one parameterized planner edge executable.  A supplied set
`B` is a **strong backdoor** to Horn (respectively affine) relations when,
for every assignment to `B`, restricting every explicit relation produces an
AND-closed (respectively minority-closed) relation or the empty relation.

The solver enumerates the `2^|B|` assignments to `B`.  Each residual Horn
instance is converted to its complete canonical Horn clause set and solved by
forward chaining.  Each residual affine instance is converted to GF(2)
equations and solved by Gaussian elimination.  The returned certificate keeps
the branch assignments, residual signatures, branch status, and any satisfying
witness; the original constraints are checked again before a SAT result is
returned.

For explicitly listed truth tables, the relation table length is part of the
input.  Enumerating all candidate Horn clauses or all orthogonal masks is
polynomial in that explicit length (though intentionally unoptimized here).
The total bound is therefore `2^k * poly(explicit-input-size)` for a supplied
backdoor of size `k`.  Finding a small backdoor, or proving that an arbitrary
CNF has one, is not included.  If any branch leaves the target language, the
solver returns `UNKNOWN` rather than silently using the native solver.

The exact-one control is adversarial: assigning one variable per clause turns
positive 1-in-3 constraints into affine residuals, while the unassigned
relation is not affine.  This demonstrates a real FPT boundary and preserves
the existing Horn+affine NP-hardness result instead of treating a supplied
backdoor as a universal decomposition theorem.
