# Local-marginal code barrier

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
`38/7`. Full overlap consistency at level eight remains unresolved.

The [affine-overlap report](REED_MULLER_LEVEL_D_AFFINE_OVERLAP_REPORT.md)
adds every shared affine four-point flat, line, and singleton marginal to
those 620 eight-point tables. Its 28-variable-orbit quotient has an exact
primal/dual optimum `31/5`, improving the lower bound for the full level-eight
relaxation to `31/5`. The independent replay reconstructs the quotient and
reduced costs without an LP solver; the full arbitrary-scope level-eight case
is still explicitly unresolved.

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
```
