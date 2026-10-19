# Finite certificate cost accounting

This appendix separates the costs of constructing a finite model, discovering
a certificate, and replaying a published certificate. It records measured
facts for the current RM(2,5) artifacts and does not extrapolate them into a
polynomial-time claim.

## Published artifact sizes

The byte counts below are the working-tree sizes on 20 October 2026:

| artifact | variables | equality rows | nonzero matrix entries | JSON bytes |
| --- | ---: | ---: | ---: | ---: |
| affine-overlap quotient | 28 | 53 | 215 | 28,310 |
| full level-eight quotient | 2,174 | 27,926 | 214,059 | 6,822,694 |

The largest numerator or denominator component in a rational string in the
affine-overlap certificate uses 8 bits; the corresponding maximum in the full
certificate is 6 bits. These are properties of the saved finite witnesses,
not bounds for a family of instances.

## Construction, discovery, and verification

`T_construct` is the time to enumerate code supports, scopes, stabilizers,
orbits, and the quotient matrix. `T_discover` is the time used by the producer
to obtain a primal/dual witness. `T_verify` is the time for the independent
standard-library replay. The repository keeps the first two operations
separate in the producer scripts; this revision does not claim asymptotic
bounds for either one.

For a reproducible local measurement, on Windows with Python 3.10.10, the
standalone affine-overlap replay was run as:

```text
cd local_marginal_code_lab
python REED_MULLER_LEVEL_D_AFFINE_OVERLAP_INDEPENDENT_REVIEW.py
```

It completed in 44.742 seconds on the author workstation. The focused suite
of eight exact tests, including the new compact-dual identity and mutation
controls, completed in 44.453 seconds. These are wall-clock observations, not
hardware-independent complexity bounds. The full-model CI stage has a 900
second per-stage timeout; its actual runtime is intentionally reported by the
workflow rather than inferred from that ceiling.

Peak memory and the producer's certificate-search time are not recorded here.
They should be measured on a pinned environment before being used in a paper
as quantitative claims. No finite certificate in this repository is being
presented as an efficient algorithm for arbitrary SAT instances.

## Reproduction

The matrix and objective are rebuilt by
`REED_MULLER_LEVEL_D_AFFINE_OVERLAP_INDEPENDENT_REVIEW.py`; the exact cost
identity is checked by `test_compact_dual_identity` in the companion test
module. The full-model replay uses the analogous independent checker and
objective reconstruction described in
`REED_MULLER_LEVEL_D_FULL_REPORT.md`.
