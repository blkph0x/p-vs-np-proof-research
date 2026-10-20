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

## The unit witness stops at the exact boundary

The level `d-2` in the theorem is sharp for this family. Fix a pin `j` and
let `H_j` be the affine subspace obtained by fixing the first `s` coordinate
bits to the corresponding bits of `j`. Its indicator is the Reed--Muller
polynomial

```text
h_j(x) = product_{i=0}^{s-1} (1 + j_i + x_i),
```

so `h_j` is a codeword of weight `d`. Self-duality makes it a dual word as
well. Put `S = H_j \ {j}`, which has size `d-1`. Every codeword `c` with
`c_j=1` obeys

```text
0 = <h_j,c> = c_j + sum_{x in S} c_x  (mod 2),
```

and therefore its projection onto `S` has odd parity. In particular the
all-zero assignment on `S` is absent from the pinned-code projection. The
unit local witness would require exactly that atom on the scope `S`, so it is
infeasible at level `d-1`. Combined with the dual-distance construction, the
maximum level supporting the unit witness is exactly `d-2` for every member of
`RM(s,2s+1)`.

The repository's boundary test reconstructs `h_j` from the generator rows for
several family members and pins, checks its exact dual orthogonality, and
checks the `d-1` scope size. This is a structural boundary theorem for the
declared local-marginal model, not a lower bound for arbitrary algorithms.

## Exact size law for the explicit all-scope model

The same family gives a precise representation-size warning. Write
`q = 2^s`, so `n = 2q^2` and the maximum unit-witness level is `k = 2q-2`.
Let

```text
M_s = sum_{i=0}^k binom(n,i)
```

be the number of coordinate scopes. The unrestricted atom-slot envelope is
`A_s = sum_{i=0}^k 2^i binom(n,i)`. Because every scope below `d-1` projects
to the full cube when the pin is omitted and to the pin-one half-cube when the
pin is included, the actual supported atom count is

```text
B_s = sum_{i=0}^k [2^i binom(n-1,i) + 2^(i-1) binom(n-1,i-1)],
```

where the second term is zero at `i=0`. Since `k <= n/2`, binomial
coefficients increase through `k`, and therefore

```text
binom(n,k) <= M_s <= (k+1) binom(n,k),
2^k binom(n-1,k) <= B_s <= (k+1) 2^(k+1) binom(n-1,k),
2^k binom(n,k) <= A_s <= (k+1) 2^k binom(n,k).
```

The standard elementary bounds
`(n/k)^k <= binom(n,k) <= (e n/k)^k` then give

```text
log M_s = Theta(k log(n/k)) = Theta(2^s s),
log B_s = Theta(k log(n/k)) = Theta(2^s s).
```

Equivalently, the scope count and the actual supported atom count are
`exp(Theta(sqrt(n) log n))`; `A_s` is a matching unrestricted envelope. This
is an exact scaling law for the unquotiented all-scope representation.
Symmetry quotients or implicit separation may be much smaller; this
calculation does not rule out them, and it is not a lower bound for arbitrary
SAT algorithms. The test suite and independent replay check the displayed
inequalities with exact integers for the first six family members.

This is a barrier for this exact local projection-marginal architecture. A
stronger hierarchy, global valid inequalities, a different representation, or
an efficient separation algorithm could evade it. The input itself has `n`
coordinates, and constructing the saved generator matrix is polynomial in `n`;
the result therefore gives an explicit, reproducible family rather than a
random-existence argument. It still says nothing about arbitrary SAT solving.

## An exact boundary-level value for the plain local model

The first level after the unit witness fails has an exact value for the plain
projection-marginal model. Let `k = d-1`, and let `H` range over all affine
`(s+1)`-flats through the pinned point `j`. Each `H` is the support of a
minimum-weight codeword of `RM(s,2s+1)`, hence a dual check by self-duality. On
the scope `S = H \ {j}`, every allowed pinned projection has odd parity. Its
local table therefore has expected Hamming weight at least one:

```text
sum_{i in S} x_i >= 1.
```

There are the Gaussian-binomial number
`P = [2s+1 choose s+1]_2` of such flats. Every non-pin coordinate belongs to
`Q = [2s choose s]_2` of them. Summing the inequalities and using the shared
singleton marginals gives

```text
W = 1 + F, where F = sum_{i != j} x_i
          >= 1 + P/Q
          = 1 + (2^(2s+1)-1)/(2^(s+1)-1).
```

For the matching upper bound, put `p = 1/(d-1)`. On every scope below the
boundary, assign mass `p` to each one-hot non-pin atom and mass
`1-|T|p` to the all-zero atom, where `T` is the set of non-pin coordinates in
the scope. At a boundary scope of size `d-1` omitting the pin, use the same
one-hot masses and zero mass on the all-zero atom. Every one-hot assignment is
allowed. Below the boundary, a relation on the prescribed coordinates would be
a nonzero dual word below distance `d`. At a boundary scope, any relation on
the scope together with the pin has support exactly `d` and is unique if it
exists; a one-hot non-pin assignment has total parity `1+1=0` on that support,
so it satisfies the relation. The boundary tables marginalize to the smaller
tables because `(d-1-|T|)p = 1-|T|p`; scopes containing the pin have at most
`d-2` free coordinates and obey the same identity. Thus these tables are
feasible and have reduced objective `F=(n-1)p` and total objective
`W=1+(n-1)p`.

Consequently, for the plain model,

```text
OPT_F(L_{d-1}(RM(s,2s+1), j))
  = (2^(2s+1)-1)/(2^(s+1)-1),
OPT_W(L_{d-1}(RM(s,2s+1), j))
  = 1 + (2^(2s+1)-1)/(2^(s+1)-1).
```

Restriction gives the same lower bound for every level `k >= d-1`. For `s=2`
the exact boundary value is reduced `31/7` (total `38/7`), the affine-flat
star optimum recorded in the finite RM(2,5) campaign, while the exact
level-eight value is reduced `31/5` (total `36/5`).
This is an analytical theorem for the declared projection-marginal model; it
does not imply a bound for arbitrary SAT algorithms or for P versus NP. The
incidence identity is also the elementary mechanism already used in the
repository's all-dual report, so no novelty claim is made for that counting
argument itself.

The independent replay recomputes both Gaussian-binomial incidence counts and
the rational bound for `s=1,...,8`.

Together with the dual-distance unit witness, this gives the first two exact
levels of the family. The unit witness has reduced objective zero and total
objective one:

```text
OPT_F(L_k) = 0                                  for k <= d-2,
OPT_W(L_k) = 1                                  for k <= d-2,
OPT_F(L_{d-1}) = (2^(2s+1)-1)/(2^(s+1)-1),
OPT_W(L_{d-1}) = 1 + (2^(2s+1)-1)/(2^(s+1)-1).
```

The second line is a boundary theorem, not a claim that the same value persists
at higher levels.

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
