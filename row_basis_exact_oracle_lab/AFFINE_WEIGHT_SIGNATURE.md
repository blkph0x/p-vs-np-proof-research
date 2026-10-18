# Exact affine objective signatures

Let a row be the affine bit `r dot u xor b`, with integer weight `w`.  Its
indicator has the Walsh expansion

`[r dot u xor b = 1] = (1 - (-1)^b chi_r(u))/2`.

For each nonzero form `r`, define the alternating signature
`A(r)=sum w(-1)^b` over rows with that form.  The constant coefficient is
determined by `sum(w) - A(0)`.  Independence of the Walsh characters therefore
implies that two affine row-cost systems agree on every assignment exactly
when their constant numerators and all nonzero `A(r)` values agree.

The conclusion does not rely on nonnegative weights; signed weights are
accepted as an adversarial control.  In particular, if a target has `n`
distinct nonzero forms with coefficient one, every exact affine representation
has at least `n` nonzero-weight rows, because one row contributes to only one
form.  With nonnegative costs these are positive cost-bearing rows.

The explicit trace/Reed--Solomon family has one distinct form per column, so
the saved `k=7,8,9` targets force at least `16,256`, `65,280` and `261,632`
rows even after allowing affine offsets, duplicate rows, and signed weights.
This is still a full-objective theorem for affine row maps.  Nonlinear maps and
encodings that preserve only a decision threshold remain outside scope.
