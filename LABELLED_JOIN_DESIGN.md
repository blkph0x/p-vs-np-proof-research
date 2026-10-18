# Deterministic labelled joins with zero or two terminals

This independently checked construction supports the small-terminal route in
`PERTURBATION_ROUTE_REVIEW.md`, section 5. It is a design and isolated executable
audit, not an integrated solver or a novelty claim. The construction is exact
for **nonnegative** weights, including binary-encoded integer weights. It does
not remove the arbitrary-terminal parity-matching problem.

## Model and result

Let an undirected multigraph have N vertices and M distinct edge IDs. Loops and
parallel edges are allowed. Edge e has nonnegative integer weight w(e) and label
ell(e) in GF(2)^p; put K = 2^p. A solution is an edge subset F, with odd-degree
boundary partial(F), label L(F) = XOR of its edge labels, and ordinary sum of
its selected weights. Loops contribute zero boundary. Infeasible minima are
infinity.

For a supplied target label z, the minimum-weight solution with boundary empty
or a supplied pair of distinct vertices {u,v} can be computed deterministically
in 2^{O(p)} poly(N,M,b) bit operations, where b bounds the weight bit length.
The empty set is initially allowed. An additional nonempty requirement for
empty boundary and label zero is handled separately by edge pinning below.

## Construction and proof

The lifted graph has vertices (v,a), a in GF(2)^p. Each original edge e=vw gives
transitions (v,a) to (w,a XOR ell(e)), of weight w(e), in both directions.
A lifted walk is reconstructed by XORing its original edge IDs. Its resulting
edge subset has the walk's boundary and total label; its weight is at most the
walk cost. This last assertion uses nonnegative weights and permits repeated
edges to cancel.

Write d((u,0),(v,a)) for lifted shortest-walk distance. For nonzero a define

    c(a) = min_v d((v,0),(v,a));       c(0) = 0.

These closed walks alone need not cover disconnected Eulerian solutions.
Construct a second graph on the K labels, with transition x to x XOR a of
cost c(a) for each nonzero a with finite cost. Let E(z) be its shortest distance
from zero to z. Each selected transition carries a realizing closed walk;
XOR all its edge IDs to construct the Eulerian witness.

**Eulerian equality.** Let OPT_E(z) be the minimum cost of an Eulerian edge
subset with label z. Every such subset decomposes into edge-disjoint cycles,
including loops and parallel-edge cycles. Each nonzero-labelled cycle is a
candidate closed walk for its label, so replacing its cost by c(label) and
combining the labels gives E(z) <= OPT_E(z). Zero-labelled cycles can be omitted
because their weights are nonnegative. Conversely, the XOR of the closed
walks realizing a label-space path is Eulerian, has label z, and has weight
at most that path's cost. Therefore OPT_E(z) <= E(z). This also proves matching
feasibility in both directions, including infinity cases. At an optimum the
reconstructed witness cost equals E(z), even if intermediate walks cancel.

For distinct terminals define

    J(u,v,z) = min_a [d((u,0),(v,a)) + E(z XOR a)].

**Two-terminal equality.** Any feasible edge subset with boundary {u,v}
contains a simple u-v path: each connected component has an even number of
odd vertices, so u and v lie together. Removing that path leaves an Eulerian
subset. The path's label a gives a term of the displayed minimum at most the
original subset's cost, by the Eulerian equality. Thus J <= OPT_J. Conversely,
XOR a realizing lifted path-walk with the Eulerian correction. The result has
boundary {u,v}, label z, and weight at most the displayed sum, so OPT_J <= J.
Again, the final witness has exactly the optimum cost.

## Why both stages matter

Take a unit-cost, label-zero u-v edge and a disjoint unit triangle whose label
XOR is one. The requested label-one {u,v}-join costs four, but no single
label-one u-v walk exists. Even making the graph connected by adding a
label-zero bridge of weight 100 between the components leaves optimum four;
the cheapest label-one u-v walk instead costs 204.

For the Eulerian stage, take two disjoint unit triangles labelled one and two
in GF(2)^2. No single closed walk has label three, yet their union costs six
and has label three. The label-space closure is necessary, not optional.

## Nonempty label-zero Eulerian solutions

The unrestricted value E(0) is zero, realized by the empty set. Requiring a
nonempty *walk* does not enforce a nonempty reconstructed edge subset: in a
one-edge forest an out-and-back walk cancels completely, and no nonempty
Eulerian subset exists.

For a nonempty Eulerian subset of label zero, pin each possible edge e in
turn and **delete it from the residual graph**. Solve the residual request
with boundary partial({e}) and label ell(e), then add w(e) and restore e.
Take the minimum over e. For a loop this residual request is Eulerian; for a
nonloop it uses the two-terminal primitive. Deletion prevents cancellation
of the pinned edge. Removing e from any nonempty optimum proves one
inequality; reinserting it in any feasible residual witness proves the other.
Zero weights are valid: a zero-cost label-zero loop gives nonempty optimum
zero. Nonzero labels and distinct terminal pairs already imply nonemptiness.

## Explicit cost and certificate obligations

The lift has NK states and at most 2MK arcs. Running Dijkstra from (v,0) for
every original vertex v supplies all required path distances and c(a). With
an indexed binary heap, a coarse bound is

    O(N K (M+N) log(2+NK) + K^2 log(2+K))

arithmetic operations, followed by K comparisons per supplied terminal pair
and target. The second term is Dijkstra on at most K(K-1) label transitions.
There is no enumeration of subsets of the K labels. A finite lifted shortest
path needs at most NK-1 arcs, and a label-space shortest path at most K-1
transitions; zero-cost cycles may be removed. Distances therefore use
O(b + log(2+N) + 2p) bits. Edge pinning multiplies the bound by at most M.
Storing all N lifted distance/predecessor arrays costs O(N^2 K) entries;
witness reconstruction and M-bit XOR masks add polynomial factors in M.
The tiny Python audit uses a lazy heap and stores XOR masks during search;
its corresponding heap bound may use log(2+MK), and each XOR costs up to M
bits. These choices preserve the claimed parameterized bit bound.

A future independent optimality certificate can supply, for **every base
vertex source**, lifted distance potentials, realizing predecessor paths,
and the reachable-state set. Check source distance zero, Bellman inequalities
on reachable arcs, realizing paths with the claimed costs, and that no arc
leaves the claimed reachable set. These prove all finite distances and all
unreachability claims, hence the global closed-walk minima c(a). The same
checks on the label graph certify E. Checking all K displayed terms then
certifies J. Edge pinning additionally requires every pin case or a justified
pruning lower bound. A witness alone certifies only an upper bound. This
certificate format is documented here but has not been implemented.

For more terminals, an exact construction still has to handle terminal
pairings and label allocations. Explicit pairing enumeration has factorial
dependence on terminal count. This primitive does not establish an arbitrary-
terminal 2^{O(p)} poly(N,M,b) algorithm, automatic perturbation discovery, or
a polynomial general minimum-distance algorithm.

## Isolated falsifiable audit

Only `labelled_join_next/test_labelled_join_primitive.py` contains executable
code for this design. Its independent oracle enumerates edge subsets only
on graphs with at most eight edges. The candidate uses lifted shortest paths
and label-space closure; it refuses more than 4096 lifted states or p > 8.

Eight tests passed in 0.174 seconds on 2026-10-18. They include all 761 simple
graphs through four vertices with each edge absent or carrying either one-bit
label; 120 seeded weighted multigraphs with p <= 3, loops, parallel edges and
zero costs; all labels and all zero/two-terminal requests on those instances;
40 random nonempty edge-pin checks; the disconnected and connected failures
above; nonempty cancellation; exact 10^100-scale integer weights; and invalid
input/state-cap rejection. Relaxation counts are checked against 2NMK for
the lift and K(K-1) for label closure. These finite checks support, and do not
replace, the proof.

Reproduce from `overnight_research_2026_10_18/labelled_join_next`:

    python -m unittest -v test_labelled_join_primitive

No stable solver, saved baseline result, or top-level Python module was
modified for this audit.
