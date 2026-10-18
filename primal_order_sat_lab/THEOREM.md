# Exact primal-order search and conditional SAT solving

For a CNF $F$, form its primal graph by joining two variables whenever they
occur in a common clause. Fix an order and a cut. A processed variable is in
the SAT frontier exactly when it occurs in a clause containing an unprocessed
variable. This is equivalent to having a primal-graph neighbor on the
unprocessed side of the cut, so the SAT frontier width is the graph vertex-
separation width of the same order.

The subset dynamic program stores, for each processed set $S$, the lexicographically
first order reaching $S$ with the smallest bottleneck width. Extending by one
variable updates the bottleneck with the boundary of the new set. Induction over
subsets proves that the final record is an exact minimum-width order. The saved
records expose every subset and boundary, and the independent reviewer rebuilds
them from clause scopes rather than importing the primal-graph code.

Given that order, the frontier SAT DP enumerates at most $2^w$ states per cut,
where $w$ is the exact minimum boundary width, and checks all clauses when their
last variable arrives. Therefore the combined small-instance algorithm is exact,
but its order search takes exponential time in the number of variables and its
SAT phase is exponential in the resulting width.

The monotone two-clause construction $F_G=\bigwedge_{uv\in E(G)}(x_u\lor x_v)$
has the same primal graph as $G$ and is always satisfiable. Consequently, a
polynomial universal minimum-order routine for this route would imply a
polynomial routine for the corresponding vertex-separation layout problem. The
construction is a reduction of the order subproblem; it is not a proof that
SAT itself is outside P.
