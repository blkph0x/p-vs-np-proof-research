# Quadratic-length trace family

This artifact strengthens the earlier explicit trace-code obstruction for one
specific representation route: a solver that keeps a binary row basis and
branches on the exceptional syndrome columns (columns of transformed weight
greater than two).

## Construction

For an integer `k >= 4`, let `q = 2^k` and

`t = floor(q/(2k))`, `r = kt`.

Take all polynomials of degree less than `t` over `GF(q)`. Evaluate each
polynomial at every field element `a`. For every nonzero `beta` retain the
binary coordinate

`Tr(beta f(a))`,

where `Tr` is the absolute trace from `GF(q)` to `GF(2)`. This gives

`n = q(q-1)`

binary column functionals on an `r`-dimensional message space. The producer
and independent replay are in `quadratic_code_family.py` and
`verify_quadratic_code_family.py`; the saved finite certificate is
`QUADRATIC_CODE_FAMILY_RESULTS.json`.

## Why the exceptional columns have full rank

A nonzero polynomial of degree less than `t` has at most `t-1` roots, so it is
nonzero at at least `q-t+1` evaluation points. For any nonzero field value
`y`, exactly `q/2` values of `beta` satisfy `Tr(beta y)=1`; the omitted value
`beta=0` has trace zero. Therefore every nonzero binary message has Hamming
weight at least

`d = (q-t+1)q/2`.

The number of binary vectors of weight at most two in `F_2^r` is

`B = 1 + r + binomial(r,2)`.

Since `r <= q/2`,

`B <= 1 + q/4 + q^2/8`,

while `t <= q/(2k)` gives

`d >= (q-q/(2k)+1)q/2`.

Consequently

`d-B >= q^2(3k-2)/(8k) - q/4 - 1`.

For `k >= 4`, `(3k-2)/(8k) >= 5/16` and `q >= 16`, so this final expression is
at least `5q^2/16-q/4-1 >= 75`; the distance gap is strict. A nonzero
functional that vanished on every exceptional column would
therefore be one on at most `B` columns: after an invertible row change, all
remaining columns would be distinct vectors of weight at most two. This
contradicts the distance bound `d > B`. Thus the exceptional columns span all
`r` dimensions in every row basis. A rank-`r` subset of those columns has all
`2^r` syndromes as subset sums, so a DP whose state key is the native syndrome
cannot avoid those states by reachability pruning.

The construction also has

`q/4 <= r <= q/2`,

because `r >= q/2-k` and `2^k >= 4k` for `k >= 4`,

so `n = q(q-1) < q^2 <= 16r^2`. The route's syndrome enumeration is therefore
forced to have at least `2^r = 2^(Omega(sqrt(n)))` states on this family.

Here `n` is the number of binary columns. If the input is serialized as an
explicit list of `r`-bit columns, its bit length is `L=Theta(nr)=Theta(r^3)`;
the same statement is then `2^(Omega(L^(1/3)))` states. That is still
superpolynomial in the ordinary bit encoding, but it is weaker than the
column-count exponent and should not be conflated with it.

This is a lower bound for that representation and branching route. It does
not establish `P != NP`, because a different algorithm may avoid this
representation entirely.

## Replayed evidence

The saved cases are `k = 4,5,6,7`, with ranks `8,15,30,63`, column counts
`240, 992, 4032, 16256`, and state lower bounds
`2^8, 2^15, 2^30, 2^63`. The formula sweep checks `k = 4` through `12`.
The independent verifier reconstructs the field arithmetic, columns, all
sampled row transforms, distances, rank bounds, and a forged-record rejection.
