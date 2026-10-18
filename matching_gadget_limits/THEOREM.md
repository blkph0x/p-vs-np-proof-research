# What direct perfect-matching boundary gadgets can enforce

**Scope:** finite ordinary perfect-matching gadgets with terminal deletion semantics, including arbitrarily many mandatory internal vertices. Exact proofs and small independently replayed examples. No novelty claim; no impossibility of general reductions to matching is claimed. This does not resolve P versus NP.

The actionable distinction is between an exact relation on every boundary state and a relation that is correct only when the boundary is promised to contain valid paired encodings. Unweighted exact relations obey a strong exchange law; arbitrary signed weighted threshold relations obey a weaker two-sided law that still excludes exact paired copying and AND. Six-vertex matching gadgets nevertheless realize both copying and AND on the promised valid domain. The unresolved composition requirement is how invalid encodings would be excluded while preserving externally usable ports. Ordinary matching gadgets cannot provide a transparent filter that turns this particular promised copy gadget into exact copy, even by assigning signed costs and a common threshold.

## 1. Model and all-size exchange theorem

Let G=(V,E) be a finite loopless graph, possibly with parallel edges, and let T be a set of distinct terminal vertices. Vertices in V minus T are internal. For S contained in T, remove precisely the vertices of S and all their incident edges. Define

    F(G,T) = {S subset T : G-S has a perfect matching}.

Every remaining vertex, including every remaining terminal, must be matched once. The empty graph has its empty perfect matching. Internal vertices are not optionally disposable. There is no external validity promise in this definition.

If F is nonempty, all its sets have the same parity: |S| is congruent to |V| modulo two. “Even delta-matroid” means fixed parity across feasible sets, not necessarily that every feasible set has even size. If F is empty, it is an infeasible signature and is not called a delta-matroid here.

**Theorem 1, simultaneous symmetric exchange.** For any A,B in F and any terminal e in A symmetric-difference B, there is a **distinct** terminal f in A symmetric-difference B such that both

    A' = A symmetric-difference {e,f},
    B' = B symmetric-difference {e,f}

belong to F.

**Proof.** Choose perfect matchings M_A of G-A and M_B of G-B, and view both as edge subsets of G. In their edge symmetric difference, each vertex has degree zero, one or two. A vertex in A symmetric-difference B is absent from exactly one matching and present in the other, so has degree one. Every other vertex has degree zero or two: it is absent from both, matched by the same edge in both, or matched by two different edges.

The component containing e is therefore a path P, not a cycle. Its edges alternate between M_A and M_B. Its other endpoint f is distinct from e and has degree one, hence belongs to A symmetric-difference B. In particular f is a terminal; an internal vertex is present in both original perfect matchings and cannot be an endpoint.

Replace M_A by M_A symmetric-difference E(P). At each internal path vertex, one matching edge is removed and the other is inserted. At each endpoint, being matched is toggled. All other vertices retain their matching status. The result is a perfect matching of G-A'. Applying the same flip to M_B gives a perfect matching of G-B'. This proves the assertion for the chosen e. The construction works for every e in the boundary difference. ∎

The ordinary symmetric exchange axiom requires only A' to be feasible. Thus Theorem 1 and fixed parity prove that every nonempty F(G,T) is an even delta-matroid. Terminal degree restrictions are unnecessary. Extra internal vertices, nonplanarity, parallel edges and arbitrary gadget size do not change the proof.

This is standard matching-delta-matroid structure. For primary sources, see [Bouchet and Schwärzler, *The delta-sum of matching delta-matroids*](https://doi.org/10.1016/S0012-365X(97)00044-7), and [Kazda, Kolmogorov and Rolínek, *Even Delta-Matroids and the Complexity of Planar Boolean CSPs*](https://arxiv.org/pdf/1602.03124), Definition 5 and Appendix A. The latter also distinguishes the proper gadget-composition operation from unrestricted conjunction on externally shared variables. The proof above supplies all conditions needed here independently of terminology.

A fixed switch between deleted and retained states, or complementing any fixed set of terminal bits, merely replaces every set S by S symmetric-difference C. The exchange law is invariant under this operation and under terminal permutations. Changing such conventions cannot evade an exact-support obstruction.

## 2. Exact paired-rail copying and AND are excluded

Use the encoding specified in the task: each logical port i has two terminals P_i={i_0,i_1}, with logical zero represented by deleting neither terminal (00) and logical one by deleting both (11). This is the **00/11 paired encoding**; conclusions are stated for this explicit encoding rather than an unspecified meaning of “dual rail.” Let D_k be the domain of all unions of whole pairs P_1,...,P_k. It has 2^k valid states among the 2^(2k) possible physical boundary subsets.

### Exact three-copy equality

If all physical states must be handled, three-copy equality has feasible family

    F_copy = {empty, P_1 union P_2 union P_3}.

Take A empty, B all six terminals, and any e in B. Theorem 1 requires an f distinct from e with the two-element set {e,f} feasible. Neither allowed state has size two. This is a contradiction. No terminal-deletion perfect-matching gadget of any size realizes this exact family.

The same argument already excludes exact equality between two 00/11 ports, and in general equality among k>=2 such ports. More generally, a feasible family consisting of exactly two sets whose symmetric difference has more than two elements violates exchange.

### Direct AND, under both common arity conventions

For the three-variable relation z=x AND y, the valid logical tuples are 000,100,010,111, with x,y as inputs and z as output. Under the paired encoding its exact physical feasible states are

    empty, P_x, P_y, P_x union P_y union P_z.

Take A empty, B all six terminals, and e one output terminal. If f is the other output terminal, {e,f}=P_z encodes inputs zero and output one, which is forbidden. If f is any input terminal, {e,f} is an invalid partially selected pair state and is also forbidden by the word **exact**. There is no possible exchange partner.

For a three-input AND gate z=x AND y AND w, there are four logical ports and eight physical terminals. The identical proof takes A all-zero, B all-one, and e an output rail. It excludes exact implementation of this relation too. The argument applies to any positive number of inputs when using the 00/11 encoding.

With one terminal per logical bit, the usual AND relations with at least two inputs already violate fixed parity: both the all-zero tuple and an input-only singleton are allowed. That simpler observation concerns a different encoding.

These conclusions concern the entire physical boundary relation. They do **not** prove that AND or equality cannot be realized correctly on D_k while additional invalid boundary states remain feasible.

## 3. Positive promised-domain copy and AND gadgets

Take six terminals 0,...,5 and no internal vertices. Logical pairs are

    P_1={0,1}, P_2={2,3}, P_3={4,5}.

Let the graph consist of three disjoint cross-pair edges

    {0,5}, {1,2}, {3,4}.

A deleted set is feasible exactly when it is a union of these three graph edges. In bitmask notation, its full boundary family is

    {0,6,24,30,33,39,57,63}.

The valid paired-encoding domain is

    D_3 = {0,3,12,15,48,51,60,63}.

Their intersection is exactly {0,63}: all logical values agree. Equivalently, the graph formed by the logical pairs and the cross-pair edges is one alternating six-cycle; a subset that is a union of edges of both pairings must be either empty or the whole cycle.

This is a correct promised-domain copy gadget. It is not an exact copy gadget. For example, starting at A=0 and B=63, the alternating path from terminal 0 is edge {0,5}; exchange reaches A'=33, an invalid logical encoding that remains physically feasible. Invalid states are exactly how this example satisfies the theorem.

This explicit counterexample prevents the inference “the desired encoded relation fails exchange, therefore it is impossible even under an external valid-encoding promise.” Such an inference would be false.

For a positive AND control on the same six terminals and logical pairs, use edges

    {0,4}, {1,5}, {2,4}, {3,5}, {0,3}.

Its complete feasible boundary family is

    {0,3,6,9,12,20,23,29,34,43,46,54,63}.

Intersecting with D_3 gives exactly {0,3,12,63}, the paired encoding of z=x AND y. The undeleted graph has perfect matching {{1,5},{2,4},{0,3}}. Deleting pair {0,1} leaves matching {{2,4},{3,5}}; deleting pair {2,3} leaves {{0,4},{1,5}}; deleting every terminal leaves the empty matching. The four remaining valid pair-union states have no perfect matching. Thus AND, like copy, is possible with a valid-domain promise. Both full signatures and matching witnesses are saved in RESULTS.json; PROMISED_AND_CONTROL.md gives the explicit truth table.

## 4. Why independently adding validity is not a free composition

Pair validity itself is easy: a single graph edge on a terminal pair has deletion support {00,11}. Three disjoint logical-pair edges realize D_3. Thus both the cross-pair copy signature F and the validity signature D_3 are individually realizable by ordinary perfect-matching gadgets.

Their set intersection is not realizable, because F intersect D_3 is the forbidden exact copy family. Matching realizability is therefore **not closed under arbitrary relation intersection on the same external terminal bits**.

Merely taking the union of the two gadgets' edge sets does not enforce intersection. In the six-vertex example, the union graph contains all logical-pair edges, so every state in D_3 is feasible: remaining pairs can match internally. It accepts eight valid logical states, not just the two equality states. A matching can use edges from different pieces; it is not required to provide an independent perfect matching inside each piece on the same surviving vertices.

**Precise transparent-filter impossibility.** Suppose there were an ordinary perfect-matching construction that could attach an independently enforceable validity filter to this cross-pair copy gadget, retain six externally usable terminals with the same deletion semantics, and produce a composite graph K satisfying, for **every** external S,

    G_cross-S has a perfect matching AND S is in D_3
       iff
    K-S has a perfect matching.

Then F(K,T)={empty,T}, contradicting Theorem 1. Hence no construction satisfying these exact transparent-interface conditions exists. The conclusion allows arbitrary additional internal vertices and arbitrary internal wiring because K itself would still be a finite graph.

Proper matching-gadget wiring can join and consume interfaces, or existentially eliminate internal boundary variables. That does not implement unrestricted intersection while retaining all those variables externally. A validity test using the two rails as its entire interface consumes those rail occurrences. Passing their values onward to independent consumers requires another transparent operation, which is precisely the missing requirement.

This statement does not exclude a globally designed reduction whose external inputs are promised valid, a construction that changes its interface or decoding map, or a proof that invalid states cannot occur on the particular closed instances produced by a reduction. Any such proposal must state and prove its actual whole-instance equivalence. The local promised-domain truth table alone supplies no such proof.

## 5. Weighted gadgets: exact scope of the obstruction

Assign finite real edge costs and let mu(S) be the minimum weight of a perfect matching of G-S, or infinity if none exists. In the finite experiments, all costs and comparisons are integers.

### Nonnegative costs and zero optimum

If every edge cost is nonnegative, a perfect matching has cost zero exactly when each chosen edge has cost zero. Consequently

    {S : mu(S)=0} = F(G_0,T),

where G_0 retains all vertices but only zero-cost edges. Any nonempty zero-optimum support therefore satisfies Theorem 1. A gadget whose allowed states have optimum zero and all other states have positive cost or are infeasible cannot realize exact paired copy or exact paired AND.

The same promised-domain caveat remains: setting all cross-pair edges to zero realizes copy correctly on D_3, with extra zero-cost invalid physical states.

### Global minimum support, including signed weights

Let c be the minimum of mu(S) over **all** physical boundary states, and suppose some state is feasible. The family {S:mu(S)=c} is also an even delta-matroid, even when some edge costs are negative.

To prove this, take optimum matchings M_A and M_B for any two globally minimizing states. For the alternating path from Theorem 1, flip both matchings simultaneously. Each path edge merely changes which matching contains it, so

    weight(M_A') + weight(M_B')
       = weight(M_A) + weight(M_B) = 2c.

Each flipped matching belongs to some physical boundary state and therefore has weight at least c. Both must have weight exactly c. Their two new boundary states are global minimizers, proving simultaneous exchange on the minimizing support. Fixed parity is unchanged.

This also excludes an exact constant-cost truth table whose desired states all have cost c and every undesired state has larger cost or is infeasible. A modular terminal offset sum_{t in S} a_t does not evade this particular argument: the sum of the two offset values is preserved by the simultaneous exchange as well.

### Arbitrary signed thresholds obey a weaker two-sided law

Fix any finite real threshold K and define F_K={S:mu(S)<=K}. If nonempty, F_K retains the fixed vertex parity. It also obeys the following necessary condition, weaker than ordinary symmetric exchange:

    For every A,B in F_K and e in A symmetric-difference B,
    some distinct f in A symmetric-difference B has
    A symmetric-difference {e,f} in F_K OR
    B symmetric-difference {e,f} in F_K.

**Proof.** Choose optimum matchings for A and B. The simultaneous alternating-path flip of Theorem 1 produces matchings at A' and B' with

    weight(M_A') + weight(M_B') = mu(A) + mu(B) <= 2K.

At least one flipped matching therefore has weight at most K; its boundary state's minimum cost is at most that matching's cost. This proves the disjunction. Edge costs may be signed and K may be negative, zero or positive. A fixed constant and modular terminal offset sum_{t in S}a_t also preserve this two-matching total, so they do not evade the condition. The condition is necessary; no sufficiency characterization is claimed. ∎

**Corollary: signed costs and thresholds still cannot implement exact paired copy or exact paired AND.** For k>=2 copied ports, take A empty and B all 2k terminals. Each candidate two-bit flip gives |A'|=2 and |B'|=2k-2, so both states are forbidden. For AND with at least one input, take A empty, B all terminals, and e an output rail. If f is the other output rail, A' encodes all inputs zero and output one, while B' encodes all inputs one and output zero: both are forbidden. If f belongs to an input pair, both A' and B' contain partially selected pairs and are forbidden by exact physical-boundary semantics. No f satisfies even the weaker law. Hence no graph with any number of internal vertices, arbitrary signed edge weights and a common threshold has exactly either relation as its accepted boundary family.

The same argument excludes a weighted threshold version of the transparent validity filter in Section 4, when the composite retains that exact external terminal-deletion relation. It still does not exclude correctness restricted to an externally promised valid domain.

### Threshold supports need not obey ordinary delta-matroid exchange

The set {S:mu(S)<=K} need not be a delta-matroid for a positive threshold. Here is a counterexample with strictly positive edge costs.

Use four terminals numbered 0,1,2,3, and two internal vertices numbered 4,5. Connect every terminal i to both internal vertices, assigning both incident edges cost i+1. There are no other edges. Feasibility requires deleting exactly two terminals; the two remaining terminal weights sum to mu(S).

At threshold K=5, the accepted deleted masks are

    {6,9,10,12}.

For A=9={0,3}, B=6={1,2}, take e=3. Toggling e together with f=0 gives empty, which is infeasible. Toggling it with f=1 or f=2 gives deletion masks 3 or 5, whose costs are seven and six respectively. Neither meets the threshold. Thus exchange fails. The globally minimizing support is different and does obey the theorem.

The weaker two-sided law nevertheless holds here. For the displayed A=9,B=6,e=3, taking f=1 gives A'=3 of cost seven and B'=12 of cost three. The latter meets K=5; the simultaneous total remains ten. Thus ordinary one-sided exchange fails while the necessary threshold condition survives. It would be incorrect to call every threshold support a delta-matroid. It would also be incorrect to use this failure as a way around the exact copy/AND obstruction, since those relations violate the weaker law too.

### Signed zero levels are not necessarily global minima

In the same bipartite graph, change the four terminal weights to 1,-1,2,-2. Its exact zero-optimum support is {3,12}, which fails exchange: the two feasible masks differ in all four terminal bits and no two-bit exchange remains at zero. Other boundary states have negative cost, so zero is not the global minimum.

This verifies why either nonnegativity or a genuine global-minimum hypothesis is needed for the exact zero-level argument. An exact cost level mu(S)=0 differs from the cutoff mu(S)<=0: the latter includes negative-cost states and satisfies two-sided exchange. Signed counting signatures are also outside these minimum-cost proofs.

## 6. What the reproducible experiment establishes

`matching_boundary.py` exhaustively computes minimum matching costs and witnesses for small graphs by a subset recursion; it is explicitly capped at ten vertices and is not presented as a scalable matching algorithm. The independent matching checker verifies every returned edge set against the original deleted-vertex request. The exchange routine constructs the alternating path, verifies both flipped perfect matchings, and checks exact preservation of total cost.

`run_experiments.py` checks all labelled simple graphs with at most five vertices and every terminal-prefix size, then seeded signed/nonnegative weighted cases. In every nonempty weighted case it tests two-sided exchange at every distinct finite optimum value, covering every distinct nonempty cutoff support for that graph. Enumerating all labelled graphs and all prefix sizes covers arbitrary terminal placements up to relabelling. It saves exact signatures, witness matchings and exchange failures for all examples in this theorem, and records source/input hashes. `test_matching_boundary.py` contains targeted regression tests for the support/domain distinction, transparent-intersection failure, signed-zero and positive-threshold caveats, quantitative simultaneous flips, and the stronger exact copy/AND threshold exclusions. Run the test suite and experiment to generate `RESULTS.json` and `RESULTS.md`.

The finite experiment can catch mistakes in the examples or certificate code. The all-size exclusions come from the proof, not from failure to find a gadget in a bounded graph search.

## 7. Exact missing ingredient for the candidate reduction

A candidate reduction built from promised-domain copy and logical gadgets still needs a uniform polynomial-size composition theorem proving that all accepted global perfect matchings decode to valid logical assignments, that every satisfying logical assignment extends to an accepted matching, and that costs and any threshold are preserved in both directions. This theorem must explain how validity is enforced without assuming the exact transparent filter ruled out above.

One possible route would use a different interface or a restricted global invariant. A global cost-budget encoding could also have a different contract, but signed weights and a threshold alone cannot supply the exact local copy/AND interface ruled out above. A general reduction using different interfaces or whole-instance invariants is not excluded by this local theorem, and none has been supplied here. Before using such a route as a universal solver, it needs an exact whole-instance proof and an algorithmic construction with polynomial bounds. The existence of a promised-domain gadget or a small truth-table match is not that missing proof.
