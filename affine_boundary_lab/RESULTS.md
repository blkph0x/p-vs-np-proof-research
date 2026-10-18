# Saved compact boundary controls

The frozen experiment contains **102 original requests: 96 EXACT and
6 UNKNOWN**. Every exact marginal has a complete one-bit proof replayed by
the independent-structure checker. UNKNOWN cases contain no message, proof
or key. Current source hashes and source stability are recorded in
[RESULTS.json](RESULTS.json).

Bounded reference cases directly enumerate **2,506 original active-variable
assignments**. The larger product controls use their proved identities rather
than enumeration. The largest signed example has 512 retained variables and
512 summed variables; its exact output is scalar 2^256 times the sign of a
256-term quadratic polynomial. Another example returns 256 retained pins
with scalar 2^256. A 512-bit unused active scope returns 2^512, while inactive
original coordinates introduce no multiplicity.

All **12 tests pass** (3.386 seconds in the final local run), including
1,098 small phase/boundary combinations, 300 seeded cases, 80 closed-affine
cross-checks, malformed and altered proofs, sparse original coordinates,
canonical keys, exact work boundaries and huge-dimension rejection.

Run `python run_experiments.py` to regenerate the examples, then
`python -m unittest discover -s . -p 'test*.py' -v` to replay the suite.
The primitive preserves signed affine marginals; it makes no general SAT
tractability or bounded weighted-sum-width claim.
