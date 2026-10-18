# Compact signed boundaries and original-CNF comparison

**P versus NP remains unresolved.** This phase implements polynomial operations
on individual compact affine pieces and a fully checked, bounded solver that
adds and multiplies such pieces. It does not bound how many pieces general SAT
requires. The original-CNF comparison gives 54 exact results and four UNKNOWNs;
the separate exponential reference solves all 58. There is no general coverage
or speed improvement claim.

## What is now implemented

For f(y,z)=c*1[A_y*y+A_z*z=b]*(-1)^q(y,z), with q quadratic over GF(2), summing
the internal variables z yields either zero or another compact affine quadratic
piece on y. The one-bit implementation proves each step by solving a support
equation or applying sum_t (-1)^(tL)=2*1[L=0]. A separately written block method
checks the projected support through a left nullspace, proves a bijective
internal parametrization, and applies quadratic pair-sum identities.

These procedures store equations and quadratic monomials, not boundary truth
tables. Their cost is polynomial in the explicit dimensions, input lengths and
coefficient bit lengths. Dimension guards prevent a short binary header from
silently requesting an enormous coordinate universe. Scalars, constant signs,
inactive coordinates, empty supports and original retained-coordinate order
are included in the certificates.

The weighted solver represents each original OR clause exactly as 1 minus its
all-false pin. It follows a component/group tree, multiplies every pair of child
pieces, sums newly internal variables, and merges identical canonical pieces.
Each structural node accounts for every original factor occurrence. Marginal
requests can be reused only with identical bound inputs; equal messages never
justify dropping a factor. Unused original variables contribute the correct
power of two. Native signed affine factors are also accepted, with signed sums
kept distinct from ordinary nonnegative SAT counts.

The implementation charges all cross-products before merging, retains limits on
pieces, nodes, arithmetic work and coefficient bits, and reports UNKNOWN without
a partial count when a cap is exceeded. Its worst-case time and certificate size
remain exponential.

## Results on the complete original formulas

The benchmark freezes the 40 earlier original-formula controls, 15 larger
coefficient-phase originals, and three historical mixed/sliding fixtures. It
counts logical satisfying assignments, which differ from earlier slack-encoding
coefficients. These are 58 retained requests, including repeated formulas from
different earlier controls; they are not claimed to be 58 distinct formulas.
The two old star-order controls use the same original clause order in this new
factor-tree benchmark. No input is replaced by a smaller surrogate after a failure.

| Method | Exact, checked original counts | UNKNOWN |
|---|---:|---:|
| Weighted affine DAG, fixed recorded caps | 54 | 4 |
| Separate bounded branch/component reference | 58 | 0 |

All 58 reference counts have an independent direct enumeration, closed-form,
bitset truth-table, or transfer calculation. The planted 24-variable/96-clause
original has exactly 64 satisfying assignments; the planted 32-variable/128-clause
original has 680. The independent bitset calculation covers all original logical
assignments and is explicitly exponential. Its large integer width is counted;
it is not a unit-cost shortcut or a polynomial solver.

| Original input where the new method stopped | Recorded stopping point |
|---|---|
| Complete positive binary interaction, 16 variables | Combined node count reaches 4,097, above 4,096 |
| Planted 24 variables, 96 clauses | Retained pieces reach 257, above 256 |
| Planted 32 variables, 128 clauses | Combined node count reaches 4,097 |
| Connected historical mixed family, 72 variables | Combined node count reaches 4,097 |

Positive original controls include 24 disjoint ternary clauses on 72 variables,
a connected 40-clause chain on 81 variables, and a signed sliding chain on 66
variables. Their exact counts agree with independent product/transfer formulas.
These structural successes coexist with the four preserved failures above.

## Verification and reproducibility

All **46 tests** pass: 12 production boundary tests, 11 block-reference tests,
14 weighted-DAG tests, and nine original-count reference tests. The frozen
artifact audit checks 38 source references, including all four independent-review
records, and replays every exact saved claim:

- 96 production marginals, each independently recomputed by the block method
  and compared symbolically, including 512 retained boundary coordinates;
- 73 additional block-reference marginals;
- 16 native/structured weighted-DAG contractions;
- 58 original counting-reference certificates and 54 weighted original counts.

Each lab also has a separate review. In particular, the root block-reference
review independently sums 19,895 original assignment words across 500 held-out
requests, compares all 3,239 boundary values, and rejects 1,312 proof mutations.
The counting-reference review enumerates all 744 distinct models of the two
planted originals using another search, and independently checks the signed
chain count. These are code and ordinary mathematical reviews, not proof-assistant
formalization. No novelty claim is made for the underlying algebra.

Evidence and implementation entry points:

- [Frozen tests](AFFINE_BOUNDARY_TEST_SUMMARY.json) and [artifact replay](AFFINE_BOUNDARY_ARTIFACT_AUDIT.json).
- [Same-original comparison](WEIGHTED_AFFINE_CROSSCHECK.json).
- [Boundary theorem](affine_boundary_lab/THEOREM.md) and [independent block theorem](affine_boundary_reference/THEOREM.md).
- [Weighted-DAG theorem](weighted_affine_dag_lab/THEOREM.md).
- [Original reference counts and complete proofs](original_count_reference_lab/RESULTS.json).

## Next experiment

[AFFINE_SUM_COMPRESSION_NEXT.md](AFFINE_SUM_COMPRESSION_NEXT.md) gives checked
mathematical identities for merging distinct pieces: compatible parallel affine
cosets, equal supports whose phases differ by an affine function, and exact
subtraction of a codimension-one pinned subset. These
identities may compress sums beyond identical-key merging. They are a proposed
next implementation, not a demonstrated speedup. Every discovery attempt and
rewrite must be charged and certified, and the same 58 original inputs must
remain the comparison target. The overall resolution goal remains active.

The [independent next-design review](AFFINE_SUM_COMPRESSION_REVIEW.md) checks
the mathematical conditions and retains a reproducible 33,320-case phase/sign
audit plus 1,000 affine-union controls. Those finite checks supplement the stated
identities; they do not establish performance of an implementation that does not
yet exist.
