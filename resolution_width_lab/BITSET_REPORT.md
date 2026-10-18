# Bit-mask bounded-width resolution stress

This run stores each clause as positive and negative bit masks while
retaining the reference weakening/resolution rules and literal indexes.
The seven exact controls are compared with the tuple-indexed closure.
The PHP(5,4) rows use the fixed cap below.

Caps: `200000` clauses and `10000000` candidate steps.

| family | instance | width | seed | status | reason | closure | candidates | pairs | seconds | reference |
| --- | --- | ---: | ---: | --- | --- | ---: | ---: | ---: | ---: | --- |
| all_assignments | all_assignments_n1 | 1 | 0 | UNSAT | — | 3 | 1 | 1 | 0.000 | True |
| all_assignments | all_assignments_n2 | 2 | 0 | UNSAT | — | 9 | 16 | 22 | 0.000 | True |
| all_assignments | all_assignments_n3 | 3 | 0 | UNSAT | — | 27 | 224 | 364 | 0.001 | True |
| all_assignments | all_assignments_n4 | 4 | 0 | UNSAT | — | 81 | 2220 | 4510 | 0.007 | True |
| pigeonhole | pigeonhole_2_1 | 1 | 0 | UNKNOWN | NO_WIDTH_W_REFUTATION | 2 | 0 | 0 | 0.000 | True |
| pigeonhole | pigeonhole_3_2 | 2 | 0 | UNSAT | — | 73 | 627 | 693 | 0.002 | True |
| pigeonhole | pigeonhole_4_3 | 3 | 0 | UNSAT | — | 2049 | 266343 | 960463 | 1.191 | True |
| pigeonhole_stress | pigeonhole_5_4 | 3 | 0 | UNKNOWN | NO_WIDTH_W_REFUTATION | 2230 | 112350 | 670950 | 0.837 | — |
| pigeonhole_stress | pigeonhole_5_4 | 4 | 2230 | UNKNOWN | STEP_CAP | 38368 | 10000001 | 266450100 | 283.342 | — |

The bit-mask representation reaches the same exact-control closures
with different machine-level timings. For PHP(5,4), width 3 reaches a
complete fixed point; seeded width 4 reaches the ten-million-candidate
cap and remains `UNKNOWN`. This is a resource frontier, not a proof that
no width-4 refutation exists.
