# Every redundant parity check still leaves a constant RM gap

The local projection-marginal relaxation has a `Theta(sqrt(n))` gap on the
explicit self-dual family `RM(s,2s+1)`. This follow-up gives the stronger
relaxation every nonzero dual parity check for free. The gap becomes smaller,
but it does not disappear: the exact fractional optimum is still separated
from the pinned integer optimum by a ratio approaching two.

This is a code-polytope obstruction, not a lower bound for arbitrary linear
programs, SAT algorithms, or P versus NP.

## The all-dual relaxation

For a binary linear code `C`, let `Q_all(C)` intersect the Boolean
even-parity polytope for every nonzero `h in C^perp`. Pin coordinate `j` to one
and minimize `sum_i x_i`. Integer feasible points are exactly codewords of
`C` with `c_j=1`. This is the same all-redundant-parity relaxation studied in
[`ALL_DUAL_LP_THEOREM.md`](../ALL_DUAL_LP_THEOREM.md), applied here to an
explicit deterministic family.

For `RM(s,2s+1)`, write

\[
n=2^{2s+1},\qquad d=\delta=2^{s+1},\qquad p=1/(d-1).
\]

The point

\[
x_j=1,\qquad x_i=p\quad(i\ne j)
\]

is feasible for every dual check. A check of weight `w >= d` containing the
pin needs odd parity on its `w-1` free coordinates; a check omitting the pin
needs even parity on all `w` coordinates. In either case, a mixture of the two
adjacent permitted cardinalities has expected free weight `p(w-a)`, where `a`
is the pin bit. The producer and independent reviewer record these mixtures
with exact `Fraction` arithmetic for every `w` from `d` through `n` and both
pin cases. No floating-point LP solver is used.

## Matching lower bound

The minimum-weight affine checks already force the same objective. Let `N` be
an `r`-dimensional normal subspace of `F_2^m`, where `m=2s+1` and `r=s`.
The affine subspace `N^perp + j` has codimension `r`, size `d`, and its
indicator is

\[
\prod_{v\in B}(1+v\mathbin{\cdot}(x+j)),
\]

for any basis `B` of `N`. This is a degree-`r` Boolean polynomial, hence a
codeword of `RM(r,m)`, and it contains the pinned coordinate `j`.

The number of choices of `N` is the binary Gaussian binomial

\[
A={m\brack r}_2.
\]

For a fixed other coordinate `i`, the affine check contains both `i` and `j`
exactly when `N` is orthogonal to `i-j`; the count is

\[
B={m-1\brack r}_2.
\]

Each such even-parity check has the valid forbidden-set inequality
`x_j <= sum_{i in support(h)-{j}} x_i`. Summing the `A` inequalities and
using the uniform `B` incidence gives

\[
\sum_{i\ne j}x_i \ge A/B
 = (2^m-1)/(2^{m-r}-1)=(n-1)/(d-1).
\]

The uniform point attains this bound, so its all-dual fractional optimum is
exactly

\[
1+(n-1)/(d-1).
\]

The Gaussian-binomial arithmetic is independently recomputed; a deliberately
truncated implementation was rejected during development and replaced by an
exact product-then-divide calculation.

## Saved results

| family | `n` | `d` | all-dual fractional optimum | integer/fractional ratio | word replay |
| --- | ---: | ---: | ---: | ---: | --- |
| `RM(1,3)` | 8 | 4 | `10/3` | `6/5` | all 16 words |
| `RM(2,5)` | 32 | 8 | `38/7` | `28/19` | all 65,536 words |
| `RM(3,7)` | 128 | 16 | `142/15` | `120/71` | theorem-backed |

For the symmetric family `n=d^2/2`, the ratio tends to two. Thus every
redundant parity check substantially tightens the earlier local relaxation,
but parity checks alone do not recover the integer optimum on this explicit
family. The all-dual check list itself has exponentially many codewords; this
certificate gives an analytic separation proof rather than claiming that the
checks can be enumerated in polynomial time.

## Reproduction and scope

```text
cd local_marginal_code_lab
python run_all_dual_reed_muller.py
python REED_MULLER_ALL_DUAL_INDEPENDENT_REVIEW.py
python -m unittest -v test_all_dual_reed_muller.py
```

The machine-readable records are
[`REED_MULLER_ALL_DUAL_RESULTS.json`](REED_MULLER_ALL_DUAL_RESULTS.json) and
[`REED_MULLER_ALL_DUAL_INDEPENDENT_REVIEW.json`](REED_MULLER_ALL_DUAL_INDEPENDENT_REVIEW.json).
The Reed--Muller construction is sourced in
[`REED_MULLER_THEOREM.md`](REED_MULLER_THEOREM.md) via [Reed's 1954 paper](https://doi.org/10.1109/TIT.1954.1057465)
and [MIT's coding-theory notes](https://ocw.mit.edu/courses/6-895-essential-coding-theory-fall-2004/resources/lect05slx4/).
