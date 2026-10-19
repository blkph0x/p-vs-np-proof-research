# Exact full level-eight RM(2,5) result

This checkpoint settles the optimum of the **defined** pinned local
projection-marginal relaxation through level eight for RM(2,5). It does not
settle SAT, P versus NP, or any hierarchy outside this model.

## Model

The code is RM(2,5), evaluated on the 32 points of F_2^5. Coordinate 0 is
pinned to one. For every coordinate scope S with 1 <= |S| <= 8, the model
contains a probability table on the exact projection of the pinned code onto
S. Every table is normalized, and every pair of nested scopes has the exact
marginal-consistency equations. The objective is the sum of the singleton
masses assigned value one away from the pinned coordinate.

The support is computed from the 32,768 pinned codewords. In particular, it
does not assume that every eight-scope has only a single parity condition:
scope 510 (the point set {1,...,8}) is a negative control whose projection
contains exactly 128 atoms because the dual relation on {0,...,7} fixes the
parity of its first seven coordinates.

## Exact quotient

The automorphism group GL(5,2) fixes the pin and preserves the code. Scope
orbits are represented by 2, 2, 3, 5, 8, 14, 23, and 35 representatives at
sizes 1 through 8. The orbit-stabilizer totals are independently checked
against C(32,k) at every size.

For each representative, the setwise stabilizer action is enumerated from
all linear maps induced on the scope span. The saved generator closures and
their orders are checked independently. Averaging over GL(5,2) preserves
feasibility and the objective, so the quotient is exact.

The resulting quotient has:

- 2,174 variable orbits;
- 27,926 normalization or marginal equations;
- 214,059 nonzero matrix entries.

The saved primal assigns one rational mass to each variable orbit. Its masses
have denominator at most 35. Every equality is checked exactly over the
rationals, all masses are nonnegative, and its objective is exactly 31/5.

## Why this is the full value

The affine-overlap model in
[REED_MULLER_LEVEL_D_AFFINE_OVERLAP_REPORT.md](REED_MULLER_LEVEL_D_AFFINE_OVERLAP_REPORT.md)
is a projection of this full model. Its exact dual certificate therefore gives
the lower bound

    full optimum >= 31/5.

The full quotient primal certificate gives

    full optimum <= 31/5.

Consequently the full level-eight relaxation has the exact value

    full optimum = 31/5.

The pinned integer optimum is 8, so the finite relaxation's
integer-to-fractional ratio is 40/31.

## Independent replay

From the repository root:

    python local_marginal_code_lab/run_reed_muller_level_d_full.py
    python local_marginal_code_lab/REED_MULLER_LEVEL_D_FULL_INDEPENDENT_REVIEW.py

The independent pure-standard-library replay rebuilds the code projections,
all 92 scope orbits, stabilizer closures, all variable and row orbits, the
quotient matrix, the singleton objective vector, and every rational primal
equation. It also runs the complete replay on adversarial certificate copies
and rejects:

- the impossible atom on scope 510;
- a perturbed primal mass;
- a mutated stored matrix row;
- a mutated stored objective vector.

The objective is accepted only after the replay independently reconstructs one
singleton value-one coefficient for each non-pin point and compares that
vector with the saved certificate. The matrix control mutates the saved
certificate, invokes the full replay, and requires the replay to fail with a
quotient-matrix mismatch; it is not a data-structure-only comparison.

The machine-readable certificate is
[REED_MULLER_LEVEL_D_FULL_RESULTS.json](REED_MULLER_LEVEL_D_FULL_RESULTS.json);
the replay summary is
[REED_MULLER_LEVEL_D_FULL_INDEPENDENT_REVIEW.json](REED_MULLER_LEVEL_D_FULL_INDEPENDENT_REVIEW.json).
The finite artifact sizes and the measured affine-overlap replay cost are
recorded in [REED_MULLER_CERTIFICATE_COSTS.md](REED_MULLER_CERTIFICATE_COSTS.md);
producer and discovery asymptotics remain deliberately unclaimed.

This result is a finite, representation-specific relaxation boundary. It is
not a polynomial-time SAT algorithm, a lower bound against arbitrary SAT
algorithms, or a resolution of P versus NP.
