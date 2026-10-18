# Symmetry-certified high-rank family

Let the columns be every nonzero vector of `F_2^r`, so `n=2^r-1`. Every
invertible row transform permutes this column set. Therefore the objective is
independent of the chosen basis, without enumerating `GL(r,2)`.

There are `r + binomial(r,2)` columns of weight at most two. Consequently

`q = 2^r-1-r-binomial(r,2)`.

The total column weight is `r 2^(r-1)`, the weight contributed by the low-weight
columns is `r^2`, and hence

`excess = r 2^(r-1) - r^2 - 2q`.

For `r >= 4`, the exceptional columns span all of `F_2^r`: choose two indices
`i,j` and two other indices `k,l`; the sum of the two weight-three vectors
`e_i+e_k+e_l` and `e_j+e_k+e_l` gives `e_i+e_j`, and a further weight-three
vector recovers each `e_i`. Thus the exceptional rank is exactly `p=r`, and
the native syndrome state count is `2^r` for every row basis.

`projective_family.py` checks the formula directly at ranks 4, 5, 6, 7, 8 and
12, including nontrivial invertible transforms. This is an exact structural
family, not a hardness proof: here `2^r=n+1`, so the state count is polynomial
in the encoded column count.
