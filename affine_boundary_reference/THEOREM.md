# Independent block reference for compact affine boundary functions

This is a separate implementation of the block method in
`../AFFINE_BOUNDARY_DESIGN.md`. It imports no code from the one-bit
`affine_boundary_lab/boundary.py` producer. It provides a polynomial
symbolic oracle and certificate checker, plus a complete symbolic comparison
of two output functions. It does not implement an arbitrary signed-message
DAG or a general SAT algorithm. Novelty is not claimed.

## Input and output meaning

There are n fixed original coordinate positions. `active` explicitly names
the coordinates belonging to the input function; by default all positions
are active. The ordered `retained` list must be a subset of active. Only
active coordinates outside retained are summed. Inactive coordinates do not
create factors two.

The original input denotes

    H(x) = c * 1[A*x=b] * (-1)^q(x).

Support equations are binary `(mask,rhs)` rows, and each phase monomial is
a mask with zero, one or two set bits; mask zero is the constant monomial.
Duplicate phase monomials cancel modulo two. Rational c is exact. Boolean
objects are rejected wherever exact integers are required. A canonical
binary hash binds n, the ordered retained and active lists, original support
rows, normalized polynomial and rational scalar. The checker reconstructs
the mathematics as well as checking that binding.

The returned message has the same schema as the independent one-bit lab:
`n, retained, zero, equations, phase, scalar, free_ids`. Masks always retain
original coordinate IDs. Nonzero support rows are reduced with pivots
following the ordered retained list. Its phase uses only free retained
coordinates; a constant phase is absorbed in the scalar. A zero message
has empty equations, phase and free IDs, and scalar `[0,1]`.

## Producer: eliminate support blocks, then internal pairs

Write active coordinates as retained y and internal z. Eliminate only the
internal columns of the support equations. Residual equations give the
exact boundary consistency conditions D*y=e. On that support, the reduced
rows provide

    z = a + B*y + N*t,

where each free original internal coordinate is a distinct parameter t_i.
There are d=number_of_internal_coordinates-rank(A_z) such parameters.
The mapping is bijective for each allowed y. Boundary coordinates remain
themselves. Temporary parameter bits use positions n,n+1,... internally;
they never appear in the final boundary message.

Substitute this mapping into q. While an internal cross term t_i*t_j is
present, use

    sum_(s,t) (-1)^(s*t+s*L+t*M+Q) = 2*(-1)^(Q+L*M),

where L,M are affine in the remaining coordinates. After all such pairs
are removed, each remaining internal bit has an affine boundary coefficient
L_i(y), and its summation gives `2 * 1[L_i(y)=0]`. Append those support
equations and retain the boundary-only phase. If p pairs and r single bits
were summed, the scalar is multiplied by 2^(p+r), with p+r<=d. Reduce the
final support and substitute its pivots into the boundary phase to produce
the canonical message. Inconsistency and signed cancellation can yield
the zero function.

## Independent certificate checks

The checker does not rerun the producer's support elimination or pair
routine. It computes ker(A_z^T), whose vectors describe every linear
combination of original equations eliminating z. Multiplying those
combinations into the boundary part and right-hand side gives exactly the
boundary projection conditions. This is necessary and sufficient because
im(A_z) is the orthogonal complement of ker(A_z^T) over GF(2).

The supplied parameterization is then checked against that projected
support. Boundary coordinates must remain themselves; each declared free
internal coordinate must be its own distinct formal parameter. Every
original equation must vanish after substitution, on the whole boundary
support. The checker verifies there are exactly d free internal parameters.
The explicit identity on free original coordinates gives injectivity, and
the checked nullity gives surjectivity for each valid boundary assignment.
Thus no assignment, multiplicity, or consistency condition is lost.

The checker reconstructs the initial restricted polynomial. For each
recorded pair it independently partitions coefficients and checks the
four-term summation identity. The pair must consist of two distinct active
internal parameters and its quadratic coefficient must be one. It then
derives all leftover linear boundary conditions itself, checks the exact
power of two, and compares the reported message with the resulting function.
Initial zero-scalar and inconsistent-support shortcuts are separately
verified. A false zero claim cannot be justified by testing some boundary
assignments.

These are ordinary mathematical proofs and executable certificates, not a
proof-assistant formalization. The two implementations share the underlying
GF(2) and quadratic identities, but use different elimination strategies.

## Complete symbolic output equivalence

`equivalent_messages` binds the original n and **ordered** retained list.
It accepts well-formed output functions and verifies free-coordinate
metadata. It can compare phases that have not been reduced to free
coordinates; this is useful when the two algorithms normalize differently.

Canonical zero functions are compared first. For two nonzero functions:

1. Reduce both affine supports in the same retained-coordinate order.
   Equality of the reduced augmented row spaces is equality of the supports.
2. Their scalar magnitudes must agree, since phases are signs on nonempty
   support. Otherwise the functions differ.
3. Parametrize the common support and substitute into the XOR of the two
   phase polynomials. If the scalars agree, the resulting polynomial must
   be identically zero. If they are opposite, it must be the constant one.

Every Boolean polynomial is represented multilinearly, so its coefficients
determine its function uniquely. This proves both directions of the test
without enumerating the retained assignments. Phases need not agree away
from the common support. For example, adding `x2*(x0+x1+1)` changes no
supported value when `x0+x1=1`. A constant phase can also be offset by
negating the scalar.

## Costs and scope

Let a be the number of active coordinates, k the boundary size, s the
original equation count, and B the scalar bit length. Gaussian support
elimination, left-nullspace construction, polynomial substitution and pair
elimination all take polynomial bit time in n,a,s. The intermediate phase
has at most O(a^2) terms; the conservative implementation can require
O(a^4) elementary operations during substitution. A full pair trace can
store O(a^3) polynomial coefficients. Masks and linear-combination vectors
have polynomial bit length. The output scalar grows by at most a bits;
there are no irrational or floating-point quantities.

The comparison uses only support row reduction and quadratic substitution,
so it is polynomial in the compressed message descriptions. It can check a
128-bit or larger boundary without a 2^128-entry table. The dimension n is
charged explicitly: a binary-encoded declaration of enormous numbers of
unused active variables would itself require an enormous exact scalar.

Caps guard coordinate count, input/derived rows, phase terms, internal
coordinates, scalar bits and counted work. Major row scans, coefficient
products and pair-phase scans are counted. Parsing, hashing, sorting, Python
bookkeeping and bit operations still have additional polynomial costs; the
work counter is not total machine time. Certificates contain whole phase
snapshots, so verifier/producer memory includes the trace, not only the
largest single phase. UNKNOWN endorses no message. Invalid certificates
and incompatible message schemas are rejected explicitly.

The class is closed under products and marginalization, but not arbitrary
addition. The reference therefore validates affine components and canonical
message merging; it cannot assume that a general weighted sum has a single
affine description, or that a general SAT decomposition stays small.

## Evidence and reproduction

The tests include 4,718 small support/phase/boundary configurations, 400
seeded cases with reordered or inactive coordinates, 220 comparisons with
the one-bit implementation, exact signs and rational scalars, and deliberate
certificate/request mutations. Wide controls use 96 pinned boundary bits
and 128 freely retained bits with a nontrivial quadratic phase. Inactive
coordinate controls ensure only owned variables contribute factors two.
Saved original requests and certificates, symbolic reference outputs,
bounded full assignment oracles, cap interruptions and source hashes are
in `RESULTS.json`.

Run `python run_experiments.py`, then `python -m unittest -v test_reference.py`.
