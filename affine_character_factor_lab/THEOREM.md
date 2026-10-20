# Exact character expansion for factorized affine coupling

This lab tests one concrete way to preserve factorized structure before
expanding a global Boolean sum. It is an exact algorithm for a restricted
input family. It is not a solver for unrestricted SAT and it does not resolve
P versus NP.

## Input and ownership

The original variables are partitioned into disjoint blocks (B_1,ldots,B_s).
Each block owns one or more original factor occurrences. A factor has an
explicit scope contained in its owning block and an integer truth table. The
block value is the product of its owned factors. Repeated factors remain
separate occurrences in the request; no equality of tables permits an
occurrence to be dropped. The global coupling is an explicitly supplied
system

\[
 A x=b \pmod 2.
\]

The counted value is

\[
 Z=\sum_{x\in\{0,1\}^n}1[Ax=b]\prod_{j=1}^s f_j(x_{B_j}).
\]

The verifier recomputes the block products from those original factor IDs and
does not trust a producer's block value or operation counters.

## Character identity and exact evaluator

Row reduction produces independent equations (A'x=b'), with rank (r), or
detects an inconsistent zero row. For a consistent system, the elementary
orthogonality identity over (mathbb F_2) is

\[
 1[A'x=b'] = 2^{-r}\sum_{\lambda\in\mathbb F_2^r}
 (-1)^{\lambda\cdot(A'x+b')}.
\]

Because the blocks have disjoint variables, every character term factors:

\[
 Z=2^{-r}\sum_{\lambda\in\mathbb F_2^r}
 (-1)^{\lambda\cdot b'}
 \prod_j \widehat f_j(A_j'^T\lambda),
\]

where

\[
 \widehat f_j(u)=\sum_{y\in\mathbb F_2^{|B_j|}}
 f_j(y)(-1)^{u\cdot y}.
\]

The implementation computes every character and every local transform before
adding terms. It records the row-reduced equations, each character, each
restricted local mask, each local transform, the product, and the signed term.
The independent checker recomputes all of those values and then checks the
division by (2^r). A nonintegral result is rejected rather than rounded.

## Cost and the actual parameter

The 20 October implementation precomputes a block's exact unnormalised
Walsh spectrum when its charged cost is strictly lower than direct repeated
sums. For width `k`, `N=2^k` entries and `C=2^r` characters, the compared
costs are `C*N` versus `N + k*N + C`: local product evaluations, butterfly
additions/subtractions, and spectrum lookups. Ties and `C<=2` stay direct.
This borrows standard [FWHT arithmetic](https://docs.sympy.org/latest/modules/discrete.html)
within the [normal-factor-graph duality](https://arxiv.org/abs/1102.0316)
interpretation; no new transform is claimed.

The certificate still records every character, mask and exact local value.
Its independent arithmetic checker deliberately uses direct sums, so the
verification work bound below remains unchanged. Producer local arithmetic
can instead be bounded by `sum_j min(C*2^k_j, (k_j+1)*2^k_j+C)` under this
charged convention, plus the other operations already listed below.
The spectrum temporarily stores `sum_j 2^k_j` integers over selected blocks.
Work and integer-size caps apply during precomputation. An unused spectrum
entry can exceed a tight integer-size cap even if the requested direct sums
would cancel; that path returns UNKNOWN, never a false exact value.

With (k=\max_j |B_j|), the explicit character certificate uses

\[
 O\left(2^r\sum_j 2^{|B_j|}\right)
\]

local evaluations, plus polynomial exact-arithmetic overhead. The source
factor tables and original scopes are part of the input size. This is
polynomial for bounded block size and (r=O(\log n)), but exponential in the
independent affine rank in general. The operation counter charges every local
assignment and every character-product operation. Caps return `UNKNOWN` with
no value; exhaustion is never interpreted as unsatisfiable.

This is a representation result, not a lower bound against other algorithms.
The factorization is supplied as part of the input. Discovering such blocks or
an affine system from an arbitrary CNF is a separate computational problem.

## Component-aware refinement

The same incidence information gives a strictly better composition rule. Build
the bipartite graph whose left vertices are factor blocks and whose right
vertices are nonzero affine rows, joining a row to every block it touches. If
the graph has components (C_1,ldots,C_t), the original sum is the product of
the component sums. The implementation relabels each component locally,
retains its original block and row IDs in the parent certificate, and applies
the character evaluator separately. Its exponential factor is therefore

\[
 \sum_{i=1}^t 2^{r_i}
\]

for component ranks (r_i), rather than (2^{\sum_i r_i}). The verifier
reconstructs the incidence components independently and checks every child
certificate before multiplying the child values. Scalar zero rows are checked
directly; a scalar contradiction returns an exact zero.

## Exact controls and rank barrier

For (m) disjoint two-variable OR factors and one global even-parity equation,
each block has Fourier values (3) at the zero character and (-1) at the
nonzero character. Therefore

\[
 Z_m=\frac{3^m+(-1)^m}{2}.
\]

The input has (2m) variables and one affine equation, so all (m=128)
controls are evaluated with only two global characters. In contrast, adding
one independent parity equation per pair gives rank (m). The same family then
has exactly one satisfying assignment, but the character expansion has
(2^m) terms. The saved rank-14 run verifies all 16,384 characters; a rank-16
run with a 100,000-work cap returns `UNKNOWN` before a value is produced.

These paired controls isolate the useful effect: preserving the product before
expansion removes the dependence on the number of blocks when the affine rank
is small. The component-aware path additionally solves 128 independent local
parities using 128 rank-one components. A cumulative chain of parity rows
connects those same blocks into one component of rank (m); its character
count is (2^m), and the rank-16 run reaches the explicit work cap. Thus
component discovery removes a real product blow-up but does not remove the
rank parameter for connected coupling. The experiment sharpens the next search
target to a richer quotient for high-rank connected structure, rather than
treating local factorization as a general P=NP route.

An independent cross-check then sends the same connected chain to the audited
weighted affine DAG. With the interleaved order `[OR_i, parity_i]`, all saved
sizes through (m=128) are independently verified exact and the largest
certificate retains only three terms. Listing all OR factors first reaches the
declared work cap at (m=12). This finite comparison shows that a compact
elimination order can beat the raw character rank on a structured connected
family, while order discovery and worst-case width remain unresolved.

## Verification scope

The saved run contains 23 records: 21 independently verified exact results, a
charged rank-16 `UNKNOWN`, and one deliberately mutated certificate rejected by
the checker. Small cases are also compared with a separate direct assignment
enumerator, and a deterministic 220-case random cross-check matched both the
direct oracle and the checker. Source hashes, full original controls, exact
certificates, and review results are saved beside this theorem.
