# Independent review: labelled joins with zero or two terminals

Reviewed on 2026-10-18 against `LABELLED_JOIN_DESIGN.md`. The construction is
correct for the stated nonnegative-weight, undirected multigraph model. The
proof also extends to nonnegative rational weights encoded exactly. This is
an independent mathematical/code-design audit with finite executable checks,
not a machine-checked formal proof or a novelty claim. The independent
optimality-certificate format remains a design, not an implemented verifier.

## Exact optimization statement

Give every edge a distinct ID, a label in GF(2)^p, and a nonnegative weight.
Solutions are edge subsets, with ordinary additive weight and XOR label. A
loop has zero boundary. Write K=2^p. For a pair of vertices the boundary is
the binary vector e_u+e_v; equal vertices therefore mean zero boundary, not
a singleton terminal. The design handles zero boundary separately and uses
distinct vertices for the two-terminal formula.

For a nonzero label a, let

    c(a) = min_v dist_lift((v,0),(v,a)).

An infinite value means that no closed walk anywhere in the graph has that
label. Define E(b) by shortest paths from zero in the label graph whose
transition x -> x XOR a has cost c(a), for every finite c(a) with a nonzero.
Set E(0)=0, including when the original graph has no vertices or edges.

Then E(b) is exactly the minimum weight of an edge subset with zero boundary
and label b. The proof requires both directions:

1. An even-degree edge subset decomposes into edge-disjoint cycles, including
   loops and two-edge parallel cycles. Replace each nonzero-labelled cycle
   by a closed-walk cost c(a); omit zero-labelled cycles. The resulting walk
   in the label graph has the required total label and no greater cost.
   Thus E(b) is at most the optimum subset cost.
2. Realizing closed walks for a label-graph path can be combined by XOR of
   original edge IDs. Boundary and label are preserved, and cancelling an
   edge cannot increase the weight because weights are nonnegative. The
   result is a feasible even-degree subset of cost at most E(b), proving the
   reverse inequality.

This argument covers infeasibility as well: a finite value constructs a
subset, and any feasible subset constructs a finite label-graph walk.
Eulerian subsets need not be connected. Minimizing the closed-walk costs
without the subsequent label-space closure would miss feasible unions of
cycles in separate components.

For distinct u,v, the exact answer is

    J(u,v,z) = min_a [dist_lift((u,0),(v,a)) + E(z XOR a)].

Any feasible subset has u and v in the same component, since each component
has an even number of odd-degree vertices. It contains a simple u-v path;
removing that path leaves an even-degree subset. Its path label supplies a
term in the displayed minimum no larger than its weight. Conversely, XORing
a realizing lifted walk with a realizing Eulerian correction produces the
specified boundary and label at no greater cost. These inequalities prove
equality, including infinity. In particular, although intermediate walks
may cancel, the final reconstructed support has exactly the computed optimum
weight. If it had strictly smaller weight, the two proved inequalities would
be inconsistent.

## Nonempty requirement and edge cases

Only the request with zero boundary and zero label can accept the empty
subset. A nonempty lifted walk is not sufficient: traversing a bridge out
and back cancels to the empty support.

For a general target z, the nonempty zero-boundary optimum can be written

    min_e [w(e) + OPT_(G-e)(boundary(e), z XOR label(e))].

Every pin must remove e from the residual graph, then restore it afterwards.
This ensures that the returned support contains e. Removing any edge of an
optimal nonempty support proves one inequality; reinserting a pinned edge
into a residual optimum proves the other. For a loop the residual request
has zero boundary, so it uses E rather than a pair of distinct terminals.
The design states the needed special case z=0 correctly; for z nonzero the
ordinary unconstrained optimum is already nonempty.

Isolated vertices, disconnected components, loops, parallel edges, zero-cost
edges, and p=0 do not invalidate the proof. Lifted paths cannot cross between
base components, while the Eulerian correction can select cycles in any
component. All reconstruction must use the original edge IDs, because two
parallel edges are different selectable coordinates. Zero-cost cycles can
be removed from shortest paths when bounding path length. For a graph with
no edges, the nonempty minimum is infinity. Negative weights are outside this
argument: the non-increase under XOR cancellation and the omission of
zero-labelled cycles both use nonnegativity.

## Complexity and certificate boundary

The design's indexed-heap arithmetic bound

    O(N K (M+N) log(2+NK) + K^2 log(2+K))

is valid: there are N lifted searches on NK states and at most 2MK arcs,
followed by a shortest-path search on K labels and at most K(K-1) transitions.
After those computations, each supplied terminal-pair/label query needs K
comparisons. Pinning all edges multiplies the bound by at most M. Original
edge-bitmask reconstruction and stored arrays contribute polynomial factors.
The result is polynomial in N, M, K, and input weight bit length, hence
2^{O(p)} times a polynomial; it is not polynomial in p.

For integer weights of at most b bits, a simple lifted shortest path uses at
most NK-1 arcs and a simple label-graph path at most K-1 transitions. The
claimed O(b+log(2+N)+2p) distance bit bound therefore holds. For rational
weights, multiply by the product of all positive input denominators. Its
bit length is at most the sum of their bit lengths, and the scaled integer
weights still have polynomial bit length. This gives an exact rational
extension without a pseudo-polynomial dependence on numerical magnitudes.

The proposed future certificate obligations are sufficient when implemented
literally: for each base source, require the source in its claimed reachable
set, source distance zero, Bellman inequalities on all reachable arcs,
realizing paths to every claimed reachable state, and closure of the set
under outgoing arcs. Realizing paths give upper bounds, potentials give
lower bounds, and reachability closure proves the remaining states
unreachable. A collection of predecessor pointers must actually trace to
the source; zero-cost predecessor cycles are not realizing paths. Repeat
these checks in the label graph, then verify all K terms for J. A nonempty
edge-pin optimum additionally needs coverage of every pin or valid lower
bounds for omitted pins. A reconstructed feasible witness alone establishes
only an upper bound.

The design does not settle arbitrary-terminal label-constrained joins,
automatic discovery of a useful graph representation, general minimum
distance, or P versus NP.

## Independent finite checks

A separate in-memory Python implementation was written from the mathematical
formulas and compared with an exhaustive edge-subset oracle. No top-level
Python module or stable solver was created or changed for this review.

The audit included all 2,925 multisets of at most three edges chosen from
24 edge types on two vertices: the three possible unordered endpoint pairs
(including both loops), four two-bit labels, and weights zero or one.
Repeated edge types create distinct parallel edges. It also included 400
seeded graphs with zero to five vertices, at most eight edges, zero to three
label bits, and exact nonnegative rational weights with numerators zero to
five and denominators one to five.

Across these 3,325 graphs, 42,852 zero-boundary/two-terminal/label requests
and nonempty zero-boundary requests agreed with the exhaustive oracle.
Every finite ordinary result was reconstructed by XOR of original edge IDs;
its boundary, label, and exact support weight were independently checked.
Nonempty zero-boundary values were independently computed through edge
deletion and pinning and matched the nonempty-support oracle. These finite
checks support the argument but do not replace its general proof.
