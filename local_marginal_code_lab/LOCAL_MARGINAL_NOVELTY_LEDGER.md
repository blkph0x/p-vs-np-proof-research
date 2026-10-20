# Novelty ledger and comparison boundary

This ledger prevents a finite certificate from being promoted to a new
complexity-theory theorem before the relevant literature has been compared.
It records what the repository uses, what is inherited, and what remains an
open novelty question.

| Repository component | Closest established result or tool | Status of the claim here |
| --- | --- | --- |
| `RM(s,2s+1)` self-duality, distance, and short-support projections | Reed--Muller parameter identities and the standard dual-distance projection/orthogonal-array observation | **Inherited mechanism.** The repository proves and replays the stated finite family, including an exact `d-1` boundary obstruction for the unit witness, the exact plain-model boundary value `1+(2^(2s+1)-1)/(2^(s+1)-1)`, and an explicit all-scope size law. The incidence count and sparse witness are recorded as a scoped formulation theorem; no novelty claim is made for the dual-distance or counting mechanisms themselves. |
| Projection-marginal LP `L_k(C)` | Local consistency and marginal relaxations; named Sherali--Adams/Lasserre systems | **Two boundaries are now explicit.** `L_k(C)` is proved identical, level by level, to configuration Sherali--Adams for the declared finite-domain CSP whose relations are the exact projections `R_S(C)`. No equivalence is claimed for a sparse Boolean parity-check encoding, and the Lasserre relationship remains formulation-specific. |
| Exact RM(2,5) reduced value `31/5` (total pinned weight `36/5`) | Coding-theory and hierarchy gap results, including stronger asymptotic lower bounds for other models | **Finite certificate.** Whether this exact quotient value is new is an open literature-comparison task. The result is not advertised as a new asymptotic hierarchy theorem. |
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
| [Sherali--Adams (1992)](https://doi.org/10.1016/0166-218X(92)00190-W) | A hierarchy for a specified linear or polynomial formulation. | The exact equality `L_k(C)=SA_k(I_k(C))` in the hierarchy note uses an extensional CSP whose relations are already the exact global projections `R_S(C)`. The repository has not proved an equality or separation for a sparse parity-check encoding. |
| [Schoenebeck (2008)](https://schoeneb.people.si.umich.edu/papers/LasserreNew.pdf) | Linear-level Lasserre gaps for random `k`-CSPs, including XOR-implied predicates. | This uses a semidefinite moment hierarchy and random CSP instances. The RM result uses rational local tables supported on exact code projections and does not import a Lasserre lower-bound theorem. |
| [Barak et al. (2011)](https://eccc.weizmann.ac.il/report/2011/142/) | Reed--Muller and local-testability machinery in long-code compression and very high-round SDP plus Sherali--Adams gaps for Unique Games. | The construction, objective, and conclusion are different: the repository studies a pinned codeword weight in `L_k(C)`, not a Unique Games gap or a local tester. This source is a stronger neighboring hierarchy result, not a direct proof or disproof of the finite `31/5` value. |
| [Puchert--Tillmann (2020)](https://arxiv.org/abs/2004.03387) | Exact separation for forbidden-set cuts from redundant parity checks. | The all-dual experiment is positioned against this parity-polytope literature. The RM local tables add exact projection support and overlap equations; no novelty claim is made for the redundant-check mechanism. |

The repository has not found a cited theorem in this ledger that states the
exact reduced value `31/5` (total pinned weight `36/5`) for the same pinned `RM(2,5)` level-eight projection-marginal
polytope. That is a bounded search status, not a novelty proof: a publication
claim still requires a systematic literature search and an expert comparison.
