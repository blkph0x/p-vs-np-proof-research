# Width preservation under the two-bridge exact-one gadget

For a positive exact-one clause on original variables `(x,y,w)`, introduce
fresh bits `(z0,z1)` and use the fixed scopes

    H(x,z0,z1),       A(y,w,z0,z1),

where `H` and `A` are the Horn and affine relations in
`TWO_BRIDGE_FACTOR_THEOREM.md`. Let `G` be the primal graph of the original
exact-one formula, with a triangle on every clause, and let `G'` be the primal
graph after this replacement.

The original graph is a minor of `G'`: for each clause contract the edge
`x-z0`. The affine scope then supplies edges `x-y` and `x-w`, while `y-w` was
already present. Delete the remaining bridge vertices and duplicate edges.
Pathwidth is minor-monotone: deleting vertices or edges cannot increase a path
decomposition, and contracting an edge replaces its two overlapping bag
intervals by their union without increasing the largest bag. Hence

    pathwidth(G) <= pathwidth(G').

For the reverse direction, take a path decomposition of `G` of width `p`.
Every clause triangle occurs together in some bag (the bag intervals of a
clique pairwise intersect). Insert a new bag containing that triangle and its
two fresh bridge vertices next to that bag. This covers both gadget scopes and
the bridge edge, and has size at most five. Since any nonempty clause gives
`p >= 2`, the resulting width is at most `p+2`; the empty formula is unchanged.
Therefore

    pathwidth(G) <= pathwidth(G') <= pathwidth(G)+2.

The bound is about the fixed local encoding and primal-graph/pathwidth
representations. It does not prove a lower bound for arbitrary algorithms or
resolve P versus NP. The saved finite controls compute both widths exactly on
all 16 four-variable clause families, and an independent replay checks every
bound and source hash.
