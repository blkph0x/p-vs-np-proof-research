# Exact finite comparison and its limits

The producer compares the same formula rows by two independently replayable
records.  The variable order is row-major order, with variables numbered from
zero.  The frontier boundary at a cut contains an already assigned variable
when it occurs in a clause with a variable at or after the cut.  The dynamic
program stores exactly the assignments to that boundary that satisfy every
clause whose last variable has been assigned.

For the all-assignment formula on `n` variables, every clause spans all
variables.  At cuts before the final variable the boundary has sizes
`0, 1, ..., n-1`; all `2^t` states at cut `t` survive.  The final cut rejects
all `2^n` assignments.  Therefore the exact totals are

    maximum boundary width = max(0, n - 1)
    retained states = 2^n - 1
    accepted transitions = 2^n - 2.

The input itself has `n * 2^n` literal occurrences, so this identity is not a
super-polynomial-in-input-size lower bound.

For the pigeonhole formula with `h + 1` pigeons and `h` holes, row-major order
has maximum boundary width `h^2`.  Immediately before the final pigeon, all
`h^2` variables of the first `h` pigeons still occur with a future variable.
After `j` variables of the final pigeon have been assigned, exactly the
`h(h-j)` earlier same-hole variables and the `j` current-row variables remain
live, giving `h^2 - j(h-1) <= h^2`.  The first `h^2` value proves the maximum.
The independent reviewer checks this formula for every saved `h` and checks
all state and transition totals by recomputation.

CDCL rows are imported from the separately hashed proof certificates and their
proof replay.  The comparison therefore relates a supplied-order state-space
measure to one resolution proof trace.  It does not establish that frontier
width controls all proof systems, that the CDCL heuristic is optimal, or that
either quantity lower-bounds every polynomial-time SAT algorithm.

All stored textual source hashes use canonical LF line endings before hashing;
this keeps the replay invariant across the Windows producer and Linux CI.

The order extension uses the exact recurrence

    D(S) = min_{v in S} max(D(S - {v}), boundary(S)).

Every order has a final variable v, so induction on |S| proves this recurrence
finds the minimum possible maximum boundary for the primal graph. The saved
controls exhaust all subsets for 2, 6, 12, and 20 variables. Their exact
optima are 1, 3, 7, and 11, compared with row-major widths 1, 4, 9, and 16.
Those four values are finite order certificates; they do not establish an
asymptotic formula or a polynomial order-discovery algorithm.

## Width bridge

The width extension uses the complete finite weakening/resolution closure for
seven saved formulas: all-assignment instances for `n=1,...,4` and pigeonhole
instances `(2,1)`, `(3,2)`, and `(4,3)`. The independent reviewer reconstructs
each clause universe, repeats every width sweep, and checks the first width
containing the empty clause. The resulting finite minima are

    all assignments: 1, 2, 3, 4
    pigeonhole:     2, 2, 3.

The bridge aligns these rows with the supplied-order frontier state totals and
one proof-producing CDCL trace. It compares measurements from three bounded
representations; it does not prove that resolution width controls other proof
systems, that CDCL is optimal, or that either quantity lower-bounds arbitrary
SAT algorithms. The closure has explicit 100,000-clause and 500,000-candidate
caps, and any cap outcome is recorded as `UNKNOWN`.

## Semantic-clutter control

For each `n >= 1`, let

    F_n = z AND NOT z AND AND_{i<j}(x_i OR x_j).

The unit pair gives a width-one refutation, while width zero has no initial
clause and cannot derive the empty clause. The primal graph is a clique on the
`x_i` variables plus an isolated `z`. Any order has a cut immediately before
the last clique variable with the other `n-1` clique variables in the prefix,
so its boundary is at least `n-1`; ordering `z` first and the clique variables
after it attains widths `0,1,...,n-1`. The independent subset recurrence checks
this exact optimum for `n=1,...,8`.

Removing either unit leaves a model with all clique variables true and the
remaining value of `z` satisfying the one unit. Thus the large frontier is
representation clutter, not an unsatisfiable core. This does not show that
semantic preprocessing is generally easy; it shows why a frontier-based
hardness claim must account for preprocessing and discovery costs.
