# Exact order discovery and its charged exponential cost

For a graph with vertex set `V`, let `b(S)` be the number of vertices in a
prefix `S` that have a neighbor outside `S`. For a supplied order, the maximum
of `b(S)` is its vertex-separation width.

The exact order oracle uses the recurrence

    D(empty) = 0,
    D(S) = min_{v in S} max(D(S-{v}), b(S)).

The minimizing predecessor is saved, so an optimal order is reconstructed by
backtracking. Induction on the final vertex proves the recurrence: every order
of `S` has a final vertex `v`, and all earlier prefixes form an order of
`S-{v}`; conversely appending `v` realizes the displayed maximum.

The oracle evaluates every subset and every candidate final vertex, using
`O(n 2^n)` transitions and `O(2^n)` storage. It is an exact audit algorithm,
not a polynomial discovery theorem.

The mixed relation solver composes with the reconstructed order. On the saved
two-bridge exact-one controls, the discovered order is replayed by the
proof-producing frontier DP and matches direct satisfiability. The saved
adversarial counts retain the subset and transition work, so order discovery
is not hidden inside a successful solve.
