# Compact exact boundary marginalization for real-affine signatures

Design only; no new implementation. This complements
`AFFINE_DECOMPOSITION_NEXT_REVIEW.md` with a block-elimination derivation and
certificate requirements. It uses the real rational subset of the affine
class in Cai, Guo and Williams,
[*Holographic Algorithms Beyond Matchgates*, Definition 2.4](https://homepages.inf.ed.ac.uk/hguo/papers/HA-general.pdf).
The closure and algorithms below are proved directly. Novelty and general
SAT coverage are not claimed.

## Exact statement

Let y in GF(2)^k be an **ordered retained boundary** and z in GF(2)^m be
internal variables. The compressed input is

    H(y,z) = lambda * 1[A_y y + A_z z = b] * (-1)^q(y,z),

where lambda is rational, the equations are binary, and q is a Boolean
polynomial of degree at most two. Boolean squares reduce by x_i^2=x_i.
All equations, linear coefficients and quadratic pairs are explicit;
there is no 2^(k+m)-entry input table.

**Closure.** The pointwise marginal F(y)=sum_z H(y,z) is identically zero,
or has a compressed representation

    F(y) = lambda' * 1[D y = e] * (-1)^Q(y),

with affine support and a quadratic Boolean phase. One may take
lambda'=lambda*2^h for an integer 0<=h<=m, leaving any constant sign in Q.
For a nonzero output this has polynomial description length and is
constructible in polynomial bit time in the explicit dimensions and input
encoding. The boundary is never summed, even when an equation pins it.

## Constructive proof A: support parametrization and internal pairs

Eliminate columns of A_z, carrying A_y and b through the same row operations.
This gives boundary conditions D_0 y=e_0 and, on their support, a bijection

    z = a + B y + N t,     t in GF(2)^d,

where d=m-rank(A_z) and N has independent columns spanning ker(A_z).
Every valid boundary assignment has exactly one z for each t; there is no
extra multiplicity from the solved internal pivots. Inconsistent boundary
conditions yield zero. Substitute into q to obtain a quadratic R(y,t).

When an internal cross term t_i*t_j occurs, write

    R = t_i*t_j + t_i*L(y,u) + t_j*M(y,u) + R_0(y,u),

where u denotes the other internal coordinates and L,M are affine. Then

    sum_(t_i,t_j) (-1)^R = 2 * (-1)^(R_0 + L*M).

This is the four-case identity used by the closed affine evaluator. The
new phase remains quadratic, including after reducing shared-variable
squares. Repeating removes two internal coordinates each time. After p
such steps, no internal-internal cross term remains, so

    R(y,t) = Q(y) + sum_i t_i*L_i(y).

Each remaining L_i is affine in the boundary alone, and

    sum_(t_i) (-1)^(t_i*L_i(y)) = 2 * 1[L_i(y)=0].

If r=d-2p coordinates remain, append all these boundary equations and take
lambda'=lambda*2^(p+r). The exponent is d-p<=m. The resulting support is
affine; if its equations are inconsistent, the result is zero. This proves
the closure pointwise, including signed cancellations.

## Constructive proof B: one internal variable per step

This gives a particularly simple independent producer/checker design.
Keep the current support equations and phase, and choose an internal bit t.

1. If a support equation contains t, solve that equation as t=a(w), with
   a affine in the remaining variables w. XOR that equation into all other
   rows containing t, remove the solved row, and substitute t=a(w) into q.
   There is exactly one allowed t, so **no factor two** is introduced.
   Substitution preserves quadratic degree.
2. If no support equation contains t, write q=q_0(w)+t*L(w), where L is
   affine. Replace the phase by q_0, append the equation L(w)=0, and
   multiply the scalar by two. This includes L=0 (a redundant equation and
   a factor two) and L=1 (inconsistent support and exact zero).

The newly appended equation can pin another internal bit, which is then
handled by rule 1. At most m steps eliminate all internal coordinates.
Thus an internal pair in proof A is one free summation followed by one
forced substitution in this derivation, with the same factor two.

## Proposed exact certificate interface

Bind the externally supplied ordered boundary/internal IDs, rational scalar,
support rows, right-hand side and phase coefficients. Require disjoint IDs,
valid dimensions and degree at most two; do not accept a table or a claimed
support rank in place of these original data. Hashing must use binary
integer magnitudes as in the existing labs, but mathematical checks also
reconstruct the request.

A compact one-bit certificate records the eliminated internal ID and either
the chosen support row or the free-summation rule. The checker maintains
the original equations, scalar and phase and replays each exact identity.
For a pivot step it checks the row contains the chosen bit, derives a(w),
and verifies the specified XOR/substitution; for a free step it verifies
the bit occurs in no support row, extracts L itself, and appends the exact
equation. Every internal ID must be eliminated exactly once; no boundary
ID may be eliminated. Neither stated freedom nor factors two are trusted.
Full intermediate snapshots are optional because the checker can derive them.

Alternatively, a block certificate supplies D_0,e_0,a,B,N. Verify:

- A_z*N=0, independent N, and dim(N)=m-rank(A_z).
- The consistency conditions for A_z z=b+A_y y are precisely D_0 y=e_0,
  checked by row elimination or a complete left-nullspace basis of A_z.
- On that affine boundary support, A_z*(a+B*y)=b+A_y*y. Check these affine
  identities after a boundary parametrization, not by enumerating y.
- Recompute the substituted phase and every internal-pair identity, then
  derive the remaining affine L_i equations and the exact power of two.

For final support compression, compare augmented row spaces or replay
Gaussian row operations. An explicit 0=1 consequence certifies zero.
If the reported phase is normalized differently, substitute a common
boundary-support parametrization into the phase difference and require
every Boolean polynomial coefficient to vanish; phases need agree only
**on** their common support. An alternative canonical convention absorbs
the phase at a chosen support origin into lambda' and uses zero constant
phase in free boundary coordinates. The output schema must fix which
convention it uses. It must not silently change the boundary ordering.

Malformed evidence is INVALID. Budget exhaustion is UNKNOWN with no
marginal/value claim. A zero-support conclusion requires verified
inconsistency or a zero input scalar; it is not inferred from a sample of
boundary assignments. Signed cancellation is represented by the derived
inconsistent equations when it makes the whole marginal zero.

## Representation and bit costs

Let N=k+m and let s be the original number of support equations. During the
one-bit method there are at most s+m equations, each with N binary
coefficients, and O(N^2) phase coefficients. A step uses binary row XORs
and multiplication/substitution of affine Boolean polynomials. There are
m steps, so both arithmetic and storage are polynomial in s,N. Dense
coefficient-array implementations avoid any truth-table expansion. The
only rational scalar operation is multiplication by at most 2^m; its
numerator/denominator encoding grows by at most O(m) bits. Gaussian and
phase operations have polynomial bit cost as well.

The complexity measure charges the dimensions N, not only the bit length
of a binary-encoded huge variable count. Even summing m unused bits can
require an m+1-bit scalar. Explicit caps must guard dimensions, work, phase
terms, support rows and scalar bits before allocation. A symbolic
power-of-two scalar is a possible later representation, with a different
interface and cost proof; it is not assumed here.

## Controls and limits for the next implementation

Required exact controls include

    sum_t (-1)^(t*b)             = 2 * 1[b=0],
    sum_(s,t) (-1)^(s*t+s*a+t*b) = 2 * (-1)^(a*b),
    sum_t 1[t=a+b] * (-1)^(t*c) = (-1)^(a*c+b*c),
    sum_t (-1)^t                = 0.

Products of the first two controls give arbitrarily wide boundaries with
compact outputs. Also test zero scalar, inconsistent original support,
constant constraints, no internals, no boundary, unused internal variables,
pinned boundary bits, dependent equations, and repeated substitution that
cancels quadratic terms. The no-boundary case must agree with the existing
closed affine evaluator; bounded small cases can enumerate all y,z as an
independent oracle. Proof mutations must target pivot eligibility, omitted
equations, repeated/omitted internal elimination, boundary ordering, scalar
factors, signs, and false zero claims.

Products of compatible affine messages remain affine: stack equations,
add phases modulo two and multiply scalars. Marginalization is now compact
as well. This preserves counts and signs, whereas support-only existential
projection would lose both. A message-DAG application must still preserve
shared original variables and assign each internal summation exactly once.
Arbitrary addition is not closed: the two affine pins [1,0] and 2*[0,1]
sum to [1,2], outside this class. Consequently a sum-of-affine decomposition
can require growing numbers of components; neither that growth nor an
encoding of general OR/slack tensors is settled by this primitive. The old
Boolean DP's MSB table order must not be conflated with this lab's ordered
symbolic coordinates or the newer LSB truth-table convention.
