# Exact coefficient extraction: what is compressed and what is computed

**Scope.** For P(z)=product_i(z^a_i+z^b_i), with q pairs of nonnegative binary-encoded exponents, the coefficient C_W counts choices of total W. It is an integer between zero and 2^q. The preceding packed-cost matching reduction makes positivity of this chosen coefficient an NP-complete decision problem. A compact product, a nonzero whole polynomial or a short coefficient value does not by itself provide a cheap coefficient query. This lab proves useful exact methods and identifies their costs; it makes no novelty claim and resolves neither P=NP nor P!=NP.

## 1. Exact preprocessing can materially reduce the query

Let L=sum_i min(a_i,b_i), and d_i=|a_i−b_i|. Then

    P(z)=z^L product_i(1+z^d_i).

Let z0 be the number of zero differences, and retain r=q−z0 positive differences. Their gcd is g. If W<L, W>L+sum d_i, or W−L is not divisible by g, the coefficient is zero. If every difference is zero, P is the monomial 2^q z^L, so the answer is immediate.

Otherwise divide the positive differences and offset by g. Write R(y)=product_(i=1)^r(1+y^e_i), D=sum e_i, t=(W−L)/g. Then C_W=2^z0[y^t]R. Complementing a subset proves [y^t]R=[y^(D−t)]R, so it suffices to extract h=min(t,D−t). A large absolute W can therefore become an easy small h. These are constructive arithmetic reductions in the bit size of the exponents, not assumptions that h must always be small.

## 2. Carry-free integer digits give a positive exact algorithm

Every coefficient of R is at most 2^r. Choose s=r+1 and B=2^s, strictly exceeding this bound. In the base-B representation of R(B), each coefficient occupies one digit, without carries. The target digit depends only on

    U = R(B) mod B^(h+1),
    [y^h]R = floor(U/B^h).

The floor is already the top digit because U<B^(h+1). Higher polynomial terms contribute multiples of the modulus. Factors with e_i>h may be replaced by one for this query. The implementation maintains an integer U and uses the exact recurrence

    U <- (U + (U << (s e_i))) mod 2^(s(h+1))

for each e_i<=h, starting at U=1. This is repeated multiplication by 1+B^e_i modulo the digit modulus. Returning 2^z0 times the top digit gives C_W exactly. A separate sparse dictionary recurrence, checked against independent full choice enumeration, supplies a second method.

Let N=(r+1)(h+1). The retained packed integer uses at most N bits. A shifted temporary integer can use almost 2N bits before masking; an addition is also bounded by 2N here. Several such integers may coexist. Thus the retained-bit cap is not a total process-memory cap, and auxiliary memory remains O(N) with implementation-dependent constants. With linear-time integer shifts, additions and masking, the loop uses O(rN) bit operations, plus preprocessing and the O(q)-bit output. The recorded `bit_work_proxy=rN` is an asymptotic work proxy, not a literal instruction or allocation count.

This method genuinely helps when the reduced target h is small, and packs many coefficient states into a few integer operations. It is only pseudopolynomial in h. If h is exponential in the binary input length, N is exponential too. Computing the full R(B) would retain roughly sD bits; truncating to the needed digit is a real improvement but does not remove the worst-case dependence on a numerical exponent.

For example, r=40 and differences 1,2,...,2^39 have D=2^40−1. At target h=2^39−1, the packed residue needs 41*2^39 retained bits. The bounded implementation returns UNKNOWN before allocating that integer.

This particular family is nevertheless easy by a different exact identity:

    product_(i=0)^(r−1)(1+y^(2^i)) = sum_(j=0)^(2^r−1) y^j.

Each exponent has one binary representation, proving that every coefficient in range is one. The supplied recognizer checks the complete binary-ladder shape after normalization and returns its count in polynomial bit time. This is a substantive special-case shortcut; failure of the generic packed method on it is not an inherent hardness claim.

## 3. Roots of unity compute a folded sum

Over a field with an element omega of exact multiplicative order M and invertible M, define

    F = M^(-1) sum_(j=0)^(M−1) omega^(−Wj) P(omega^j).

Expand P into its coefficients. The inner geometric sum is M when the exponent difference is divisible by M, and zero otherwise: when omega^k!=1, multiplying the sum by 1−omega^k gives 1−omega^(kM)=0, and division is valid in the field. Therefore

    F = sum_(e congruent W mod M) C_e

in that field. Over a prime field F_p this is the nonnegative folded integer sum reduced modulo p. The implementation verifies primality with a bounded exact trial check, verifies M divides p−1 and the exact order of omega, and saves every exact modular evaluation. Failure of a verification or evaluation cap returns UNKNOWN; invalid field parameters are rejected.

For 0<=W<=degree(P), the sufficient condition M>degree(P) removes exponent aliasing and yields C_W mod p. If W exceeds the degree, C_W=0 directly; a root filter may still wrap W onto a lower exponent, so its nonzero folded result must not be misreported as that coefficient. This boundary is tested explicitly.

A direct M-point implementation uses M evaluations, each with q factors. Reducing binary factor exponents and the target modulo M once is exact. Binary modular exponentiation then gives O(M (q+1) log(M+1)) field multiplications, plus input reductions and field/root validation; the added one accounts for weighting even an empty product. With schoolbook arithmetic, each multiplication costs polynomially in log p. A more efficient transform can change this operation bound, but merely saying “apply a transform” does not remove its M-sized domain. Choosing M above an exponentially large degree can reintroduce exponential work even though log M and log p are short. Finding and validating suitable primes and roots is also part of an actual algorithm; this lab takes supplied candidates and uses explicit bounded verification rather than an uncharged field-existence oracle.

### Aliasing produces false positives

The earlier gap example is P(z)=(z+z^6)(1+z^36)^3, W=36. Its support is {1,6,37,42,73,78,109,114}, so C_36=0. With M=5, the folded integer sum at residue one is C_1+C_6=2. The order-five filter over F_11 with omega=3 returns two, a positive value unrelated to target attainability.

Testing residues 2,3,5,7 separately also does not enforce one common matching. Cost six witnesses residues modulo two and three; cost one witnesses residues modulo five and seven. Every test passes and their product 210 exceeds the maximum cost 114, yet no cost equals 36. The logical form is “for every modulus there exists a choice,” whereas the Chinese remainder theorem would need one choice obeying every modulus. The saved experiment supplies those different choice vectors.

### Removing aliasing does not prevent modular cancellation

Let P(z)=(1+z)^5(1+z^2)^2. Its degree is nine and

    C_4 = binomial(5,4) + 2 binomial(5,2) + 1 = 26.

An order-twelve filter over F_13, omega=2, has no exponent aliasing, yet returns zero because 26=0 modulo 13. A positive integer count can disappear in the field. The tiny example P(z)=2, over characteristic two, does the same even without a nonconstant factor.

With no aliasing, a nonzero residue proves C_W>0. A zero residue is inconclusive unless the coefficient bound rules out a positive multiple of p. Since C_W<=2^q, p>2^q is sufficient: the residue then is the exact coefficient. Alternatively, verified residues of the same coefficient modulo pairwise coprime moduli with product greater than 2^q uniquely determine it by CRT. The control uses p=13 and p=37, both with order twelve, and reconstructs 26 from residues zero and 26; the product 481 exceeds 128.

CRT reconstruction alone does not check that supplied residues came from the original polynomial, or even from the same underlying count. `reconstruct_bounded_count` is only that arithmetic uniqueness operation. Its caller must independently establish the no-aliasing filter equations for the same original product and target. A regression deliberately supplies fabricated residues (one modulo 13 and one modulo 37): they consistently reconstruct one, which is not the actual coefficient 26. This is not a failure of CRT; it exposes the required binding premise.

There is one useful rejection even with aliasing: the entire folded integer sum is nonnegative and at most 2^q. If p>2^q and the filter returns zero, that folded sum is exactly zero, so C_W=0. A positive folded sum generally cannot certify the particular target. The implementation distinguishes an exact filter value from an exact target decision.

Conditioned on obtaining alias-free filters for uniformly chosen primes from a verified set of K distinct eligible primes, a positive coefficient at most 2^q vanishes for at most q of them: the product of q+1 distinct prime divisors would exceed 2^q. Thus the false-zero probability is at most q/K. This conditional guarantee addresses characteristic cancellation only. It does not supply eligible primes for free, remove the M evaluations, or address aliasing; no unproved randomized polynomial coefficient algorithm is asserted.

## 4. Identity testing and ordinary evaluations do not select a coefficient

Over the integers or rationals, every input factor and hence the whole product is nonzero. For P(z)=1+z, P(1)=2 and the formal polynomial is nonzero, while [z^2]P=0. A whole-product identity test answers a different question from the requested coefficient query.

Even every evaluation in a small field may be insufficient for these large-degree products. Over F_p, 1+z and 1+z^p agree at every field element, because x^p=x, but their coefficients at z^1 differ when p>1. The saved p=5 example checks all five evaluations. This is a collision of polynomial functions on that field, not equality of the two formal polynomials. Larger fields or an appropriate degree promise address that collision but do not themselves implement a selected-coefficient oracle.

## 5. Numerical shortcuts require certified precision

All executable extraction and root filters here use exact integer arithmetic. No floating-point value is treated as a proof of zero or nonzero.

For a complex root-of-unity formula, the final answer is an integer if aliasing is controlled. Rounding would be justified if a rigorous error analysis bounded the total complex error by less than one half. It is sufficient, for example, that every weighted summand have absolute error below one quarter and that summing/averaging introduce a further absolute error below one quarter: the average of the summand errors is then below one quarter, and the combined error below one half. Since summands can have magnitude 2^q, fixed relative accuracy independent of q is not enough; phase and modular-angle computations must also receive explicit error budgets. No numerical implementation or unproved precision bound is supplied here.

A different shortcut, evaluating near zero, can require exponentially many fractional bits. At z=1/2 the values of 1+z^W and 1+z^(W+1) differ by exactly 2^(−W−1), yet the z^W coefficients are one and zero. To guarantee disjoint symmetric error intervals from this single evaluation requires an error smaller than 2^(−W−2), hence W+O(1) fractional bits for ordinary fixed-point approximation. W may have only O(log W) input bits. This is a limitation of that particular evaluation shortcut; normalization or a different algorithm can solve these simple examples quickly.

## 6. What would still constitute a general improvement

The lab supplies exact lattice/endpoint reductions, bounded sparse counting, carry-free packed digits, one-sided modular rejections/confirmations under explicit conditions, CRT reconstruction with checked premises, and a polynomial algorithm for a recognized binary-ladder family. These are useful positive tools. They do not give a general polynomial-in-input-bit-length exact coefficient query.

A general shortcut must preserve the specified coefficient, bind every residue to the same original product, avoid or account for both exponent aliasing and characteristic cancellation, and charge degree/target-dependent state counts, evaluation counts, field construction and integer bit lengths. The missing theorem is an algorithm with polynomial bounds in q and the binary exponent/target lengths for all inputs, together with exact correctness. Such a theorem would resolve the NP-complete target problem; neither the compact product representation nor the failures of the tested shortcuts supply it.

Run `python -m unittest -v test_coefficient` and `python run_experiments.py`. Results save exact requests, witnesses, modular evaluations and before/after source hashes. Bounded checks verify implementations and examples; the all-size claims above follow from their proofs.
