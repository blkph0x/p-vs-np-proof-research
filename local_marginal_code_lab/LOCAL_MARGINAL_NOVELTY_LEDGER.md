# Novelty ledger and comparison boundary

This ledger prevents a finite certificate from being promoted to a new
complexity-theory theorem before the relevant literature has been compared.
It records what the repository uses, what is inherited, and what remains an
open novelty question.

| Repository component | Closest established result or tool | Status of the claim here |
| --- | --- | --- |
| Strict full locality-ten lower bound for `RM(2,m)`, every `m>=6` | Boolean Bonferroni inequalities and nonnegative combinations of existing local-marginal identities | **Scoped lower bound; novelty `UNKNOWN`.** The [control](RM2_LEVEL10_CONTROL.md) proves reduced weight at least `644(2^m-1)/2849`, strictly above the level-nine value. It excludes the entire symmetrized level-nine optimal face using an actual ten-nonpin-coordinate table. It does **not** determine the full level-ten optimum. Seven exact tests and a separate mathematical audit check the derivation; no optimizer or general complexity conclusion is needed. |
| Exact full locality-nine value for `RM(2,m)`, every `m>=5` | Fixed-level local-marginal relaxations, finite-geometry moments and LP duality | **Formulation-specific follow-up; novelty `UNKNOWN`.** The [proof](REED_MULLER_QUADRATIC_LEVEL9_THEOREM.md) gives reduced `7(2^m-1)/31` with a seven-term nonnegative identity and common rank moments. The [284-variable selected-model search](RM2_NINE_SCOPE_DISCOVERY.md) is freshly reproduced and independently reconstructed. RM(2,5) reaches integer total eight; the all-size gap ratio tends to `31/28`. No new general hierarchy or algorithmic lower bound is claimed. |
| Gaussian rank moments and local atom inversion | Uniform subspace inclusion probabilities, matroid-flat Möbius inversion, and the Crapo--Rota Critical Theorem | **Inherited counting mechanism, with an additional scoped positivity obligation.** The low-rank cases are genuine codimension-two subspace distributions. The classical count does not automatically prove nonnegativity when the scope rank exceeds the construction's virtual ambient dimension. The level-eight and level-nine proofs separately discharge that obligation; their exact optimization formulas retain novelty `UNKNOWN`. |
| `RM(s,2s+1)` self-duality, distance, and short-support projections | Reed--Muller parameter identities and the standard dual-distance projection/orthogonal-array observation | **Inherited mechanism.** The repository proves and replays the stated finite family, including an exact `d-1` boundary obstruction for the unit witness, the exact plain-model boundary value `1+(2^(2s+1)-1)/(2^(s+1)-1)`, and an explicit all-scope size law. The incidence count and sparse witness are recorded as a scoped formulation theorem; no novelty claim is made for the dual-distance or counting mechanisms themselves. |
| Projection-marginal LP `L_k(C)` | Local consistency and marginal relaxations; named Sherali--Adams/Lasserre systems | **Two boundaries are now explicit.** `L_k(C)` is proved identical, level by level, to configuration Sherali--Adams for the declared finite-domain CSP whose relations are the exact projections `R_S(C)`. No equivalence is claimed for a sparse Boolean parity-check encoding, and the Lasserre relationship remains formulation-specific. |
| Sparse parity check-local configuration versus clause LP | Configuration SA for local CSP relations and the ordinary 0/1 clause relaxation | **Exact finite positioning control.** On the pinned four-variable ternary-parity encoding, the check-local level-two value is `0`, while the simplified sparse 3-CNF clause LP has exact value `1`. This is an encoding-specific comparison, not a new all-size hierarchy theorem. |
| Exact RM(2,5) reduced value `31/5` (total pinned weight `36/5`) | Coding-theory and hierarchy gap results, including stronger asymptotic lower bounds for other models | **Finite certificate.** Whether this exact quotient value is new is an open literature-comparison task. The result is not advertised as a new asymptotic hierarchy theorem. |
| Exact full level-eight value for `RM(2,m)`, every `m>=4` | Reed--Muller geometry, local-marginal relaxations, and the existing finite six-term dual identity | **20 October 2026 formulation-specific follow-up; novelty `UNKNOWN`.** The [audited theorem](REED_MULLER_QUADRATIC_LEVEL8_THEOREM.md) proves reduced optimum `(2^m-1)/5` and total optimum `(2^m+4)/5` using explicit common moments and transport of the finite lower bound. Its total integer/LP ratio tends to `5/4`. This is a fixed-level statement for the declared projection model, not a growing-round lower bound or a new general algorithm. |
| Fresh affine-overlap rational LP search | SoPlex exact LP methods and standard primal/dual optimality certificates | **Reproduced engineering workflow, not a new optimization method.** [Discovery records](EXACT_LP_DISCOVERY/discovery.json) bind a newly source-built model, solver outputs, and independent exact verification. Historical discovery remains `UNRECORDED`; new full-model and cut discovery have not been executed. |
| All-redundant-parity fractional witness | Fundamental polytopes, pseudocodewords, and redundant-parity-check separation | **Related, not yet differentiated.** The repository's all-size theorem is retained, with novelty unclaimed until a theorem-by-theorem comparison is complete. See Kashyap's decomposition discussion and Puchert--Tillmann's separation result. |
| Boolean square and later weight polynomials | Moment/SOS constraints for the square; integer-valid cuts for the later polynomials | **Terminology fixed.** Only the explicit Boolean-square constraint is called a moment/SOS constraint. The remaining seven-cut sequence is a finite integer-cut LP, not a claimed bounded-degree SOS hierarchy. |
| PHP width replay | Classical resolution-width and pebble-game theorems | **Validation infrastructure.** The replay checks known mathematics and does not claim a new width lower bound. |
| X3C and syndrome-decoding reductions | Standard NP-completeness reductions | **Background/boundary controls.** These reductions are included to test scope limits, not as the central contribution. |

The relevant comparison sources currently tracked by the repository are:

- [Reed, *A class of multiple-error-correcting codes and the decoding scheme*](https://doi.org/10.1109/TIT.1954.1057465)
- [Sherali and Adams, *A hierarchy of relaxations and convex hull characterizations*](https://doi.org/10.1016/0166-218X(92)00190-W)
- [Schoenebeck, *Linear level Lasserre lower bounds for certain k-CSPs*](https://schoeneb.people.si.umich.edu/papers/LasserreNew.pdf)
- [Kashyap, *A Decomposition Theory for Binary Linear Codes*](https://ece.iisc.ac.in/~nkashyap/Papers/code_decomp_final.pdf)
- [Puchert and Tillmann, *Exact Separation of Forbidden-Set Cuts Associated with Redundant Parity Checks of Binary Linear Codes*](https://arxiv.org/abs/2004.03387)
- [Proof Complexity Zoo](https://proofcomplexityzoo.gitlab.io/zoo/)

The acceptance rule is simple: a future manuscript may label a statement
“new” only after it gives the prior theorem, the exact difference in model or
assumptions, and a citation. Until then, the repository uses “exact,”
“finite,” “formulation-specific,” or “related” instead.

## Direct theorem comparison at this checkpoint

The comparisons below are deliberately about hypotheses and conclusions, not
about whether the cited work is stronger in an informal sense.

| Source | Object and conclusion | Difference from the repository's RM results |
| --- | --- | --- |
| [Reed (1954)](https://doi.org/10.1109/TIT.1954.1057465) | Reed--Muller construction, parameters, distance, and decoding context. | Supplies the code family identities used here. The local-marginal boundary theorem adds a finite optimization statement for a pinned projection model; it does not claim a new code parameter theorem. |
| [Sherali--Adams (1992)](https://doi.org/10.1016/0166-218X(92)00190-W) | A hierarchy for a specified linear or polynomial formulation. | The exact equality `L_k(C)=SA_k(I_k(C))` in the hierarchy note uses an extensional CSP whose relations are already the exact global projections `R_S(C)`. The finite four-variable clause comparison now positions one sparse ternary-parity encoding: its ordinary clause LP has value `1`, while the declared check-local level-two configuration model has value `0`. This is not an all-size simulation theorem. |
| [Schoenebeck (2008)](https://schoeneb.people.si.umich.edu/papers/LasserreNew.pdf) | Linear-level Lasserre gaps for random `k`-CSPs, including XOR-implied predicates. | This uses a semidefinite moment hierarchy and random CSP instances. The RM result uses rational local tables supported on exact code projections and does not import a Lasserre lower-bound theorem. |
| [Barak et al. (2011)](https://eccc.weizmann.ac.il/report/2011/142/) | Reed--Muller and local-testability machinery in long-code compression and very high-round SDP plus Sherali--Adams gaps for Unique Games. | The construction, objective, and conclusion are different: the repository studies a pinned codeword weight in `L_k(C)`, not a Unique Games gap or a local tester. This source is a stronger neighboring hierarchy result, not a direct proof or disproof of the finite `31/5` value. |
| [Puchert--Tillmann (2020)](https://arxiv.org/abs/2004.03387) | Exact separation for forbidden-set cuts from redundant parity checks. | The all-dual experiment is positioned against this parity-polytope literature. The RM local tables add exact projection support and overlap equations; no novelty claim is made for the redundant-check mechanism. |
| [Feldman--Wainwright--Karger (2005)](https://research.google/pubs/using-linear-programming-to-decode-binary-linear-codes/), [published paper](https://doi.org/10.1109/TIT.2004.842696) | LP decoding of binary linear codes, using parity-check relaxations and pseudocodewords. | This is an established comparison for parity-only relaxations. The repository's pinned objective and mutually consistent tables supported on exact global projections require their own model comparison; a shared use of the term fractional distance does not identify the polytopes or normalizations. |
| [Ghazi--Lee, Theorem 1](https://arxiv.org/html/1410.4241) | For a random `(d_v,d_c)`-LDPC code with `d_c>=5`, some linear number `eta n` of SA rounds admits, with high probability, fractional value `1/(d_c-3)` for odd `d_c` or `1/(d_c-4)` for even `d_c`, under their decoding normalization. | This is a growing-round result for a random ensemble and its decoding formulation. It does not supply the deterministic RM2 fixed-locality formulas. The repository's configuration-SA identification is for its declared exact-projection CSP, not an automatic identification with this sparse parity-check presentation. |
| [Cameron--Kusuma--Solé, introduction and Theorem 3.1](https://arxiv.org/pdf/1510.01509) | Restates Delsarte's field result and extends it to finite commutative rings: orthogonal-array strength of a linear code is dual minimum Hamming weight minus one. | For RM2's dual distance eight, uniformly sampling the code gives uniform projections through seven coordinates; conditioning one coordinate leaves uniformity on six others. This explains a projection mechanism, but not the biased rank moments with singleton `1/5` or `7/31`, nor their optimality. |
| [Brändén--Leite, Section 7.1, Theorem 7.7](https://arxiv.org/html/2412.06595v3) | Restates Crapo--Rota, Chapter 16, Theorem 1: characteristic-polynomial evaluations count linear maps whose kernels avoid a represented matroid; contraction gives prescribed flat intersections. Their Theorems 7.5 and 7.8 concern nonnegative characteristic-polynomial decompositions. | This is the closest method-level bridge to the rank moments and Möbius atom formulas. It is not a cited theorem asserting positivity of these virtual moments above the virtual ambient rank, or asserting the pinned RM2 local-LP optimum. |
| [Coregliano--Jeronimo--Jones](https://arxiv.org/abs/2112.09221) | A higher-order Krawtchouk/MacWilliams LP hierarchy retrieves the largest possible linear-code size at given blocklength and distance by level `O(n^2)`; its levels incorporate interactions among codewords. | The optimized object is code size over a class of codes, not the minimum pinned weight in one specified RM code. Codeword-tuple level and coordinate locality are different parameters. Completeness of that hierarchy supplies neither a decoder nor the present fixed-code optimum. |

The repository has not found a cited theorem in this ledger that states the
exact reduced value `31/5` (total pinned weight `36/5`) for the same pinned `RM(2,5)` level-eight projection-marginal
polytope. That is a bounded search status, not a novelty proof: a publication
claim still requires a systematic literature search and an expert comparison.

The 20 October 2026 all-`m` theorem does not change that acceptance rule. Its
mathematical review checks the proof, while novelty of the exact family
formula remains `UNKNOWN`. The standard dual-code and affine-flat facts are
inherited; the cited finite identity is an explicit dependency. Reproducing
the affine LP search establishes provenance for a new run, not priority for
the finite optimum or the family theorem.

## The precise subspace-counting bridge

Write \({D\brack2}_2=(2^D-1)(2^D-2)/6\). For a uniform
codimension-two subspace \(U\) of \(\mathbb F_2^D\) and a specified
rank-\(r\) subspace \(A\), ordinary subspace counting gives
\[
 \Pr[A\subseteq U]=\frac{ {D-r\brack2}_2 }{ {D\brack2}_2 },
\]
where the numerator is zero when \(D-r<2\). The repository's level-eight
numerators are \((35,7,1,0,\ldots)\) at \(D=4\), and its level-nine
numerators are \((155,35,7,1,0,\ldots)\) at \(D=5\).
For any scope with span dimension at most \(D\), this is an actual
probability distribution. The codimension-two indicator is a degree-at-most-two
Boolean polynomial with value one at zero, supplying the required pinned
RM2 projection support.

If \(B\) is closed in the binary matroid on a scope \(S\), grouping
inclusion-exclusion by closed sets expresses its atom as
\[
 \mu_S(B)=
 \frac{1}{ {D\brack2}_2 }
 \sum_{\substack{F\text{ closed in }S\\B\subseteq F}}
 \mu_{\mathrm{flats}}(B,F)\,{D-\operatorname{rank}(F)\brack2}_2 .
\]
A nonclosed atom is zero by pairing terms whose added point is already
in the span. This is the standard connection between subspace avoidance
and matroid Möbius inversion. The source statement most directly verified
in this comparison is the [Crapo--Rota theorem reproduced as Theorem 7.7
by Brändén--Leite](https://arxiv.org/html/2412.06595v3); the Gaussian
conditioning formula above explicitly spells out the connection used here.

The essential limitation is the rank hypothesis. When
\(\operatorname{rank}(S)>D\), the repository defines formal moments by
the same rank rule, but there is no embedding of the scope span into
\(\mathbb F_2^D\). The classical counting interpretation alone therefore
does not prove positivity. The separate eight- and nine-scope arguments
are necessary. Indeed, the [ten-coordinate control](RM2_LEVEL10_CONTROL.md)
has a formal level-nine atom of mass \(-1/155\), disproving unrestricted
extension of those moments.

The focused primary-source comparison establishes that the counting,
orthogonal-array, LP, and hierarchy mechanisms are inherited. It has not
established a direct prior theorem with the same model and exact family
values. This is a bounded search outcome, not evidence of priority;
novelty of the scoped optimization statements remains **UNKNOWN**.

## Level-ten follow-up: exact lower bound, open optimum

The new control uses ten nonpin coordinates in a six-dimensional span.
Its assignment-wise Boolean inequality gives
\(C=q-8r+28v\ge0\). A nonnegative combination with the existing level-nine
identity proves
\[
 p\ge\frac{644}{2849}>\frac7{31}\qquad(m\ge6).
\]
The row coefficients, all 1,024 Boolean assignments, the equality-face
obstruction, and exact row implication from independently rebuilt atom
incidences are checked by [seven tests](test_rm2_level10_control.py).
The independent mathematical audit found no correction. These are
written mathematics and finite exact controls, not formal verification.
The subsequent [virtual-dimension theorem](REED_MULLER_VIRTUAL_DIMENSION_THEOREM.md)
proves the D6 witness feasible, with singleton `5/21`, and generalizes it
to every `D>=3`. The proof is self-contained after the standard RM parameters:
conditioning handles nonempty atoms, a relation-space expansion handles the
empty atom, and self-orthogonality establishes pinned projection support.
The same moments fail explicitly at `D+5` while working through `D+4`.
This is a proved boundary for that construction, not an exact LP-optimum law.
The full level-ten optimum remains open.

The [subsequent selected-scope certificate](level10_exploration/REPORT.md)
strengthens the lower bound to `p>=3843/16627` for all `m>=6`.
Its 79-variable, 104-row model has matching exact primal/dual witnesses,
but only the dual lower bound transports to the full relaxation. The
independent D6 construction supplies `p<=5/21`. The original single
Bonferroni-row model is retained at exact optimum `92/407`; obtaining a
larger lower bound required actual additional marginal constraints.

Taking `D=m-1` proves nonintegrality at locality `m+3` for `RM(2,m)`, `m>=4`.
The exhibited multiplicative gap tends to one in this growing-locality
regime. The bounded literature comparison has not established priority for
this parameterized construction or its exact first-failure boundary.

## Exact comparison with locally explainable non-signaling code functions

[Chiesa, Manohar and Shinkar, *On Local Testability in the Non-Signaling
Setting*](https://eccc.weizmann.ac.il/report/2019/070/download/) (May 2019),
Definition 1.1 and Definition 5.5, already define consistent local
distributions supported on code projections. Lemma 5.6 identifies projection
support with satisfaction of every dual constraint supported inside the scope.
Thus this model architecture is inherited, not a new relaxation concept.

Here is the exact change of coordinates for this repository's pin. Write
`K={c restricted to nonpin coordinates: c in RM(2,m), c_0=0}`.
The constant-one codeword shows that the pinned relation is `1+K`.
Replacing every local bit `x_a` by `y_a=1+x_a` over GF(2) is a bijection
between `L_k` and their `(K,k)`-explainable `k`-non-signaling functions.
Pin-containing tables are determined by the nonpin tables because the pin
is deterministic. The objective becomes `(2^m-1)-sum_a E[y_a]`.

The comparison identifies definitions exactly. It does not attribute the
specific rank-moment construction, its sharp locality boundary, or the
finite optimal fractions to that paper. Whether those statements follow
from existing results remains a separate novelty question.
