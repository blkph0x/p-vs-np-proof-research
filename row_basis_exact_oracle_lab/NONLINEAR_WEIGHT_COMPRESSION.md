# Nonlinear objective-compression boundary control

The Walsh lower bounds apply to affine row maps.  They cannot be extended to
arbitrary nonlinear rows without an additional circuit or representation
restriction.  For source forms `r_i`, let

`h(u) = sum_i [r_i dot u = 1]`.

Define a nonlinear row `b_j(u)` as the `j`-th binary digit of `h(u)` and give
it weight `2^j`.  With `ceil(log_2(n+1))` rows (equivalently
`max(1,n.bit_length())`),

`sum_j 2^j b_j(u) = h(u)`

for every assignment.  A single nonlinear threshold row likewise decides
`h(u) <= t`.  These are exact identity controls, not a P=NP algorithm: each
nonlinear row still has to be represented and evaluated, and the construction
does not turn an arbitrary SAT instance into a small-state solver.

For the explicit families the digit-row counts are 14, 16 and 18 for
`k=7,8,9`, compared with 16,256, 65,280 and 261,632 source forms.  The
control records why nonlinear and threshold-only encodings remain a genuine
open boundary after the affine signature theorem.
