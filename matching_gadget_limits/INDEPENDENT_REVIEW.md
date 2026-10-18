# Independent review of the matching boundary obstruction

Reviewed 2026-10-18. This review covers the revised `THEOREM.md`, its explicit graphs, the matching/enumeration routines, and the strengthened threshold argument. No outstanding mathematical correction was found. The producer files were not edited by this reviewer. This is a human-readable proof audit with finite executable checks, not a formal proof-assistant verification or a resolution of P versus NP.

## Exchange and cost conservation

The model is precise: finite loopless graphs, parallel edges distinguished by edge identity, a fixed set of terminal vertices, and every undeleted vertex mandatory in the perfect matching. Arbitrarily many internal vertices do not affect the proof. Internal vertices cannot be endpoints of the symmetric-difference paths because they are present in both source matchings.

For matchings at deleted sets A and B, the degree-one vertices in their edge symmetric difference are exactly A symmetric-difference B. The component through any chosen such terminal e is an alternating path to a distinct terminal f. Flipping that same path in both matchings gives valid matchings at both exchanged boundary sets. The edge multiset across the two matchings is preserved, so their total cost is preserved even with signed edge weights. Parallel edges cause no problem: distinct parallel edges can form an alternating two-edge cycle, not a path endpoint ambiguity.

For globally minimizing boundary states of cost c, both flipped matching costs are at least c and sum to 2c. Thus both new states also attain c. The global qualification is essential: minimizing only over a promised subset of boundary states would not supply the lower bound for a flipped state outside that subset. A modular terminal offset and a fixed additive constant preserve the two-matching total as stated.

For a finite threshold K, the same identity gives a weaker conclusion. If both source costs are at most K, at least one flipped matching has cost at most K. Taking the minimum matching cost at that new boundary state can only improve it. Therefore the stated two-sided disjunction holds for every signed threshold support. It does not imply ordinary one-sided symmetric exchange, and no sufficiency claim is justified or made.

The exact paired-copy and paired-AND exclusions follow from this weaker condition, not merely from ordinary exchange. For copy, every two-bit flip from the empty and full states is a proper intermediate state on both sides when there are at least two logical ports. For AND, choose an output rail: pairing it with the other output rail yields output-only and all-inputs-without-output states, both forbidden; pairing it with an input rail yields partial pairs on both sides, also forbidden. This covers any positive number of AND inputs. Consequently arbitrary signed costs and a common cutoff cannot rescue either exact physical-boundary relation.

Fixed terminal bit complements and permutations preserve both exchange statements. They change the naming of physical states, not the need to handle all physical states in an exact-interface claim.

## Promises, thresholds, and composition

Both promised-domain examples are correct. The cross-pair copy graph has full support `{0,6,24,30,33,39,57,63}` and intersects the specified 00/11 paired domain only in `{0,63}`. The new five-edge AND graph has full support `{0,3,6,9,12,20,23,29,34,43,46,54,63}` and intersects that domain in `{0,3,12,63}`. Extra physically feasible states are necessary to avoid the exact-interface obstruction; a validity promise is a substantive change in the claim.

The positive threshold counterexample is also correct. In the stated bipartite graph, cutoff 5 accepts `{6,9,10,12}`. For A=9, B=6 and e=3, no exchange from A remains accepted, so ordinary exchange fails. Choosing f=1 gives exchanged costs 7 and 3, exhibiting the weaker two-sided alternative. The signed zero-level example `{3,12}` is an exact level set, not a sublevel set and not a global-minimum support; its failure of ordinary exchange contradicts none of the proved statements.

The transparent-filter conclusion has the right quantifiers: it excludes a single ordinary matching graph retaining the same external terminal-deletion interpretation and implementing the required conjunction for every physical boundary state. The arbitrary number of internal vertices is already included in the theorem. Edge union does not implement conjunction because a matching can use edges from both pieces. Restricting only to promised valid states, consuming or changing interfaces, or proving a special whole-instance invariant is outside this particular impossibility statement. The revised text correctly leaves those general reduction approaches open while identifying the missing validity, cost, and composition proof.

## Independent finite checks

In addition to reading the producer's tests, the reviewer used a separate exhaustive edge-subset matching oracle, rather than the producer's subset recursion:

- On 250 seeded signed weighted multigraphs with at most six vertices and eight edges, independently enumerated matching supports and optimum boundary costs. For the cases with multiple global minima, checked 13 source-state pairs and 30 simultaneous path-subset flip pairs. All flips preserved boundary validity and global minimum cost. The small flip count reflects that most sampled graphs had a unique global minimizing boundary state.
- On a separate 250 seeded multigraph sample, checked weak two-sided exchange at 394 threshold cutoffs. These are cutoff checks, not a claim of 394 distinct support families. Every check passed. The exact copy family and paired AND with one, two, or three inputs failed the necessary condition, as the proof predicts.
- Independently checked the copy-domain intersection, the failure of edge union to enforce intersection, the positive threshold support, and the signed zero-level support.
- Enumerated all 32 edge subsets of the new promised-AND graph. Its complete support and its four accepted valid encodings agree with the revised theorem; the corresponding accepted edge masks were 22 for deleted mask 0, 12 for mask 3, 3 for mask 12, and 0 for mask 63, using the theorem's edge order.

These checks support the examples and implementation. The all-size assertions rest on the alternating-path and total-cost proofs above. No universal graph-reduction impossibility or complexity-class separation follows from this local obstruction.
