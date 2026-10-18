# An explicit false positive from gluing promised NOT matching gadgets

This control refutes one concrete ordinary-perfect-matching composition of
individually correct promised-domain NOT gadgets. It does not refute all
matching compositions, validity encodings, weighted constructions or general
reductions. No novelty or P-versus-NP claim is made.

## The isolated gadget is NOT only on its promised domain

There are four terminals 0,1,2,3 and two mandatory internal vertices 4,5.
Connect each internal vertex to every terminal: this is K_(2,4), with eight
edges. There are no other local edges. A terminal deletion state S means that
the vertices in S have already been matched outside the gadget.

The remaining local bipartition has two internal vertices and 4-|S|
terminals. A perfect matching therefore exists exactly when |S|=2. Every
such state has two internal perfect matchings. In four-bit integer notation
the complete feasible deletion support is

    {3, 5, 6, 9, 10, 12}.

Group terminals {0,1} into the left port and {2,3} into the right port.
Encode a Boolean zero by deleting neither terminal of its port and a one by
deleting both. The promised paired domain is {0,3,12,15}; intersecting it
with the full feasible support gives {3,12}. Thus the gadget implements NOT
on this domain. The four additional feasible masks delete one terminal from
each port and are invalid encodings. Local promised-domain correctness does
not exclude them.

## The precise ordinary gluing

Take k>=1 copies, with global vertex 6i+j denoting local vertex j of copy i.
For each i and rail r in {0,1}, add the wire edge

    (6i+2+r, 6((i+1) mod k)+r).

These edges join the right port of gadget i to the left port of gadget i+1,
rail to corresponding rail. All 6k vertices must be matched. The graph has
8k local edges and 2k wire edges; local internals have no wire connections.
For k=1 the wire edges join distinct terminals in the same gadget, so the
definition still makes sense.

Let x_i denote the Boolean state of gadget i's left port. If every wire uses
either both rails or neither, wire i imposes the same state on right(i) and
left(i+1). The local promised NOT condition is then

    x_i != x_((i+1) mod k)       for every i.

Following the cycle toggles the Boolean value k times. These constraints are
unsatisfiable for odd k and have exactly the two alternating assignments for
even k.

## A perfect matching exists even for every odd cycle

For every wire, select its rail-zero edge only. In each gadget select the two
local edges (1,4) and (3,5).

The outgoing rail-zero edge matches local terminal 2; the incoming rail-zero
edge matches local terminal 0. The two local edges match vertices 1,3,4,5.
Thus every vertex appears exactly once, and these 3k edges are a perfect
matching of the original 6k-vertex graph, for **every k>=1**.

Each wire now has occupancy 01, an invalid paired-port state. Each gadget's
external deletion mask is 5={0,2}, which belongs to its full local feasible
support but not to the promised domain. In particular, every odd cycle is a
false positive for the proposed reduction from Boolean feasibility to ordinary
perfect-matching existence. This is an explicit witness, not an inference from
failure to find an obstruction or from a large matching optimizer.

## Every satisfying Boolean assignment still extends

Given a satisfying assignment x, choose both wire-i edges exactly when
x_(i+1)=1. This gives left(i) state x_i and right(i) state x_(i+1).

If x_i=1, its left terminals are matched on wires and its right terminals are
free; match local vertices (2,4) and (3,5). If x_i=0, its right terminals are
matched on wires and its left terminals are free; match (0,4) and (1,5).
The NOT condition ensures these are the only two cases. Each vertex is covered
once, giving a perfect matching with valid ports and the specified assignment.

Conversely, any perfect matching whose every wire uses both or neither rail
decodes to a satisfying assignment. The two mandatory internal vertices must
match exactly two local terminals, leaving exactly two terminals matched on
wires. With valid paired ports this means exactly one of the two ports is
one, which is NOT. Wires enforce agreement between neighboring copies.

Thus completeness holds, and soundness holds **conditional on global port
validity**. Ordinary matching feasibility does not enforce that condition:
the preceding construction violates it at every wire. On an even cycle the
invalid matching still exists, but the instance is also Boolean-satisfiable,
so it is a positive control rather than a feasibility false positive.

## Saved controls and independent checks

`RESULTS.json` preserves the original graph, stable edge IDs, explicit partial-
rail matching, direct vertex-coverage checks, wire/deletion states, exhaustive
Boolean results, and every satisfying-assignment extension for these cases:

| k | Vertices | Edges | Boolean assignments checked | Satisfying assignments | Ordinary matching | Classification |
| ---: | ---: | ---: | ---: | ---: | --- | --- |
| 3 | 18 | 30 | 8 | 0 | Explicit witness | False positive |
| 4 | 24 | 40 | 16 | 2 | Explicit witnesses | Positive control |
| 5 | 30 | 50 | 32 | 0 | Explicit witness | False positive |
| 7 | 42 | 70 | 128 | 0 | Explicit witness | False positive |
| 11 | 66 | 110 | 2048 | 0 | Explicit witness | False positive |

In total, 2,232 Boolean assignments and seven explicit whole-graph matchings
were checked: five partial-rail witnesses and the two valid extensions for
k=4. The source hashes are stored as a filename-to-SHA256 map; sources were
unchanged during the run. Original graph hashes are stored separately.

Eight tests passed in 0.042 seconds. They independently enumerate the local
deletion signature, check graph indexing, check direct coverage of every
constructed matching, enumerate Boolean assignments through k=11, and verify
every satisfying extension. A separate bounded recursion checks all global
matchings only for k=1,2 (at most twelve vertices). Additional tests reject
tampered witnesses and invalid inputs, enforce a Boolean enumeration cap, and
replay a serialized original graph and witness. No general matching optimizer
is used for the larger saved graphs. Constructing and checking the explicit
cycle witness itself takes O(k) graph operations; the Boolean truth-table
enumeration is a bounded experimental control, not a general algorithm claim.

Reproduce from `overnight_research_2026_10_18/matching_composition_controls`:

    python -m unittest -v test_not_cycle
    python not_cycle.py

The missing ingredient for this gluing is a proof or mechanism excluding
partial-wire states while preserving the intended interfaces and problem.
Changing the gadget, wiring, accepted matching class, objective or decoding
model would define a different construction and needs its own equivalence
proof. Existing labs and production solvers were not modified for this control.
