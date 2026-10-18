# Compressed affine DAG saved controls

22 original requests: 19 EXACT with independently replayed certificates; 3 UNKNOWN.

Among the 18 unchanged requests from the frozen control set, 0 become newly exact and 0 regress to UNKNOWN. This status comparison does not equate the different transient-retention semantics or claim a runtime benefit.

Every exact value agrees with the analytic formula stated with its original input. These are deliberately structured controls, not a general complexity or speed claim. Full inputs, all exact certificates, source hashes, elapsed times, and the saved external baseline results for the 18 unchanged requests are in `RESULTS.json`.

| Original request | Status | Exact value or stopping reason | Input-list peak | Retained peak | Live-ID peak | Products | Pair attempts |
|---|---|---|---:|---:|---:|---:|---:|
| shared_pair_private_clause_1 | EXACT | 7 | 2 | 1 | 2 | 0 | 1 |
| shared_pair_private_clause_4 | EXACT | 49 | 4 | 2 | 3 | 12 | 21 |
| shared_pair_private_clause_16 | EXACT | 196609 | 4 | 2 | 3 | 60 | 117 |
| shared_pair_private_clause_64 | EXACT | 55340232221128654849 | 4 | 2 | 3 | 252 | 501 |
| shared_pair_private_clause_128 | EXACT | 1020847100762815390390123822295304634369 | 4 | 2 | 3 | 508 | 1013 |
| phase_induced_even_boundary_1 | EXACT | 0 | 2 | 1 | 2 | 1 | 1 |
| phase_induced_even_boundary_3 | EXACT | 6 | 2 | 2 | 2 | 2 | 2 |
| phase_induced_even_boundary_32 | EXACT | 4294967294 | 2 | 2 | 2 | 2 | 2 |
| phase_induced_even_boundary_128 | EXACT | 340282366920938463463374607431768211454 | 2 | 2 | 2 | 2 | 2 |
| wide_signed_phase_product_4 | EXACT | -168/55 | 1 | 1 | 1 | 1 | 0 |
| wide_signed_phase_product_32 | EXACT | -45097156608/55 | 1 | 1 | 1 | 1 | 0 |
| wide_signed_phase_product_128 | EXACT | -3572964852669853866365433378033566220288/55 | 1 | 1 | 1 | 1 | 0 |
| negative_constant_free_universe | EXACT | -1536/7 | 1 | 1 | 1 | 0 | 0 |
| signed_phase_zero_sum | EXACT | 0 | 1 | 0 | 1 | 0 | 0 |
| paired_ors_global_even_2_cap_256 | EXACT | 5 | 4 | 2 | 2 | 6 | 6 |
| paired_ors_global_even_6_cap_256 | EXACT | 365 | 16 | 8 | 8 | 42 | 69 |
| paired_ors_global_even_12_cap_16 | UNKNOWN | sum compression cap: retained pieces cap after arrival processing | 64 | 17 | 17 | 88 | 210 |
| products_before_merge_cap | UNKNOWN | cross-product cap before merging | 2 | 2 | 2 | 4 | 2 |
| unit_streaming_retained_cap_one | EXACT | 1 | 2 | 1 | 2 | 1 | 2 |
| aggregate_compression_inputs_cap | UNKNOWN | sum compression cap: max_inputs | 2 | 1 | 2 | 0 | 1 |
| unit_implication_chain_32_with_free_variables | EXACT | 4 | 16 | 5 | 5 | 186 | 308 |
| signed_sparse_unit_context | EXACT | -1374389534720/3 | 2 | 1 | 2 | 1 | 1 |

The 128-bit boundary controls retain compact affine messages instead of constructing a 2^128 table. Input lists, retained sets, and transient live IDs are different measured objects; the complete input list and all certificates still occupy memory. Pending canonical objects and work counters are separately recorded in JSON.

The product-cap and aggregate-input-cap controls deliberately stop even though their logical counts are known. Compression does not refund generated cross-products, and per-node calls do not reset aggregate compressor budgets. The one-piece unit control reports its transient extra piece rather than concealing it.

The unchanged external baseline remains in `../weighted_affine_dag_lab/RESULTS.json` and its 58-original-CNF comparison remains in `../WEIGHTED_AFFINE_CROSSCHECK.json`. The parent records the separate new 58-request comparison, including improvements and regressions. These additional native controls do not replace that dataset.

Source hashes were unchanged over this run. Timing includes producing and independently replaying the certificate on this machine; no comparative speed conclusion is drawn. The new streaming retained-set cap differs from the baseline transient dictionary cap, and that distinction must be preserved in comparisons.
