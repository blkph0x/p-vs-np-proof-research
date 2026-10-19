# Local-marginal code barrier

Terminology note: the later files retain historical `SOS` names for stable
paths, but their added inequalities are reported as valid integer-domain
polynomial cuts unless an explicit bounded-degree SOS/moment representation is
provided. The degree-two Boolean-square audit is the current explicit SOS
moment result.

The lab defines an exact local projection-marginal relaxation for a pinned
binary linear code. It verifies a dual-distance theorem showing that the
deterministic unit-vector marginals survive through level `delta-2`, even when
the true pinned codeword has much larger weight.

The even-parity controls enumerate all small scopes, while the Golay control
uses the independently checked dual-distance certificate for level six
instead of pretending to enumerate every local atom.

The theorem also includes an exact probabilistic extension: random half-rate
binary generators have both distances at least `n/16` with positive probability
for multiples of 16, forcing the same local witness through level `n/16-2`.
The arithmetic replay covers lengths 32 through 1024 and makes no deterministic
code-family claim.

The deterministic follow-up in
[`REED_MULLER_THEOREM.md`](REED_MULLER_THEOREM.md) closes that family-design
gap with the self-dual `RM(s,2s+1)` codes. The saved producer and independent
reviewer cover `RM(1,3)`, `RM(2,5)`, and theorem-backed `RM(3,7)`; mutation
controls reject forged rows, witnesses, dual bases, and level fields.

The all-dual follow-up in
[`REED_MULLER_ALL_DUAL_REPORT.md`](REED_MULLER_ALL_DUAL_REPORT.md) supplies
every redundant parity check analytically. Exact rational mixtures prove the
uniform point feasible, and balanced minimum-weight affine checks prove its
fractional optimum. The resulting integer/fractional ratios are `6/5`,
`28/19`, and `120/71` for the three saved cases, so this stronger parity-only
relaxation still has a limiting factor-two gap.

The combined follow-up in
[`REED_MULLER_ALL_DUAL_LOCAL_REPORT.md`](REED_MULLER_ALL_DUAL_LOCAL_REPORT.md)
adds every pinned-code projection marginal through the boundary level `d-1`
while retaining all dual parity inequalities. Sparse one-hot local tables
remain feasible at the same exact fractional optimum; the saved ratios are
again `6/5`, `28/19`, and `120/71`. This tests a stronger hierarchy edge
without claiming a general lower bound.

The finite level-`d` follow-up in
[`REED_MULLER_LEVEL_D_REPORT.md`](REED_MULLER_LEVEL_D_REPORT.md) closes the
smallest saved gap. For pinned `RM(1,3)`, an exact integer dual certificate
checks all 982 supported atoms at level four and matches a pinned weight-four
codeword, so the local and combined optima are exactly four. The independent
replay is pure standard-library code and rejects mutated rows, assignments,
and shape claims. Larger-family level-`d` cases remain open.

The companion [RM(2,5) affine-flat star report](REED_MULLER_LEVEL_D_FLAT_STAR_REPORT.md)
records an exact negative control for a weaker level-eight proposal: 620
affine three-flat tables sharing only singleton marginals still have optimum
`38/7`. The subsequent full replay resolves the corresponding finite model;
this report remains the weaker negative control.

The [affine-overlap report](REED_MULLER_LEVEL_D_AFFINE_OVERLAP_REPORT.md)
adds every shared affine four-point flat, line, and singleton marginal to
those 620 eight-point tables. Its 28-variable-orbit quotient has an exact
primal/dual optimum `31/5`, improving the lower bound for the full level-eight
relaxation to `31/5`. The independent replay reconstructs the quotient and
reduced costs without an LP solver. The companion
[compact dual note](REED_MULLER_AFFINE_OVERLAP_DUAL_NOTE.md) turns the saved
dual into a six-term positive objective-gap identity and the adversarial test
reconstructs that identity with exact rational arithmetic.

Finite certificate sizes, rational bit lengths, and measured replay timing are
listed in [REED_MULLER_CERTIFICATE_COSTS.md](REED_MULLER_CERTIFICATE_COSTS.md);
unmeasured producer and peak-memory costs are left explicitly open.

The [full level-eight report](REED_MULLER_LEVEL_D_FULL_REPORT.md) now closes
the finite arbitrary-scope case for this RM(2,5) model. It includes every
scope of size at most eight, exact pinned-code projection support, and every
containment marginal. Its exact quotient has 2,174 variable orbits and 27,926
rows; an independently replayed rational primal gives the matching value
`31/5`. The pinned integer optimum is eight, so the finite ratio is `40/31`.
This remains a result about the stated relaxation, not a general SAT solver
or a P-versus-NP resolution.

The [SOS moment audit](REED_MULLER_SOS_MOMENT_INDEPENDENT_REVIEW.md) gives the
next exact boundary. Writing `t` for the nonpin Hamming weight, every Boolean
assignment satisfies `(5t-31)^2 >= 0`, but the full level-eight witness has
expectation `-992/7` (or `-992/175` after dividing by 25). The independent
replay checks the exact singleton and pair moments, all 32 possible counts,
and mutation rejection. This is a valid global cut for the finite relaxation,
not a universal SAT method.

The [two-cut replay](REED_MULLER_SOS_TWO_CUT_REPORT.md) adds the valid
integer-weight polynomial `(t-6)(t-7)` and closes the finite relaxation at
`367/57`. The [three-cut replay](REED_MULLER_SOS_THREE_CUT_REPORT.md) adds
`(t-6)(t-7)(t-23)(t-24)`, which the two-cut witness violates by `-2400/19`,
and closes the next finite relaxation exactly at `5231/801`. The [four-cut
replay](REED_MULLER_SOS_FOUR_CUT_REPORT.md) adds the valid integer-domain
polynomial `t(31-t)(t-3)(t-4)(t+28)`, which the three-cut witness violates by
`-3248000/89`, and closes the next finite relaxation exactly at
`1219047171/184149541`. The [fifth-cut replay](REED_MULLER_SOS_FIVE_CUT_REPORT.md)
adds the valid core polynomial `t(31-t)(t-3)(t-4)`, which the four-cut witness
violates by `-61440933600/184149541`, and closes the next finite relaxation
exactly at `324713143/48731153`. All four results have independent exact
replays and remain scoped certificates rather than general SAT algorithms. The
[six-cut replay](REED_MULLER_SOS_SIX_CUT_REPORT.md) adds
`(t-6)(t-7)(31-t)(t+32)^2`, which the fifth-cut witness violates by
`-6759234824400/48731153`, and closes the next finite relaxation exactly at
`22465669893401/3255387995415`.

```text
python -m unittest discover -v
python run_experiments.py
python INDEPENDENT_REVIEW.py
python run_reed_muller.py
python REED_MULLER_INDEPENDENT_REVIEW.py
python -m unittest -v test_reed_muller.py
python run_all_dual_reed_muller.py
python REED_MULLER_ALL_DUAL_INDEPENDENT_REVIEW.py
python -m unittest -v test_all_dual_reed_muller.py
python run_all_dual_local_reed_muller.py
python REED_MULLER_ALL_DUAL_LOCAL_INDEPENDENT_REVIEW.py
python -m unittest -v test_all_dual_local_reed_muller.py
python REED_MULLER_LEVEL_D_INDEPENDENT_REVIEW.py
python -m unittest -v test_reed_muller_level_d.py
python run_reed_muller_level_d_flat_star.py
python REED_MULLER_LEVEL_D_FLAT_STAR_INDEPENDENT_REVIEW.py
python -m unittest -v test_reed_muller_level_d_flat_star.py
python run_reed_muller_level_d_affine_overlap.py
python REED_MULLER_LEVEL_D_AFFINE_OVERLAP_INDEPENDENT_REVIEW.py
python -m unittest -v test_reed_muller_level_d_affine_overlap.py
python run_reed_muller_level_d_full.py
python REED_MULLER_LEVEL_D_FULL_INDEPENDENT_REVIEW.py
python -m unittest -v test_reed_muller_level_d_full.py
python run_reed_muller_sos_three_cut.py
python REED_MULLER_SOS_THREE_CUT_INDEPENDENT_REVIEW.py
python -m unittest -v test_reed_muller_sos_three_cut.py
python run_reed_muller_sos_four_cut.py
python REED_MULLER_SOS_FOUR_CUT_INDEPENDENT_REVIEW.py
python -m unittest -v test_reed_muller_sos_four_cut.py
python run_reed_muller_sos_five_cut.py
python REED_MULLER_SOS_FIVE_CUT_INDEPENDENT_REVIEW.py
python -m unittest -v test_reed_muller_sos_five_cut.py
python run_reed_muller_sos_six_cut.py
python REED_MULLER_SOS_SIX_CUT_INDEPENDENT_REVIEW.py
python -m unittest -v test_reed_muller_sos_six_cut.py
```

The [seventh-cut replay](REED_MULLER_SOS_SEVEN_CUT_REPORT.md) adds
`(t-6)(t-7)(31-t)`, which the six-cut witness violates by
`-3473117738496/217025866361`, and closes the next finite relaxation exactly at
`35873801083/5129253893`. The producer, independent reviewer, and adversarial
suite are all checked into the repository.

The [candidate-cut scan](REED_MULLER_SOS_CANDIDATE_SCAN_REPORT.md) checks a
declared family of 2,144 exact degree-at-most-five integer-weight polynomials
against the seven-cut witness. Thirty-nine are violated; the strongest
lexicographically first candidate is `(t-6)(t-7)(t-30)(t-31)` with expectation
`-657769331520/5129253893`. This scan only proves separation and deliberately
does not claim the optimum after adding the candidate.
