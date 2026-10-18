# Primary-source check for the coefficient investigation

Checked 17 October 2026 UTC. This is a scope check, not an independent proof
of the cited papers. No result below is claimed as a discovery of this project.

The current numerical-parameter algorithms are substantially stronger than
our deliberately simple certificate-producing controls. Timothy Chan's
[Derandomizing Pseudopolynomial Algorithms for Subset Sum](https://arxiv.org/html/2601.01390v1)
states a deterministic near-linear bound in the numerical target, and also
derandomizes output-sensitive bounds. The paper's Section 2 constructs halvers
using canonical small subsets and combines clipped sumsets. This still
charges numerical target or output size. It does not supply a bound polynomial
in their binary bit lengths. Our interval controls are not advertised as
improving the paper's general worst-case bounds.

Ce Jin and Xiao Mao's recent
[Subset Sum in Almost-Linear Time](https://arxiv.org/pdf/2610.20742)
states O(n+Delta^(1+o(1))) time, with Delta the maximum numerical item weight.
Theorem 1.1 also treats bounded integer variables and specifies a word-RAM
model with words of Theta(log(n U Delta)) bits. Its source page lists
14 October 2026 submission; the PDF title page is dated 16 October 2026.
We inspected the abstract, input definition and theorem, not all 83 pages
of proof. Inference for this project: the bound can still be exponential
on our base-six SAT weights; small binary encoding alone does not make Delta
small. The paper's additive structure and geometric decomposition may guide
a future representation experiment, but have not been implemented here.

A search also returned an apparently promising small-space result whose
current primary record says it was **withdrawn**. Thejas Radhika Sajith's
[Subset Sum in Near-Linear Pseudopolynomial Time and Polynomial Space](https://arxiv.org/abs/2508.04726)
was withdrawn in version 3 on 25 October 2025. The stated problem concerns
an unjustified degree bound or degree conversion at FFT leaf computations.
Old search abstracts do not show that limitation consistently. We do not
rely on the withdrawn randomized claim. This is directly relevant to our
requirement to charge polynomial degree and arithmetic size explicitly.

All three references concern algorithms or their limitations, not an
unconditional resolution of P versus NP. Conditional lower bounds mentioned
in those papers must not be treated as proved separations of complexity classes.
