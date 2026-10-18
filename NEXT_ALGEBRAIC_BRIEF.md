# Next investigation: compressed products and exact coefficient queries

The previous goal turn made concrete progress: it preserved correct general
SAT encodings into simultaneous-bound and exact binary-weight matching,
proved which simpler replacements lose correctness, and saved independently
replayed tests and original inputs. P versus NP remains unresolved.

For the disjoint four-cycle encoding, let (a_i,b_i) be its two matching weights.
The generating polynomial is

    P(z) = product_i (z^(a_i) + z^(b_i)).

It has a polynomial-size product description with binary exponents. The
coefficient of z^W is positive iff a matching has exact total weight W.
The coefficients are nonnegative counts, so there is no cancellation. This
query includes SAT via the checked packing reduction. The degree can be
exponential in the input bit length, despite the compact product, while
every coefficient itself is at most 2^q and has only q+1 bits.

Investigate coefficient isolation rather than confuse it with polynomial
identity testing: the whole product is nonzero regardless of whether one
chosen coefficient vanishes. Evaluating at a large integer base can pack
coefficients into digits, but the resulting integer has roughly degree times
base-bitlength bits. Modular exponentiation avoids that huge integer but does
not automatically isolate one coefficient. Prove the exact algebra, numerical
bit costs and any probabilistic guarantee before presenting an algorithm.

## A concrete modular false-positive control

The saved 16-vertex gap example has

    P(z) = (z + z^6) (1 + z^36)^3,   target W=36.

Its support is {1,6,37,42,73,78,109,114}, so [z^36]P=0. Nevertheless, testing
attainability of the target residue separately modulo 2,3,5,7 all succeeds:
cost6 witnesses the first two and cost1 witnesses the last two. Their product
210 exceeds the whole cost range. This does not contradict the Chinese
remainder theorem: each residue test can choose a different matching. One
common matching obeying all four residues would have weight36 and does not
exist. Save explicit witnesses and test this quantifier issue next.

Reducing P modulo z^M-1 folds coefficients by exponent residue. A root-of-unity
filter has the same aliasing unless the modulus/order and evaluation scheme
are justified. Requiring an order larger than the degree and enumerating all
its evaluations can reintroduce exponential work. Do not assert that no
better algebraic method exists: test the concrete proposal and charge its
actual operations and bit lengths.

Candidate work: implement independent sparse-polynomial, bounded modular and
exact coefficient controls for this family; prove/review the aliasing identity
and the distinction between separate and simultaneous residue witnesses.
Then assess whether any proposed compression provides a genuinely polynomial
exact query, rather than a short representation with an expensive query.
Avoid revisiting already excluded same-coordinate or pure linear auxiliary
coverage claims. No new proof of P=NP or P!=NP is assumed.
