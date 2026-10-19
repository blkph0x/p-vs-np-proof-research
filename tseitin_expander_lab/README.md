# Tseitin expander campaign

This lab records exact odd-charge Tseitin contradictions on four named small
connected cubic graphs plus a deterministic Möbius-ladder sweep with sizes
6, 8, ..., 20. It stores the CNF, parity certificate, proof-producing CDCL
result, and a second replay that rebuilds both the encoding and the resolution
trace.

The experiment is a finite solver and proof-complexity control. The ladder
conflict counts are measurements of this fixed decision policy; they are not
an all-size theorem or an assertion that the ladder family is a uniform
expander. It does not claim a new asymptotic lower bound or a solution to P
versus NP. See
[`THEOREM.md`](THEOREM.md), [`REPORT.md`](REPORT.md), and the cited
Ben-Sasson--Wigderson paper in the repository citation ledger.
