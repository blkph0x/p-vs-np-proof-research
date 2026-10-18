# An explicit Reed--Muller local-marginal gap

This report adds a deterministic code family to the local projection-marginal
barrier. It does **not** prove a lower bound for arbitrary algorithms or for
P versus NP.

## Family and certificate

For a positive integer `s`, set

\[
m=2s+1,\qquad r=s,\qquad n=2^m.
\]

`RM(r,m)` is the binary evaluation code whose coordinates are the points
`x` of `F_2^m` and whose generator rows are the evaluation vectors of every
square-free monomial `x_I = product_{i in I} x_i` with `|I| <= r`. The saved
certificate reconstructs these rows from their monomial masks, recomputes the
dual basis, and stores a pinned coordinate `j=0`.

The campaign contains `RM(1,3)`, `RM(2,5)`, and `RM(3,7)`. The first case
enumerates all codewords and every local scope through level two. The second
enumerates all `2^16 = 65,536` codewords but intentionally does not enumerate
its level-six scopes. The third case has dimension 64, so the certificate uses
the proved formula and an explicit minimum-weight witness instead of expanding
`2^64` codewords. The independent checker reconstructs all three generator
matrices without importing the producer.

## Distance and duality proof

Every nonzero multilinear Boolean polynomial of degree at most `r` in `m`
variables has at least `2^(m-r)` nonzero evaluations. Induct on `m`. Write

\[
f(x,y)=g(x)+y h(x),
\]

where `deg(g) <= r` and `deg(h) <= r-1`. If `h=0`, the two `(m-1)`-variable
slices are equal and the induction bound doubles. If `h != 0` and both slices
are nonzero, apply the induction bound to `g` and `g+h`. If one slice is zero,
the other is `h`, and the stronger degree bound for `h` gives the same total.
The base cases are constant nonzero polynomials and the zero polynomial. The
bound is attained by

\[
f(x)=\prod_{i=1}^{r}(1+x_i),
\]

whose support is the codimension-`r` affine subspace `x_1=...=x_r=0`.
Therefore

\[
\dim RM(r,m)=\sum_{i=0}^{r}\binom mi,
\qquad d(RM(r,m))=2^{m-r}.
\]

For monomials on supports `I` and `J`, their evaluation-row inner product is
the parity of `2^(m-|I union J|)`. If `|I| <= r` and `|J| <= m-r-1`, then
`|I union J| <= m-1`, so the inner product is zero over `F_2`. The dimensions
of the two spaces add to `2^m`, hence

\[
RM(r,m)^\perp = RM(m-r-1,m).
\]

With `m=2s+1` and `r=s`, the family is self-dual and both primal and dual
distance equal

\[
d=\delta=2^{s+1}.
\]

The saved witness is the affine indicator through the pinned point. For a
general pin `j`, the producer expands

\[
\prod_{i=0}^{r-1}(1+j_i+x_i),
\]

so the witness has weight `2^(m-r)` and evaluates to one at `j`.

## Consequence for the local relaxation

The local-marginal theorem in [`THEOREM.md`](THEOREM.md) says that a dual
distance `delta` leaves the unit-vector point feasible through level
`delta-2`. Applying it here gives

\[
k=2^{s+1}-2,\qquad
\operatorname{OPT}_{\text{integer}}(C_j)=2^{s+1},\qquad
\operatorname{OPT}_{\text{local}}=1.
\]

Thus the explicit deterministic family has a multiplicative gap
`2^(s+1) = Theta(sqrt(n))` at a level that is also `Theta(sqrt(n))`. The
certificate proves the family formula and the affine witness; only `RM(1,3)`
has a complete scope-by-scope support replay because the number of scopes grows
as `sum_{i<=k} binom(n,i)`.

This is a barrier for this exact local projection-marginal architecture. A
stronger hierarchy, global valid inequalities, a different representation, or
an efficient separation algorithm could evade it. The input itself has `n`
coordinates, and constructing the saved generator matrix is polynomial in `n`;
the result therefore gives an explicit, reproducible family rather than a
random-existence argument. It still says nothing about arbitrary SAT solving.

## Public sources and replay commands

The family is the standard Reed--Muller construction introduced in Reed's
original 1954 paper, [“A class of multiple-error-correcting codes and the
decoding scheme”](https://doi.org/10.1109/TIT.1954.1057465). The MIT OpenCourseWare
lecture notes provide an independent coding-theory reference for the
construction and its parameters: [Essential Coding Theory,
Lecture 5](https://ocw.mit.edu/courses/6-895-essential-coding-theory-fall-2004/resources/lect05slx4/).
The repository proves the specific identities used above and does not treat a
source citation as evidence of a P-versus-NP result.

```text
cd local_marginal_code_lab
python run_reed_muller.py
python REED_MULLER_INDEPENDENT_REVIEW.py
python -m unittest -v test_reed_muller.py test_local_marginal.py
```

The machine-readable records are
[`REED_MULLER_RESULTS.json`](REED_MULLER_RESULTS.json) and
[`REED_MULLER_INDEPENDENT_REVIEW.json`](REED_MULLER_INDEPENDENT_REVIEW.json).

The stronger all-redundant-parity experiment is recorded separately in
[`REED_MULLER_ALL_DUAL_REPORT.md`](REED_MULLER_ALL_DUAL_REPORT.md); it keeps
the family explicit while testing whether every dual XOR check closes the
local gap.
