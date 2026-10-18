# Resolution width, frontier states, and CDCL traces

The same seven finite CNFs are replayed in three representations:
minimum refutation width from bounded weakening/resolution closure,
supplied-order frontier state counts, and one proof-producing CDCL trace.

| family | parameter | variables | clauses | min width | width closure | frontier width | frontier states | CDCL conflicts | CDCL resolution steps |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| all_assignments | 1 | 1 | 2 | 1 | 3 | 0 | 1 | 1 | 1 |
| all_assignments | 2 | 2 | 4 | 2 | 9 | 1 | 3 | 2 | 3 |
| all_assignments | 3 | 3 | 8 | 3 | 27 | 2 | 7 | 4 | 7 |
| all_assignments | 4 | 4 | 16 | 4 | 81 | 3 | 15 | 8 | 15 |
| pigeonhole | 1 | 2 | 3 | 2 | 8 | 1 | 2 | 1 | 2 |
| pigeonhole | 2 | 6 | 12 | 2 | 73 | 4 | 12 | 2 | 10 |
| pigeonhole | 3 | 12 | 34 | 3 | 2049 | 9 | 60 | 6 | 42 |

The width sweep is complete only for the displayed finite controls and
uses an explicit 100,000-clause/500,000-candidate cap. Each saved sweep
is recomputed by an independent reviewer. The frontier order is supplied
row-major order, and the CDCL fields come from separately replayed
first-UIP resolution certificates.

These measurements do not imply that width controls every proof system,
that CDCL is optimal, or that any value lower-bounds arbitrary SAT
algorithms. They are a finite adversarial comparison, not a P-versus-NP
resolution.
