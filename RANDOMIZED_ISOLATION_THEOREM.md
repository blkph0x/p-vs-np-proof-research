# Random affine isolation: a conditional bridge, not a P=NP algorithm

Let `S` be a nonempty set of Boolean assignments on `n` variables, with
`s=|S|`. Choose an `r` by `n` binary matrix `A` uniformly and a target
`b` uniformly in `F_2^r`. Retain `x` exactly when `Ax=b`.

For distinct assignments `x,y`, the pair `(Ax,Ay)` is uniform on
`F_2^r x F_2^r`: each row acts on the nonzero difference `x+y` as a fair bit,
independently across rows. Therefore, with `X=|{x in S: Ax=b}|`,

\[
  \mathbb E[X]=\mu=s/2^r,
  \qquad
  \mathbb E[X(X-1)]=s(s-1)/2^{2r}\le\mu^2.
\]

For every nonnegative integer `X`,
`1_{X=1} >= X-X(X-1)`. Hence

\[
  \Pr[X=1]\ge\mu-\mu^2.
\]

Take `r=ceil(log_2 s)+1`. Then `1/4 <= mu <= 1/2`, so a single random affine
hash isolates exactly one member of `S` with probability at least `3/16`.
Repeating independent hashes drives the failure probability down
geometrically. The proof is all-size and uses the complete uniform matrix
family, not a finite experiment.

Applied to a CNF, the surviving assignments are precisely the models of the
CNF conjoined with the generated XOR equations. This gives a randomized
reduction from SAT to unique-SAT-with-XOR: if a polynomial-time unique solver
accepted whenever a unique model exists, repeating over the possible ranks and
hashes would yield an RP procedure for SAT. That conditional consequence is a
complexity boundary, not a solver for unrestricted SAT. The missing ingredient
is still a polynomial unique-SAT/XOR algorithm.

## Scope and controls

The implementation represents every row as an `n`-bit mask and evaluates the
original CNF independently before applying the hash. It exhaustively checks
small hash families, exact probabilities, the second-moment inequality,
unique-survivor decoding, contradictory and tautological clauses, and malformed
inputs. The independent replay uses separate direct parity arithmetic and
records source hashes. No finite experiment is used as the all-size proof.

