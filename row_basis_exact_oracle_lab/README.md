# Exact row-basis oracle lab

This lab enumerates every invertible binary row transform for ranks through
four, checks the minimum column-weight objective, and compares that global
oracle with the bounded strict-descent discovery routine used by the native
binary-code solver.

```text
python -m unittest -v test_exact_oracle.py
python run_experiments.py
python INDEPENDENT_REVIEW.py
python rank5_driver.py
python RANK5_REVIEW.py
python run_exception_rank_bound.py
python EXCEPTION_RANK_BOUND_REVIEW.py
python run_projective_family.py
python PROJECTIVE_FAMILY_REVIEW.py
python run_explicit_code_family.py
python EXPLICIT_CODE_FAMILY_REVIEW.py
```

The rank-three trap is deliberately retained: local descent stops at a worse
objective than the exact GL(3,2) optimum. The separate rank-five C++ oracle
visits all 9,999,360 elements of GL(5,2) on four fixed inputs and is replayed
with independent Python arithmetic; rank-six and universal discovery remain
open.

The rank-tradeoff control compares this objective with the native solver
parameter: two exceptional columns of rank two beat four exceptional columns
of rank one on count, but the latter has the smaller syndrome-state exponent.
Exception count alone is therefore not the right downstream objective.

`EXCEPTION_RANK_BOUND.md` proves a route-specific probabilistic obstruction:
for every rank `r >= 6`, some full-rank matrix with `16r^2+r` columns forces
exceptional rank `r` under every row basis, so the native syndrome route needs
at least `2^r` states. The exact arithmetic records cover ranks 6, 7, 8, 16 and
32. This is an existence theorem for one representation route, not a P-versus-NP
resolution.

`PROJECTIVE_FAMILY.md` records an exact arbitrary-rank symmetry control: taking
all nonzero vectors as columns makes every row basis a column permutation. The
rank-12 replay has 4,095 columns and 4,096 states, and is a formula check rather
than a hardness result.

`EXPLICIT_CODE_FAMILY.md` gives a deterministic trace/Reed--Solomon family.
The k=7, 8 and 9 records force ranks 14, 32 and 54, with state counts `2^14`,
`2^32` and `2^54`; the review also exhausts every k=7 degree-one message.

`EXPLICIT_OBJECTIVE_PULLBACK_REVIEW.md` checks the natural free-message
generator map separately. Its positive three-assignment defects are 8,192,
32,768 and 131,072, so fixed unary costs cannot reproduce codeword Hamming
weight on all free messages. Constrained and nonlinear maps remain outside its
scope.

`LINEAR_WEIGHT_SIGNATURE.md` proves the corresponding exact theorem for every
homogeneous linear map with nonnegative additive costs: Walsh-character
independence forces matching aggregate weight on each nonzero linear form.
Because the explicit family has one distinct form per column, any such full
objective-preserving lift needs at least 16,256, 65,280 or 261,632 positive
cost-bearing rows in the saved k=7, 8 and 9 instances. Affine, signed,
nonlinear and threshold-only encodings are not covered by the homogeneous
theorem. `AFFINE_WEIGHT_SIGNATURE.md` closes the affine-offset extension even
with signed weights: matching the constant and nonzero Walsh coefficients
still forces at least the same 16,256, 65,280 and 261,632 nonzero rows. Only
nonlinear and threshold-only encodings remain outside these two theorems.

`NONLINEAR_WEIGHT_COMPRESSION.md` records the remaining boundary explicitly:
arbitrary nonlinear rows equal to the binary digits of the source Hamming
weight reproduce the full objective with only 14, 16 or 18 rows on the saved
families. This is an identity control, not a solver, because evaluating each
row still requires the source-form computation.
`NONLINEAR_CIRCUIT_COMPRESSION.md` strengthens the control to an explicit
XOR/AND circuit: the saved families require exactly 553,152; 3,069,184; and
16,223,488 gates in the ripple construction. Circuit integration and its
resulting search cost remain outside the theorem.
