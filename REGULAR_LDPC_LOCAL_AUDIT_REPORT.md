# Finite replay of the regular-LDPC gadgets

`regular_ldpc_local_audit.py` is an independent, standard-library-only replay
of the first local transformations used in Jia et al., arXiv:2606.23161. It does not
claim to formalize the paper's all-size NP-completeness proof. It checks the
parity mechanics that a transcription error would most easily break:

- 120 random hypergraph families exhaustively enumerate every even cover before
  and after large-edge decomposition, including indexed duplicate edges;
- 160 random families exhaustively check the 3-uniform padding gadget and its
  claimed unique correction subset;
- 120 random 3-left-regular Tanner graphs exhaustively check every support before
  and after variable replication for `m` in `{2,4,6}`;
- 90 further small reductions check forward validity through decomposition,
  padding and replication, with 152 mapped supports satisfying the paper's
  `tB <= |Psi(X)| <= t(B+1)+3` interval; 41 of those small outputs are
  enumerated completely and match the mapped support set exactly.
- 314 exhaustive indexed decomposition families (up to four vertices and two
  edges), and 445 exhaustive indexed padding families (up to three vertices
  and three edges), including repeated hyperedges and the empty family.

The replay finished with `all_checks_passed: true`; the exact counts, seed and
source hashes are in [REGULAR_LDPC_LOCAL_AUDIT.json](REGULAR_LDPC_LOCAL_AUDIT.json).
The reverse-bijection checks for the individual gadgets are exhaustive on each
finite instance. The composed pass checks forward validity and weight accounting,
and its 41 complete final-code enumerations check the reverse set equality where
the output is small enough. The all-size reverse argument remains the paper's
written proof.

## `(3,3)` completion phase

`regular_ldpc_33_local_audit.py` separately reconstructs the paper's Theorem 18
completion: check splitting, two-copy coupling, degree-four variable splitting,
replication amplification, and the suffix construction that removes all
degree-two checks. On a cubic three-variable case and a four-variable case with
one degree-four check, the replay exhausts the pre-completion supports, checks
all canonical lifts, verifies the exact weight formula, and confirms that the
final graphs have every variable and check of degree three. The final graphs
have 2,034 and 1,158 variables respectively; this is a degree and mapping audit,
not exhaustive enumeration of those large final codes.

The same implementation now runs 12 seeded fresh inputs (16 attempts after
rejecting degree-one checks). For each case it checks every original support's
lift, the exact first-phase weight identity, both-sided degree three, and the
paper's suffix lower bound. The final graphs range from 2,034 to 18,702
variables; these are structural all-size obligations, not brute-force support
enumerations.

The exact rows and source hashes are in
[REGULAR_LDPC_33_LOCAL_AUDIT.json](REGULAR_LDPC_33_LOCAL_AUDIT.json).
