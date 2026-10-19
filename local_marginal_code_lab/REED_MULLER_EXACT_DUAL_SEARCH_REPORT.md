# RM(2,5) SOS-strengthened exact-dual search

## Purpose

The SOS-strengthened RM(2,5) level-eight replay currently has the exact finite
bracket

\[
  64263/10000 \leq \operatorname{OPT} \leq 7037/1095,
  \qquad \operatorname{gap}=403/2190000.
\]

This note records an attempted closure of that remaining gap.  It is a search
record, not a certificate: the published status remains `BRACKETED_NOT_EXACT`.

## Exact-support reconstruction

The floating SOS LP has 625 positive primal orbit variables and 719 nonzero
equality-dual rows.  The SOS multiplier is `35/876`.  We reconstructed a
rational dual on those 719 rows by solving the active-support equations over
the rationals.  The resulting dual objective is exactly `7037/1095`, matching
the independently reconstructed primal objective.

That matching objective is necessary but not sufficient.  An exact replay of
all 2,174 reduced costs found 169 negative entries.  The violations are tiny
(the worst is about `-3.1e-12` in floating scale), but a negative exact reduced
cost invalidates a weak-duality certificate.  The candidate was therefore
rejected and was not substituted into the production result.

## Degeneracy and repair attempts

The active-support coefficient matrix has rank 215, leaving a large dual
nullspace.  A floating feasibility repair over the 719-row support produced
nonnegative reduced costs to solver tolerance, but rational reconstruction of
an arbitrary LP vertex was unstable and amplified roundoff.  An L1-minimal
repair with explicit slack margins was infeasible when restricted to those
rows, indicating that a closure certificate may require dual rows that are
zero in the particular floating solution.  A sparse full dual LP over all
27,926 equality rows was started, but did not finish within the exploratory
run budget; no result from that run is used as evidence.

## Reproducibility and interpretation

The exploratory scripts used to discover this route are outside the committed
production path.  The committed runner and independent reviewer continue to
rebuild the saved primal, SOS cut, and conservative exact dual bracket from
source data.  The current claim is only the finite bracket in
`REED_MULLER_SOS_STRENGTHENED_REPORT.md`; this search neither proves the
strengthened finite optimum nor bears on arbitrary SAT or P versus NP.

The next rigorous options are to obtain an exact dual basis with the missing
degenerate rows, or to retain the bracket and add a different globally valid
moment constraint.  Either route must finish with rational reduced-cost
checks and an independent mutation test before changing the status.
