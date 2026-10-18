# Homogeneous minimum distance: established literature boundary

This note records the exact scope of the established coding-theory result that
the project must not re-prove incorrectly.

## Primary source

Alexander Vardy, *Algorithmic Complexity in Coding Theory and the Minimum
Distance Problem*, STOC 1997, DOI [10.1145/258533.258559](https://doi.org/10.1145/258533.258559),
[author PDF](https://www.researchgate.net/profile/Alexander-Vardy/publication/221591825_Algorithmic_Complexity_in_Coding_Theory_and_the_Minimum_Distance_Problem/links/00463517a8f459b272000000/Algorithmic-Complexity-in-Coding-Theory-and-the-Minimum-Distance-Problem.pdf).

The paper defines `MINIMUM DISTANCE` as follows (Section 3, p. 7): given a
binary parity-check matrix `H` and `w>0`, ask whether there is a **nonzero**
binary vector `z` with `Hz^T=0` and `wt(z)<=w`. It then states that its main
polynomial transformation from maximum-likelihood decoding establishes
NP-completeness of this decision problem (Section 3.3, p. 11). This is the
homogeneous kernel problem, not an affine nonzero-syndrome instance.

The paper's construction is not the degree-three X3C encoding used in this
checkpoint. It passes through finite-field subset sum, finite-field code
constructions, and a binary concatenation; therefore it does not imply that
the homogeneous problem remains NP-hard under the project's column-weight-three
promise. That restricted claim remains unproved here.

## Boundary that remains open

The same source explicitly distinguishes bounded-distance decoding: the input
includes a distance promise on every small set of columns, and the paper states
that NP-hardness for that promise problem remains open. Thus the following
implications are invalid:

* affine decoding hardness automatically implies homogeneous minimum-distance
  hardness under the same sparse promise;
* homogeneous minimum-distance NP-completeness automatically proves `P!=NP`;
* Vardy's theorem settles bounded-distance decoding.

The project now has both the self-contained affine degree-three theorem and
this source-bound homogeneous reference. They answer different questions and
are kept separate in the reports.

## Reproducibility record

The claims above are a scope audit of the cited primary paper, not a new
complexity theorem or a formalization of Vardy's full reduction. The relevant
problem statement and theorem locations are fixed by the cited PDF; the
project's independent finite checks apply only to its own affine reduction.

