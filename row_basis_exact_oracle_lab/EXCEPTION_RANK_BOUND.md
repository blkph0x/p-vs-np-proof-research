# A route-specific exceptional-rank lower bound

Fix `r >= 6`, and let

`B = 1 + r + binomial(r,2)`

be the number of vectors in `F_2^r` of weight at most two. Draw
`m = 16 r^2` columns independently and uniformly from `F_2^r`, then append
the `r` standard basis columns. The appended columns ensure that the resulting
matrix has row rank `r`.

For a fixed invertible row transform `A` and nonzero functional `w`, an
exceptional column can fail to contribute outside `ker(w)` only when its
transformed value is in

`U union ker(w)`, where `U` is the weight-at-most-two set.

There are at most `B + 2^(r-1)` such values, so the probability that all `m`
random columns fail for this fixed `(A,w)` is at most

`rho^m`, with `rho = (B + 2^(r-1))/2^r`.

For `r >= 6`, `B <= 3*2^(r-2)`, hence `rho <= 7/8`. There are at most
`2^(r^2)` invertible matrices and fewer than `2^r` nonzero functionals. Since
`(7/8)^8 < 1/2`, the union bound is

`2^(r^2+r) (7/8)^(16 r^2) < 2^(-r^2+r) < 1`.

Therefore some choice of the random columns has the property that, for every
row basis, the exceptional columns are not contained in any hyperplane. Their
binary rank is consequently `p=r`. Appending the identity columns cannot lower
that rank. The resulting matrix has

`n = 16r^2 + r`

columns, while every rank-first native solver must allocate at least
`2^p = 2^r = 2^(Omega(sqrt(n)))` syndrome states.

`exception_rank_bound.py` checks the inequalities with exact rational arithmetic
for representative ranks and does not sample or claim an explicit deterministic
matrix. This is a lower bound for the row-basis/exceptional-syndrome route; it
does not prove P != NP or rule out unrelated polynomial algorithms.
