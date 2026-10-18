# Dense Walsh spectrum inside a simple 3-CNF family

The public “Vohra Duality” abstract describes a low-dimensional Fourier-space
route for 3-SAT. The full paper is not openly available for an independent
semantic audit, so this lab tests the narrow representation claim that a
polynomial-size 3-CNF necessarily has a polynomial-size explicit Walsh/Fourier
support.

For each `i`, use variables `x_i,a_i,b_i` and the four clauses containing every
sign pattern of `a_i,b_i`:

```
(x_i or  a_i or  b_i)   (x_i or  a_i or not b_i)
(x_i or not a_i or  b_i) (x_i or not a_i or not b_i)
```

The four-clause conjunction is logically equivalent to `x_i`. Therefore the
whole formula has `3n` variables, `4n` clauses, and its satisfying indicator is
`1` exactly when all `x_i=1`; the `a_i,b_i` variables are free.

With the normalized Walsh character `chi_S(z)=(-1)^|S intersect z|`, summing
over the free helpers cancels every coefficient whose subset contains a helper
variable. For the `2^n` subsets using only x-variables, the coefficient is
`(+/-)2^(-n)`, so all are nonzero. The exact spectrum therefore has `2^n`
nonzero coefficients while the explicit formula has size `O(n)`.

The lab enumerates the full truth table for `n<=4` and compares an integer
Walsh-Hadamard transform against the closed form. It also checks the analytic
support for `n<=12`. The independent verifier passes every saved row.

The stronger cyclic family reuses the original variables as helpers. For each
`i`, the four sign patterns on `(x_i,x_{i+1},x_{i+2})` force `x_i=1` (indices
are cyclic), so for `n>=3` the formula has `n` variables, `4n` clauses, three
distinct literals per clause, and the unique model `1^n`. Its satisfying
indicator is a point mass, hence every one of the `2^n` Walsh coefficients is
nonzero with magnitude `2^-n`. Exact truth-table transforms are independently
replayed for `3<=n<=8`, with analytic checks through `n=14`.

Because the abstract names a finite field, the same cyclic spectra are also
computed modulo the odd primes `3,5,7`. The normalized coefficients are
`(+/-)(2^n)^(-1)`, which is nonzero in every odd characteristic, so all `2^n`
modes survive there as well. The independent verifier replays all 18 saved
prime-field rows. Characteristic two is deliberately outside this normalized
statement: 2^n is not invertible and the usual Walsh characters collapse, so
a finite-field FWHT claim must specify its field characteristic.

There is a basis-independent strengthening. Replace the first literal in the
four-clause block for `x_i` by `x_i` or `not x_i` according to a target vector
`t`. For every `t` in `{0,1}^n`, the resulting `4n`-clause formula has the
unique model `t`, still with three distinct variables per clause. Its satisfying
indicator is therefore the point mass `delta_t`. The `2^n` target formulas
produce the standard basis of the full function space on `{0,1}^n`, so their
linear span has dimension exactly `2^n` over every field. Consequently, any
exact *linear* state representation that contains or can recover all these
indicators cannot have dimension polynomial in `n`. This is a representation
barrier only: a SAT decision algorithm need not expose the full indicator, and
the statement does not rule out nonlinear or otherwise implicit algorithms.
The saved target-span rows and independent replay check this identity for
`n=3..8`, while the forcing argument is valid for every `n>=3`.

This is a representation barrier only. It does not prove P != NP and does not
rule out a different algorithm whose state is not the explicit Fourier support.
It does show that “low-dimensional Fourier space” must be defined with an
additional invariant; formula size alone cannot guarantee it. If a proposed
algorithm's state is specifically the explicit Walsh support of the satisfying
indicator, the cyclic family is a direct contradiction to a polynomial-support
claim. The abstract's “Hamiltonian space” may be a different representation,
so this does not audit that unpublished definition.
