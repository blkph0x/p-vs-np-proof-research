# A checked real-affine target family on arbitrary graphs

This lab implements a positive exact algorithm for a specified transformed
family. It does not solve unrestricted SAT, search all common bases, or prove
that a failed supplied basis cannot be replaced by another one. Novelty is
not claimed. The contribution here is a complete, executable application with
original-network binding, signed arithmetic, certificates, and scope controls.

## 1. Primary-source applicability

Cai, Guo and Williams, *Holographic Algorithms Beyond Matchgates*,
[author preprint, January 2018](https://homepages.inf.ed.ac.uk/hguo/papers/HA-general.pdf),
[arXiv record](https://arxiv.org/abs/1307.7430), define affine signatures in
Definition 2.4 and product-type signatures in Definition 2.5. Their affine
class has affine Boolean support and a fourth-root-of-unity phase; its
equivalent quadratic representation has even cross coefficients modulo four.
Theorem 2.2 preserves the complete bipartite contraction under inverse basis
actions. Theorems 1.1 and 1.2 concern finding transformations to the two
tractable classes, including succinct symmetric inputs. Those general search
algorithms are **not implemented here**. The paper explicitly permits general,
nonplanar graphs for these target classes. Section 2.1 specifies algebraic
numbers for the computational model.

We implement the following rational real subset of their affine class, and
give an independent elementary evaluation proof below:

\[
 f(x)=c\,1[x=x_0+Bt]\,(-1)^{q(t)},\qquad
 c\in\mathbb Q\setminus\{0\},\quad t\in\mathbb F_2^d,
\]

where the columns of B are independent and q is a quadratic Boolean
polynomial. Taking the phase exponent 2q modulo four places this subset in
the source's class. Zero tensors are handled separately. Imaginary phases,
general algebraic bases, product-type and Fibonacci recognition are outside
this implementation.

## 2. Network and basis convention

The input is a bipartite network with E Boolean edge variables. Each edge
occurs exactly once on each side. A node lists ordered, distinct incident
edge IDs and its full rational truth table. Table index is
`sum(x_j * 2**j)`. Scalar nodes are allowed. Multiple graph edges between
nodes are allowed. No planarity promise is used.

For a supplied invertible rational 2-by-2 matrix T, row nodes transform as
f' = f T^(tensor k), and column nodes as g' = (T^-1)^(tensor k) g.
For each original edge, summing its new index gives
sum_y T[x,y] T^-1[y,z] = 1[x=z]. Expanding all finite sums therefore proves
equality of the **whole** original and transformed contractions. A separate
transpose, a gate-dependent basis, or an omitted equality node would not be
this identity. The checker recomputes every node transformation from the
external original input, with a separate axis-indexing implementation.

The supplied-basis decision in this lab is complete for the stated real
affine subclass on explicit tables: it returns EXACT if every transformed
node has a checked representation (or any transformed node is zero),
UNSUPPORTED if a transformed nonzero node fails recognition, and UNKNOWN if
a resource cap interrupts the calculation. UNSUPPORTED carries no assertion
about a different basis or a larger tractable family.

## 3. Recognition and its explicit certificate

For a nonzero table, choose one supported point x0 and compute the span of
all differences x+x0. Its dimension is d. All supported points already lie
in that coset. Thus support size 2^d proves that the support is exactly the
coset; a smaller size rejects it.

Reduce a basis so that its pivot coordinates form an identity matrix.
Then t_i=(x+x0) at pivot i. Choose c=f(x0). Every supported value must be
c or -c. The phase at t=0 is zero by construction; phases at unit vectors
give its linear coefficients, and phases at pairs of unit vectors give its
quadratic coefficients. Finally check the resulting expression at **every**
table entry. This final check rejects higher-degree phases, including a
cubic sign on all eight ternary inputs.

The certificate contains x0, basis vectors, pivots, c, linear coefficients,
and quadratic pairs. The checker does not rerun the recognizer. It verifies
the pivot identity, the generated support, and every rational table value.
Checking the pivot identity proves basis independence. It also rejects
duplicate quadratic pairs and malformed or Boolean-valued integer fields.

## 4. Polynomial global evaluation, with cancellation retained

Replace each local affine-support description by its linear equations in
the original edge variables. Its coordinates t_i are affine expressions in
the edge at the pivot port. Multiplying all local factors gives

\[
 Z=C\sum_{Ax=b}(-1)^{Q(x)},\qquad C=\prod_v c_v,
\]

where Q has Boolean degree at most two. Gaussian elimination detects
inconsistency, giving Z=0. Otherwise it produces a bijective parameterization
x=a+Ny, with independent nullspace columns and d=E-rank(A). Substitute this
into Q using x_i^2=x_i, obtaining a quadratic polynomial R(y).

To sum R exactly, select a present cross term y_i y_j and write

\[
 R=y_i y_j+y_i A(z)+y_j B(z)+C_0(z),
\]

where A and B are affine and z contains the remaining variables. Direct
summation over the four choices gives

\[
 \sum_{y_i,y_j}(-1)^R=2(-1)^{C_0(z)+A(z)B(z)}.
\]

The new exponent still has degree at most two. Each step removes two
variables and records the new polynomial. When no cross term remains, a
nonzero linear coefficient gives zero; otherwise the sum is the constant
sign times 2 to the number of remaining free variables. Multiply by the
factor 2 from each pair elimination and by C.

This is a complete exact evaluator, including negative answers and signed
zeros. The checker independently verifies the rank and augmented rank of
the assembled equations. For a consistent certificate it checks a
particular solution, every homogeneous basis vector, independence, and the
required nullity, proving the parametrization is onto and one-to-one. It
reconstructs the restricted polynomial and checks each pair-elimination
identity. It does not invoke the producer's elimination or summation solver.
Elementary rational and Boolean-polynomial primitives are shared. These are
executable checks and an ordinary mathematical proof, not a proof-assistant
formalization.

## 5. Representation, arithmetic, and budgets

Let L be the total number of explicitly listed tensor entries, a the largest
arity, E the edge count, and S the original binary input length. Transforming
all tables takes O(L a) rational arithmetic operations. Recognition is
polynomial in L and a (the support scan and full phase check can be bounded
by O(L a^2), apart from basic bit-vector costs). Global elimination has at
most 2E support equations. The deliberately simple phase-substitution code
can use O(E^4) elementary operations, and pair summation O(E^3). Neither
stage enumerates 2^E assignments. These bounds are polynomial, without a
treewidth or topology restriction.

Bit costs are included in the conclusion. Matrix inversion uses exact
rationals whose encoding length is O(the basis encoding length). For a
node of arity k, a common denominator for a transformed entry divides the
product of all original denominators at that node, times the common basis
denominator to the k-th power. Numerator magnitude also accounts for at
most 2^k summands. Its bit length is therefore polynomial in that node's
explicit input length and k times the basis length. Across all scalar
products the bound is O(S + E*S_basis + E); free-variable summation adds at
most E bits. All intermediate exact arithmetic consequently has polynomial
bit length. The exact integer masks used by GF(2) calculations have O(E)
bits. Signed cancellation does not justify floating-point arithmetic.

This statement is about **explicit truth-table inputs**. Constructing the
degree-d equality table costs 2^d entries. We do not claim the source's
stronger succinct-signature recognition algorithm, or polynomial conversion
of arbitrary high-degree CNF incidence nodes into these explicit tables.
The formula builder checks a table cap before constructing such a table.
It also bounds binary-encoded counts of unused variables before allocation.

The implementation has caps for edges, total original entries, counted work,
and checked rational numerator/denominator bit lengths. These are named
operation/representation bounds, not a wall-clock bound: parsing already
materialized input, hashing, Python bookkeeping, and some polynomial setup
are additional work. A rational expression may have transient products
larger than the checked final rational; the proof above, rather than the
diagnostic peak-bit statistic, bounds those intermediates. The verifier
uses its own external caps and reports UNKNOWN upon their exhaustion.
UNKNOWN and UNSUPPORTED contain no value or proof. Producer statistics are
diagnostic and are not trusted as part of a value certificate.

## 6. Original SAT and slack encodings

`formula_network` assigns one edge to each literal occurrence. The row for
each variable is equality on all its occurrences; an unused variable has
the scalar 2. Each column evaluates its literals in the specified order,
including their signs. Repeated occurrences and whole repeated clauses
remain present. The SAT column is OR. A k-literal slack column has value
binomial(k-1,t-1) when t literals are true, and zero when t=0; the empty
clause is zero. Thus the ternary slack signature is [0,1,2,1].

`solve_formula` and `verify_formula` rebuild these nodes from the externally
supplied n, literal lists, and mode. This keeps original shared assignments
intact. For the prior normalized base-six packing, the local slack factor
counts precisely the choices of the k-1 slack bits that complete that digit.
Therefore its full contraction is the original coefficient, not merely the
number of satisfying assignments. One ternary clause has Boolean count 7
and slack count 10; duplicating that clause gives Boolean count 7 and slack
count 16. The tests retain these distinctions.

An exact zero certifies UNSAT for these two original nonnegative encodings,
because their positive weights occur exactly on satisfying assignments.
For a general signed network zero may instead be cancellation. For example,
the unary pair [1,-1] and [1,1] has two nonzero assignments but contraction
zero. We do not infer UNSAT from an unrelated signed surrogate.

## 7. Working positive family and limits on the present application

Start with an arbitrary bipartite equality network. Its partition function
is 2 to the number of connected components containing edges, with scalar
nodes accounted for separately. Apply the inverse basis of
T=[[1,2],[1,3]] to this target network, obtaining dense signed original
tensors. Supplying T to this evaluator recovers the target family exactly.
The saved examples include K3,3 and a connected cubic network with 80 nodes
and 120 edges. Both original networks are rejected by the real-affine
recognizer in the identity basis, but the checked common basis yields value
2. The latter is evaluated without 2^120 enumeration. This is a genuine
positive transformed family on arbitrary topology; it is not a reduction
of arbitrary SAT to that family.

Other positive controls exercise quadratic signs, cancellation, inconsistent
affine constraints, empty products, and many unused variables. Original
single/repeated ternary OR and slack clauses, all eight ternary polarities
(an UNSAT formula), and a balanced planted 24-variable/96-clause formula
test the practical boundary under specified identity, Hadamard, and shear
bases. Failure of these tests means only that the supplied basis has an
unsupported local tensor, or that its declared budget was exhausted.
It is not an all-bases nonexistence theorem, does not cover the full complex
affine class, and establishes neither P=NP nor P!=NP.
