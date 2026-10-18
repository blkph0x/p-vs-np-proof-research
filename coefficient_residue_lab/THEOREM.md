# Coefficient folding and the quantifier gap in separate residue tests

This lab studies explicit finite controls for the product

    P(z) = product_(i=1..q) (z^a_i + z^b_i),

where every exponent is a nonnegative integer given in binary. It proves the
exact folding identity, preserves multiplicities, and distinguishes separate
modular witnesses from one common witness. It gives bounded coefficient-table
algorithms and independently replayable certificates, not a polynomial-time
general coefficient query, a lower bound for all algorithms, a novelty claim,
or a resolution of P versus NP. No previous lab is modified.

## 1. What a coefficient counts

Expanding the product chooses one of two summands from each factor. For each
choice vector x in {0,1}^q let w(x)=sum_i (a_i if x_i=0 else b_i). Then

    P(z) = sum_(x in {0,1}^q) z^w(x),
    [z^s]P = number of x with w(x)=s.

This remains true when a_i=b_i: both choices contribute, so their multiplicity
must not be collapsed into a single choice. The empty product is one. Every
coefficient is a nonnegative integer at most 2^q, with at most q+1 binary bits,
and the sum of all coefficients is 2^q. Write D=sum_i max(a_i,b_i) for the
degree. D can have exponentially large numerical value compared with the
binary input length; this does not make its binary encoding large.

In particular, the product is always a nonzero polynomial, whether or not a
particular coefficient vanishes. A test for polynomial identity is therefore
not a test for positivity of the coefficient at a specified target W.

## 2. Exact cyclic folding

Let M be a positive integer, and reduce P in Z[z]/(z^M-1). There is a unique
representative R_M(z) of degree less than M. For every r in {0,...,M-1},

    [z^r]R_M = sum_(s >= 0, s congruent r mod M) [z^s]P.

**Proof.** A monomial z^s becomes z^(s mod M), because z^M=1 in the quotient.
Linearity gives the displayed sum. The relation is monic, so polynomial
division over Z supplies the unique representative of degree less than M.
All sums are finite. QED.

Nonnegativity makes a folded coefficient positive exactly when some original
choice has that residue. It does not imply that the exact target coefficient
is positive. This lab uses integer coefficients, not coefficients reduced
modulo a prime; reducing the coefficient values themselves can introduce
additional cancellation and needs a separate guarantee.

Over the complex numbers, if zeta is a primitive M-th root of unity, the exact
root-of-unity average

    (1/M) sum_(j=0..M-1) zeta^(-r*j) P(zeta^j)

equals the same folded sum. Indeed the average of zeta^((s-r)*j) is one if
M divides s-r and zero otherwise, by the finite geometric series. Thus this
filter alone has the same exponent aliasing. No numerical approximation or
root-of-unity evaluation routine is implemented here.

If M>D and 0<=W<=D, congruence to W uniquely selects exponent W in the support
range, so folding isolates its coefficient. The range condition on W matters:
for the empty product, target W=M has exact coefficient zero but folded
coefficient one. Choosing a sufficiently large order does not by itself
supply an efficient procedure that examines all of its residues/evaluations.

## 3. Separate witnesses versus one common witness

For positive moduli M_1,...,M_t, independent positive residue queries assert

    for every j there exists x_j such that w(x_j) is congruent W mod M_j.

A simultaneous query instead asserts

    there exists x such that for every j, w(x) is congruent W mod M_j.

These quantifiers cannot be interchanged. For one fixed integer w, all the
congruences hold exactly when lcm(M_1,...,M_t) divides w-W. This uses the lcm,
not the product unless the moduli are pairwise coprime. The empty list of
congruences is vacuous and corresponds to modulus one. A joint residue table
therefore uses the lcm and one common original choice vector.

For the concrete gap example,

    P(z) = (z+z^6)(1+z^36)^3, W=36,

the full expansion is:

| Exponent | 1 | 6 | 37 | 42 | 73 | 78 | 109 | 114 |
|----------|---|---|----|----|----|----|-----|-----|
| Coefficient | 1 | 1 | 3 | 3 | 3 | 3 | 1 | 1 |

There are sixteen original binary choices, eight support exponents, degree
114, and exact target coefficient zero. In the following table, bits refer
in order to pairs (1,6),(0,36),(0,36),(0,36).

| Modulus | Target residue | Folded target coefficient | Witness bits | Actual weight | Residue support size |
|---------|----------------|---------------------------|--------------|---------------|----------------------|
| 2 | 0 | 8 | (1,0,0,0) | 6 | 2 |
| 3 | 0 | 8 | (1,0,0,0) | 6 | 2 |
| 5 | 1 | 2 | (0,0,0,0) | 1 | 4 |
| 7 | 1 | 4 | (0,0,0,0) | 1 | 6 |
| Joint lcm 210 | 36 | 0 | none | none | 8 |

Although 2*3*5*7=210>D, the separate checks use different witnesses. No single
weight in the support is congruent to 36 modulo all four moduli. The ordinary
Chinese remainder implication for one fixed weight is fully respected.

## 4. Sparse counted layers and proof replay

Let C_0 be the sparse table {0:1}. For exact coefficients, the next layer is

    C_(i+1)(s) = C_i(s-a_(i+1)) + C_i(s-b_(i+1)),

where missing entries mean zero. For cyclic coefficients the indices are
interpreted modulo the external positive modulus M. The producer implements
this by adding each predecessor count once for each of its two summands.
Thus it handles equal exponents, collisions and coefficient multiplicity.

`build_coefficient_proof(choices, target, modulus=None, ...)` returns EXACT
only after all q layers are complete. Its certificate stores every nonzero
coefficient in every layer, the target coefficient and a realizing original
choice vector when that coefficient is positive. Each sparse layer has
strictly increasing keys and positive integer counts. Backtracking decreases
the factor index at every step and must reach the coefficient-one root at
exponent zero. Residue witnesses retain their actual original integer sum;
that sum may differ from the target.

`verify_coefficient_proof(choices, target, certificate, modulus=None, ...)`
receives the external original pairs, target and modulus. It reconstructs
every required recurrence without calling the producer and compares the
entire next layer, not merely the target entry or supplied positive witness.
It checks the root, row structure, coefficient bounds, the claimed target,
and the witness against the original choices. Completeness of each recurrence
certifies zero as well as positive coefficients. An induction on the factor
index proves that a verified layer is the exact original coefficient table.

A versioned binary SHA-256 binding records factor count, ordered exponent
pairs, target, exact/cyclic mode and external modulus. Integers use byte-length
prefixes and unsigned binary magnitudes, avoiding decimal conversion limits.
The hash is an integrity check; the mathematical verification still checks
every recurrence and witness even if a caller recomputes a binding for a
different request. No certificate-stored copy of the original product is
trusted as a replacement for the external inputs.

The separate helper `verify_choice_witness` proves only existence of that
particular original weight/residue. It does not prove a coefficient count or
absence of a target. `joint_residue_proof` computes the lcm of the supplied
moduli and delegates to the same bounded cyclic-table producer.

## 5. Costs, explicit caps and honest UNKNOWN results

Let S_i be the number of nonzero entries in layer i. For full sparse tables,

    S_i <= min(2^i, D_i+1), where D_i=sum_(j<=i) max(a_j,b_j).

For cyclic tables, S_i<=min(2^i,M). A complete producer run processes exactly
2*sum_(i=0..q-1) S_i predecessor/choice arcs and stores sum_(i=0..q) S_i
entries. It also reads/hashes the input, constructs a witness and sorts each
stored layer for canonical output. Counts have at most i+1 bits; exact state
keys have at most the degree's bit length, and residue keys have at most the
modulus's bit length. Integer addition, reduction, comparison and hashing
have their ordinary bit costs. Neither a word-sized arithmetic assumption
nor a polynomial support bound is asserted. The witness needs O(q) choices;
proof size and verification time depend on all stored layers.

The implementation reports transitions, states created, largest layer,
largest state/count bit lengths, input exponent/hash sizes, and degree bit
length. It uses dictionaries rather than arrays of length D or M. Its three
explicit caps bound entries per layer, total stored entries and processed
arcs. Statistics include entries stored in a partial layer; an arc that hits
a storage limit counts as processed. Input validation, hashing, canonical
sorting and bit operations are additional work, not hidden in an assertion
that transition count equals elapsed CPU cost. Timings are saved separately.

On a producer cap, status is UNKNOWN and no target coefficient, final
decision, witness or complete certificate is returned. The independent
verifier has its own limits. It returns UNKNOWN if those are insufficient,
INVALID for malformed or mathematically false evidence, and VERIFIED only
after checking every layer. Partial work is never a proof of zero. Limits
are operational safeguards, not evidence that a different method cannot
answer the same query.

The saved positive growth controls use binary-power choices (0,2^i). Their
all-one vector is an explicitly checked exact-target witness. Separate
moduli 17,19,23 finish with small tables, while the full or joint-lcm7429
tables hit the 128-state cap. A joint table can be much larger than any
individual residue table; prior to folding, binary-power prefixes have 2^i
distinct exponents. These easy positive instances demonstrate this table
representation's limitation, not inherent hardness of the instances or a
lower bound for all joint-residue/coefficient algorithms.

For comparison, integer-base evaluation also has an exact but potentially
expensive interpretation. If B>2^q, the coefficients of P are the base-B
digits of P(B), with no carries. Yet P(B)>=B^D, so its binary length is at
least floor(D*log2(B))+1. Storing that integer can be exponential in the
binary input size. Modular exponentiation by itself does not supply the
missing coefficient-isolation argument. This observation does not exclude
other algebraic methods.

## 6. Finite evidence and reproduction

The tests independently expand all 820 products of length zero through three
with exponent pairs from {0,1,2}^2, comparing full and cyclic coefficients for
five moduli. Another 120 seeded products of at most eight factors are checked
against explicit original choice enumeration. Other controls cover equal
choices, empty products, non-coprime/repeated/empty modulus lists, the main
gap, JSON replay, original-input changes even with recomputed bindings,
malformed layers and witnesses, exact cap boundaries, separate verification
caps, and exponents exceeding Python's decimal-string conversion limit.

`RESULTS.json` preserves original pairs/targets, complete certificates for
finished queries, separate residue witnesses and their actual weights,
bounded independent expansions where at most eight factors are present,
UNKNOWN outcomes, costs and current source hashes. It records explicit
original positive witnesses for growth controls without enumerating all their
choices. Source stability is checked across the saved experiment.

Run from this directory:

    python run_experiments.py
    python -m unittest discover -s . -p "test*.py" -v

Written proofs are ordinary mathematical arguments with independent review;
they are not proof-assistant formalizations.
