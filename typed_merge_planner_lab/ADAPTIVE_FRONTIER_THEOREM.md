# Adaptive frontier SAT solver

This lab composes two exact finite procedures: minimum vertex-separation order
discovery on the primal graph, followed by the cut-by-cut relation frontier
dynamic program.

For a relation instance with variables `V`, the primal graph joins two
variables whenever they occur in one constraint scope.  For a processed prefix
`S`, let `b(S)` be the number of processed variables adjacent to an unprocessed
variable.  The order oracle evaluates

    D(empty) = 0,
    D(S) = min_{v in S} max(D(S - {v}), b(S)).

The saved predecessor proves by induction that the reconstructed order has
minimum vertex-separation width.  Given that order, the frontier DP stores
exactly the boundary assignments that extend through every constraint whose
last variable has been processed.  Restricting a transition to the next
boundary is existential projection, so duplicate states are safely merged.
At the final empty boundary, the empty state is present exactly when the
instance is satisfiable.

The bounded solver therefore returns an exact SAT or UNSAT result for every
finite relation instance with `n <= max_order_variables`, and it saves both the
order certificate and every frontier cut.  It returns `UNKNOWN` above the
explicit order cap.

For a supplied order of width `w`, frontier work is
`O(n * 2^w * R)` up to relation-table membership costs.  Automatic minimum
order discovery costs `O(n * 2^n)` transitions and `O(2^n)` storage.  Building
the primal graph costs `O(sum_i |scope_i|^2)`.  A dense-scope control reaches
width `n-1`, so the composition is not a polynomial SAT algorithm: the
certificate charges both the order search and the frontier state space instead
of hiding either cost.  The result is a parameterized exact solver and a
reproducible boundary experiment, not a resolution of P versus NP.
