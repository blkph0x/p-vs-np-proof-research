# High-Width Core Stress Test — New Research Increment

**Status: theorem-backed counterexample families, finite exhaustive audits and working native min-weight algorithms. No proof of P=NP or P≠NP.**

## Question

Previous work treated binary-code pieces that are internally 4-connected as candidate irreducible nuclei, then looked for large trellis/pathwidth and hard affine-plus-cardinality merges. This lab asks whether those features imply that a code's minimum distance is computationally difficult. They do not.

## Result 1: an explicit all-size internally 4-connected high-width family

Take the cycle matroid M(K_t) of the complete graph on t≥5 vertices. It is represented over GF(2) by the reduced vertex-edge incidence matrix, with n=C(t,2) columns. Its rowspace is the **cut-space code**; the orthogonal dual is the **cycle-space code**.

We prove directly (see THEOREMS.md) that:

- M(K_t) is internally 4-connected for every t≥5.
- **Its matroid pathwidth is exactly t−2.** Since trellis width equals matroid pathwidth, the optimal maximum trellis table has exactly 2^(t−2) states.
- Cut-space minimum nonzero weight equals the graph's global minimum edge cut, t−1 for K_t.
- Cycle-space minimum nonzero weight equals graph girth, 3 for K_t.

The two native graph problems have standard polynomial algorithms (Stoer–Wagner global min cut and BFS shortest-cycle/girth), despite high trellis width. The cut-space/global-min-cut equality assumes a connected graph with at least one edge, as every K_t here is. A disconnected graph instead requires the smallest min-cut of its nontrivial connected components; an edgeless graph has no nonzero cut-space word.

| Clique t | Code length n | Exact optimal width | Trellis states | Cut code minweight | Cycle code minweight |
| --- | --- | --- | --- | --- | --- |
| 5 | 10 | 3 | 2^3 | 4 | 3 |
| 6 | 15 | 4 | 2^4 | 5 | 3 |
| 8 | 28 | 6 | 2^6 | 7 | 3 |
| 10 | 45 | 8 | 2^8 | 9 | 3 |
| 12 | 66 | 10 | 2^10 | 11 | 3 |
| 16 | 120 | 14 | 2^14 | 15 | 3 |
| 32 | 496 | 30 | 2^30 | 31 | 3 |
| 64 | 2016 | 62 | 2^62 | 63 | 3 |
| 128 | 8128 | 126 | 2^126 | 127 | 3 |
| 256 | 32640 | 254 | 2^254 | 255 | 3 |

At t=128, n=8,128, the **exact optimal width is 126**, so an optimal trellis must contain 2^126 states at some cut. The dual cycle code has dimension 8,001 yet its minimum weight is exactly 3, recognized from a triangle. For t=256, pathwidth is exactly 254 on n=32,640 coordinates. Thus the family is simultaneously internally 4-connected, high-width, and efficiently solvable *by a different algorithmic theory*. The rank-width lower bound alone does not imply hardness of the underlying decision problem.

**Why internal 4-connectivity holds:** if one color class of a two-coloring of the K_t edges is disconnected as a spanning graph, the opposite color class is connected (all edges between its components are on the other side). A connectivity cut of order at most 2 therefore has a disconnected side of graphic rank at most 2, which has at most three edges; the three-edge case is a triangle. No nontrivial 3-separation is possible.

**Why pathwidth is exactly t−2:** immediately before the first prefix of an arbitrary edge order whose edges connect all vertices, that prefix has exactly two connected components. All cross edges are in the suffix, so the suffix is connected, giving λ=t−2. Conversely, order all edges lexicographically by their lowest endpoint. Every prefix has λ≤t−2. Both directions are elementary and apply for every t≥3.

## Result 2: finite random-core audits against exact zero-error width

The included C++ verifier enumerates *all unordered coordinate cuts* for random binary column matroids of length 18 through 26, computing GF(2) ranks from columns and checking all low-order separations. The n=28 run exhausts only the balanced cuts and **does not certify internal 4-connectivity**.

| n | dimension | Internal 4 certified? | Cuts exhaustively audited | Certified middle-cut LB | Greedy trellis states | Exact minweight |
| --- | --- | --- | --- | --- | --- | --- |
| 18 | 9 | True | 131071 | 4 | 128 | 3 |
| 20 | 10 | True | 524287 | 5 | 128 | 3 |
| 22 | 11 | True | 2097151 | 6 | 256 | 4 |
| 24 | 12 | True | 8388607 | 6 | 512 | 4 |
| 26 | 13 | True | 33554431 | 7 | 1024 | 4 |
| 28 | 14 | False | 20058300 | 8 | 2048 | 4 |

The full audits found zero 3-connectivity/internal-4-connectivity violations for the n≤26 samples. The computed central-cut minimum λ is an unconditional finite-instance lower bound on optimal trellis width: any coordinate order passes through a cut of size n/2.

The minimum-distance answers were independently recomputed using (i) enumeration of all 2^k codewords from the generator and (ii) an exact **syndrome trellis DP** over a heuristic order. All answers agreed. The trellis DP keeps only partial syndromes extendable by suffix variables, has at most 2^λ distinct syndrome states at a cut, and verifies its reconstructed minimum-weight nonzero word against a parity-check matrix. Its cost remains exponential in width.

The heuristic order can be considerably worse than the certified lower bound. For example, the n=28 sample has exact central-cut lower bound 8 but its greedy trellis needed 2,048 (=2^11) syndrome states. This demonstrates an ordering gap, not an optimality lower bound of 11.

The full n=26 search checks 33,554,431 unordered cuts; n=28 balanced-only checks 20,058,300 balanced cuts. The results store generator columns, cut histograms, a minimizing witness cut, the scan mode, and runtimes. The generator seeds and C++ source are included.

## Result 3: a separate probabilistic high-width existence theorem

For a uniformly random binary k×2k matrix, a fixed k-column submatrix has rank deficiency at least s with probability at most 4·2^(−s²). This follows by union-bounding over s-dimensional subspaces of its kernel.

Union-bounding over both sides of all balanced coordinate partitions gives probability at most

    2^(2k+3−s²)

that *any* balanced side has rank < k−s+1. Full row rank fails with probability less than 2^(−k). Choose

    s=ceil(sqrt(2k+6)).

The sum of failure bounds is less than 1, so some full-rank binary code of length n=2k has, **for every balanced cut**,

    λ(S) ≥ k−2s+2 = k−O(sqrt(k)).

Hence there exist binary linear codes with trellis/pathwidth **Ω(n)**. This is an existence argument, not a claim that an arbitrary stored large random seed has passed an exponential cut audit, nor a claim that random-code minimum distance is provably hard on typical instances.

| n | k | t threshold | Existence lower bound | Min trellis states |
| --- | --- | --- | --- | --- |
| 28 | 14 | 6 | 4 | 2^4 |
| 40 | 20 | 7 | 8 | 2^8 |
| 80 | 40 | 10 | 22 | 2^22 |
| 200 | 100 | 15 | 72 | 2^72 |
| 512 | 256 | 23 | 212 | 2^212 |
| 1000 | 500 | 32 | 438 | 2^438 |
| 2000 | 1000 | 45 | 912 | 2^912 |

This existence theorem is standard probabilistic-method reasoning developed explicitly here; no novel P-versus-NP conclusion follows.

## Result 4: the appropriate hardness criterion is algorithm-relative

The explicit family defeats three insufficient tests:

1. **Sum indecomposability** alone does not imply hardness: M(K_t) is internally 4-connected.
2. **High optimal trellis width** alone does not imply hardness: pw(M(K_t))=t−2, while global graph algorithms solve minweight.
3. **Large code dimension** alone does not imply hardness: the cycle-space code has dimension C(t,2)−t+1 and girth 3.

The relevant hard merge is generally AFFINE + CARDINALITY, which contains NP-complete binary linear-code minimum distance (Vardy, 1997), but special subclasses such as graphic codes evade that hardness through a stronger native theory. One must **prove** that a candidate family defeats every offered polynomial native algorithm, not merely observe that explicit-state DP is expensive.

## Scorecard

| Claim | Status |
|---|---|
| M(K_t) internally 4-connected for t≥5 | all-size elementary proof; independent finite audits t=5,6 |
| pw(M(K_t))=t−2 | all-size elementary proof; exact finite checks t=5,6; trellis verification t≤12 |
| Graphic cut/cycle minimum weight polynomial | known graph algorithms, implemented and tested |
| Random n≤26 internally 4-connected | all cuts exhaustively checked in C++ |
| Random n=28 internally 4-connected | **not established**; only balanced cuts scanned |
| Existential binary codes with trellis width Ω(n) | first-principles probabilistic proof |
| Random minimum distance hard on average | **not established** |
| A universal polynomial merge tree for SAT | **not established** |
| P=NP | **not proved** |

## Independent reproduction

Run `python -m unittest -v test_lab`. To regenerate the exhaustive C++ results, run `python run_lab.py` after installing g++ or let the script compile `rank_audit.cpp` automatically. The complete n≤26 re-scan can take tens of seconds; use `FAST_AUDIT=1 python run_lab.py` to validate the saved exhaustive certificates and rerun the smaller DP/native checks without repeating the full scan.

`rank_audit.cpp` supplies an independently rerunnable exhaustive numerical certificate; a single witness mask by itself does **not** prove the minimum, which is why the full enumeration code and seed are included.

## Literature cross-check

- Navin Kashyap, **Matroid Pathwidth and Code Trellis Complexity** (SIAM J. Discrete Math. 22, 2008): trellis-width = matroid pathwidth and optimizing it is NP-hard. https://epubs.siam.org/doi/10.1137/070691152
- Alexander Vardy, **The Intractability of Computing the Minimum Distance of a Code** (IEEE Trans. Inf. Theory 43(6), 1997): binary minimum-distance decision is NP-complete. https://doi.org/10.1109/18.641542
- Classical graphic matroid representation, global min-cut and shortest-cycle algorithms. The particular K_t pathwidth proof is supplied explicitly rather than assumed from a source.

## Next genuinely hard adversary

Build or certify an **internally 4-connected high-trellis-width non-graphic binary-code family** with growing dimension, and attack the minimum-weight decision with every theory in the typed portfolio. But even surviving a large finite portfolio is not a complexity lower bound: a general hardness statement would require a reduction or proof-complexity lower bound that accounts for the new representation language.
