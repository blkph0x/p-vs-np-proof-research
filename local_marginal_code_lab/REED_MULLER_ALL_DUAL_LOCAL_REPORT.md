# All dual parity checks plus local marginals still leave the RM gap

The previous all-dual experiment constrained the singleton marginals with the
parity polytope of every nonzero dual check. This follow-up adds the complete
local projection-marginal system through the boundary level one below the dual
distance. On the explicit self-dual family `RM(s,2s+1)`, the exact fractional
optimum is unchanged.

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
n=2^{2s+1},\qquad d=\delta=2^{s+1},\qquad k=d-1,
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

For any binary linear code whose dual distance is `d`, projection onto a
coordinate set of size less than `d` is surjective. Otherwise a nonzero linear
relation among the projected columns would give a dual word supported on fewer
than `d` coordinates.

Take a scope `S` of size at most `k=d-1`. Below the boundary, the set `S`
together with the pin has size less than `d`, so the pinned projection is full.
At the boundary `|S|=d-1` with the pin omitted, there can be at most one new
relation: a dual word supported on `S` together with the pin. If it exists, the
pinned projection has odd parity; otherwise it remains full. In either case,
every one-hot assignment is supported. Scopes containing the pin stay below
the boundary and are full on their free coordinates.

Use the following sparse table on every scope, where `T` is the set of
non-pin coordinates in the scope:

\[
\mu_S(1_T)=p\quad\text{for each one-hot assignment }1_T,
\qquad
\mu_S(0_T)=1-|T|p,
\qquad p=1/(d-1).
\]

For boundary scopes `|T|=d-1`, the all-zero mass is zero. These tables are
exactly marginal-consistent, and their singleton means are the all-dual point
above. They provide a feasible witness for the combined model at value
`1+(n-1)/(d-1)`. The next level is a genuine boundary for this construction:
a minimum dual support of size `d` that omits the pin has even parity, so its
one-hot assignments are rejected. The RM(1,3) test suite saves this negative
control explicitly.

The all-dual inequalities already prove that no smaller fractional value is
possible. Hence the combined relaxation has the exact optimum

\[
\operatorname{OPT}_{\mathrm{combined}}
=1+\frac{n-1}{d-1},
\]

while the pinned integer optimum is `d`.

## Saved certificates

| family | `n` | local level `k=d-1` | integer optimum | combined fractional optimum | ratio |
| --- | ---: | ---: | ---: | ---: | ---: |
| `RM(1,3)` | 8 | 3 | 4 | `10/3` | `6/5` |
| `RM(2,5)` | 32 | 7 | 8 | `38/7` | `28/19` |
| `RM(3,7)` | 128 | 15 | 16 | `142/15` | `120/71` |

`RM(1,3)` replays every scope and every pinned-code projection at level three.
`RM(2,5)` replays all `65,536` codewords and checks the arithmetic exactly.
`RM(3,7)` uses the proved Reed--Muller distance/duality identities and an
explicit theorem-backed projection argument instead of expanding `2^64`
codewords. The independent reviewer reconstructs all arithmetic and rejects
mutated support, sparse-marginal, optimum, and ratio fields.

The ratio tends to two because `n=d^2/2`. Thus even the conjunction of all
redundant XOR parity inequalities with all local projection tables through the
dual-distance boundary `Theta(sqrt(n))` leaves a constant-factor gap on this
explicit family. A
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
