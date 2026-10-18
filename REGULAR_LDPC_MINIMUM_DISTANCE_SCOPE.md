# Sparse homogeneous minimum distance: current literature scope

This note records a primary-source result that closes the specific sparse
homogeneous gap left open by the checkpoint's self-contained affine reduction.
It is a literature audit, not an independent re-derivation of the paper's
full reduction. Separate finite replays of the local gadgets and the
`(3,3)` completion phase are saved in
[REGULAR_LDPC_LOCAL_AUDIT_REPORT.md](REGULAR_LDPC_LOCAL_AUDIT_REPORT.md); it is
useful for catching local transcription errors but does not replace the
all-size proof.

## Primary source

Chenyuan Jia, Qingqing Peng, Ke Liu, Guanghui Wang and Guiying Yan,
*On the Intractability of the Minimum Distance Problem for Regular LDPC Codes*,
arXiv:2606.23161 (2026), [primary preprint](https://arxiv.org/abs/2606.23161).

The paper identifies codewords with even covers of a Tanner graph. Its Section
V states that constant left degree is the same as constant parity-check column
weight. Theorem 16 states that `MinDistance_3` is NP-complete (and W[1]-complete
when parameterized by the target weight), where every variable node has degree
exactly three. In matrix language, this is homogeneous binary minimum distance
with every column of the parity-check matrix having weight three; row weights
are unrestricted in that theorem. The proof uses polynomial hyperedge
decomposition, padding and variable replication, with explicit bijections and
threshold accounting.

Theorem 18 further states NP-completeness and W[1]-completeness for
`MinDistance_(3,3)`, where both variable and check nodes have degree exactly
three. Thus the source reaches a strictly regular binary parity-check family,
not only an arbitrary dense matrix.

The same section records the lower-degree boundary: left degree at most two is
polynomial-time, while every fixed left degree at least three is hard. This is
consistent with the project controls and makes column weight three the first
hard regular regime in that formulation.

## What this does and does not establish

This source supplies the missing homogeneous sparse-hardness reference for the
project's binary-code branch. It is stronger than the checkpoint's affine
nonzero-syndrome X3C reduction with column weight three, but it is not that
reduction and its all-size proof has not been formalized here. The finite local
replay is recorded separately and is explicitly narrower than the theorem.
The result is also a 2026 arXiv preprint; it should be labelled as such until
peer-reviewed publication or an independently checked formalization is
available.

This checkpoint relies only on the column-weight-three and `(3,3)` statements.
The later fixed-right-degree and arbitrary-biregular extensions in the preprint
use additional high-girth gadgets and are outside the finite replay recorded
here; they are not needed for the sparse homogeneous boundary being audited.

Neither this theorem nor Vardy's unrestricted homogeneous MDP theorem proves
`P != NP`. NP-completeness says that a polynomial algorithm for this restricted
minimum-distance problem would imply `P = NP`; it does not provide a lower bound
separating the classes. The bounded-distance decoding promise discussed by
Vardy remains a separate problem.

## Reproducibility boundary

The claims above are tied to Theorems 16 and 18 and the definitions in the
linked preprint. The checkpoint's own finite tests still certify only its local
solvers and its affine reduction. The added gadget and `(3,3)` replays are finite
and source-hashed; no test result in this repository is being promoted to an
independent proof of the paper's all-size regular-LDPC reductions.
