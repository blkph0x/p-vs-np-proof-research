# Next investigation: exact basis changes and jointly tractable tensors

The preceding turn made concrete progress: exact coefficient algorithms,
independently replayed proofs, explicit arithmetic controls and an actual
same-input improvement. P versus NP remains unresolved and the full goal
remains active. The latest report is ALGEBRAIC_PHASE_REPORT.md.

We now have two equivalent general SAT encodings worth keeping intact:
ordinary Boolean OR clauses with shared equality variables, and the packed
coefficient's local factors f=[0,1,2,1] for a ternary clause (indexed by its
number of true literals). The latter sums slack multiplicities and has the
same positivity decision, but a different count. Neither may be substituted
for the other without explicitly proving the operation being preserved.

Investigate exact tensor basis changes as a possible way to exploit
cancellation and jointly tractable signatures beyond the positive table
representations already tested. On a bipartite incidence network, use a
consistent convention: row tensors transform by T tensor powers and column
tensors by inverse T tensor powers, so every contracted edge cancels T with
its inverse. Verify that identity on original small formulas, including
shared variables, every literal polarity, repeated clauses and contradictory
units. Rational matrices permit exact initial experiments; any restriction
to rational coefficients must not become an unproved statement over complex
bases. All matrix inverses and denominator growth must be charged.

Primary starting references:

- Cai and Lu, [Signature Theory in Holographic Algorithms](https://pages.cs.wisc.edu/~jyc/papers/signature-thy.pdf):
  parity conditions, matchgate identities, and simultaneous basis admissibility.
- Cai and Lu, [Holographic Algorithms: From Art to Science](https://www.sciencedirect.com/science/article/pii/S0022000010000899):
  simultaneous realizability and algorithms for symmetric signatures.
- Cai, Guo and Williams, [Holographic Algorithms Beyond Matchgates](https://arxiv.org/abs/1307.7430):
  other tractable target families and checked transformations.

Read the actual definitions before implementing; conventions and cyclic
port order matter. No theorem from those papers has yet been independently
reproved or applied to this project's signatures. Search snippets are leads,
not certificates, and a prior characterization may settle a proposed search
without inventing a new result.

Useful concrete tasks: derive the exact small polynomial equations for one
common invertible two-by-two basis to transform the required copy/OR or
copy/slack-factor signatures; preserve every gate type and polarity in the
test. Encode invertibility explicitly, e.g. auxiliary u with u det(T)=1.
A finite grid search can discover candidates but cannot prove nonexistence.
An exact algebraic obstruction needs a checkable identity or independently
verified polynomial-ideal certificate and a precise field/model scope.
Try positive signatures that really are jointly realizable as controls.

Even a valid local matchgate realization does not solve arbitrary networks:
identify the global graph restrictions of the claimed evaluator. Planar
perfect-matching counting, general matching existence, minimum cost and
signed partition-function evaluation are different problems. A proposed
crossing gadget must preserve its full boundary tensor and ordered ports;
a sign-changing crossing is not the ordinary logical crossing unless the
global signs are proved harmless. Signed cancellations can erase witnesses,
so a zero partition value needs the original-count preservation argument.

The desired outcome is a genuine exact algorithmic advance with a complete
scope and cost proof, or a precise rejection of a concrete proposed route.
Do not claim a general P!=NP consequence from a restricted basis obstruction.
Do not declare a P=NP algorithm based only on individually transformed gates,
a finite successful batch, a modular count, or an uncharged tensor contraction.
Keep the original general SAT decision task as the objective.
