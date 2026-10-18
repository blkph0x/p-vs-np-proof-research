# Proof-complexity scaling report

This report is generated from `SCALING_RESULTS.json`. Every row has a
complete CDCL resolution trace that is replayed by `review_scaling.py`.

## All-assignment family

| n | clauses | decisions | conflicts | resolution steps | seconds |
| ---: | ---: | ---: | ---: | ---: | ---: |
| 1 | 2 | 0 | 1 | 1 | 0.000033 |
| 2 | 4 | 1 | 2 | 3 | 0.000074 |
| 3 | 8 | 3 | 4 | 7 | 0.000211 |
| 4 | 16 | 7 | 8 | 15 | 0.000672 |
| 5 | 32 | 15 | 16 | 31 | 0.002157 |
| 6 | 64 | 31 | 32 | 63 | 0.007993 |
| 7 | 128 | 63 | 64 | 127 | 0.027474 |
| 8 | 256 | 127 | 128 | 255 | 0.103283 |
| 9 | 512 | 255 | 256 | 511 | 0.401380 |
| 10 | 1024 | 511 | 512 | 1023 | 1.521227 |

## Pigeonhole family

| pigeons | holes | variables | clauses | decisions | conflicts | resolution steps | seconds |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 2 | 1 | 2 | 3 | 0 | 1 | 2 | 0.000034 |
| 3 | 2 | 6 | 12 | 1 | 2 | 10 | 0.000183 |
| 4 | 3 | 12 | 34 | 6 | 6 | 42 | 0.001242 |
| 5 | 4 | 20 | 75 | 24 | 18 | 164 | 0.008101 |
| 6 | 5 | 30 | 141 | 80 | 50 | 590 | 0.046639 |
| 7 | 6 | 42 | 238 | 240 | 130 | 1962 | 0.256403 |
| 8 | 7 | 56 | 372 | 672 | 322 | 6104 | 1.384350 |
| 9 | 8 | 72 | 549 | 1792 | 770 | 17992 | 7.728615 |

The first family has exponential size in its parameter, so its
exponential-in-`n` trace is not a super-polynomial-in-input-size
lower bound. The pigeonhole family has polynomial-size CNFs in the
hole parameter and is unsatisfiable by the injection counting proof.
These measurements concern this resolution-based CDCL implementation
and do not lower-bound every SAT algorithm or settle P versus NP.
