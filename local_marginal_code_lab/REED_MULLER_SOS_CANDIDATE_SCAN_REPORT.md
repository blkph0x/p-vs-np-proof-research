# RM(2,5) exact candidate-cut separation scan

The saved seven-cut witness is feasible for the seven finite cuts already
certified in this directory. The next question is whether a simple, valid
integer-weight inequality separates that witness. This scan answers that
narrow question exactly for a declared finite family.

## Candidate family

For integer nonpin weight `t` in `0..31`, the scan enumerates:

- every square `(t-r)^2`, `0 <= r <= 31`;
- every adjacent-root product `(t-a)(t-a-1)`, `0 <= a <= 30`;
- the boundary product `t(31-t)`; and
- every pairwise product of those generators whose degree is at most five.

Each candidate is checked at all 32 allowed integer weights, so domain
nonnegativity is exact. The witness expectation is evaluated in the binomial
moment basis reconstructed from the complete level-eight quotient and the
saved seven-cut primal masses. No floating-point value selects the candidate.

The scan checks `2,144` candidates. `39` have negative expectation under the
seven-cut witness. The lexicographically first strongest saved candidate is

```text
p(t) = (t-6)(t-7)(t-30)(t-31)
E[p(t)] = -657769331520/5129253893.
```

The polynomial is nonnegative for every integer `t` in `0..31`, because it is
the product of two adjacent-root factors, each of which is nonnegative on the
integer domain.
Thus the seven-cut witness is not feasible for the next relaxation obtained by
adding this valid cut.

## Scope boundary

This is a **separation-only** result. It does not solve the LP after adding the
candidate, does not provide a matching primal/dual optimum, and does not claim
that this cut closes the finite gap. The independent reviewer recomputes the
moments, candidate family, exact ranking, source hashes, and mutation controls.

Run:

```text
python run_reed_muller_sos_candidate_scan.py
python REED_MULLER_SOS_CANDIDATE_SCAN_INDEPENDENT_REVIEW.py
python -m unittest -v test_reed_muller_sos_candidate_scan.py
```
