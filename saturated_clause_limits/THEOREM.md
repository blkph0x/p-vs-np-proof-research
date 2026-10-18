# What common-cost saturation can and cannot repair

**Scoped result:** an exact flat OR penalty on every physical paired boundary is impossible for ordinary perfect matching at a global minimum. A flat OR penalty on the promised valid paired domain is nevertheless constructible with nonnegative costs. This is a proof and explicit control, not a general impossibility of matching reductions, a novelty claim, or a resolution of P versus NP.

## 1. The exact interface and global-minimum obstruction

Let a finite graph G have terminal pairs P_i={a_i,b_i}, i=1,...,k, and any number of mandatory internal vertices. A logical zero deletes neither terminal of its pair; a logical one deletes both. For any physical deleted-terminal subset S, let mu(S) be the minimum perfect-matching cost of G−S, or infinity if infeasible. Edge costs may be arbitrary finite reals. An optional adjusted cost has the form

    F(S) = mu(S) + d + sum_{t in S} alpha_t,

where d is a constant and the terminal offsets alpha_t are arbitrary fixed reals. Define D_k as the 2^k unions of complete terminal pairs. The paired OR relation is

    R_OR = D_k minus {empty}.

The **exact flat penalty contract** asks that every S in R_OR have the same optimum c, while every physical S outside R_OR has adjusted cost strictly greater than c or is infeasible. This makes R_OR precisely the global-minimum support over all physical states, including partially selected pairs.

Every nonempty global-minimum matching boundary support satisfies even symmetric exchange. Here is the needed proof rather than an appeal to terminology. For two minimizing deleted sets A,B and an e in A symmetric-difference B, take optimum matchings M_A,M_B. In their edge symmetric difference, the component of e is an alternating path ending at a distinct f in A symmetric-difference B. Both endpoints are terminals: every internal vertex is matched in both original matchings. Flipping the path in both matchings gives perfect matchings at

    A' = A symmetric-difference {e,f},
    B' = B symmetric-difference {e,f}.

Every path edge changes which matching contains it, so the sum of the two matching costs is unchanged. The two modular offsets also have unchanged sum because each of e,f belongs to exactly one of A,B and exactly one of A',B'. The two constants contribute 2d before and after. The flipped adjusted costs sum to 2c, and each is at least the global minimum c. Both must equal c. Thus both new states are global minimizers. All feasible deleted sets also have parity |V(G)| modulo two. The earlier matching_gadget_limits/THEOREM.md gives the full terminal-deletion exchange framework and its distinction between thresholds and exact levels.

For k>=2 take A=P_1, B=P_2 and e=a_1. The only possible f lie in (P_1 union P_2) minus {e}. If f=b_1, then A' is empty, forbidden by OR. If f lies in P_2, then A' selects only one terminal from each of two pairs, forbidden by exact physical-boundary validity. No exchange partner works. Therefore **no exact flat OR gadget satisfying this contract exists for k>=2**, regardless of graph size, signed edge weights, modular offsets or additional internal vertices.

The witness uses only four changing terminals and the two one-true assignments. At k=1 the relation has a single state and no such obstruction. This is an all-size proof; bounded graph enumeration is not its basis.

## 2. Raw threshold OR exists, but its rewards do not add like clause violations

Take k disjoint terminal-pair edges, each of cost one, with no internal vertices. A physical boundary is feasible exactly when it belongs to D_k. If j logical inputs are true, the minimum matching cost is k−j. Hence the common threshold k−1 accepts precisely R_OR on the entire physical boundary.

There is no contradiction: threshold supports need not satisfy ordinary symmetric exchange. The weaker two-sided threshold law allows the counterpart B'=P_1 union P_2 when A' is empty in the preceding witness. Thus exact threshold OR is possible even though exact flat minimum OR is impossible.

The numerical score rewards additional true literals: at j=2 it is one below the clause threshold. Simply summing these scores and thresholds does not enforce conjunction. For two independent two-literal clauses, an assignment with true-literal counts (0,2) has raw cost 2+0=2, equal to the sum of thresholds 1+1. One clause is still false. A satisfied clause's extra reward has concealed the other clause's violation.

The scalar expression

    penalty = max(0, mu − (k−1))

equals one when j=0 and zero when j>=1 on these valid boundaries. This arithmetic identity alone is not a construction of a matching graph realizing the transformed objective. In particular it cannot give the exact flat physical support excluded in Section 1. Applying an arithmetic transformation outside a matching solver and replacing it by a composable graph gadget are different requirements.

## 3. Positive result: flat OR is constructible on the promised domain

The exact obstruction must not be extended to correctness restricted to D_k. The following construction implements the desired flat clause penalty on every valid paired encoding, using only costs zero and one.

Use k terminal pairs (a_i,b_i) and k−1 internal pairs (u_j,v_j). Add these edges:

* Each terminal-pair edge a_i b_i has cost one.
* Each internal-pair edge u_j v_j has cost zero.
* For every i,j, add a_i u_j and b_i v_j, both of cost zero.

There are 4k−2 vertices and k+(k−1)+2k(k−1)=2k^2−1 edges. The case k=1 consists just of a single cost-one terminal edge.

Consider a valid state retaining m of the k terminal pairs. If a perfect matching uses t cost-one terminal edges, each of the other m−t retained a-terminals must use a distinct u-vertex, and each corresponding b-terminal must use a distinct v-vertex. There are k−1 of each. Therefore

    cost = t >= max(0, m−(k−1)).

This bound is attained. If m<=k−1, assign each retained terminal pair to a distinct internal pair, matching a_i to u_j and b_i to v_j. Match every unused internal pair with its own edge. The cost is zero. If m=k, pay for one terminal-pair edge, assign the remaining k−1 terminal pairs to the internal pairs, and obtain cost one. Thus on the entire valid domain,

    mu(S) = 1 if S is empty, and 0 for every nonempty S in D_k.

This is a polynomial-size construction of the scalar-saturated truth table **on a promised interface**. It is stronger than a positive control needing negative cancellation: all edge costs are nonnegative. Invalid physical states can have the same zero cost as accepted valid states; they need not have a smaller cost. Consequently the full global-minimum support is larger than R_OR and can satisfy exchange.

For k=2 label terminals 0,1,2,3, with pairs {0,1},{2,3}, and internals 4,5. Edges {0,1},{2,3} cost one; edges {4,5},{0,4},{2,4},{1,5},{3,5} cost zero. Its complete finite signature is

| Deleted mask | Optimum | Encoding |
|---:|---:|:---|
| 0 | 1 | both logical inputs false |
| 3 | 0 | first input true |
| 6 | 0 | invalid partially selected pairs |
| 9 | 0 | invalid partially selected pairs |
| 12 | 0 | second input true |
| 15 | 0 | both inputs true |

Every other physical state is infeasible. For A=3, B=12 and e=0, exchange can choose f=2 and reach A'=6, B'=9. These invalid zero-cost states are exactly why the construction does not contradict the exact-support theorem.

## 4. Six vertices are minimal for this two-input promised control

Fix four distinct terminal vertices arranged into P_1,P_2. At least four vertices are needed. With no internal vertices, suppose the three accepted paired states have a common adjusted cost c, including arbitrary signed costs, constant d and modular offsets. Write beta_i=sum_{t in P_i}alpha_t. Let a be the minimum edge cost within P_1 and b the minimum within P_2; both edges must exist because deleting the other pair is an accepted state. Deleting both pairs leaves the empty matching of cost zero. Therefore equality of the accepted costs gives

    b+d+beta_1 = a+d+beta_2 = d+beta_1+beta_2 = c.

It follows that a=beta_1 and b=beta_2. The two disjoint within-pair edges form a matching at the false state S=empty with adjusted cost

    a+b+d = beta_1+beta_2+d = c.

Other edges can only improve that optimum, so the false state cannot have cost greater than c. This also covers parallel edges by taking their minimum costs. With exactly one internal vertex, every valid paired deletion leaves an odd number of vertices, so no accepted valid state has a perfect matching. Thus five vertices are also impossible. The six-vertex construction attains the lower bound. No minimum-size claim is made for larger arities.

## 5. Exact remaining obligation and reproducibility

Saturation is therefore not a missing local truth-table operation on a promised valid domain: the construction above supplies it explicitly. The unresolved obligation is a whole-instance composition that enforces valid paired states and copies variables consistently across all clause occurrences, while preserving the relevant objective and its exact decoding in both directions.

A transparent matching filter that retains the same external terminals and turns this promised flat OR support into exactly R_OR at the global minimum is impossible by Section 1. This does not exclude a different global interface, a special invariant on closed instances, a different decoding map, or a general reduction not using this local contract. Those proposals need their own uniform polynomial construction and proof. An independently realizable validity relation cannot be silently intersected with a matching boundary signature while retaining all external ports; matching realizability lacks that unrestricted closure, as the prior matching-gadget audit shows.

The code imports the earlier bounded matching reference without editing it. Tests check the minimal exchange witness, exact raw threshold semantics, scalar saturation, all valid states of the constructive gadgets up to ten vertices, explicit invalid states, and the two-clause compensation example. The experiment saves complete matching witnesses and input/source hashes. It also exhausts all 4,096 simple four-vertex graphs with each edge absent or weighted −1, 0 or 1, checking the forced-offset inequality from Section 4. This finite check supports the implementation; the preceding algebra proves minimality for arbitrary finite weights and arbitrary internal-size alternatives below six.

No failed bounded search is used as an impossibility result. The larger-arity minimum graph size is uninvestigated, and a sound universal clause/copy composition remains unproved. No conclusion about P versus NP follows from these scoped results.
