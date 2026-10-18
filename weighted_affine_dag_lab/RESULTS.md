# Weighted affine DAG saved controls

18 original requests: 16 EXACT with independently replayed certificates; 2 UNKNOWN.

Every exact value agrees with the analytic formula stated with its original input. These are deliberately structured controls, not a general complexity or speed claim. Full inputs, all exact certificates, source hashes, and elapsed wall-clock times are in `RESULTS.json`.

| Original request | Status | Exact value or stopping reason | Peak pieces | Pre-merge products |
|---|---|---|---:|---:|
| shared_pair_private_clause_1 | EXACT | 7 | 1 | 0 |
| shared_pair_private_clause_4 | EXACT | 49 | 2 | 12 |
| shared_pair_private_clause_16 | EXACT | 196609 | 2 | 60 |
| shared_pair_private_clause_64 | EXACT | 55340232221128654849 | 2 | 252 |
| shared_pair_private_clause_128 | EXACT | 1020847100762815390390123822295304634369 | 2 | 508 |
| phase_induced_even_boundary_1 | EXACT | 0 | 2 | 2 |
| phase_induced_even_boundary_3 | EXACT | 6 | 2 | 2 |
| phase_induced_even_boundary_32 | EXACT | 4294967294 | 2 | 2 |
| phase_induced_even_boundary_128 | EXACT | 340282366920938463463374607431768211454 | 2 | 2 |
| wide_signed_phase_product_4 | EXACT | -168/55 | 1 | 1 |
| wide_signed_phase_product_32 | EXACT | -45097156608/55 | 1 | 1 |
| wide_signed_phase_product_128 | EXACT | -3572964852669853866365433378033566220288/55 | 1 | 1 |
| negative_constant_free_universe | EXACT | -1536/7 | 1 | 0 |
| signed_phase_zero_sum | EXACT | 0 | 0 | 0 |
| paired_ors_global_even_2_cap_256 | EXACT | 5 | 2 | 6 |
| paired_ors_global_even_6_cap_256 | EXACT | 365 | 8 | 42 |
| paired_ors_global_even_12_cap_16 | UNKNOWN | retained term cap | 17 | 88 |
| products_before_merge_cap | UNKNOWN | cross-product cap before merging | 2 | 4 |

The 128-bit boundary controls retain compact affine messages instead of constructing a 2^128 table. The global-parity paired-OR failure demonstrates that even a structured, independently solvable input can exceed this planner’s component cap. The product-cap failure is intentional: identical output components do not erase the cost of producing all input pairs.

The separate original-CNF benchmark in `../WEIGHTED_AFFINE_CROSSCHECK.json` reports 54/58 EXACT counts with replay and four UNKNOWN requests at the default caps. The complete binary interaction on 16 variables, planted 32-variable/128-clause input, and legacy connected mixed 12 fixture exceed 4,096 combined nodes. The planted 24-variable/96-clause input reaches 257 retained pieces. The 72-variable disjoint, 81-variable chain, and 66-variable sliding fixtures complete exactly. All 58 were also solved by the separate bounded branch/component reference; no general speed or coverage advantage is claimed. These failures are not replaced by the positive controls above.

Source hashes were unchanged over this run. Timing includes producing and independently replaying the certificate on this machine; no comparative speed conclusion is drawn.
