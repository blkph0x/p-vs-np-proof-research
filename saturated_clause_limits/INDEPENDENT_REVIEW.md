# Independent review of the clause-saturation control

Reviewed 2026-10-18: `THEOREM.md`, the constructive graph routine, its tests, and the recorded scope are mathematically consistent. No producer edits or outstanding corrections were needed. This is a proof audit supported by finite checks, not formal proof-assistant verification or a P-versus-NP result.

## The positive construction

The k-port graph has 2k terminal vertices and 2(k−1) mandatory internal vertices, hence 4k−2 vertices, and 2k²−1 edges. Its edge costs are all zero or one. At a valid paired state retaining m terminal pairs, let t be the number of paid terminal-pair edges in a perfect matching. Every remaining a-terminal needs a distinct u-vertex and every remaining b-terminal needs a distinct v-vertex. There are only k−1 of each, so t≥max(0,m−(k−1)). This lower bound does not assume that an arbitrary matching sends both members of a terminal pair to the same internal pair.

The proposed construction attains the bound by choosing that convenient pairing explicitly: assign each unpaid retained terminal pair to one distinct internal pair, and match unused internal pairs internally. If all k terminal pairs remain, pay for one and assign the rest to the k−1 slots. Thus the false input has cost one and all other valid inputs have cost zero. The k=1 boundary case is the single cost-one edge and also satisfies the formula.

The two-input full signature is exactly {0:1,3:0,6:0,9:0,12:0,15:0}. In particular the invalid physical states 6 and 9 attain the same global minimum as accepted logical states. They are not hidden lower-cost states: all weights are nonnegative. Their presence supplies the exchanges missing from the exact paired OR relation.

## Obstruction and minimum size

The global-minimum support argument correctly flips the same alternating path in both source matchings. The sum of edge costs, modular terminal offsets, and additive constants is preserved. Since each new adjusted cost is at least the global minimum, both attain it. For k≥2, the stated exact OR support violates the one-sided exchange consequence with A=P_1, B=P_2 and e=a_1. Signed weights and arbitrary additional internal vertices do not alter that argument. It applies only when the accepted states are precisely the minimum support across all physical states.

Raw threshold OR is consequently a valid counterpoint: the disjoint pair-edge construction realizes it exactly, and its weak two-sided threshold exchange is sufficient. This does not realize a common accepted cost. The displayed two-clause compensation example correctly shows that adding those raw scores and cutoffs can conceal a false clause.

The six-vertex minimum for promised flat OR2 is proved with the correct hypotheses, including signed edge costs, a constant, and arbitrary modular terminal offsets. With only the four terminals, let a,b be the best within-pair edge costs. Equality of the three accepted adjusted optima forces a=beta_1 and b=beta_2, where beta_i is the sum of offsets on pair i. Selecting both within-pair edges then gives the false state a matching of adjusted cost exactly c; extra edges can only reduce its optimum. A fifth vertex leaves every valid deletion state with odd cardinality and cannot help. The exhibited six-vertex graph therefore attains the true minimum in this model. No minimum-size statement for higher arities follows or is claimed.

## Independent executable checks

All seven supplied tests passed. Independently enumerated every edge subset of the constructive graphs for k=1,2,3: 131,202 subsets in total. Requiring every internal vertex to be covered and every other vertex to have matching degree zero or one recovers all three complete physical signatures; their 28 finite boundary costs agree exactly with the producer. This oracle uses edge-subset enumeration rather than the imported matching recursion.

Separately constructed the claimed matching for every valid paired assignment through k=8, covering 510 states. Direct edge membership, exact required-vertex coverage, and original edge-cost sums all passed. The general optimality assertion still rests on the capacity lower bound above, not on extrapolation from these finite checks.

The final composition caveat is necessary and correctly stated. A promised local flat penalty exists. A reduction must still ensure that its global matching never uses invalid paired states, that repeated variables agree, and that the objective and decoding are preserved. The exact transparent minimum-support interface is excluded; arbitrary different interfaces, whole-instance invariants, and general reduction techniques are not excluded by this review.
