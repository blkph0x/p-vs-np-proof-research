# Exact coefficient queries retain NP-hardness

Consider the decision problem

\[
  \textsf{BINOMIAL-COEFFICIENT}:
  \quad [z^W]\prod_{i=1}^m (z^{a_i}+z^{b_i})>0,
\]

where all exponents and `W` are nonnegative integers written in binary. A
choice of one term from every factor is a polynomial-size certificate: add the
chosen exponents and compare with `W`. Thus the problem is in NP.

## Parsimonious reduction from X3C

Let an explicit X3C instance have universe `U={0,...,n-1}`, `n=3k`, and
triples `T_1,...,T_m`. Set `B=m+1`, define

\[
 e_i=\sum_{u\in T_i}B^u,\qquad W=\sum_{u=0}^{n-1}B^u,
\]

and output the product

\[
 P(z)=\prod_{i=1}^m(1+z^{e_i}).
\]

For a selected subfamily `S`, let `c_u` be the ordinary number of selected
triples containing `u`. Each `c_u` is at most `m=B-1`, so adding the encoded
exponents creates no carries in base `B`. Therefore

\[
 \sum_{i\in S}e_i=W
 \quad\Longleftrightarrow\quad
 c_u=1\text{ for every }u
 \quad\Longleftrightarrow\quad S\text{ is an exact cover}.
\]

Every subfamily contributes one monomial, so the target coefficient is exactly
the number of exact covers. The reduction is parsimonious, and the decision
version is NP-complete. The counting version is #P-hard (and lies in #P under
the natural choice-counting representation), by the corresponding standard
counting X3C result.

The largest exponent has `O(n log(m+1))` bits. Under the usual explicit X3C
encoding this is polynomial in the input length; the construction itself is
therefore polynomial-time and polynomial-size. The restricted output already
has `a_i=0`, and each nonzero exponent is the sum of exactly three base powers.

## What this does and does not establish

The product is a short representation of an exponentially large coefficient
table. The theorem says that an exact polynomial-time method for isolating one
coefficient of every such product would imply `P=NP`; an exact counting method
would imply `FP=#P`. It does not rule out algorithms using a different
representation, approximation, promises, cancellations with a separately
proved isolation argument, or a direct SAT algorithm. It also does not prove
`P\ne NP`.

## Reproducible checks

`test_coefficient_complexity_barrier.py` exhausts all 256 families of the
complete `2x2x2` tripartite universe, checks every contained subfamily, tests
duplicate and malformed factors, and verifies the coefficient bit bound.
`coefficient_complexity_review.py` repeats the reduction with independent
base-digit arithmetic and additional seeded families while checking that the
source remains unchanged.

