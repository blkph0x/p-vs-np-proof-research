# Independent review of the promised-NOT cycle control

Reviewed 2026-10-18, including the completed `THEOREM.md`. The construction, indexing, Boolean extension, and stated narrow composition obstruction are correct. This review changes no producer files and makes no general impossibility or P-versus-NP claim.

## All-size argument

The local graph has terminal pairs {0,1} and {2,3}, with internal vertices 4 and 5 adjacent to all four terminals. Its two mandatory internal vertices must match two distinct surviving terminals, and there are no terminal-terminal or internal-internal edges. It therefore has a perfect matching after terminal deletion exactly when two terminals were deleted. The complete local deletion support is {3,5,6,9,10,12}. Restricting to whole-pair deletions {0,3,12,15} leaves {3,12}, precisely NOT.

In the global construction, local vertex j of gadget i is 6i+j, and wire i connects right rail r of gadget i to left rail r of gadget i+1, with indices modulo k. For every positive k, select rail 0 on every wire and the local edges {1,4} and {3,5} in every gadget. Each local vertex 0 is covered by the incoming selected wire, each local vertex 2 by the outgoing selected wire, and vertices 1,3,4,5 by the two local edges. These are 3k distinct edges covering all 6k vertices once. The argument also holds for k=1: its single selected wire joins local vertices 2 and 0 without creating a loop.

Every wire is only partially selected, with rail mask 1. Every gadget consequently sees local deleted mask 1+(1<<2)=5. This state is locally feasible but violates both whole-pair port promises. Thus an odd Boolean NOT cycle is unsatisfiable while its particular glued matching graph has the explicit perfect matching above. Boolean unsatisfiability follows by composing k negations: x_0=x_0 XOR (k mod 2), impossible for odd k.

## Extension and scope

The convention x_i = gadget i's left-port bit is consistent with selecting both rails of wire i exactly when x_(i+1)=1. Its incoming wire then deletes the left pair exactly when x_i=1. For a satisfying NOT assignment, x_i and x_(i+1) differ. If x_i=1, match the surviving right pair by {2,4},{3,5}; if x_i=0, match the surviving left pair by {0,4},{1,5}. These are exactly the source's local edge choices. This extends both alternating assignments of every even cycle. Conversely, any perfect matching whose wires are all empty or full induces whole-pair local deletions; the local signature forces NOT at each gadget, so its decoded assignment satisfies the Boolean cycle.

The failure is therefore soundness of this specific rail-by-rail gluing: unrestricted global matchings need not preserve the local validity promise. It does not show that all possible wiring rules, encodings, weighted constructions, or whole-instance reductions fail.

## Executable checks

All eight supplied tests passed on review. Separately replayed the five saved witnesses directly from their serialized edge lists, checked their equality to the explicit formula above and exact vertex coverage, and confirmed both recorded source hashes. The saved cases have lengths 3,4,5,7,11; four are odd false positives and one is an even positive control. The result records 2,232 enumerated Boolean assignments and seven checked matchings, including both valid extensions for length four. No matching optimizer is needed for the all-size witness. Finite checks validate the saved examples; the indexing and parity arguments establish the general statement.
