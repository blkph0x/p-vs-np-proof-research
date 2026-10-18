# Keeping every clause cutoff makes matching feasibility NP-complete

The proposal examined here is to retain a separate linear cost bound for each local condition instead of summing those costs. This can preserve the intended conjunction, but the resulting problem already contains SAT. The reduction below uses only disjoint four-cycles, nonnegative 0/1 costs, and bounds at most two. It is a precise complexity classification of this augmented problem, not a P-versus-NP resolution or a hardness claim about ordinary perfect matching.

## Decision problem and theorem

The input is a finite loopless graph G=(V,E), an explicit list of q nonnegative integer edge-cost rows w_1,...,w_q, and nonnegative integer bounds b_1,...,b_q. Ask whether there is a perfect matching M satisfying

    sum_{e in M} w_j(e) <= b_j   for every j=1,...,q.

Rows and bounds are part of the input. Numbers may be binary encoded. A matching is a polynomial-size witness: verify that each original vertex occurs exactly once, then add the selected costs in every original row and compare with its bound. Exact integer additions and comparisons have polynomial bit complexity. Thus the problem belongs to NP.

**Theorem.** This problem is NP-complete even when G is a disjoint union of four-cycles, every edge-cost entry is 0 or 1, and every bound belongs to {0,1,2}. In particular the graph is simple, bipartite and has maximum degree two. The hardness persists with all numerical parameters bounded by constants, so it is strong NP-completeness in the usual numerical-encoding sense. The number q of bounds grows with the formula; no hardness for a fixed number of bounds is proved here.

The NP-complete starting problem is satisfiability with at most three literals per clause, listed as problem 11 on page 95 of Richard Karp's primary paper [*Reducibility among Combinatorial Problems* (1972)](https://link.springer.com/chapter/10.1007/978-1-4684-2001-2_9). The [original scanned paper](https://theory.stanford.edu/~trevisan/cs172-07/karp.pdf) was retrieved and its page 95 checked visually; `KARP_PAGE_95.png` preserves that source page. The following reduction and its edge weights are proved directly rather than attributed as a novel literature result.

## Construction

First remove repeated copies of a literal within each clause and drop any clause containing both a variable and its negation. These operations preserve every assignment's truth value. Every remaining nonempty clause contains distinct variables and has size at most three. Keep empty clauses for the special case below.

For each variable x_i make one four-cycle with vertices a_i,b_i,c_i,d_i and edges, in this order,

    e_i0={a_i,b_i}, e_i1={b_i,c_i},
    e_i2={c_i,d_i}, e_i3={a_i,d_i}.

Its only perfect matchings are F_i={e_i0,e_i2} and T_i={e_i1,e_i3}. Interpret them as x_i=0 and x_i=1 respectively. Since the cycles are disjoint, choosing a perfect matching of the whole graph is exactly choosing one truth value for every variable. The same cycle choice is shared by every cost row, so variable consistency is automatic.

For a nonempty normalized clause C_j, initialize its entire cost row to zero. For each positive literal x_i in it, put weight one on e_i0, which is selected exactly when x_i=0. For each negative literal NOT x_i, put weight one on e_i1, selected exactly when x_i=1. Set

    b_j = |C_j|-1.

Each literal therefore contributes one exactly when it is false. No clause contains a repeated variable after normalization, so these assignments never require a cost larger than one. Only one representative edge of each relevant matching is charged; charging both would incorrectly double the literal count.

Under the matching corresponding to assignment x,

    sum_{e in M_x} w_j(e) = number of false literals in C_j.

Consequently the jth bound holds exactly when C_j has a true literal. All bounds hold exactly when the entire formula is satisfied. This proves both directions, including recovery of a satisfying assignment from any feasible matching.

For an empty clause, use a row charging all four edges of one designated cycle with weight one and bound one. Every perfect matching selects exactly two of those edges and violates this bound. If there are no variables, add a dummy four-cycle for this purpose. This preserves the graph and numerical restrictions and correctly represents an unsatisfiable input. A formula with no clauses and no variables maps to the empty graph, whose empty perfect matching is feasible. Tautological and repeated-literal input clauses are handled by the normalization above, not by silently assuming their absence.

There are four vertices and four edges per variable, with at most one dummy cycle. There is at most one bound per input clause. A dense cost matrix has O(nm) entries; a sparse representation has at most three nonzero entries per nonempty clause row (four for an empty-clause row). Either representation is polynomial in the explicit formula size. Unused named variables can first be discarded or renumbered so that n does not depend on a large binary variable label. The implementation accepts an explicit variable count; the polynomial reduction uses the variables actually present in the formula.

For the hardness restriction, repeated whole clauses may also be discarded before the construction. At most sum_{r=0}^3 2^r binomial(n,r) normalized clauses remain. Thus the theorem holds with a number of bounds polynomial even in the graph's vertex count. Retaining repeated clause rows, as the executable controls permit, does not change feasibility.

This establishes NP-hardness, and NP membership completes the theorem. Keeping all the same rows and graph but dropping the bounds makes every instance immediately feasible: choose F_i in each cycle. Even an arbitrary single linear edge objective is easy on this graph, since one independently chooses the cheaper of F_i and T_i in each component. The difficulty demonstrated is the conjunction of many global bounds on the same matching.

## Concrete controls

The formula (x OR y OR z) AND (NOT x OR y) AND (NOT y OR z) is a satisfiable example; its satisfying assignments extend directly to bounded matchings.

The two unit clauses (x) AND (NOT x) produce two bounds of zero. They require opposite matchings of the same cycle, so no matching obeys both.

A control using only distinct-variable clauses of length exactly three takes all eight polarity choices on x,y,z. Every assignment falsifies exactly one clause, so no matching satisfies all eight bounds of two. Nevertheless, for every assignment the eight objective values are a permutation of

    0,1,1,1,2,2,2,3.

Their sum is 12, below the sum of the bounds, 16. Thus replacing these eight inequalities by the single unweighted sum inequality accepts every matching of this unsatisfiable instance. This is one explicit failure of that particular aggregation, not a claim that every possible scalar reduction or different encoding is impossible.

## Executable evidence and scope

`clause_bounds.py` builds the original graph and rows and supplies an exact vertex-coverage and cost-bound witness checker. Its bounded generic graph oracle does not know the cycle encoding. The experiment compares all matching outcomes with direct evaluation of the original, unnormalized CNF; it also checks each row's exact false-literal count. The tests additionally use a separate edge-subset oracle for every pair of raw two-variable clauses of length at most two, including duplicates, tautologies and empty clauses. Mutation controls reject malformed witnesses and cost rows. Verification always uses the supplied original instance; accepting a witness for a modified bound does not certify the old request.

`RESULTS.json` stores explicit SAT/UNSAT instances, assignments, matching edge IDs, exact row costs and violated bounds, together with source hashes. Exhaustive and seeded checks are finite validation of the construction; the all-size conclusion follows from the reduction proof. Enumeration budgets fail explicitly instead of reporting an unfinished search as infeasible.

Run in this directory:

    python -m unittest -v test_clause_bounds
    python clause_bounds.py

The proof concerns exact feasibility with polynomially many simultaneous bounds. It does not establish strong hardness for a fixed number of objectives, make ordinary matching hard, classify approximation or parameterized algorithms, or prove P differs from NP. A general polynomial algorithm for this augmented problem would imply P=NP; this reduction supplies no such algorithm and rules out no particular future proof method.
