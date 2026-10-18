# Formal Results and Proofs — High-Width Core Stress Lab

## Theorem A: the graphic matroid of K_t is internally 4-connected (t>=5)

Let the ground set E be all edges of the complete graph K_t. For an edge set S, let c(S) be the number of connected components of the spanning graph (V,S), including isolated vertices. The graphic matroid rank is r(S)=t-c(S). Since r(E)=t-1,

    lambda(S)=r(S)+r(E-S)-r(E)=t+1-c(S)-c(E-S).

If (V,S) is disconnected, then (V,E-S) is connected: every edge between two different S-components necessarily lies in E-S, and the resulting complete multipartite spanning subgraph is connected. Symmetrically, if the complement graph is disconnected, the S graph is connected.

If both spanning graphs are connected, lambda(S)=t-1>=4. Otherwise exactly one is connected and lambda(S) equals the graphic rank of the disconnected side.

For any edge set of graphic rank at most two, the number of edges is at most C(3,2)=3 (a rank-r graph has at most C(r+1,2) edges). Therefore any separation with lambda<=1 has a side of at most one edge: K_t's matroid is 3-connected.

Likewise, a lambda=2 cut with at least three edges on both sides must have a disconnected side with rank exactly two and at most three edges; since the side has at least three, it consists exactly of a 3-cycle/triangle. Every 3-separation therefore has a triangle side. Hence M(K_t) is internally 4-connected.

## Theorem B: exact pathwidth pw(M(K_t))=t-2 (t>=3)

**Lower bound.** Consider any ordering of the edges. Let S be the prefix *immediately before* the first prefix whose spanning graph becomes connected. Adding one edge decreases component count by at most one, so the preceding prefix has exactly two connected components. The complement graph must be connected because it contains all edges crossing those two components. Hence

    lambda(S)=t+1-2-1=t-2.

Thus every edge order has width at least t-2.

**Upper bound.** Order edges (u,v), u<v, lexicographically by u then v. During the first vertex's star, before its last edge, the prefix graph has one star plus isolated vertices; its rank is at most t-2 while the suffix is connected, so lambda<=t-2. Once all edges incident with vertex zero have been visited, the prefix graph is connected. Thereafter the suffix has at least two spanning components (vertex zero is isolated), so lambda=t-c(E-S)<=t-2. Hence the constructed order has width at most t-2.

Therefore pw(M(K_t))=t-2. By the established trellis-width/matroid-pathwidth equivalence, both the cut-space code and the dual cycle-space code have an optimal trellis whose maximum state count is 2^(t-2).

As n=C(t,2), this is 2^Theta(sqrt(n)), superpolynomial in the code length.

## Theorem C: native graph minimum distance

For a connected graph G with at least one edge, the reduced vertex-edge incidence matrix generates all binary graph cuts (cut-space). Every nontrivial vertex subset U has a nonzero edge cut delta(U), so the minimum nonzero Hamming weight equals graph edge connectivity/min-cut. For disconnected G, the global min-cut is zero even when the cut-space contains nonzero words; its nonzero minimum weight is instead the smallest min-cut among connected components containing an edge. An edgeless graph has no nonzero cut-space word.

The dual code is the kernel of the incidence matrix: its words are even-degree edge subsets (binary cycle-space). Every nonzero even-degree subgraph contains a cycle; conversely any cycle gives an even-degree subgraph. Thus minimum nonzero word weight equals graph girth/shortest cycle.

Global min cut and shortest cycle admit polynomial graph algorithms. For K_t the minimum cut is t-1 and the girth is 3.

Therefore internal 4-connectivity, superpolynomial trellis size, and large code dimension do not imply computational hardness for these code families.

## Theorem D: existential random codes of linear pathwidth

Let G be a uniformly random k x 2k binary matrix with independent unbiased entries. Fix a k-column submatrix A.

If rank(A)<=k-s, its kernel contains an s-dimensional subspace U. There are at most

    [k choose s]_2 <= 4*2^(s(k-s))

such subspaces: the denominator of the Gaussian-binomial product is at least the positive constant product_(j>=1)(1-2^(-j))>1/4. For each fixed U, the event A U=0 has probability 2^(-ks). By union bound,

    P(rank(A)<=k-s) <= 4*2^(-s^2).

There are at most 2*C(2k,k) balanced half-matrices across all size-k coordinate cuts, counting both sides, so

    P(some balanced side has rank<=k-s)
      <= 8*C(2k,k)*2^(-s^2)
      <= 2^(2k+3-s^2).

Separately, G has row rank less than k only if a nonzero linear combination of its k rows vanishes across all 2k columns. The union bound gives

    P(rank(G)<k)<2^k*2^(-2k)=2^(-k).

Set s=ceil(sqrt(2k+6)). The total failure probability is less than 1 (in fact at most 1/8+2^(-k)). Therefore a full-rank G exists such that for every size-k coordinate subset S,

    r(S)>=k-s+1; r(E-S)>=k-s+1.

Thus

    lambda(S)=r(S)+r(E-S)-k>=k-2s+2=k-O(sqrt(k)).

Every variable ordering has a k-coordinate prefix, so its trellis width is at least this bound. Therefore binary linear codes with trellis/pathwidth Omega(n) exist.

This proof is existential, not an explicit polynomial-time deterministic construction of a certified good code and not a hardness proof for minimum distance on random instances.

## Lemma E: the exact trellis DP is sound

Given a parity-check matrix H whose kernel is the code C, a coordinate order pi and a prefix assignment x_prefix, its partial syndrome is

    s=H_prefix*x_prefix.

The prefix can extend to a codeword iff s belongs to the span of the remaining parity-check columns. The algorithm retains exactly such syndromes and the minimum Hamming weight for each syndrome and a Boolean nonzero-used flag. At each coordinate it tries bit 0/1, updates syndrome/weight and discards states not in the suffix span. Keeping only the lowest cost for each (syndrome,flag) is valid because future transitions depend solely on this pair. At the end, syndrome=0 with the nonzero flag is exactly a nonzero codeword, and minimizing the stored cost gives its minimum weight.

The number of feasible syndromes at a cut equals the size of span(prefix columns) intersect span(suffix columns), or 2^lambda, since all vector spaces are over GF(2). This lemma does not provide a polynomial bound on the width or discovery of a good order.
