# Ordered crossings, exact signs and a polynomial Pfaffian evaluator

## Scope and conventions

This is a check on a specific possible reduction, not a resolution of P versus NP.
Boundary ports 0,1,2,3 occur in that cyclic order on the outer face. A mask's bit
i is its value at port i (little endian). For graph deletion signatures, bit one
deletes that external vertex. All calculations use exact rationals. The local
obstruction below also holds over any field of characteristic other than two.
It does not prohibit a different global encoding or a simultaneous non-diagonal
basis transformation. Such a transformation must preserve all other tensors.

## Ordinary crossing fails a necessary planar-matchgate identity

Let C(x)=delta(x0,x2) delta(x1,x3). Its entries at masks 0,5,10,15 are one;
all others are zero. Every planar matchgate with these cyclic external ports
satisfies the necessary identity

    f0 f15 - f3 f12 + f5 f10 - f9 f6 = 0.

This follows directly from the matchgate identity for numeric masks alpha=1
and beta=14, up to an overall sign.
For C its left side is 2. Hence no such standard-basis planar matchgate realizes
the full ordinary crossing tensor. Port order matters: two adjacent equality
wires have a different tensor and do satisfy the identity. The argument covers
arbitrary signed or complex edge weights, not just nonnegative ones.

The necessary matchgate identity is a previously proved theorem, not a new result:
Cai and Gorenstein, [Matchgates Revisited, Theorem 1](https://arxiv.org/html/1303.6729).
The source explains the ordered outer-face convention and the parity condition.
Our exhaustive identity checker checks every alpha,beta pair for these four-port
tables; that finite computation corroborates the displayed algebra.

## The real planar signed crossing is different

Let X agree with C except X15=-1. The graph from that paper's Figure 6 has external
vertices 0,1,2,3 clockwise, interior vertices 4,5, and edges

    01, 04, 43, 15, 52, 32 of weight +1; 45 of weight -1.

It is the six-vertex rectangular ladder in that figure. Enumerating every perfect
matching after every subset of exterior deletions gives exactly X. In particular,
with no deletions the three products are +1,+1,-1, summing to one; with all exterior
vertices deleted the remaining edge has weight -1. Full matching lists are saved.
X obeys all four-port matchgate identities. This is an affirmative gadget check.

However, contract either crossing against EQ4, whose only nonzero entries are at
0000 and 1111. The original contraction is 2; the replacement contraction is 0.
Both original assignments existed. This is a closed tensor-network countercontrol,
not a claim that EQ4 is itself a planar matchgate. It is exactly the kind of shared
logical-variable tensor whose preservation a proposed SAT reduction must prove.

Nor can nonzero unary edge rescalings repair just this discrepancy. Restricted
to the allowed crossing assignments, such rescaling has the form A(a)B(b). For
C, the two-by-two table has product f00*f11 = f01*f10. For X the two products are
negatives, with nonzero entries. Multiplying rows and columns by nonzero factors
preserves their ratio. Thus no diagonal local gauges remove the minus sign in
characteristic other than two. Zero rescalings cannot preserve the four nonzero
target entries. This is not a theorem about general basis changes.

## Exact signed pairing sums really can be computed in polynomial time

For an ordered n-by-n skew-symmetric rational matrix A, the Pfaffian is the sum
over perfect pairings of the product of their upper-triangular edge entries,
multiplied by (-1) to the number of interleaving chord crossings. Odd dimension
has value zero; the empty matrix has value one. Vertex order is part of the input.
The independent reference expands all pairings only for n<=12 and checks the
crossing parity directly. It is factorial-time and is never the efficient method.

The efficient producer uses pivoted skew elimination. After a simultaneous row
and column swap, write

    A = [ 0  t  u ; -t  0  v ; -u^T  -v^T  B ],  t != 0.
    S = [ 1  0  v/t ; 0  1  -u/t ; 0  0  I ].

Then det(S)=1 and S^T A S = diag([[0,t],[-t,0]], B'), where
B'ij=Bij+(vi*uj-ui*vj)/t. Consequently Pf(A)=t Pf(B'). A simultaneous transposition
changes the Pfaffian sign. If the first row is zero, every term vanishes. These
identities follow by the alternating multilinear definition of the Pfaffian
(equivalently, the top coefficient in the exterior power of the corresponding
two-form); they do not assume a nonzero determinant at the final step.

Each certificate records the swap, pivot and entire remaining skew matrix. The
verifier receives the external original matrix, checks its binary SHA-256 binding,
then constructs S and checks the full matrix product S^T A S, independently of
the producer's Schur-complement formula. It checks the final zero-row, odd-size or
empty justification and every scalar sign. Merely checking Pf(A)^2=det(A) would
lose the sign, so that weaker check is not used as the certificate.

The producer uses O(n^3) rational arithmetic operations. Certificates contain
O(n^3) rational entries. This deliberately simple verifier uses O(n^4) operations
for its dense matrix products over all reductions. These are polynomial **bit**
algorithms as well: clear all input denominators using a common product D, whose
bit length is at most the total input bit length. The integer matrix DA has
polynomial input height. Each remaining Schur-complement entry is a ratio of
determinants of submatrices of DA by the block determinant/Cramer identities.
Hadamard's determinant bound gives polynomial numerator and denominator lengths
(O(n(log n + log max|DAij|))); pivot products are Pfaffians of eliminated blocks,
whose matching expansion gives the same kind of polynomial bit bound. Permuting
rows and columns does not change those bounds. Exact gcd reduction preserves them.
Per-operation intermediate products have at most sums of polynomial bit lengths.

Implementation caps return UNKNOWN without a value; they never reinterpret
exhaustion as zero. Runtime counters are diagnostic, not mathematical claims.

## Why the positive algorithm is insufficient for general SAT

For the ordered four-vertex graph with edges 01,23,02,13 all of weight one, there
are exactly two perfect matchings. One crosses and one does not. Their signed sum
is zero. The ordinary matching count is two. This graph can itself be embedded
planarly with another order; the example concerns the explicitly fixed chord
order and the signed sum, not intrinsic graph nonplanarity.

More generally, for the complete ordered graph with every upper entry one,
Pf(A)=1 at every even size: expansion at vertex zero has n-1 alternating terms,
each smaller Pfaffian one, and n-1 is odd. Its unsigned count is (n-1)!!.
Thus we have a genuine efficient signed calculation, with a precise explanation
of why its zero value cannot generally be used as a no-witness certificate.
Computing a Pfaffian, counting planar matchings with an appropriate orientation,
and deciding existence of an arbitrary graph matching remain distinct operations.

No new complexity classification or novelty is claimed. These arguments and
certificates are independently checked human-readable mathematics and code, not
proof-assistant formalization.
