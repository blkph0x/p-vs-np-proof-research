# Indexed bounded-width resolution stress

The indexed closure uses the same weakening and binary-resolution
rules as the reference closure, but indexes clauses by literal before
testing a resolution pair. The exact controls are cross-checked against
the reference implementation; the 5-into-4 stress rows use the fixed
resource cap shown below.

Caps: `100000` clauses and `1000000` candidate steps.

| family | instance | width | seed | status | reason | closure | candidates | indexed pairs | seconds |
| --- | --- | ---: | ---: | --- | --- | ---: | ---: | ---: | ---: |
| all_assignments | all_assignments_n1 | 0 | 0 | UNKNOWN | NO_WIDTH_W_REFUTATION | 0 | 0 | 0 | 0.000 |
| all_assignments | all_assignments_n1 | 1 | 0 | UNSAT | — | 3 | 1 | 1 | 0.000 |
| all_assignments | all_assignments_n2 | 0 | 0 | UNKNOWN | NO_WIDTH_W_REFUTATION | 0 | 0 | 0 | 0.000 |
| all_assignments | all_assignments_n2 | 1 | 0 | UNKNOWN | NO_WIDTH_W_REFUTATION | 0 | 0 | 0 | 0.000 |
| all_assignments | all_assignments_n2 | 2 | 0 | UNSAT | — | 9 | 18 | 24 | 0.000 |
| all_assignments | all_assignments_n3 | 0 | 0 | UNKNOWN | NO_WIDTH_W_REFUTATION | 0 | 0 | 0 | 0.000 |
| all_assignments | all_assignments_n3 | 1 | 0 | UNKNOWN | NO_WIDTH_W_REFUTATION | 0 | 0 | 0 | 0.000 |
| all_assignments | all_assignments_n3 | 2 | 0 | UNKNOWN | NO_WIDTH_W_REFUTATION | 0 | 0 | 0 | 0.000 |
| all_assignments | all_assignments_n3 | 3 | 0 | UNSAT | — | 27 | 229 | 369 | 0.002 |
| all_assignments | all_assignments_n4 | 0 | 0 | UNKNOWN | NO_WIDTH_W_REFUTATION | 0 | 0 | 0 | 0.000 |
| all_assignments | all_assignments_n4 | 1 | 0 | UNKNOWN | NO_WIDTH_W_REFUTATION | 0 | 0 | 0 | 0.000 |
| all_assignments | all_assignments_n4 | 2 | 0 | UNKNOWN | NO_WIDTH_W_REFUTATION | 0 | 0 | 0 | 0.000 |
| all_assignments | all_assignments_n4 | 3 | 0 | UNKNOWN | NO_WIDTH_W_REFUTATION | 0 | 0 | 0 | 0.000 |
| all_assignments | all_assignments_n4 | 4 | 0 | UNSAT | — | 81 | 2218 | 4508 | 0.020 |
| pigeonhole | pigeonhole_2_1 | 0 | 0 | UNKNOWN | NO_WIDTH_W_REFUTATION | 0 | 0 | 0 | 0.000 |
| pigeonhole | pigeonhole_2_1 | 1 | 0 | UNKNOWN | NO_WIDTH_W_REFUTATION | 2 | 0 | 0 | 0.000 |
| pigeonhole | pigeonhole_3_2 | 0 | 0 | UNKNOWN | NO_WIDTH_W_REFUTATION | 0 | 0 | 0 | 0.000 |
| pigeonhole | pigeonhole_3_2 | 1 | 0 | UNKNOWN | NO_WIDTH_W_REFUTATION | 0 | 0 | 0 | 0.000 |
| pigeonhole | pigeonhole_3_2 | 2 | 0 | UNSAT | — | 73 | 584 | 646 | 0.003 |
| pigeonhole | pigeonhole_4_3 | 0 | 0 | UNKNOWN | NO_WIDTH_W_REFUTATION | 0 | 0 | 0 | 0.000 |
| pigeonhole | pigeonhole_4_3 | 1 | 0 | UNKNOWN | NO_WIDTH_W_REFUTATION | 0 | 0 | 0 | 0.000 |
| pigeonhole | pigeonhole_4_3 | 2 | 0 | UNKNOWN | NO_WIDTH_W_REFUTATION | 30 | 0 | 0 | 0.000 |
| pigeonhole | pigeonhole_4_3 | 3 | 30 | UNSAT | — | 2049 | 234752 | 837438 | 3.618 |
| pigeonhole_stress | pigeonhole_5_4 | 3 | 0 | UNKNOWN | NO_WIDTH_W_REFUTATION | 2230 | 112350 | 670950 | 2.990 |
| pigeonhole_stress | pigeonhole_5_4 | 4 | 2230 | UNKNOWN | STEP_CAP | 27377 | 1000001 | 3110477 | 15.974 |

For `pigeonhole_5_4`, width 3 reaches a complete bounded closure without
the empty clause. Width 4 is deliberately reported as `UNKNOWN` after
the step cap, even though the indexed implementation has already reused
the complete width-3 seed. This is an implementation frontier, not a
proof that the formula has no width-4 refutation.

The independent [pebble-game bridge](PEBBLE_REPORT.md) now settles the finite
question: PHP(5,4) has a width-4 refutation even though this capped indexed
search did not reach it.
