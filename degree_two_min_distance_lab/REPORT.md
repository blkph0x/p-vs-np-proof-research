# Homogeneous minimum distance with column weight at most two

For a binary parity-check matrix whose columns have weight at most two, build
an undirected multigraph on the check rows. A weight-two column is an ordinary
edge. A weight-one column is an edge to a dummy vertex whose parity is not
constrained. A zero column is an immediate weight-one codeword.

Any nonzero homogeneous codeword supported only on ordinary edges is an
Eulerian subgraph, so it contains a cycle. Any codeword using dummy edges uses
an even number of them; one path between two dummy endpoints, together with
those two columns, is no heavier than the whole support. Therefore the exact
minimum distance is the minimum of:

1. the shortest ordinary multigraph cycle; and
2. two dummy columns plus the shortest ordinary path between their endpoints.

Breadth-first search finds each shortest path. Running it once per ordinary
edge for cycles and once per pair of weight-one columns is polynomial in the
explicit matrix size: with `r` rows, `e` weight-two columns, and `t` weight-one
columns, the work is `O((e+t^2)(r+e))` and the stored graph is linear. The
certificate records the selected columns, checks the zero syndrome, and an
independent brute-force verifier matches all saved controls. The six named
adversarial controls cover duplicate/parallel edges, a forest with no nonzero
kernel, and a zero column; 96 additional deterministic random instances with
at most eight columns are also checked exhaustively.

This gives a complete positive algorithm for the degree-two boundary. The
project's separate degree-three affine reduction is NP-complete for a nonzero
syndrome, while a 2026 primary preprint records homogeneous minimum-distance
hardness already at constant column weight three. The degree-two solver does
not imply a general SAT algorithm or resolve P versus NP; it identifies the
first sparse parity regime where the graph reduction is genuinely polynomial.
