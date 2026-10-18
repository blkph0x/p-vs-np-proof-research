# Full FWHT-Zeta cost audit

The public IEEE abstract for [The Vohra Duality](https://ieeexplore.ieee.org/abstract/document/11717448)
names a Fast Walsh-Hadamard-Zeta transform, but the accessible record does not
define the claimed low-dimensional Hamiltonian space or its conversion from an
arbitrary 3-CNF. This report isolates a necessary cost distinction.

For an explicit vector indexed by all assignments to `n` Boolean variables,
the unnormalized Walsh-Hadamard transform has `2^n` entries. Its butterfly
network has `n` stages and `2^(n-1)` butterflies per stage. Each butterfly
performs one addition and one subtraction, so a full FWHT costs exactly
`n * 2^n` arithmetic operations.

The standard subset zeta transform has the same `n * 2^(n-1)` pair updates,
with one addition per update. A straightforward full FWHT followed by a zeta
pass therefore performs exactly `3 * n * 2^(n-1)` add/subtract operations.
The state vector itself has `2^n` entries before coefficient bit costs are
counted. These are exact operation counts for the stated full-vector route,
not a lower bound against an algorithm that proves and exploits a different
implicit representation.

`fwht_cost.py` counts both transforms directly. `review_fwht_cost.py` is an
independent implementation that recomputes the formulas, replays sample
vectors through both transforms for dimensions `0..8`, and checks every source
hash. `FWHT_COST_RESULTS.json` records dimensions `0..20`; the largest row
already has 1,048,576 explicit states and 20,971,520 FWHT arithmetic
operations, before any formula-dependent work.

The exact 3-CNF family in [`REPORT.md`](REPORT.md) supplies the complementary
representation control: a formula with `O(n)` clauses can have `2^n` nonzero
Walsh coefficients, including over tested odd prime fields. Therefore a claim
that a full explicit Fourier state is always low-dimensional is false for that
specified representation. A valid polynomial-time claim would need an
all-instance invariant showing how the proposed Hamiltonian state is obtained
without materializing these `2^n` degrees of freedom, plus a polynomial
bit-complexity proof. The public abstract alone does not establish either
condition, so this audit records a conditional barrier rather than a refutation
of an unavailable full paper.

Run:

```text
python run_fwht_cost.py
python review_fwht_cost.py
```
