# A bounded local-marginal relaxation misses pinned code distance

Fix a binary linear code `C` and a coordinate `j`. For every coordinate scope
`S` of size at most `k`, introduce a probability table `mu_S` on assignments
to `S`. Require normalization, exact marginal consistency whenever one scope
is contained in another, and zero mass on assignments that are not the
projection of the pinned code

    C_j = {c in C : c_j = 1}.

Minimize the expected Hamming weight, using the singleton marginals. This is
an explicit local projection-marginal relaxation; the result below does not
identify it with a named hierarchy.

Let `delta` be the minimum nonzero weight in the dual code. If `k <= delta-2`,
the point mass at the unit vector `e_j` on every scope is feasible:

* a scope not containing `j` has at most `delta-2` coordinates. Applying the
  dual-distance annihilator argument after adjoining `j` makes its projection
  from `C_j` the full cube;
* a scope containing `j` has at most `delta-3` other coordinates, and the same
  argument makes the all-zero assignment on them extend with `c_j=1`.

All these point masses are automatically marginally consistent, and their
objective value is one. If the true minimum weight in `C_j` is `D>1`, the
relaxation therefore has an integrality gap of at least `D` through level
`delta-2`.

The saved Golay control is self-dual with dual distance eight and pinned
integer optimum eight. It therefore admits the unit-marginal witness through
level six. The small even-parity controls enumerate every local scope and
also test the boundary: at full scope the unit vector is rejected by the
parity equation.

This is a precise limitation of one local-summary architecture. Lifted
hierarchies with additional multiplied constraints, global cuts, or different
representations are outside the claim, so it is not a P-versus-NP lower bound.

The finite gap has an asymptotic probabilistic extension. Let `n` be a
multiple of 16, `r=n/2`, and choose an `r` by `n` binary generator matrix with
independent uniform entries. Put `t=n/16` and

    S = sum_{i=0}^{t-1} binom(n,i).

For each nonzero message, its codeword is uniform in `{0,1}^n`, so the union
bound for a codeword of weight below `t` is at most `S/2^r`. For each nonzero
dual candidate `x`, `Gx=0` has probability `2^-r`; there are at most `S-1`
such low-weight candidates. Thus both primal and dual distance are at least
`t` with probability at least `1-2S/2^r`. The elementary generating-function
bound with `x=1/15` gives

    S <= (16/15)^n 15^(n/16),

and the exact inequality `2^57 < 15^15` makes `2S < 2^(n/2)` already at
`n=16`, hence certainly
for every `n>=32` in this progression. A good matrix therefore exists, has no
zero column, and its pinned code has integer optimum at least `n/16`, while
the local-marginal point remains feasible through level `n/16-2`.

This is an existence and probability statement for a random matrix whose
input description is polynomial in `n`; it is not a deterministic
short-description code family and it is not a lower bound for arbitrary
algorithms. The saved arithmetic replay checks lengths 32 through 1024 with
exact integers.

The deterministic family follow-up is recorded in
[`REED_MULLER_THEOREM.md`](REED_MULLER_THEOREM.md). It supplies an elementary
distance/duality proof and saved certificates for the self-dual family
`RM(s,2s+1)`, so this lab now contains both a random-existence control and an
explicit short-description family. Neither result extends the claim beyond
the exact local projection-marginal relaxation defined here.
