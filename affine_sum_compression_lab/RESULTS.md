# Affine sum compression controls

Saved 109 original requests: 102 EXACT with independently replayed certificates and 7 UNKNOWN with no output sum.
Bounded direct comparison checked 1847 assignments; 6 wide requests matched explicit algebraic expected messages.

The natural singleton order produces one piece; the recorded adverse order produces four. Settled cap one on two identical pieces reports actual live peak two and live-plus-pending peak three.

Producer and verifier operation counts and timings are separate in RESULTS.json. The certificate proves sum equality, not irreducibility. All six source references were unchanged during the run.

| Control | Status | Incoming | Final | Live peak | Retained peak | Producer work | Verifier work |
|---|---|---:|---:|---:|---:|---:|---:|
| empty_sum | EXACT | 0 | 0 | 0 | 0 | 1 | 1 |
| zero_input | EXACT | 1 | 0 | 1 | 0 | 11 | 13 |
| rational_identical_addition | EXACT | 2 | 1 | 2 | 1 | 55 | 54 |
| exact_cancellation | EXACT | 2 | 0 | 2 | 1 | 24 | 23 |
| same_support_affine_pin | EXACT | 2 | 1 | 2 | 1 | 60 | 65 |
| parallel_signed_union | EXACT | 2 | 1 | 2 | 1 | 70 | 76 |
| nested_effective_restricted_sign | EXACT | 2 | 1 | 2 | 1 | 54 | 55 |
| nested_wrong_effective_sign_refused | EXACT | 2 | 2 | 2 | 2 | 41 | 32 |
| nested_constant_one_after_restriction | EXACT | 2 | 1 | 2 | 1 | 50 | 47 |
| unequal_magnitudes_refused | EXACT | 2 | 2 | 2 | 2 | 31 | 22 |
| quadratic_difference_refused | EXACT | 2 | 2 | 2 | 2 | 41 | 33 |
| higher_codimension_refused | EXACT | 2 | 2 | 2 | 2 | 41 | 30 |
| natural_order_one_piece | EXACT | 8 | 1 | 4 | 3 | 532 | 356 |
| nonconfluent_order_four_pieces | EXACT | 8 | 4 | 5 | 4 | 587 | 314 |
| retained_cap_one_actual_live_two_pending_three | EXACT | 2 | 1 | 2 | 1 | 16 | 15 |
| sparse_permuted_original_coordinates | EXACT | 2 | 1 | 2 | 1 | 53 | 51 |
| wide_parallel_64 | EXACT | 2 | 1 | 2 | 1 | 878 | 1032 |
| wide_nested_64 | EXACT | 2 | 1 | 2 | 1 | 881 | 1224 |
| wide_parallel_256 | EXACT | 2 | 1 | 2 | 1 | 3470 | 4104 |
| wide_nested_256 | EXACT | 2 | 1 | 2 | 1 | 3473 | 4872 |
| wide_parallel_512 | EXACT | 2 | 1 | 2 | 1 | 6926 | 8200 |
| wide_nested_512 | EXACT | 2 | 1 | 2 | 1 | 6929 | 9736 |
| exhaust_max_inputs | UNKNOWN | 2 | - | 0 | 0 | 2 | - |
| exhaust_max_generated | UNKNOWN | 2 | - | 2 | 1 | 12 | - |
| exhaust_max_pairs | UNKNOWN | 2 | - | 2 | 1 | 10 | - |
| exhaust_max_steps | UNKNOWN | 2 | - | 1 | 0 | 6 | - |
| exhaust_max_work | UNKNOWN | 2 | - | 0 | 0 | 2 | - |
| exhaust_max_live_pieces | UNKNOWN | 2 | - | 1 | 1 | 6 | - |
