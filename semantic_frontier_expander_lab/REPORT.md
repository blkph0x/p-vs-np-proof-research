# Semantic frontier lower bounds from expander graph CNFs

This lab strengthens the graph-order controls from raw boundary width to
semantic residual functions. For a graph `G=(V,E)`, use the monotone 2-CNF

`F_G = AND_{(u,v) in E} (x_u OR x_v)`.

Fix any variable order and cut it after `floor(n/2)` variables. A sequence of
pairs `(a_i,b_i)` is productive when `a_i` is in the prefix, `b_i` is in the
suffix, `{a_i,b_i}` is an edge, and no other selected prefix endpoint touches
`a_i` or `b_i`. For every assignment to the selected `a_i`, set all other
prefix variables to one. A suffix assignment that sets only `b_i` to zero then
distinguishes the two values of `a_i`. The `2^ell` prefix assignments therefore
leave pairwise distinct residual Boolean functions. This is a semantic
fooling-set certificate; it survives exact quotienting of raw frontier states.

If every set `W` of at most `n/2` vertices has open neighborhood at least
`epsilon*|W|` and the graph has maximum degree `d`, the standard greedy
closed-neighborhood argument constructs a productive sequence of length at
least `epsilon*n/(16*d)` for every order. The certificate implements that
argument directly, including the expansion witness and every residual
separation test.

The saved controls are the 3-cube, Petersen, Heawood, and a 16-vertex cyclic
3-regular bipartite graph. Expansion is recomputed exactly over every subset up
to half size. The independent verifier reconstructs the same expansion ratios,
productive pairs, lower bounds, and `2^ell` witnesses. The asymptotic existence
of bounded-degree expander families is a standard external graph-theory fact;
these finite controls are not presented as a new construction of that family.

This rules out polynomial-size OBDD/frontier compilation for the corresponding
expander graph-CNF family, while the formulas remain monotone 2-CNF and hence
trivially satisfiable by the all-one assignment. It is a representation lower
bound, not a proof that SAT requires exponential time and not a P-versus-NP
resolution. The subfunction-width formulation follows Bova and Slivovsky,
“On Compiling Structured CNFs to OBDDs,” DOI:
`10.1007/s00224-016-9715-z`.
