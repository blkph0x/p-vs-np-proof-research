# Novelty ledger and comparison boundary

This ledger prevents a finite certificate from being promoted to a new
complexity-theory theorem before the relevant literature has been compared.
It records what the repository uses, what is inherited, and what remains an
open novelty question.

| Repository component | Closest established result or tool | Status of the claim here |
| --- | --- | --- |
| `RM(s,2s+1)` self-duality, distance, and short-support projections | Reed--Muller parameter identities and the standard dual-distance projection/orthogonal-array observation | **Inherited mechanism.** The repository proves and replays the stated finite family; no novelty claim is made for the dual-distance implication itself. |
| Projection-marginal LP `L_k(C)` | Local consistency and marginal relaxations; named Sherali--Adams/Lasserre systems | **Formulation-specific.** The repository defines this exact relation-family polytope and proves monotonicity and exactness at `k=n`. It does not claim automatic equivalence to Sherali--Adams or Lasserre. |
| Exact RM(2,5) value `31/5` | Coding-theory and hierarchy gap results, including stronger asymptotic lower bounds for other models | **Finite certificate.** Whether this exact quotient value is new is an open literature-comparison task. The result is not advertised as a new asymptotic hierarchy theorem. |
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

