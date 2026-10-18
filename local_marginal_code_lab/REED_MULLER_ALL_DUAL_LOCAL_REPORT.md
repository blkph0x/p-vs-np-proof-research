# All dual parity checks plus local marginals still leave the RM gap

The previous all-dual experiment constrained the singleton marginals with the
parity polytope of every nonzero dual check. This follow-up adds the complete
local projection-marginal system through the dual-distance level. On the
explicit self-dual family `RM(s,2s+1)`, the exact fractional optimum is
unchanged.

This is a barrier for the stated combined relaxation. It is not a lower bound
for arbitrary linear programs, lifted hierarchies, SAT algorithms, or P versus
NP.

## Combined relaxation

Fix a binary linear code `C` and a pinned coordinate `j`. The combined model
has two kinds of constraints:

1. singleton means `x_i` satisfy the even-parity polytope for every nonzero
   `h in C^perp`; and
2. for every scope `S` with `|S| <= k`, a probability table is supported on
   the projection of the pinned code `C_j`, with exact marginal consistency.

The objective is `sum_i x_i`. Integer feasible points are pinned codewords,
so their optimum is the pinned minimum distance.

For `RM(s,2s+1)`, put

\[
n=2^{2s+1},\qquad d=\delta=2^{s+1},\qquad k=d-2,
\]

where `d` is both the primal and dual distance. The all-dual certificate from
[`REED_MULLER_ALL_DUAL_REPORT.md`](REED_MULLER_ALL_DUAL_REPORT.md) supplies the
singleton point

\[
x_j=1,\qquad x_i=p=1/(d-1)\quad(i\ne j).
\]

Every nonzero dual check has weight at least `d`, and exact adjacent-cardinality
mixtures show that this point lies in every parity polytope. The minimum-weight
affine checks give the matching lower bound

\[
\sum_i x_i \ge 1+\frac{n-1}{d-1}.
\]

## Why the local tables do not cut the point

For any binary linear code whose dual distance is `delta`, projection onto a
coordinate set of size less than `delta` is surjective. Otherwise a nonzero
linear relation among the projected columns would give a dual word supported
on fewer than `delta` coordinates.

Take a scope `S` of size at most `k=d-2`. The set `S` together with the pin has
size at most `d-1`, so every assignment on `S` (or every assignment with the
pin fixed to one when the pin is in `S`) occurs in a pinned codeword. Therefore
the following table is supported on the pinned-code projection for every
scope:

\[
\mu_S(a)=p^{|a|}(1-p)^{|S|-|a|}
\]

on coordinates other than the pin, with the pin deterministically equal to
one. These product tables are exactly marginal-consistent, and their singleton
means are the all-dual point above. They provide a feasible witness for the
combined model at value `1+(n-1)/(d-1)`.

The all-dual inequalities already prove that no smaller fractional value is
possible. Hence the combined relaxation has the exact optimum

\[
\operatorname{OPT}_{\mathrm{combined}}
=1+\frac{n-1}{d-1},
\]

while the pinned integer optimum is `d`.

## Saved certificates

| family | `n` | local level `k` | integer optimum | combined fractional optimum | ratio |
| --- | ---: | ---: | ---: | ---: | ---: |
| `RM(1,3)` | 8 | 2 | 4 | `10/3` | `6/5` |
| `RM(2,5)` | 32 | 6 | 8 | `38/7` | `28/19` |
| `RM(3,7)` | 128 | 14 | 16 | `142/15` | `120/71` |

`RM(1,3)` replays every scope and every pinned-code projection at level two.
`RM(2,5)` replays all `65,536` codewords and checks the arithmetic exactly.
`RM(3,7)` uses the proved Reed--Muller distance/duality identities and an
explicit theorem-backed projection argument instead of expanding `2^64`
codewords. The independent reviewer reconstructs all arithmetic and rejects
mutated support, product, optimum, and ratio fields.

The ratio tends to two because `n=d^2/2`. Thus even the conjunction of all
redundant XOR parity inequalities with all local projection tables through
`Theta(sqrt(n))` leaves a constant-factor gap on this explicit family. A
stronger route must use a different valid inequality family or a richer
hierarchy, and it must account for the cost of finding or separating those
inequalities.

## Reproduction

```text
cd local_marginal_code_lab
python run_all_dual_local_reed_muller.py
python REED_MULLER_ALL_DUAL_LOCAL_INDEPENDENT_REVIEW.py
python -m unittest -v test_all_dual_local_reed_muller.py
```

Machine-readable outputs are
[`REED_MULLER_ALL_DUAL_LOCAL_RESULTS.json`](REED_MULLER_ALL_DUAL_LOCAL_RESULTS.json)
and
[`REED_MULLER_ALL_DUAL_LOCAL_INDEPENDENT_REVIEW.json`](REED_MULLER_ALL_DUAL_LOCAL_INDEPENDENT_REVIEW.json).
The code-family construction is sourced and proved in
[`REED_MULLER_THEOREM.md`](REED_MULLER_THEOREM.md).
