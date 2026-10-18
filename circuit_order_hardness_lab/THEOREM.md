# Source-primal lower bound for Tseitin circuit orders

For an undirected graph `G=(V,E)`, create one source variable `x_v` for each
vertex and, for every edge `{u,v}`, an OR gate `z_e = x_u OR x_v`. Encode each
gate with its exact three-clause Tseitin relation and add the unit clause
`z_e`. Call the resulting CNF `C(G)`.

The all-one source assignment extends to a satisfying assignment of `C(G)`,
so this family has a trivial SAT witness for every input graph.

The primal graph of `C(G)` contains `G` on the source variables: the clause
`(x_u OR x_v OR NOT z_e)` puts the edge `{x_u,x_v}` into the primal graph.
For any variable order of `C(G)`, restrict the order to source variables. At
the cut immediately after each source prefix, every source vertex that has a
future source neighbor is also active in the full primal graph. Therefore

    minimum vertex-separation width(C(G)) >= pathwidth(G),

using the standard equality between minimum vertex separation and pathwidth.
The statement is a direct boundary certificate and does not rely on the gate
ordering or on a SAT solver's heuristic.

There is also a matching additive upper bound for this construction. Take a
source order of width `w`. After each source vertex is placed, place all edge
gates whose later endpoint is that vertex. Before the endpoint is placed, its
already-placed neighbors are among the previous source boundary, so at most
`w` source vertices can be carried forward. After the endpoint is placed, it
can add one active source vertex while its pending gates are discharged. Gate
variables already placed have no future neighbor. Hence the extended order
has width at most `w+1`, and

    pathwidth(G) <= pathwidth(C(G)) <= pathwidth(G)+1.

The upper-bound construction is replayed in the saved controls. The interval
is a structural statement about this pinned-OR family; it does not make
minimum-order discovery polynomial for arbitrary formulas.

The saved controls compute both exact widths by subset dynamic programming and
replay the inequality independently. The full circuit can have a larger width
because gate variables add scopes; that gap is measured rather than silently
ignored. This is a lower-bound bridge for a search representation, not a
P-versus-NP proof: it leaves open other orders, native representations and
algorithms that do not enumerate active-variable frontiers.
