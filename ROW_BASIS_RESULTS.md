# Bounded automatic row-basis discovery

Date: 2026-10-18. These are finite search results, not global optima or a P-versus-NP conclusion.

Each search starts from the stored generator-derived parity-check basis. The lexicographic objective is (number of columns of weight >2, total excess above weight 2, total column weight). A descent scans elementary destination-row XOR source-row moves and accepts only strict improvement. Seeded restarts apply eight elementary moves to the incumbent; at most 31 restarts are allowed.

The evaluation cap includes the identity score, every scored neighbor, and every restart setup score. Setup bit visits, scored-column visits, accepted moves, perturbation moves, and completed neighborhoods are separately counted in the JSON. Counters describe integer operations, not bit complexity.

| n | q before | q after | Evaluations | Setups | Restarts | Discovery seconds | Native branches completed/total | Status | Exact distance | Upper bound |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 18 | 9 | 3 | 18824 | 32 | 31 | 0.1342 | 8/8 | EXACT | 3 | 3 |
| 20 | 9 | 4 | 26942 | 32 | 31 | 0.1843 | 16/16 | EXACT | 3 | 3 |
| 22 | 11 | 6 | 30000 | 30 | 29 | 0.2171 | 64/64 | EXACT | 4 | 4 |
| 24 | 12 | 7 | 30000 | 24 | 23 | 0.2277 | 128/128 | EXACT | 4 | 4 |
| 26 | 13 | 9 | 30000 | 21 | 20 | 0.2516 | 256/512 | UNKNOWN |  | 4 |
| 28 | 14 | 12 | 30000 | 16 | 15 | 0.2592 | 256/4096 | UNKNOWN |  | 5 |

Every saved transform P is independently checked to be square and invertible. The verifier reconstructs P H from original column parities, checks equality with the emitted matrix, and independently recomputes the objective. The native solver then receives the ORIGINAL H and P, and its full certificate is replayed against that original problem. Small reference enumeration (dimension at most 14) checks exact answers and upper-bound witnesses.

Search exhaustion is not a nonexistence result. A completed neighborhood only proves local optimality under a single row XOR. No exhaustive general-linear-group search occurs in production. The separate tests use GL(3,2) as a tiny independent audit oracle.

Reproduce with `python row_basis_discovery.py`; run tests with `python -m unittest -v test_row_basis_discovery`. Full matrices, invertible transforms, descent traces, source hashes, native certificates, and reference witnesses are in `ROW_BASIS_RESULTS.json`.
