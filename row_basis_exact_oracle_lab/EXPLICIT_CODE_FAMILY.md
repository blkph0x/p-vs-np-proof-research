# Explicit concatenated-code obstruction

For `k >= 7`, set `q=2^k`, `t=floor(q/k^2)`, and `r=kt`. Let messages be
polynomials

`f(x)=a_0+a_1 x+...+a_(t-1) x^(t-1)`

over `GF(q)`. Evaluate at every `a in GF(q)`. For each nonzero `beta in GF(q)`,
replace the symbol `f(a)` by the binary coordinate `Tr(beta*f(a))`, where `Tr`
is the absolute field trace. The resulting binary linear code has dimension
`r=kt` and `n=q(q-1)` distinct coordinate functionals.

The distance proof is elementary. A nonzero degree-`<t` polynomial has at most
`t-1` roots, so at least `q-t+1` evaluated symbols are nonzero. For a nonzero
symbol `y`, exactly `q/2` field elements `beta` satisfy `Tr(beta*y)=1`; one is
`beta=0`, so the retained nonzero-beta block contributes `q/2` ones. Hence

`d >= (q-t+1) q/2`.

Because `q >= k^2 t`, the right side is at least
`(k^2-1)k^2 t^2/2`, which is larger than
`1+kt+binomial(kt,2)` for `k>=7,t>=2`.

Distinctness is also checkable: if two coordinate functionals `(a,beta)` and
`(a',beta')` agree, testing messages with only `a_0` nonzero gives `beta=beta'`
by nondegeneracy of the trace pairing. Testing messages with only `a_1`
nonzero then gives `a=a'`. The condition `t>=2` holds for every `k>=7`,
because `2^k >= 2k^2` there.

Let `U` be the at-most-two-weight vectors in `F_2^r`, with
`B=1+r+binomial(r,2)` elements. For every nonzero binary functional, the code
has at least `d` columns on which it evaluates to one. Since `d>B`, those
columns cannot all lie in any transformed copy of `U`, whose size is only `B`.
Therefore the exceptional columns span all `r` dimensions for every row basis.
The native syndrome route consequently requires `2^r` states on this explicit
family.

This is an infinite explicit family. Since `q/(2k^2) <= t <= q/k^2`, its
column count satisfies `n=O(k^2 r^2)`, while `k=O(log r)`. Thus the forced
state count is `2^r = 2^(Omega(sqrt(n)/log n))`, which is superpolynomial in
the encoded column count.

The files `explicit_code_family.py` and `EXPLICIT_CODE_FAMILY_REVIEW.py`
construct and replay the cases `k=7,8,9`:

| k | r | columns | distance lower bound | forced states |
|---:|---:|---:|---:|---:|
| 7 | 14 | 16,256 | 8,128 | 16,384 |
| 8 | 32 | 65,280 | 32,384 | 4,294,967,296 |
| 9 | 54 | 261,632 | 129,792 | 18,014,398,509,481,984 |

This is a lower bound for the particular row-basis/exceptional-syndrome route.
It is explicit and deterministic, but it is not a proof that P differs from NP:
other algorithms may use information this representation discards.
