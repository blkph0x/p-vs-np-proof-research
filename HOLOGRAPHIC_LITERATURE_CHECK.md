# Primary sources and boundaries for the holographic phase

Checked 18 October 2026, Australia/Sydney. These are established methods and
necessary conditions; this project claims no novelty or complete classification.

- Cai, Guo and Williams, [Holographic Algorithms Beyond Matchgates](https://arxiv.org/pdf/1307.7430),
  version 2, January 2018: Sections 2.1-2.2 define ordered signature networks
  and opposite row/column basis transformations preserving their contraction.
  Definition 2.4 includes affine support with quadratic phases; Definition 2.5
  defines product-type factors. Both classes admit general-graph evaluation.
  Our implementation tests a rational, real signed affine subclass. It does
  not implement the paper's full complex-basis discovery algorithm or claim
  that rejection of our subclass establishes rejection of all tractable classes.

- Cai and Gorenstein, [Matchgates Revisited](https://arxiv.org/html/1303.6729),
  version 2, March 2013: the definitions require cyclically ordered exterior
  ports in a plane graph. Theorem 1 gives necessary matchgate identities.
  Figure 6 gives a signed crossing with one negative entry. Its six-vertex
  graph was inspected on PDF page 17, then independently enumerated for all
  boundary deletions. This source supports the parity and crossing identities;
  our proposed simultaneous-basis obstruction is instead proved by explicit
  polynomial calculations in its own lab. The source's full characterization
  is not required by that obstruction.

- Cai and Lu, [Erratum to: Signature Theory in Holographic Algorithms](https://link.springer.com/article/10.1007/s00453-015-0090-y),
  published online November 2015, Algorithmica 74 (2016), 1473-1476: the original
  Theorem 6.2 has an erroneous necessity direction. The original signature-theory
  paper remains a useful lead, but the unchecked version named in the preceding
  research brief must not be used to justify a necessity claim. This phase
  avoids that theorem entirely. The publisher page confirms the erratum record;
  the authors' erratum text identifies the affected direction.

The project distinguishes algebraic evaluation, ordinary nonnegative counts,
matching existence and SAT decision. Signed sums may cancel. Exact basis
invariance protects the original count only if all tensors and all shared
edges are transformed consistently and the entire contraction is evaluated.
Finite tests do not establish polynomial cost. The lab theorems state where
tables or contractions remain exponential and where a proved polynomial
algorithm actually applies.
