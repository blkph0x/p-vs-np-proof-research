# Additional original-CNF stress controls

These 22 controls supplement, and never replace, the 58 frozen earlier requests.
Their expected counts come from their complete original clause constructions,
not from either tested weighted solver. They are structured controls, not claims
of generic hardness or a resolution of P versus NP. Random cubic graphs here
are not asserted to be expanders; only simplicity, degree and connectivity are
checked. The exact edge list, random seed, generation attempts and original
clause order are retained in every request.

## Parity constraints encoded as ordinary clauses

Take a connected simple cubic graph with V vertices and E=3V/2 edges. Each edge
is one original Boolean variable. At vertex v require the XOR of its three
incident edges to equal a supplied bit b_v. Encode this equation as exactly four
clauses, one excluding each wrong-parity assignment. The verifier reconstructs
every clause occurrence from the original graph and charges, independently of
the generator's bit enumeration. No native affine factor is supplied to the
tested solvers: they receive only the original CNF.

The binary vertex-edge incidence matrix has rank V-1. The sum of all rows is
zero because every edge occurs twice, giving rank at most V-1. In a spanning
tree, repeatedly eliminate a leaf vertex and its unique remaining tree edge;
the V-1 resulting pivots prove the reverse inequality. Thus the sole consistency
condition is XOR_v b_v=0. Odd charge gives count zero; even charge gives exactly
2^(E-V+1) assignments. The verifier also calculates the matrix and augmented
rank directly, so the result is tied to each saved original graph.

The grouped and shuffled controls retain the same multiset of clauses, with
different explicit occurrence orders. Both counts must agree, but the chosen
factor tree may require different work. Any such dependence is a property of
the tested plan, not a complexity lower bound.

## Pigeonhole constraints

Use variables x_(p,h), a clause requiring at least one hole for each pigeon,
and a negative binary clause forbidding each pair of pigeons in one hole.
These clauses imply sum(x)>=number_of_pigeons from the row constraints and
sum(x)<=number_of_holes from the column constraints. One extra pigeon is
therefore unsatisfiable. When counts are equal, every row and column must have
exactly one true entry, so there are h! satisfying assignments. No extra
row-at-most-one clauses are silently added. The checker reconstructs the entire
original clause list before applying this argument.

Both old and compressed DAG methods use the same recorded original caps. New
compression work is additional, and retained/live/pending object counts are
reported separately. UNKNOWN and verification interruptions are retained; a
known analytic answer is never substituted for a failed solver result.
