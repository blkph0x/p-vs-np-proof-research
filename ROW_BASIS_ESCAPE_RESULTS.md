# Expanded native certificates and bounded basis escape

Date: 2026-10-18. Finite exact instances and bounded heuristic search only. No global-optimum or general polynomial-time solver claim.

The earlier strict-greedy baseline remains unchanged. Its saved, independently verified transforms are replayed below with an explicit limit of 4,096 branches. Reference enumeration is bounded to the six archived generator dimensions 9 through 14.

| n | Baseline q | Complete branches | Exact distance | Recorded discovery + verification s | Fresh solve + embedded verification + independent replay s | Total using recorded discovery s |
| --- | --- | --- | --- | --- | --- | --- |
| 18 | 3 | 8 | 3 | 0.1343 | 0.6384 | 0.7727 |
| 20 | 4 | 16 | 3 | 0.1844 | 0.2828 | 0.4672 |
| 22 | 6 | 64 | 4 | 0.2173 | 1.2151 | 1.4325 |
| 24 | 7 | 128 | 4 | 0.2279 | 2.4909 | 2.7188 |
| 26 | 9 | 512 | 4 | 0.2518 | 10.1959 | 10.4477 |
| 28 | 12 | 4096 | 4 | 0.2595 | 84.6515 | 84.9110 |

The discovery timings above are the saved timings of the prior run, explicitly reused rather than presented as newly measured. The JSON separates fresh solving, its embedded certificate verification, and a second independent replay. Reference enumeration timings are separate.

## Equal-budget escape attempts

One deterministic annealing schedule, seed 20261018, starts afresh from the ORIGINAL parity-check basis on each of n=26 and n=28. Each attempt has the same 30,000 scored-evaluation cap as the prior baseline, including initial/restart setup scores. There is no free initialization from the earlier 30,000-evaluation transform and no hidden seed selection.

Four cycles cool from temperature 1.1 to 0.015. Between cycles, three elementary row XORs perturb the current incumbent. Acceptance uses energy q + 0.08 excess + 0.008 total column weight; exact-score plateaus and some worsening moves are allowed. Incumbents and final selection still use the original lexicographic tuple. Every evaluated neighbor may improve the incumbent, even if rejected as the walk state.

| n | Baseline objective | Escape objective | Scored evaluations | Discovery s | Selected | Native branches | Exact distance | Full new discovery/solve/verification s |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 26 | [9, 33, 81] | [9, 24, 73] | 30000 | 0.4086 | ANNEALING | 512 | 4 | 10.6906 |
| 28 | [12, 36, 89] | [12, 50, 104] | 30000 | 0.4412 | BASELINE |  |  |  |

All attempts, including any failures to improve, are retained. Each selected transform is checked for invertibility and exact equality to P H. Full native branch certificates, original matrices, reference witnesses, all source/baseline hashes, and detailed work counts are preserved in the JSON. A smaller finite exception count does not establish a bound on arbitrary inputs.

Reproduce with `python row_basis_escape.py`; run independent tests with `python -m unittest -v test_row_basis_escape`. The production search never enumerates GL(r,2).
