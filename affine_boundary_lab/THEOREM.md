# Compact certified real-affine boundary marginalization

This lab implements the one-bit construction in
[AFFINE_BOUNDARY_DESIGN.md](../AFFINE_BOUNDARY_DESIGN.md). It is an exact
primitive for a specified family of signed functions, not a universal SAT
solver or a claim about polynomial-size sums of such functions. Novelty is
not claimed. Its family is the rational real subset of affine signatures in
[Cai, Guo and Williams, Definition 2.4](https://arxiv.org/pdf/1307.7430).
The proof here is elementary and does not require a classification theorem.

## Input and preserved quantity

Original positions are numbered 0 through n-1. An explicit active set X
identifies the variables belonging to this function. The ordered list B of
retained positions is a subset of X. All masks keep these original positions;
there is no implicit renumbering. Coordinates outside X do not exist in this
function and introduce no summation multiplicity.

The input is a rational scalar lambda, binary equations A x=b, and a
Boolean polynomial q of degree at most two. A phase monomial is represented
by the mask of its variables; mask 0 denotes the constant 1. Repeated phase
masks cancel modulo two. The input function is

\[
H(x)=\lambda\,1[A x=b](-1)^{q(x)}.
\]

The returned function is the exact pointwise marginal
\(F(x_B)=\sum_{x_{X\setminus B}} H(x)\), including its sign, magnitude and
zeros. Retained variables are never summed, even when support equations pin
them. Empty active sets and empty retained sets are allowed.

## One-bit closure and its checked proof

Choose an internal variable t. If some support row contains t, that row
uniquely expresses t as an affine function of the remaining variables.
XOR the row into all other rows containing t, remove it, and substitute
that affine expression into q. Summing the unique supported value of t
introduces no multiplicative factor. Degree stays at most two because only
a linear factor is substituted into a degree-two polynomial, with Boolean
squares reduced by \(x_i^2=x_i\).

Otherwise the support is independent of t and
\(q=q_0+tL\), with L affine. Then

\[
\sum_{t\in\{0,1\}}(-1)^{q_0+tL}=2\,1[L=0](-1)^{q_0}.
\]

Append the exact support equation L=0, delete the terms containing t, and
double the scalar. L=0 identically yields a redundant row and a factor two;
L=1 yields inconsistent support and hence the zero function. A newly appended
row may pin a later internal variable. Repeating once for each internal
position proves closure without enumerating boundary or internal assignments.

The certificate records each chosen variable and either an eligible pivot
row index or the free rule. Verification starts from the external original
request, checks its binary hash, checks that the complete declared elimination
order is followed, and derives every changed row, coefficient and scalar.
No claimed freedom or factor two is trusted. The producer uses specialized
one-bit substitution; the checker instead expands each original monomial
through generic polynomial multiplication. The checker does not call the
producer's step or normalization functions. It shares input parsing, binary
hashing, simple arithmetic utilities and budget bookkeeping.

## Canonical output and coefficient-separated keys

The output message has fields `n`, `retained`, `zero`, `equations`, `phase`,
`scalar`, and `free_ids`. A nonzero message uses the unique reduced row-echelon
support equations with pivot columns visited in the specified retained order.
The phase is restricted to that support by substituting the solved pivot
variables. Its remaining variables are free **original-coordinate** positions.
Any constant phase is absorbed into the scalar sign. Thus the free-coordinate
phase has constant coefficient zero. It is the unique Boolean polynomial for
the sign function with that origin convention.

The producer performs column Gaussian elimination. The verifier builds an
independent incremental row basis, clearing every existing pivot before
inserting a new one, then substitutes all pivot expressions generically.
It compares the entire resulting canonical message with strict field types.
An inconsistent support or a zero input scalar gives the unique zero message:
empty equations, phase and free IDs, scalar [0,1], and `zero=True`, while
preserving n and the ordered retained list. No sampled boundary values are
used to infer a zero function.

`message_key` includes n, ordered retained IDs, zero status, canonical support
and phase, but excludes the rational scalar. It therefore permits coefficient
aggregation of equal canonical functions. A key by itself is not evidence:
the helper expects a produced or verified canonical message. The verifier
ignores the producer's convenience key and statistics and returns a fresh key
and verified message. General addition need not remain one affine message;
for example [1,0]+2[0,1]=[1,2]. Any weighted-sum application must separately
bound its number of distinct components and preserve original-variable scope.

## Public API and failure meanings

`boundary.py` provides:

```text
marginalize(n, retained, equations, phase, scalar=1,
            *, active=None, order=None, **caps)
verify_marginal(n, retained, equations, phase, scalar, result,
                *, active=None, order=None, **caps)
normalize_message(n, retained, equations, phase, scalar=1, **caps)
message_key(message)
```

`verify` is an alias of `verify_marginal`. `active=None` means all n original
positions. An explicit active list is essential when composing messages on
only part of an original variable universe. A supplied order must contain
each active internal position exactly once; the default is ascending IDs.
The normalizer calls marginalization with active=retained and an empty order,
so it performs no sums and returns a zero-step certificate.

Scalars accept exact integers, Fractions or numerator/positive-denominator
pairs. Output rationals are reduced integer pairs. Booleans and floats are
rejected as integer/rational inputs. The request hash uses length-prefixed
signed binary magnitudes, never decimal string conversion. It binds n,
ordered retained and active lists, elimination order, original equation list,
the phase after modulo-two cancellation, and the reduced scalar. Equivalent
phase lists that cancel to the same polynomial intentionally have the same
binding. The checker still reconstructs every identity from those external
mathematical data, so a substituted hash alone cannot establish correctness.

An EXACT result contains a message, proof and convenience key. On budget
exhaustion the producer returns UNKNOWN with all three fields null; it makes
no marginal or zero claim. The verifier returns `valid=True,status=VERIFIED`
only for a checked exact result. Exhausted verification returns UNKNOWN;
malformed evidence or original inputs returns INVALID. Invalid budget
configurations are caller errors and raise ValueError; producer malformed
original inputs also raise ValueError.

Default caps are coordinate dimension 4096, support rows 16384, phase terms
100000, counted work 4000000, scalar numerator/denominator bits 65536, and
elimination steps 4096. All are explicit nonnegative exact integers. Dimension
is checked before allocating a range or shifting by an original coordinate,
including binary-encoded huge n. The row/phase limits check original collections
and subsequently constructed polynomial or support states. No exponential
state allocation is hidden behind a large integer shift.

## Cost and scope

Write N=|X|, m=|X minus B| and s for the original number of support rows.
There are at most s+m rows throughout, and at most
\(1+N+\binom N2\) distinct phase monomials. A one-bit phase substitution
visits O(N squared) terms and expands at most N+1 affine terms for each
affected monomial, giving a conservative O(N cubed) bound per step.
Support updates and final row reduction are polynomial in s and N. The
checker likewise uses polynomial-size degree-two products and row bases.
The proof has m steps, each storing only a variable ID, rule and possible
row index. No truth table or 2^N loop appears in the production or checker.

Masks have at most n bits. The cost measure includes the original coordinate
dimension n, not merely its binary encoding or the number of active IDs.
Bit operations and hashing therefore have polynomial cost in the explicit
input size and n. The only growing scalar operation is doubling, at most m
times, so numerator/denominator bit length grows by at most m bits; constant
sign normalization does not increase it. Rational reduction and binary
serialization are exact. Reported work counters bound named replay operations,
not total CPU time: input decoding, hashing, sorting, membership bookkeeping
and polynomial setup also cost time. State and checked-scalar statistics are
not a claim about every transient Python allocation.

## Falsifiable controls

The suite tests the four identities from the design, all 1,098 combinations
of quadratic phases through three variables and retained subsets, 300 seeded
supported cases with arbitrary retained order and sparse active positions,
80 no-boundary comparisons with the existing closed affine evaluator, proof
mutations and exact work-budget boundaries. Independent enumeration is used
only for these explicitly small reference cases.

For every k, k independent copies of
\(\sum_t(-1)^{tb}=2\,1[b=0]\) produce k retained pins and scalar 2^k.
Independent copies of
\(\sum_{s,t}(-1)^{st+sa+tb}=2(-1)^{ab}\) produce 2k retained variables,
k quadratic terms and scalar 2^k. Saved cases reach k=256, including 512
retained and 512 internal variables. Their reference is the product identity,
not enumeration of their assignments. This is compact marginalization of
these original signed affine functions, not an encoding of unrestricted SAT.
