# Review: graph perturbations, exceptional rank, and changes of native representation

**Status:** mathematical review only; stable solver modules were not changed.
Low-rank structure gives a substantive extension, but two different parameters
lead to different algorithms. Neither is a universal coverage theorem.

## 1. Two notions of low rank must be kept separate

### A. Disjoint exceptional coordinates

Suppose a certified row representation splits the columns into

    H = [B | D],

where B is reduced graph incidence (columns of weight at most two), D has q
columns, and p=rank(D). The variables on B and D are disjoint. A choice of
exceptional variables affects the graph only through its target syndrome.

### B. A perturbation affecting the same graph coordinates

Suppose instead that

    H = B + U V,

where B is reduced graph incidence, U has p columns, and V has p rows. Both
B and UV act on the same edge coordinates. The matrices B,U,V, row changes,
and transformed target must be supplied or found and checked.

The first case admits a deterministic syndrome DP plus ordinary T-joins. The
second introduces parity constraints on the selected graph edges. Calling both
cases a rank-p graph correction would obscure an essential difference.

## 2. The exceptional-column rank DP is correct

Choose a basis Q for span(D), write each exceptional column as Q*d_i, and work
with p-bit coordinates. Let f_i(t) be the least weight of a subset of the first
i exceptional columns whose XOR is t. For unit weights,

    f_0(0)=0, f_0(t!=0)=infinity,
    f_i(t)=min(f_(i-1)(t), 1+f_(i-1)(t XOR d_i)).

This is an ordinary exact subset recurrence. Every subset either excludes or
includes column i, so induction proves completeness and optimality. Preserve
predecessors for reconstruction. Each column is processed once, costing
O(q*2^p) transitions; the syndrome basis and column coordinates are found by
polynomial-time linear algebra. Nonnegative weights replace the constant one
by the column weight without changing the recurrence.

For each of at most 2^p reachable syndromes t, solve the graph problem

    B*x_B = s XOR Q*t,

and add f_q(t). Thus, with a supplied representation, the algorithm costs

    O(q*2^p) + 2^p * polynomial graph/matching work,

plus polynomial linear algebra and certificate work. This can be exponentially
smaller than enumerating 2^q exceptional assignments. It is deterministic and
does not require parity-constrained matching.

### The nonzero case

If the requested full syndrome is nonzero, every feasible full word is already
nonzero. If the requested syndrome is zero, the sole special syndrome state is
t=0: its unrestricted optimum is the empty exceptional subset and the empty
graph T-join. Keep the least **nonempty** exceptional subset with syndrome zero
as well. Compare its weight with the shortest nonempty graph cycle. All other
reachable t already require nonempty exceptional support.

One can equivalently keep a nonempty flag at all DP states. This is useful for
implementation simplicity and for zero-weight columns. A cheaper empty witness
must never overwrite the only nonempty zero-syndrome witness.

For arbitrary s the exact special-case logic is: reject the all-zero complete
word only when s=0 and the caller explicitly requests a nonzero word. A coset
solver must not universally reject a zero graph residual.

### Certificates

Checking the recurrence at every state certifies the exceptional optimum. The
existing ordinary T-join certificate certifies each graph optimum. Their
combination supplies a deterministic global optimum certificate. If some
syndrome states or graph calls are skipped for budget reasons, the result
remains an upper bound/UNKNOWN unless a separate lower bound closes the gap.

This extension uses no novelty claim. It is the standard syndrome DP applied
only to the exceptional span rather than the full code.

## 3. Exact reduction for a general rank-p perturbation

For H=B+UV and requested target s, set z=Vx. Then

    Hx=s
      iff there is z in GF(2)^p with
          Bx=s XOR Uz AND Vx=z.

Every feasible x has exactly one such z. Consequently enumerating z gives at
most 2^p branches, but each branch is a T-join with p additional XOR constraints
on its edge set. Label edge e by column V_e; its selected labels must XOR to z.

If B is reduced incidence, add a ground vertex and complete its target parity
as in the existing native solver. That restores an ordinary even terminal set;
it does not remove the label condition Vx=z.

### A smallest failure of dropping the label condition

Take one graph edge with incidence column b=(1,1), U=b, and V=(1). Then H=0.
For target s=b the original system is infeasible. If a branch z=0 only solves
Bx=b, it returns x=1, but Vx=1 disagrees with z=0. The z=1 branch only solves
Bx=0 and returns x=0, again disagreeing with its label demand. Both ordinary
T-joins exist; neither is a valid original solution.

Postchecking only the cheapest ordinary T-join is also insufficient. In a
triangle, let the direct u-v edge have label one and the two-edge u-w-v path
have label zero on both edges. For terminals {u,v} and demanded label zero,
the ordinary optimum is the wrong one-edge path; the constrained optimum is
the valid two-edge path. Rejecting the ordinary optimum would miss it.

### Disconnected cycles matter

Take a label-zero u-v edge and a disjoint triangle whose total label is one.
The demanded {u,v}-join of label one is the edge plus that triangle. A search
for a single labelled walk from u to v cannot reach the triangle. Correct
parity-join algorithms must allow disconnected Eulerian components.

## 4. What is known about parity-constrained matching

[Geelen and Kapadia, Theorems 5.6 and 6.7](https://arxiv.org/pdf/1504.07647)
give randomized algorithms for fixed-dimensional parity matching and parity
T-joins. Their matching weights are unary/nonnegative; the weight dependence
is pseudopolynomial if arbitrary binary-encoded costs are substituted. Unit
edge costs in the present code problem fit their application. Their method
uses labelled walks, parity matching, and Pfaffians. Its parameter-sized
tables and ring give an FPT dependence on parity dimension; the displayed
polynomial bounds suppress that dependence. It is not an ordinary blossom
call, and a fixed-dimension theorem alone does not justify ignoring the
parameter when it grows. Their Theorems 1.1 and 1.2 apply to a **supplied**
graphic perturbation representation, not to discovering one on arbitrary
matrices. The zero/nonzero distinction remains explicit in their girth
reduction.

For this project's rigorous accounting, use the conservative conclusion:
the supplied unit-weight perturbation route has a randomized FPT algorithm,
with parameter dependence and error probability to be exposed before any
implementation is promoted. Do not silently substitute `2^p` ordinary
T-joins or claim an unconditionally certified optimum from random evaluation.

The exact exponent in a practical implementation still needs a bit-complexity
audit. In particular, a brute-force routine over all subsets of the 2^p labels
can introduce a double exponential even though the parameter remains FPT.
For logarithmically growing p, that distinction changes whether the route is
polynomial. The exceptional-rank DP of section 2 has the explicit single
exponential bound and does not have this ambiguity.

### One parity feasibility is weaker than parity optimization

El Maalouly, Steiner, and Wulf distinguish finding a perfect matching with the
correct parity from finding one with both that parity and a weight bound.
They give deterministic polynomial feasibility for one parity on general
graphs, and a stronger bounded result on bipartite graphs. Those statements
do not provide arbitrary-cost, multi-parity optimization on general graphs.
See [Exact Matching: Correct Parity and FPT Parameterized by Independence
Number](https://arxiv.org/pdf/2207.09797).

Schlotter and Sebő's published 2025 treatment also gives a deterministic FPT
algorithm for nonnegative minimum odd T-join using an additional component
parameter. It does not turn every fixed-one-parity optimization instance into
an ordinary shortest-path computation. Its NP-hard conservative-weight odd
**path** problem must not be confused with the nonnegative T-join problem.
See [Odd Paths, Cycles and T-joins](https://arxiv.org/abs/2211.12862).

### Practical missing certificate

A random algebraic search can output a feasible edge set whose syndrome,
labels, and weight are checked exactly. That certifies an upper bound.
Absence of a missed cheaper matching is a separate obligation. The existing
ordinary matching dual variables do not automatically certify optimality
inside a prescribed-parity class. A production route needs either a valid
parity-optimality certificate, an explicitly probabilistic status, or an exact
fallback. It must not reuse unconditional EXACT semantics without justification.

## 5. A deterministic restricted perturbation route worth testing

There is a clean additional parameter: the maximum number b of graph terminals
in any branch s+Uz. Suppose b is small. Enumerate all pairings of those
terminals and all parity-label allocations among the pairs. Solve each
two-terminal labelled join, including the possible disconnected cycle part,
and XOR the results. For a fixed even b, there are (b-1)!! pairings and at most
2^(p*b/2) label allocations before enforcing their total XOR.

Why this is exact: every T-join decomposes into terminal-pair paths and cycles.
Assign its cycles to one pair when T is nonempty, giving a partition into
two-terminal joins. Conversely XOR of a family of labelled pair joins has the
correct boundary and total label and cannot cost more than their sum for
nonnegative edge weights. Comparing the two directions proves equality of
the optimum values. The zero-terminal branch is a labelled Eulerian-subgraph
problem and is handled separately. Excluding an empty full result also needs
the usual edge-pinning/nonempty logic.

For example, if every column of U has support at most two and s=0, then
b<=2p. This gives a deterministic FPT special case using the labelled
two-terminal primitives; it may change many edge columns even when p is one.
It is therefore not identical to bounding the number of exceptional columns.
But densely supported columns of U need not have small b, so this observation
does not solve general parity matching deterministically.

## 6. Unbounded perturbation dimension is already NP-hard

The parity-label dimension cannot simply be ignored. Here is an elementary
reduction using a very easy underlying graph.

Start with any affine syndrome system Az=t, including the three-set exact-cover
encoding already proved in `degree_three_barrier.py`. Make a disjoint triangle
for each variable z_i. Assign label A_i to one edge of that triangle and zero
to its other two edges. Require graph boundary zero and total label t.

An Eulerian subset of a triangle is either empty or all three edges. Thus the
selected triangles correspond exactly to the chosen variables z, and total
edge weight equals 3*weight(z). The graph is a disjoint union of simple
triangles with unit weights, but arbitrary-dimensional labels recover general
affine-plus-cardinality optimization.

The stacked matrix [B; labels] is a rank-at-most-rank(A) perturbation of
[B; 0], which is incidence with extra isolated vertices. This is a hardness
obstruction for **unbounded** perturbation rank. It is not evidence of
NP-hardness for any fixed rank: that would conflict with the randomized
fixed-rank algorithms unless NP=RP.

## 7. Why graphic/cographic switching is not automatically safe

For C=ker(B) with graph incidence B, affine cosets are T-joins. For a graph cut
code C=rowspace(B), an affine coset has the form

    x_e = y_e XOR (a_u XOR a_v).

With y all ones, minimizing weight gives |E|-MaxCut(G). Hence arbitrary cut-code
cosets are already NP-hard at zero perturbation rank. The direct reduction
and its primary source are in `THEORY_REVIEW.md`.

This also explains why a homogeneous cogirth algorithm is compatible with
coset hardness. It minimizes over all nonzero codewords of a linear row space;
it does not force the optimizer to lie in one selected affine translate. Adding
a shift vector to the row space allows both the original space and its shifted
coset, so a smaller homogeneous codeword can hide the hard coset optimum.

Dualizing the matroid changes the code being optimized. It does not preserve
the original edgewise Hamming objective and target by itself. A safe switch
must supply an actual equivalence certificate for the requested optimization
problem. If a cut code also has a supplied cycle-space representation, such
as a valid planar-dual representation, the ordinary T-join route is available
through that certificate. A cographic label alone supplies no such promise.

A recent preprint by Cong, Xu, and Zhao reports a deterministic
2^{O(p^2)}*polynomial algorithm for **cogirth** of rank-p perturbed graphic
matroids. This is relevant to homogeneous row-space optimization. It does not
state a solver for arbitrary cut-code cosets, and has not been implemented or
independently checked here. See [Derandomizing Karger's Contraction Algorithm
for Matroids, submitted August 2026](https://arxiv.org/abs/2608.16298).

## 8. Counting still excludes universal logarithmic exceptional rank

Count codes by their r-dimensional parity-check row spaces; invertible row
changes do not create new codes. Let L=1+r+binomial(r,2), the number of allowed
ordinary column vectors. An overcount for representations whose exceptional
columns have rank at most p is

    2^n * 2^(r*p) * L^n * 2^(p*n).

The factors choose an exceptional set, a spanning list for its subspace,
ordinary column values, and exceptional subspace coordinates. Rank less than
p can be padded with zero spanning vectors. In a representation with redundant
rows, selecting r independent rows preserves both the weight-at-most-two
property and the exceptional-rank upper bound, so extra rows do not defeat
this counting argument.

For r proportional to n and p=O(log n), the expression is 2^{O(n log n)}.
There are at least 2^{r(n-r)} distinct r-dimensional binary subspaces of
GF(2)^n. Indeed the Gaussian-binomial product has factors
(2^n-2^i)/(2^r-2^i)>=2^(n-r). At r approximately n/2, the total is
2^{Omega(n^2)}. Consequently most codes have no such representation in any row
basis. Allowing either the code or its dual to have the property only adds
the two counts and leaves the separation intact.

This excludes a particular universal representation promise, not polynomial
SAT algorithms in general. Decompositions, richer representations, or growing
rank are different routes and require their own analysis.

## 9. Falsifiable next experiment and missing theorem

The immediate low-risk constructive increment is section 2: exceptional-rank
DP with full nonempty semantics and recurrence certificates. Test families
with q growing while p is fixed, including repeated exceptional columns and
zero-syndrome nonempty combinations. Compare against full exceptional-assignment
enumeration and charge span discovery, all DP transitions, graph calls, and
certificate verification. This directly tests whether work follows 2^p rather
than 2^q.

The next separate experiment is the deterministic small-terminal perturbation
case. Use rank-one perturbations with dense V, both sparse and dense U; exhaust
tiny instances against direct enumeration. Mandatory negative controls are the
one-edge inconsistent branch, the triangle whose cheapest path has the wrong
label, and the disconnected-cycle correction example above. A solution that
passes only ordinary membership checks but misses the true optimum fails.

For the unrestricted perturbation route the missing theorem is precise:

> Given a checked B+UV representation and arbitrary target s, supply a
> deterministic, proof-producing optimizer for its parity-constrained T-join
> branches with fully accounted F(p)*N^c total bit cost, or state and certify
> exactly the weaker randomized guarantee being used.

Even that theorem would only improve a parameterized solver. The separate
claim that arbitrary SAT instances can reach suitable representations or
decompositions in polynomial total work remains unproved, and the logarithmic
exceptional-rank representation promise is specifically refuted by section 8.
