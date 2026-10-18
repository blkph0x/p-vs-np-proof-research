# Exact linear objective signatures

Let `r_i` be binary linear forms on `F_2^d` and let `w_i >= 0`. Define

`F(u) = sum_i w_i [r_i dot u = 1]`.

Aggregate duplicate nonzero forms as
`S(a)=sum_{i:r_i=a} w_i`. Since

`[a dot u = 1] = (1-(-1)^(a dot u))/2`,

the Walsh expansion is

`F(u) = (sum_{a != 0} S(a))/2 - (1/2) sum_{a != 0} S(a)(-1)^(a dot u)`.

The characters `(-1)^(a dot u)` are linearly independent. Therefore two
homogeneous nonnegative additive costs agree on every assignment if and only if
their aggregated signatures `S(a)` agree for every nonzero form `a`.

This applies to a constrained homogeneous linear encoding as well: choose a
basis `u` for its linear domain and substitute every encoded coordinate as a
linear form in `u`. Exact equality of the full objective on that domain is
then subject to the same signature condition.

The explicit trace/Reed--Solomon family has `n` distinct nonzero coordinate
forms, each with target weight one. Its signature therefore has `n` entries,
and any exact homogeneous nonnegative additive lift must contain at least `n`
positive cost-bearing rows, one for each form. The result rules out compressed
linear objective preservation for this family even when the output map is
arbitrary and the source variables are linearly constrained.

The scope is exact full-objective equality, homogeneous linear maps and
nonnegative costs. Signed costs, affine offsets, nonlinear maps, and encodings
that preserve only a decision threshold are outside the theorem.
`linear_weight_signature.py` and its independent review check the identity on
small exhaustive cubes and on the `k=7,8,9` explicit families.
