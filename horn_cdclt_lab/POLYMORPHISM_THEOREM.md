# All-arity polymorphism theorem for the mixed gadget

Let

\[
H=\{000,110,001\},\qquad
A=\{0100,0010,1001,1111\}.
\]

The common Boolean polymorphisms of `H` and `A` are exactly the projections, at every
positive operation arity.

## Step 1: the affine relation forces an affine operation

Permute the coordinates of `A` by

\[
\pi(y,w,z_0,z_1)=(w,z_0,y).
\]

The image is

\[
R=\{100,010,001,111\}=\{(u,v,t):u\oplus v\oplus t=1\}.
\]

If an operation `f` preserves `A`, it preserves `R` as well, because coordinate
permutations commute with applying `f` coordinatewise.

Let `x,y` be arbitrary vectors in `F_2^k`, and let `1` be the all-ones vector. For every
coordinate, the triple `(x_i,y_i,1+x_i+y_i)` lies in `R`; preservation therefore gives

\[
 f(x)\oplus f(y)\oplus f(1+x+y)=1. \tag{1}
\]

Apply the same identity to `1+x` and `1+y`:

\[
 f(1+x)\oplus f(1+y)\oplus f(1+x+y)=1. \tag{2}
\]

Subtracting (1) and (2) shows that `f(x)+f(1+x)` is a constant `c`, independent of
`x`. Substituting `f(1+x+y)=f(x+y)+c` into (1) gives

\[
 f(x+y)=f(x)\oplus f(y)\oplus b,
 \qquad b=1\oplus c.
\]

Thus `g(x)=f(x)\oplus b` is additive on `F_2^k`. Every additive Boolean map is a parity
of a support `I`:

\[
 f(x)=b\oplus\bigoplus_{i\in I}x_i. \tag{3}
\]

Preservation of `R` additionally requires `b\oplus(|I|\bmod 2)=1`, since each input row
has odd parity.

## Step 2: the Horn relation reduces the affine support to one coordinate

Choose any `k` rows of `H`. Across those rows, the `x` and `z_0` columns are the same
vector `a`, while the `z_1` column is a vector `d` disjoint from `a`: a row of `H` is
either `000`, `110`, or `001`. Applying `f` coordinatewise produces

\[
 (f(a),f(a),f(d)).
\]

For this to lie in `H`, `f(a)=1` implies `f(d)=0` whenever `a` and `d` are disjoint.
Taking `a=d=0` gives `f(0)=0`, so (3) has `b=0`. If `I` contained two distinct
coordinates `i,j`, choose `a=e_i` and `d=e_j`; they are disjoint but
`f(e_i)=f(e_j)=1`, a contradiction. Hence `|I|\le 1`. The odd-parity condition from
Step 1 rules out `I=\varnothing`, so `|I|=1`.

Equation (3) is therefore one coordinate projection. Every projection plainly preserves
both relations, proving the claim for every arity.

This theorem is an algebraic strengthening of the finite audit. It does not by itself
prove P\ne NP; the separate primitive-positive exact-one reduction supplies the
NP-hardness consequence for the mixed constraint language.

