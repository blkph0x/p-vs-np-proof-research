# Incremental bounded-width resolution ladder

Each row compares a fresh closure at every width with a ladder that
seeds width `w` from the complete width `w-1` closure.

| family | parameter | width | seed clauses | fresh candidates | incremental candidates | status |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| all_assignments | 1 | 0 | 0 | 0 | 0 | UNKNOWN |
| all_assignments | 1 | 1 | 0 | 1 | 1 | UNSAT |
| all_assignments | 2 | 0 | 0 | 0 | 0 | UNKNOWN |
| all_assignments | 2 | 1 | 0 | 0 | 0 | UNKNOWN |
| all_assignments | 2 | 2 | 0 | 16 | 16 | UNSAT |
| all_assignments | 3 | 0 | 0 | 0 | 0 | UNKNOWN |
| all_assignments | 3 | 1 | 0 | 0 | 0 | UNKNOWN |
| all_assignments | 3 | 2 | 0 | 0 | 0 | UNKNOWN |
| all_assignments | 3 | 3 | 0 | 222 | 222 | UNSAT |
| all_assignments | 4 | 0 | 0 | 0 | 0 | UNKNOWN |
| all_assignments | 4 | 1 | 0 | 0 | 0 | UNKNOWN |
| all_assignments | 4 | 2 | 0 | 0 | 0 | UNKNOWN |
| all_assignments | 4 | 3 | 0 | 0 | 0 | UNKNOWN |
| all_assignments | 4 | 4 | 0 | 2218 | 2218 | UNSAT |
| pigeonhole | 1 | 0 | 0 | 0 | 0 | UNKNOWN |
| pigeonhole | 1 | 1 | 0 | 0 | 0 | UNKNOWN |
| pigeonhole | 1 | 2 | 2 | 6 | 6 | UNSAT |
| pigeonhole | 2 | 0 | 0 | 0 | 0 | UNKNOWN |
| pigeonhole | 2 | 1 | 0 | 0 | 0 | UNKNOWN |
| pigeonhole | 2 | 2 | 0 | 555 | 555 | UNSAT |
| pigeonhole | 3 | 0 | 0 | 0 | 0 | UNKNOWN |
| pigeonhole | 3 | 1 | 0 | 0 | 0 | UNKNOWN |
| pigeonhole | 3 | 2 | 0 | 0 | 0 | UNKNOWN |
| pigeonhole | 3 | 3 | 30 | 267204 | 234750 | UNSAT |

The independent reviewer checks equality of the complete closure at
each width and verifies that a seed is used only after a non-capped lower
width. Candidate counts measure inference attempts in this deterministic
implementation; they are not a machine-independent runtime bound.
