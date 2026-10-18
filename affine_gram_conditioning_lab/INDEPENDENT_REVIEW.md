# Independent review of the shell conditioning example

Verdict: clean. The original support equations, coefficient signs, normalized
Gram formula and all stated scope restrictions are correct. No production
source or saved producer result was changed. This review imports no producer
functions.

Every nonzero word has exactly one first-one position, so the affine shells
partition the nonzero cube. The identity full cube minus all shells equals
the zero pin follows pointwise. Evaluation at zero and at the n coordinate
unit vectors gives the indicator matrix with first row [1,0,...,0] and other
rows [1,e_j]; its determinant is one. Thus all n+1 original indicators are
linearly independent, including at the smallest width n=1.

The normalized shell vectors are orthonormal. Their squared overlaps with
the full cube sum to 1-2^-n, giving the two nontrivial eigenvalues
1 plus/minus sqrt(1-2^-n), with n-1 further eigenvalues one. Multiplying the
two nontrivial eigenvalues gives determinant 2^-n. Rationalizing the smaller
one gives 2^-n/(1+sqrt(1-2^-n)), hence the published lower and upper bounds.
The condition number equals 2^n(1+sqrt(1-2^-n))^2 and lies between 2^n and
2^(n+2). No floating-point spectral approximation is needed.

The original coefficients are all plus/minus one. Normalizing the atoms
moves their support square roots into the coefficient vector, whose squared
Euclidean norm is 2^n + (2^n-1), while the represented target norm squared
is one. Thus exponentially poor conditioning and large normalized
coefficient energy are compatible with polynomially many explicit affine
supports and constant-bit original rational coefficients.

This refutes a universal inverse-polynomial conditioning bound for every
independent affine dictionary. The target zero pin itself has a one-piece
representation, so the example does not refute a bound restricted to minimum
decompositions of a specified target, and does not establish such a bound.
It is a limitation of a proposed inference, not a SAT or signed-rank lower
bound. The polynomial size of the indexed support descriptions is preserved.

The executable review binds the current theorem, producer, saved results and
its own sources. It independently checks all 28 original records, including
the evaluation minor at widths through 256. Through n=12 it constructs every
actual support truth vector, checks all 8,190 original words, and derives 12
integer Gram matrices directly from support intersections. Subtracting all
shell rows from the full-cube row leaves [1,0,...,0], so the determinant is
the product of shell sizes. After normalizing by the diagonal norm product,
this independently agrees with the producer's generic rational elimination.
The remaining saved elimination values through n=24 are compared with the
proved formula, not described as fresh truth-vector enumeration. Wide rows
use their actual equations and explicit independent points, not full tables.

Reproduce with `python INDEPENDENT_REVIEW.py`. The adjacent JSON contains
the exact source hashes, all 12 derived integer Gram matrices, coverage
counts and source-stability check. No claim depends on a rounded eigenvalue.
