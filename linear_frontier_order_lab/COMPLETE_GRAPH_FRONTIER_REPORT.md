# Complete-graph all-order frontier barrier

This certificate targets exact dynamic programs for binary affine systems that
store the residual right-hand side at a variable-order cut. It proves an
all-order lower bound for a very easy satisfiable family.

For `K_v`, make one binary variable `x_e` for every edge and impose the vertex
parity equations

`sum(e incident to u) x_e = 0` for every vertex `u`.

The incidence matrix has rank `v-1`; the all-zero assignment is an immediate
witness. Let `P` be a prefix of an arbitrary edge order and `S` its suffix. If
`c(P)` and `c(S)` are the numbers of connected components of the two spanning
subgraphs (isolated vertices included), their incidence ranks are `v-c(P)` and
`v-c(S)`. The number of live affine residual classes is therefore

`lambda(P) = v + 1 - c(P) - c(S)`.

Let `m=binomial(v,2)`, `h=floor(m/2)`, and let `s` be the smallest integer with
`binomial(s,2) >= h`. Every graph on `v` vertices with at least `h` edges and
`c` components has

`h <= binomial(v-c+1,2)`,

because concentrating all vertices except the `c-1` isolates into one clique
maximizes the edge count. A half-edge prefix can attain this component bound by
putting all `h` edges in one connected component on `s` vertices and leaving
the other vertices isolated; its complement is connected. Hence the exact
half-cut minimum is

`min_{|P|=h} lambda(P) = s-1`.

The certificate also checks the stronger cutwise identity. For a cut with
`k` edges, put `d=min(k,m-k)` and define `q(0)=0`, while for `d>0` let `q(d)`
be one less than the smallest `t` with `binomial(t,2) >= d`. Then

`min_{|P|=k} lambda(P) = q(d)`.

For `k <= m/2`, if `P` is disconnected its complement is connected and the
component bound gives `c(P)+c(S) <= v+2-t`; if `P` is connected, the same
bound applies to `S`, which has at least as many edges. Equality is achieved by
packing the `k` edges into a connected component on the smallest feasible
vertex set and leaving the other vertices isolated. The case `k > m/2`
follows by exchanging `P` and `S`. Thus the halfway cut is the maximum of the
exact cutwise minima, rather than merely one convenient cut.

The residual classes are disjoint affine right-hand-side cosets, so an exact
frontier DP keyed by that residual must retain at least
`2^(s-1)` states on every edge order. Since
`s = (1/sqrt(2)+o(1))v`, the exponent is
`(1/sqrt(2)+o(1))v`.

The finite certificate exhausts every halfway edge subset for `v=4,5,6,7`,
every cut size for `v=4,5,6`, and replays five deterministic orders per case.
The cutwise formula sweep checks `v=4..64`; at `v=64` the halfway bound is
`lambda >= 45`, hence at least `35,184,372,088,832` residual classes. The
independent verifier reconstructs all incidence ranks, component counts,
cutwise minima, halfway witnesses, sampled orders and the forged-bound
rejection.

If the matrix is serialized explicitly, it has `m` columns of `v` bits, so its
bit length is `Theta(v^3)` and the state lower bound is
`2^(Omega(L^(1/3)))`; in column count it is `2^(Omega(sqrt(m)))`.
The same family has a sparse edge-list description: each variable records two
endpoints, each in `ceil(log_2 v)` bits, so the `m=binomial(v,2)` edge
records give input length `Theta(v^2 log v)` (the equation headers are lower
order). Since `s=Theta(v)`, inversion gives the bound
`2^(Omega(sqrt(L/log L)))` under that encoding. This is still a barrier for
the chosen residual-frontier representation, not a lower bound for arbitrary
algorithms or encodings.

This is a lower bound for the residual-frontier representation. Gaussian
elimination solves the same parity system in polynomial time, and the family
does not establish `P != NP`.
