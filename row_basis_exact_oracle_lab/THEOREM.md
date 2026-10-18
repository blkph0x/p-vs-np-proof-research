# Exact small-rank row-basis discovery and its cost

For a rank-$r$ binary check matrix, every invertible row representation is
obtained by a matrix in $GL(r,2)$. The oracle enumerates these transforms,
recomputes every transformed column weight, and minimizes the lexicographic
objective

\[
(\#\{j:w_j>2\},\;\sum_j\max(0,w_j-2),\;\sum_jw_j).
\]

The enumeration is exact for ranks at most four. Its transform count is

\[
|GL(r,2)|=\prod_{i=0}^{r-1}(2^r-2^i),
\]

which is already 20,160 at rank four and grows as $2^{r^2+O(r)}$. A cap returns
`UNKNOWN` and never supplies a false optimum.

The separate `rank5_exact.cpp` oracle exhausts rank five on four fixed inputs.
Its span-recursion visits each ordered basis once, and the observed terminal
count is

`(32-1)(32-2)(32-4)(32-8)(32-16)=9,999,360`.

`RANK5_THEOREM.md` gives the corresponding finite certificate argument and
`RANK5_REVIEW.py` independently replays the saved arithmetic and native proofs.

The saved rank-three trap has exact objective $(1,1,31)$, while the production
strict-descent search reaches a certified local minimum $(2,2,33)$ when run
without restarts. This proves
that the current heuristic is not a global discovery algorithm. It does not
prove that all possible representation-discovery algorithms are hard, and it
does not imply P differs from NP.

The native syndrome solver is governed by the rank $p$ of exceptional columns,
not only their number $q$. On the saved rank-four matrix, the exact $q$-first
representation has $(q,p,\text{excess},\text{weight})=(2,2,2,28)$, while a
representation with four exceptions has $(4,1,4,31)$. Thus minimizing exception
count can choose a representation with twice the exponential syndrome-state
parameter. Any discovery objective intended to optimize the downstream solver
must account for this rank tradeoff.

The companion `EXCEPTION_RANK_BOUND.md` proves a route-specific asymptotic
obstruction by a union bound: for every `r >= 6`, some full-rank matrix with
`16r^2+r` columns forces exceptional rank `r` under every basis. Therefore this
native representation route has instances requiring `2^r` states, or
`2^(Omega(sqrt(n)))`. The result is probabilistic existence and does not imply
P != NP.

`EXPLICIT_CODE_FAMILY.md` strengthens this to an infinite deterministic family
using Reed--Solomon evaluation and the binary trace map. At `k=7,8,9` it forces
ranks 14, 32 and 54, with state counts `2^14`, `2^32` and `2^54`; the general
family has `2^(Omega(sqrt(n)/log n))` state growth for this route. It still does
not address algorithms outside the representation.
