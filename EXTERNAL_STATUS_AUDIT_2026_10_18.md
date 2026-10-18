# External P-versus-NP status audit

This note records a time-stamped source check performed on 18 October 2026.
It is included to prevent an unverified public claim from being mistaken for a
resolution of the problem.

## Current official status

The [Clay Mathematics Institute problem page](https://www.claymath.org/millennium/p-vs-np/)
continues to label P versus NP **Unsolved**. This is the authoritative status
used by this checkpoint.

## Recent claim located

IEEE Xplore lists *The Vohra Duality: A Polynomial-Time Algebraic Framework
Proving P=NP*, added 9 October 2026. Its abstract claims a deterministic
polynomial-time algorithm for 3-SAT using a Fourier-transformed finite-field
construction and reports empirical polynomial scaling. The abstract does not
provide the all-instance correctness proof, worst-case bit-complexity proof,
or independently checked artifact needed by the project's
`RESOLUTION_STANDARD.md`. The initial catalog view did not expose the
references, although a later IEEE HTML view and Crossref metadata made the
reference list available without exposing the paper's proof.
Accordingly, this is recorded as an **unverified claim**, not evidence that
P=NP.

The DOI metadata identifies a three-page proceedings article (pp. 1--3) and
does not expose an open full-text copy through the catalog records checked.
That makes it impossible for this checkpoint to audit the claimed transform,
its all-instance invariant, or its bit-complexity bound from the public record
alone.

The project now tests one narrow interpretation of its “low-dimensional
Fourier” premise directly. Linear-size 3-CNF families have `2^n` nonzero Walsh
coefficients, including a distinct-literal cyclic family with a unique model;
closed forms and independent exact truth-table transforms over the rationals
and tested odd prime fields are recorded in
`fourier_spectrum_boundary_lab/REPORT.md`. Characteristic two is a separate
case because normalized Walsh coefficients require division by `2^n`. This does not refute an algorithm
using a different compressed state, but any explicit low-dimensional Fourier
representation must exclude these families or provide another invariant.

The stronger cyclic construction gives one distinct-literal 3-CNF for each
assignment `t` whose satisfying set is exactly `{t}`. Its Boolean indicator is
therefore the point mass `delta_t`; the `2^n` indicators form the standard
basis of the full function space on `{0,1}^n`. This rules out a universal
exact linear state representation whose dimension stays below `2^n` for this
family, over every coefficient field. It remains a barrier for that specified
linear-state language, not a lower bound against arbitrary algorithms.

The accompanying [`FWHT_COST_REPORT.md`](fourier_spectrum_boundary_lab/FWHT_COST_REPORT.md)
checks the arithmetic cost of the transform route itself. If an algorithm
materializes all `2^n` Walsh values and then applies the full subset-Zeta
transform, the exact butterfly/addition count is `3 n 2^(n-1)`. This is a
conditional cost audit, not a lower bound against an implicit or compressed
algorithm that never materializes that table.

The project does not rely on the claim, and no conclusion changes if it is
withdrawn. Any future audit would need the full paper, a precise input model,
an all-instance proof of the transform's invariant, and an independent
polynomial bit-cost analysis.

## Follow-up access check

On 18 October 2026, Crossref metadata exposed a publisher-link entry for the
paper and recorded 15 references; the raw metadata is saved in
`VOHRA_CROSSREF_METADATA.json`. The linked staging PDF endpoint returned an
IEEE access page rather than a PDF, and the IEEE document page explicitly
reported that the PDF was unavailable without access. The public HTML exposed
the abstract, keywords and reference list, then stopped at the introduction
behind a sign-in/purchase gate. The accessible material therefore still does
not define the claimed Hamiltonian space, FWHT-Zeta invariant, or worst-case
complexity proof. This is stronger provenance for the unverified status, not
evidence for or against P=NP.

## Boundary result used by this checkpoint

Separately, Jia et al.'s 2026 preprint
([arXiv:2606.23161](https://arxiv.org/abs/2606.23161)) states NP-completeness of
homogeneous minimum distance for column weight three and for `(3,3)`-regular
Tanner graphs. The local replays in this directory audit finite gadget
instances only; they do not replace the preprint's all-size proof.

The resulting project status remains: exact polynomial algorithms are proved
for the audited degree-two code family and several other restricted classes,
but no all-SAT polynomial solver or unconditional lower bound has been found.
