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
| [Haken, *The intractability of resolution*](https://www.sciencedirect.com/science/article/pii/0304397585901446) | Primary resolution lower-bound source for the pigeonhole principle; the finite CDCL traces here are a replayable experimental connection, not a reproof of Haken's all-size theorem. |
| [Ben-Sasson and Wigderson, *Short proofs are narrow—resolution made simple*](https://people.inf.ethz.ch/emo/SatSem05/Papers/BensassonWidgerson01.pdf) | Primary width-versus-size proof-complexity source motivating the separate bounded-width closure and scaling records. |
| [Atserias and Dalmau, *A Combinatorial Characterization of Resolution Width*](https://www.cs.upc.edu/~atserias/papers/width/ccc03.pdf) | Primary source for the Boolean existential pebble-game characterization used to certify the finite PHP(5,4) width bridge. The repository replays the finite game; it does not claim an all-size new theorem. |
| [Dantchev, *On Resolution Complexity of Matching Principles*](https://www.brics.dk/DS/02/2/BRICS-DS-02-2.pdf) | Primary source for Proposition 4.1, the explicit all-size width-`n`, `2^{O(n log n)}` resolution construction for ordinary PHP(n+1,n), which is independently generated and replayed in `resolution_width_lab`. |
| [Proof Complexity Zoo](https://proofcomplexityzoo.gitlab.io/zoo/) | Public map of proof systems and simulations used as a literature boundary in the peer-audit response; it is not treated as a certificate source. |
| [SAT Competition](https://satcompetition.github.io/) | Public context for industrial SAT solving and benchmark evaluation; a competition result is not a complexity classification. |
| [DRAT-trim](https://github.com/marijnheule/drat-trim) and [cake_lpr](https://github.com/marijnheule/cake_lpr) | Public formula-level proof checking tools cited in the peer-audit comparison; they are not imported as proof of the quotient certificates here. |
| [Sherali and Adams, *A hierarchy of relaxations and convex hull characterizations*](https://doi.org/10.1016/0166-218X(92)00190-W) | Primary hierarchy source used to position the exact finite local-marginal cuts; this repository does not claim a new all-size hierarchy theorem. |
| [Schoenebeck, *Linear level Lasserre lower bounds for certain k-CSPs*](https://schoeneb.people.si.umich.edu/papers/LasserreNew.pdf) | Primary hierarchy lower-bound source used to distinguish the stronger academic theorem from the finite RM(2,5) certificate. |
| [Barak et al., *Making the long code shorter, with applications to the Unique Games Conjecture*](https://eccc.weizmann.ac.il/report/2011/142/) | Primary code-based local-testability and high-round SDP plus Sherali--Adams comparison source in the Reed--Muller novelty ledger; its Unique Games construction is a neighboring theorem, not the pinned local-marginal model. |
| [Cai, Guo and Williams, *A note on the complexity of counting perfect matchings*](https://arxiv.org/abs/1307.7430) | Matchgate/holographic basis and product-type obstruction context. The exact theorem used here is cited in `simultaneous_basis_lab/THEOREM.md`. |
| [Jia et al., *The minimum distance problem for regular LDPC codes is NP-complete*](https://arxiv.org/abs/2606.23161) | Current preprint used for the regular-LDPC boundary audit; the finite replays do not replace its all-size proof. |
| [Reed, *A class of multiple-error-correcting codes and the decoding scheme*](https://doi.org/10.1109/TIT.1954.1057465) | Original Reed--Muller construction; the explicit RM(s,2s+1) local-marginal certificate proves the parameter identities used in this repository. |
| [Schaefer, *The complexity of satisfiability problems*](https://www.khoury.northeastern.edu/home/lieber/courses/csg260/f06/materials/papers/max-sat/p216-schaefer.pdf) | Lemma 3.1A, ternary XOR closure of affine relations. The affine-projection theorem reproduces the short proof and adds explicit nonemptiness. |
| [Hemaspaandra, *Dichotomy Theorems for Alternation-Bounded Quantified Boolean Formulas*](https://arxiv.org/pdf/cs/0406006) | Section 2.3 supplies the quantified 3CNF completeness basis for the affine-projection classification. |
| [Creignou, *Complexity versus stability for classes of propositional formulas*](https://www.sciencedirect.com/science/article/pii/S002001909800163X) | Publisher abstract establishes prior coNP-completeness of ordinary CNF equivalence to XOR-CNF. The affine-projection note explicitly distinguishes existential projection and the empty-relation convention. |
| [Boehler, Creignou, Reith and Vollmer, *Playing with Boolean Blocks, Part II*](https://www.researchgate.net/publication/237654012_Playing_with_Boolean_Blocks_Part_II_Constraint_Satisfaction_Problems1) | Author-uploaded primary text, Definition 3.1 and Theorem 3.4: semantic co-clone recognition for ordinary formulas. This is not a claim that the projected-CNF classification is new. |
| [MIT OpenCourseWare, *Essential Coding Theory, Lecture 5*](https://ocw.mit.edu/courses/6-895-essential-coding-theory-fall-2004/resources/lect05slx4/) | Independent public coding-theory reference for Reed--Muller construction and distance context. |
| [Vohra, *The Vohra Duality: A Polynomial-Time Algebraic Framework Proving P=NP*](https://doi.org/10.1109/ASSIC70037.2026.11717448) | Public claim logged for audit only. The paper was not available in full through the access paths checked, so the claim remains unverified. |

The repository also preserves the source links for coding theory, holographic
algorithms, LP decoding, matroid theory, graph algorithms, and related ideas in
the individual reports. A citation is evidence of provenance, not evidence
that the cited claim is correct or that it proves P versus NP.

## Citation rules for new work

The [exact LP discovery integration](local_marginal_code_lab/EXACT_LP_DISCOVERY.md)
uses [SoPlex's exact-mode configuration](https://soplex.zib.de/doc/html/EXACT.php)
and credits Gleixner, Steffy and Wolter's
[iterative-refinement method](https://optimization-online.org/wp-content/uploads/2015/06/4948.pdf)
and Gleixner and Steffy's
[limited-precision-oracle framework](https://arxiv.org/abs/1912.12820).
The [official 10.1.0 suite release](https://github.com/scipopt/scip/releases/tag/v10.1.0)
provides the measured SoPlex 8.1.0 Windows binary. Exact search is borrowed
engineering; it is not claimed as a new optimization algorithm.

The [quadratic RM level-eight proof](local_marginal_code_lab/REED_MULLER_QUADRATIC_LEVEL8_THEOREM.md)
uses the standard duality, distance and affine-flat minimum-check facts stated
by Santi, Häger and Pfister in
[Decoding Reed–Muller Codes Using Minimum-Weight Parity Checks](https://doi.org/10.1109/ISIT.2018.8437637).
The exact optimization formula's novelty remains unestablished.

The [public-method comparison](PUBLIC_METHOD_REVIEW.md) adds primary sources
for CaDiCaL/CryptoMiniSat and proof formats; D4/CPOG and projected certified
compilation; DPMC, htd and cotengra; CMR and LEMON; exact LP backends and GAP;
FLINT, subset-sum and certified approximate counting; and benchmark practices.
Each comparison states the matching input/output contract and an adoption
test. These tools have not all been installed or benchmarked here.

The [affine-hull experiment](affine_projection_recognition_lab/AFFINE_HULL_METHOD.md)
specializes Reps--Sagiv--Yorsh's best-abstraction algorithm and cites Boolean
affine-envelope work. Its algorithmic provenance is explicit; no novelty is
claimed for the model-outside-current-hull loop.

1. Name the original or primary public source near the first use of an idea.
2. State whether the source is a theorem, a preprint, an abstract, or an
   unverified public claim.
3. Separate a finite replay from the source's all-size assertion.
4. Add the report and checker to [`METHOD_INDEX.md`](METHOD_INDEX.md).
5. Regenerate [`PUBLIC_SOURCES.md`](PUBLIC_SOURCES.md) and
   [`REPOSITORY_MANIFEST.json`](REPOSITORY_MANIFEST.json) before committing.
