# Public sources and citation policy

Every external idea used by this project must have a stable public citation in
the report that uses it. This file records the primary sources that anchor the
project-wide claims; [`PUBLIC_SOURCES.md`](PUBLIC_SOURCES.md) is generated from
all source, report, and artifact files and lists every URL found with its local
provenance.

| Source | Use in this repository |
| --- | --- |
| [Clay Mathematics Institute: P versus NP](https://www.claymath.org/millennium/p-vs-np/) | Official problem statement and current public status. |
| [Cook, *The complexity of theorem-proving procedures*](https://doi.org/10.1007/BF00264290) | NP-completeness context and SAT as the canonical target. |
| [Cai, Guo and Williams, *A note on the complexity of counting perfect matchings*](https://arxiv.org/abs/1307.7430) | Matchgate/holographic basis and product-type obstruction context. The exact theorem used here is cited in `simultaneous_basis_lab/THEOREM.md`. |
| [Jia et al., *The minimum distance problem for regular LDPC codes is NP-complete*](https://arxiv.org/abs/2606.23161) | Current preprint used for the regular-LDPC boundary audit; the finite replays do not replace its all-size proof. |
| [Vohra, *The Vohra Duality: A Polynomial-Time Algebraic Framework Proving P=NP*](https://doi.org/10.1109/ASSIC70037.2026.11717448) | Public claim logged for audit only. The paper was not available in full through the access paths checked, so the claim remains unverified. |

The repository also preserves the source links for coding theory, holographic
algorithms, LP decoding, matroid theory, graph algorithms, and related ideas in
the individual reports. A citation is evidence of provenance, not evidence
that the cited claim is correct or that it proves P versus NP.

## Citation rules for new work

1. Name the original or primary public source near the first use of an idea.
2. State whether the source is a theorem, a preprint, an abstract, or an
   unverified public claim.
3. Separate a finite replay from the source's all-size assertion.
4. Add the report and checker to [`METHOD_INDEX.md`](METHOD_INDEX.md).
5. Regenerate [`PUBLIC_SOURCES.md`](PUBLIC_SOURCES.md) and
   [`REPOSITORY_MANIFEST.json`](REPOSITORY_MANIFEST.json) before committing.
