# Checked XOR3 grouping: fixed original requests

Dataset statuses: {'stress22': {'VERIFIED_EXACT': 19, 'UNKNOWN': 3}, 'original58': {'VERIFIED_EXACT': 54, 'UNKNOWN': 4}}. Newly certified: 8; regressions: 0.

Only the verified clause occurrence order is passed to the unchanged compressed solver. All original inputs and complete proof replays are in hash-bound gzip JSON files under `certificates/`. Planning is additional work; the unchanged solver cap is not presented as a cap on the entire pipeline.

| Dataset / original request | Status | Blocks | Planner + solver work | Exact block subtrees |
|---|---|---:|---:|---:|
| stress22 / cubic_parity_v8_charge0_grouped | VERIFIED_EXACT | 8 | 10018 | 8/8 |
| stress22 / cubic_parity_v8_charge0_shuffled | VERIFIED_EXACT | 8 | 10018 | 8/8 |
| stress22 / cubic_parity_v8_charge1_grouped | VERIFIED_EXACT | 8 | 10018 | 8/8 |
| stress22 / cubic_parity_v8_charge1_shuffled | VERIFIED_EXACT | 8 | 10018 | 8/8 |
| stress22 / cubic_parity_v20_charge0_grouped | VERIFIED_EXACT | 20 | 64133 | 0/20 |
| stress22 / cubic_parity_v20_charge0_shuffled | VERIFIED_EXACT | 20 | 64133 | 0/20 |
| stress22 / cubic_parity_v20_charge1_grouped | VERIFIED_EXACT | 20 | 64133 | 0/20 |
| stress22 / cubic_parity_v20_charge1_shuffled | VERIFIED_EXACT | 20 | 64133 | 0/20 |
| stress22 / cubic_parity_v40_charge0_grouped | VERIFIED_EXACT | 40 | 124505 | 0/40 |
| stress22 / cubic_parity_v40_charge0_shuffled | VERIFIED_EXACT | 40 | 124505 | 0/40 |
| stress22 / cubic_parity_v40_charge1_grouped | VERIFIED_EXACT | 40 | 124505 | 0/40 |
| stress22 / cubic_parity_v40_charge1_shuffled | VERIFIED_EXACT | 40 | 124505 | 0/40 |
| stress22 / cubic_parity_v80_charge0_grouped | VERIFIED_EXACT | 80 | 257679 | 0/80 |
| stress22 / cubic_parity_v80_charge0_shuffled | VERIFIED_EXACT | 80 | 257679 | 0/80 |
| stress22 / cubic_parity_v80_charge1_grouped | VERIFIED_EXACT | 80 | 257679 | 0/80 |
| stress22 / cubic_parity_v80_charge1_shuffled | VERIFIED_EXACT | 80 | 257679 | 0/80 |
| stress22 / pigeonhole_3_into_3 | VERIFIED_EXACT | 0 | 15254 | 0/0 |
| stress22 / pigeonhole_4_into_3 | VERIFIED_EXACT | 0 | 156176 | 0/0 |
| stress22 / pigeonhole_4_into_4 | VERIFIED_EXACT | 0 | 954653 | 0/0 |
| stress22 / pigeonhole_5_into_4 | UNKNOWN | 0 | 2792175 | unavailable |
| stress22 / pigeonhole_5_into_5 | UNKNOWN | 0 | 2145014 | unavailable |
| stress22 / pigeonhole_6_into_5 | UNKNOWN | 0 | 3003126 | unavailable |
| original58 / earlier_packed_gap | VERIFIED_EXACT | 0 | 176 | 0/0 |
| original58 / earlier_all_eight_clauses | VERIFIED_EXACT | 0 | 2205 | 0/0 |
| original58 / earlier_random_0 | VERIFIED_EXACT | 0 | 2059 | 0/0 |
| original58 / earlier_random_1 | VERIFIED_EXACT | 0 | 213 | 0/0 |
| original58 / earlier_random_2 | VERIFIED_EXACT | 0 | 502 | 0/0 |
| original58 / earlier_random_3 | VERIFIED_EXACT | 0 | 1029 | 0/0 |
| original58 / earlier_random_4 | VERIFIED_EXACT | 0 | 1355 | 0/0 |
| original58 / earlier_random_5 | VERIFIED_EXACT | 0 | 3809 | 0/0 |
| original58 / earlier_random_6 | VERIFIED_EXACT | 0 | 992 | 0/0 |
| original58 / earlier_random_7 | VERIFIED_EXACT | 0 | 344 | 0/0 |
| original58 / earlier_random_8 | VERIFIED_EXACT | 0 | 436 | 0/0 |
| original58 / earlier_random_9 | VERIFIED_EXACT | 0 | 393 | 0/0 |
| original58 / earlier_random_10 | VERIFIED_EXACT | 0 | 79 | 0/0 |
| original58 / earlier_random_11 | VERIFIED_EXACT | 0 | 1417 | 0/0 |
| original58 / earlier_random_12 | VERIFIED_EXACT | 0 | 1671 | 0/0 |
| original58 / earlier_random_13 | VERIFIED_EXACT | 0 | 2851 | 0/0 |
| original58 / earlier_random_14 | VERIFIED_EXACT | 0 | 1757 | 0/0 |
| original58 / earlier_random_15 | VERIFIED_EXACT | 0 | 1493 | 0/0 |
| original58 / earlier_random_16 | VERIFIED_EXACT | 0 | 652 | 0/0 |
| original58 / earlier_random_17 | VERIFIED_EXACT | 0 | 32 | 0/0 |
| original58 / earlier_random_18 | VERIFIED_EXACT | 0 | 46 | 0/0 |
| original58 / earlier_random_19 | VERIFIED_EXACT | 0 | 1398 | 0/0 |
| original58 / earlier_random_20 | VERIFIED_EXACT | 0 | 850 | 0/0 |
| original58 / earlier_random_21 | VERIFIED_EXACT | 0 | 308 | 0/0 |
| original58 / earlier_random_22 | VERIFIED_EXACT | 0 | 791 | 0/0 |
| original58 / earlier_random_23 | VERIFIED_EXACT | 0 | 79 | 0/0 |
| original58 / earlier_random_24 | VERIFIED_EXACT | 0 | 149 | 0/0 |
| original58 / earlier_random_25 | VERIFIED_EXACT | 0 | 46 | 0/0 |
| original58 / earlier_random_26 | VERIFIED_EXACT | 0 | 1443 | 0/0 |
| original58 / earlier_random_27 | VERIFIED_EXACT | 0 | 1219 | 0/0 |
| original58 / earlier_independent_ternary_2 | VERIFIED_EXACT | 0 | 175 | 0/0 |
| original58 / earlier_independent_ternary_4 | VERIFIED_EXACT | 0 | 378 | 0/0 |
| original58 / earlier_independent_ternary_8 | VERIFIED_EXACT | 0 | 807 | 0/0 |
| original58 / earlier_independent_ternary_16 | VERIFIED_EXACT | 0 | 1712 | 0/0 |
| original58 / empty_zero_variables | VERIFIED_EXACT | 0 | 4 | 0/0 |
| original58 / unused_variables | VERIFIED_EXACT | 0 | 4 | 0/0 |
| original58 / contradictory_units | VERIFIED_EXACT | 0 | 125 | 0/0 |
| original58 / empty_clause | VERIFIED_EXACT | 0 | 12 | 0/0 |
| original58 / repeated_literal | VERIFIED_EXACT | 0 | 47 | 0/0 |
| original58 / tautological_clause | VERIFIED_EXACT | 0 | 21 | 0/0 |
| original58 / structure_one_ternary_multiplicity | VERIFIED_EXACT | 0 | 79 | 0/0 |
| original58 / structure_repeated_ternary_not_deduplicated | VERIFIED_EXACT | 0 | 324 | 0/0 |
| original58 / structure_unused_logical_variable | VERIFIED_EXACT | 0 | 79 | 0/0 |
| original58 / structure_shared_contradictory_units | VERIFIED_EXACT | 0 | 125 | 0/0 |
| original58 / structure_original_gap_passes_interval_and_gcd | VERIFIED_EXACT | 0 | 176 | 0/0 |
| original58 / structure_all_eight_ternary_polarities_UNSAT | VERIFIED_EXACT | 0 | 2205 | 0/0 |
| original58 / structure_disjoint_24_ternary_clauses | VERIFIED_EXACT | 0 | 2569 | 0/0 |
| original58 / structure_connected_40_clause_width_two_chain | VERIFIED_EXACT | 0 | 22189 | 0/0 |
| original58 / structure_star_bad_external_order | VERIFIED_EXACT | 0 | 1292 | 0/0 |
| original58 / structure_star_good_external_order | VERIFIED_EXACT | 0 | 1292 | 0/0 |
| original58 / structure_complete_interaction_every_order_width15 | UNKNOWN | 0 | 1798584 | unavailable |
| original58 / structure_planted_mixed_3CNF_n24_m96 | UNKNOWN | 0 | 1397609 | unavailable |
| original58 / structure_planted_mixed_3CNF_n32_m128 | UNKNOWN | 0 | 2010803 | unavailable |
| original58 / structure_empty_product | VERIFIED_EXACT | 0 | 4 | 0/0 |
| original58 / structure_256_unused_variables_preserve_all_choices | VERIFIED_EXACT | 0 | 4 | 0/0 |
| original58 / legacy_mixed_12_connected_False | VERIFIED_EXACT | 12 | 56795 | 0/12 |
| original58 / legacy_mixed_12_connected_True | UNKNOWN | 12 | 2138150 | unavailable |
| original58 / legacy_sliding_64_radius2_seed17 | VERIFIED_EXACT | 0 | 134382 | 0/0 |

All cap failures and regressions remain visible. Complete blocks need not be exact balanced-tree subtrees; the table reports the completed certificate structure rather than assuming alignment. Reference counts enter only post-solve comparisons. No general complexity or runtime claim follows from these finite requests.
