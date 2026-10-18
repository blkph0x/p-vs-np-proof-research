# Polynomial-size accounting for the degree-three boundary

The gadget replay audits local parity maps. This companion audit checks the
reduction's numerical resource bounds independently of those maps.

For a 3-left-regular input with `n` variables and `M` check-splitting
auxiliaries, the first phase uses

\[
m=2\max(1,M),\qquad \lambda=m+4,
\]

and produces `N = lambda*n + 2*M` variables with threshold
`hat_w = lambda*w + 2*M`. Thus `lambda > 2*M`, and `w <= n` implies
`hat_w <= N`; the threshold gap used in the reduction is strict.

If `q>0` degree-two checks remain, the completion chooses
`c = 3 ceil((N+1)/q)` copies and `h=cq` degree-two checks. Therefore
`h >= 3N+3`, while `h <= 3(N+q)`. With `t=h/3` suffix stages, the exact
number of suffix variables is

\[
\sum_{j=0}^{t-1}(h-3j-2)=\frac{h(h-1)}6=O((N+q)^2).
\]

Check splitting gives `M <= 3n` for a 3-left-regular input, so `N=O(n^2)`;
the completion is consequently polynomial in the explicit input size. The
machine checker in `regular_ldpc_size_bounds.py` verifies these identities and
inequalities over every integer row with `1 <= n <= 32`, `0 <= M <= 3n`, every
threshold `0 <= w <= n`, and every `1 <= q <= 3n`.

This proves only the resource-accounting portion of the cited reduction. It is
not a proof of P != NP and does not replace the source paper's all-size parity
correspondence.
