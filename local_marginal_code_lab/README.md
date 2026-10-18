# Local-marginal code barrier

The lab defines an exact local projection-marginal relaxation for a pinned
binary linear code. It verifies a dual-distance theorem showing that the
deterministic unit-vector marginals survive through level `delta-2`, even when
the true pinned codeword has much larger weight.

The even-parity controls enumerate all small scopes, while the Golay control
uses the independently checked dual-distance certificate for level six
instead of pretending to enumerate every local atom.

The theorem also includes an exact probabilistic extension: random half-rate
binary generators have both distances at least `n/16` with positive probability
for multiples of 16, forcing the same local witness through level `n/16-2`.
The arithmetic replay covers lengths 32 through 1024 and makes no deterministic
code-family claim.

The deterministic follow-up in
[`REED_MULLER_THEOREM.md`](REED_MULLER_THEOREM.md) closes that family-design
gap with the self-dual `RM(s,2s+1)` codes. The saved producer and independent
reviewer cover `RM(1,3)`, `RM(2,5)`, and theorem-backed `RM(3,7)`; mutation
controls reject forged rows, witnesses, dual bases, and level fields.

```text
python -m unittest discover -v
python run_experiments.py
python INDEPENDENT_REVIEW.py
python run_reed_muller.py
python REED_MULLER_INDEPENDENT_REVIEW.py
python -m unittest -v test_reed_muller.py
```
