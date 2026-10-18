# Independent review of the narrow affine-partition recognizer

No mathematical correctness or scope defect remains in the reviewed source.
One resource-cap ordering issue was found, repaired under the parent agent's
explicit coordination, and regression-tested. This review concerns only this
standalone recognizer; it adds no DAG integration or claim about general SAT.

## Repair and frozen provenance

The original phase fitter constructed its quadratic monomial list before
checking `max_unknowns`. With caller-raised coordinate limits, that could make
a large temporary allocation despite a deliberately small unknown cap. The
repair computes `D = 1 + d + d*(d-1)//2` and rejects before constructing that
list. Existing work-counter units and mathematical decisions are unchanged.
This is a monomial-allocation preflight, not a claim that every setup operation
or temporary object is metered.

- Core before repair: `d4754df367da2b828b85642788460fcdf38bd176d09f7a3f8833c2c30a01dac8`.
- Core after repair: `e5b27146e10c185fbd5fcbbbb33314c02e7653d2aa3421e2f50d8bdd9f8ae035`.
- Regression: a mocked `combinations` raises if quadratic enumeration is reached
  for dimension 300 with `max_unknowns=1`; it is never called. A separate public
  API check rejects cap 6 and accepts cap 7 for the seven-coefficient quadratic
  space on three coordinates.

The review author applied only this coordinated production repair, its test,
and the corresponding theorem note, then refreshed the author's saved results.
The independent oracle does not use the repaired fitting algorithm. Full source
and dependency hashes, including the saved results, are recorded in
`INDEPENDENT_REVIEW.json`; hashes remained unchanged during the final review.

## Proof and checker assessment

The stated recognition theorem is sound under its exact hypotheses. Pairwise
disjoint supports contained in their affine hull cover it if and only if their
cardinalities sum to its cardinality. Equal absolute coefficients then leave
only the common quadratic sign function to determine. Affine substitution
preserves degree at most two, so the producer's coefficient equations are
linear in the unknown quadratic coefficients. Coverage makes the restriction
map injective; a consistent solution therefore has full rank and is unique.

The checker is separate from that fit. It binds all original canonical pieces,
including order and zero pieces; checks every pair's original-row contradiction
witness; and proves the proposed hull by containment and an independent rank
calculation. Values at zero, unit vectors, and sums of two unit vectors determine
a quadratic restriction exactly. Those checks are sufficient here, rather than
an inference from arbitrary samples of a general Boolean function.

Original coordinate IDs, their retained ordering, signs, rational normalization,
canonical support and phase metadata, and zero pieces are validated. Original
`n` bounds coordinate positions: positions outside `retained` introduce no
free-variable factors. Rational coefficient bit limits and the intended
UNKNOWN/INVALID distinction were checked. Work is an explicitly documented
operation counter, not complete bit-operation or allocation accounting.

`UNSUPPORTED` correctly denotes failure of this narrow test. Overlapping or
unequal-magnitude pieces may combine in other ways. No arbitrary-sum
impossibility follows from those results, and no subgroup-search or general
piece-growth bound is established.

## Replayed and independent evidence

The final commands were `python -m unittest -v test_partition.py`,
`python run_experiments.py`, and `python INDEPENDENT_REVIEW.py`. All seven unit
tests passed. The refreshed author run contains 1,349 original cases:
1,210 EXACT, 132 UNSUPPORTED, and seven UNKNOWN. Its 18 certificate mutations
remain rejected. Every EXACT certificate was replayed against its saved
original input; every non-EXACT result retains null message and certificate.

The independent review classified all 1,338 small non-UNKNOWN cases using
explicit finite supports, a separate hull basis, and complete Boolean Mobius
ANF of the signs. It checked 14,876 original assignments, including the rejection
controls. The independently reconstructed rejection reasons were one overlap,
one hull gap, one unequal magnitude, and 129 incompatible quadratic phases.

Ten saved whole-sum norm certificates were replayed through the frozen
block/nullspace/pair reference, covering 136 closed products, including wide
retained boundaries. An additional 100 seeded transformed partitions with
sparse and permuted original IDs, shifted supports, rational coefficients,
signs, and zero pieces produced 87 EXACT and 13 UNSUPPORTED results, all agreeing
with independent finite-set classification across 2,716 assignments. Their full
original inputs and results are saved in the review JSON.

Separate controls verified a two-coordinate message inside an original
100-coordinate universe without spurious free factors, exact 70/71-bit rational
cap boundaries, and rejection of four malformed original-message descriptions.
The tests support the reviewed theorem and implementation within their scope;
they are not a formal proof assistant artifact or evidence resolving P versus NP.
