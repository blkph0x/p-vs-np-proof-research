# Exact rational basis invariance on the original incidence network

This lab implements and checks a basis change on the actual bipartite network
of a supplied formula. It preserves either the number of satisfying original
assignments or the specified slack-weighted count. These are different counts
and remain separate modes. It also supplies a bounded complete contraction
reference and explicit examples where the wrong transformation changes the
answer. No tractable target family, matchgate realization, planarity condition,
general polynomial counting algorithm or P-versus-NP resolution follows from
basis invariance alone.

## 1. Primary definition and fixed convention

The primary definition used here is the ordered signature-grid contraction
and bipartite row/column transformation in Cai, Guo and Williams,
[*Holographic Algorithms Beyond Matchgates*, Sections 2.1-2.2 and Theorem 2.2](https://arxiv.org/pdf/1307.7430).
That definition assigns an order to the incident ports, treats one side as
rows and the other as columns, and pairs a basis with its inverse. The
invariance is proved directly below, rather than relying on an unverified
realizability theorem. No theorem classifying matchgate or other tractable
signatures is applied in this lab.

The original formula has variables 1,...,n and an ordered list of clauses,
each an ordered list of signed variable indices. Each literal occurrence is
a distinct incidence edge. Its edge ID is assigned by clause order and then
literal position. A variable's ports are its occurrence edge IDs in increasing
order; a clause's ports follow its literal order. A local bit tuple is stored
at index sum_j bit_j*2^j: port zero is the least significant bit. This is an
explicit storage convention; both ends and every transform use it consistently.
No planar or cyclic embedding is assumed.

Original input occurrences are preserved. Whole clauses, repeated literals
and tautologies are not silently removed. Removing them can change the
slack-weighted count even when it preserves ordinary satisfiability.

## 2. Original tensors and the two counts

At a variable of occurrence degree d, define the row tensor

    G_v(x_1,...,x_d) = sum_(b in {0,1}) product_j 1[x_j=b].

For d>=1 it is one on the two constant tuples and zero elsewhere. For d=0
the empty product gives the scalar two. This degree-zero convention is
essential: an unused original variable has two assignments. It is not
replaced by scalar one merely because it has no incident edges.

For a clause of length k, let t be the number of true literal occurrences
under its ordered raw variable bits, applying each literal's own sign.
Its column tensor is:

- `sat`: R_c=1 if t>=1, and zero otherwise.
- `slack`: for k>=1, R_c=binomial(k-1,t-1) when t>=1, and zero otherwise.
  An empty clause has scalar zero.

The slack factor counts the choices of k-1 distinct binary slack variables
whose sum is t-1. Equivalently, false_count+slack_sum=k-1. For nonempty
clauses of length at most three this is the count from the earlier base-six
packing construction. Larger clauses have the same explicitly defined local
slack-count interpretation here; no base-six packing claim is made for them.

The original contraction is

    Z = sum_(edge bits x) product_v G_v(x at v) product_c R_c(x at c).

The equality tensors force every occurrence of a used variable to agree.
Unused variables contribute their factor of two. Thus in SAT mode this is
exactly the number of satisfying original assignments. In slack mode it is
the sum, over the same shared original assignments, of the product of their
local slack extension counts. Every satisfied clause has a positive factor,
so both modes have positive count exactly when the formula is satisfiable,
but their positive values can differ. A positive ternary clause has SAT
count seven and slack count ten; two copies have slack count sixteen.

An empty formula with no variables has value one. With n unused variables
and no clauses it has value 2^n. An empty clause makes either count zero.
Contradictory unit clauses share their original variable and therefore have
count zero; they are not evaluated with independent variable assignments.

## 3. Basis invariance, including signs and denominators

Let T be any invertible two-by-two matrix over Q. Transform every variable
row and every clause column by

    G'_v = G_v T^(tensor d_v),
    R'_c = (T^-1)^(tensor k_c) R_c.

Tensor power zero is the scalar identity. In components,

    G'_v(s) = sum_x G_v(x) product_(e at v) T[x_e,s_e],
    R'_c(s) = sum_y product_(e at c) T^-1[s_e,y_e] R_c(y).

**Theorem.** The transformed contraction equals Z exactly on the same
ordered incidence network.

**Proof.** Substitute the two expressions into the transformed contraction
and interchange the finite sums. Each edge contributes

    sum_(s_e in {0,1}) T[x_e,s_e] T^-1[s_e,y_e] = 1[x_e=y_e].

The product of these identities identifies the variable-side and clause-side
original indices on every edge. The remaining sum is precisely the original
contraction. No positivity, planarity, symmetry, orthogonality or independence
between different occurrences of one variable was assumed. QED.

The algebraic identity also holds over the complex numbers, or any field
where T is invertible, with counts interpreted in that field. This executable
lab restricts matrices and arithmetic to exact rationals; no statement about
nonexistence of complex bases is inferred from that restriction. Rational
normalization and the actual inverse are computed and charged, not omitted.

Transformed entries and individual global terms may be negative. For a
contradiction, nonzero positive and negative terms can cancel to zero. The
original-count preservation argument is what makes a verified zero a correct
zero of the original problem; nonzero transformed terms are not themselves
satisfying-assignment witnesses.

## 4. Explicit wrong-convention controls

Under the convention above, applying T rather than T^-1 to the clause columns
leaves the edge factor T*T instead of the identity. This is generally wrong,
though it can work accidentally for special matrices with T^2=I.

Take the one-variable unit clause x, whose tensors are G=(1,1) and R=(0,1)^T,
and whose original count is one.

For the unnormalized Hadamard matrix H=[[1,1],[1,-1]], H^-1=H/2. Correctly
using that inverse preserves one; using H at both ends gives two, since
H^2=2I. The missing denominator cannot be discarded as an irrelevant scale
when the exact original count is the objective.

For T=[[1,1],[0,1]], the transformed row is (1,2). The correct inverse column
is (-1,1)^T, giving -1+2=1. The wrong column T*R=(1,1)^T gives 1+2=3.
Both examples are saved with exact entries and complete finite traces. They
are labelled countercontrols, not offered as valid invariance certificates.

## 5. Local trace certificates and complete contraction certificates

`transform_network(n,clauses,T,mode=...,**caps)` transforms each tensor one
port at a time. It saves its original table and every intermediate one-axis
table. This does not enumerate global edge assignments. The returned local
certificate contains the original occurrence layout, exact inverse, ordered
ports and all rational entries.

`verify_transformation` receives the external original formula, basis and
mode. It reconstructs the original equality/clause tables and port layout,
checks both T*S=I and S*T=I for the supplied inverse, and checks every local
axis update by a different traversal of all output indices. It does not call
the producer's inverse or transformation routines. Verified local action
certifies the algebraic invariance theorem; it does not certify an efficiently
computed global count.

`solve_basis` adds the complete original and transformed contraction traces:
one rational product for every global edge-bit assignment in integer index
order, followed by their exact totals. `verify_basis` checks the local proof
first, then independently evaluates each trace term against the checked
tables and original ports, multiplying nodes in reverse order. It checks both
totals, their equality, and the nonnegative integer original count. Missing,
duplicate, altered or incorrectly ordered trace data cannot certify a count.

All verifier APIs take the certificate object, not the outer result wrapper.
Verification returns EXACT with `valid=true`, INVALID for false/malformed
evidence, or UNKNOWN for insufficient verification resources. The source's
observational work counters are returned separately from the proof; verifier
counters measure its own traversal rather than trusting producer statistics.

A versioned binary SHA-256 binding includes n, all ordered signed clauses,
the selected count mode and every normalized rational basis entry. Magnitudes
are length-prefixed binary integers with explicit signs; it does not convert
large integers to decimal strings. Mathematical verification also reconstructs
the original data, so changing the request and recomputing its hash cannot
make false tables valid. Certificate rationals use canonical integer pairs
[numerator,positive_denominator], including [0,1] for zero, and survive JSON
round-trip. Floating-point inputs are rejected.

## 6. Explicit work and bit costs

Let E be the number of occurrences and N=n+m the number of tensor nodes.
For a node of degree d, the local implementation stores (d+1)2^d entries,
including the original table, and uses 3*d*2^d rational operations: two
multiplications and one addition for each output entry at each axis. It
does not materialize a 4^d-entry tensor-power matrix. Initial tensor tables
still require 2^d entries, so an unbounded variable degree can be costly.

The producer's two-by-two inverse uses seven rational binary operations
(two products, one subtraction, four divisions). The verifier instead checks
two complete matrix products, using 24 such operations. The two full global
traces use 2^(E+1)*(N+1) operations in this reference: N multiplications and
one accumulator addition for each term on each of two networks. This explicit
edge-assignment method can be worse than direct enumeration of the n original
variables. It is a finite control, not a proposed general counting speedup.

The named arithmetic count records rational additions, subtractions, products
and divisions. Input validation, tensor-index assembly, hashing, integer
binomial computation, serialization and rational reduction have additional
bit costs. They are not silently treated as free or included in a claim that
the counter equals machine instructions or wall time. Timings are also saved.

For bit complexity, let B bound the total binary description length of the
four rational entries of T. A two-by-two rational inverse has bit length
polynomial in B. Clearing the finitely many entry denominators gives a common
denominator of O(B) bits for T, and a polynomial-in-B common denominator for
T^-1. At degree d, tensor entries use at most d factors from the corresponding
matrix and sums over at most 2^d original indices. Hence their numerator and
denominator lengths are polynomial in d, B and the original tensor-entry
lengths. A global term uses E such factors from each side. All terms share a
common denominator with polynomial bit length in E and B; summing 2^E terms
adds only E bits to a magnitude bound. Unused-variable and slack multiplicity
also have polynomial bit length in the explicit formula size. Exponentially
many operations/entries remain possible despite these per-number bit bounds.

Caps bound original dimensions/occurrences, each local table, all stored
local-stage entries, global assignments per trace, rational operations and
the observed numerator/denominator bit length. Powers of two are checked
against caps before large allocation. A bit cap is checked on every produced
arithmetic value. Producer exhaustion returns UNKNOWN with no count or
certificate. Verification has separate budget accounting and can also return
UNKNOWN without endorsing the claimed count. Local transformation can finish
while full contraction is UNKNOWN; these are deliberately separate APIs.

## 7. Finite checks and reproduction

The tests cover all clause polarities through arity three under identity,
signed diagonal, unnormalized Hadamard, nonorthogonal integer, shear and
nonorthogonal rational bases. Local actions are compared with an independently
expanded tensor-power formula. Original logical and local slack choices are
enumerated independently on small instances. Tests include shared variables,
repeated clauses and occurrences, tautologies, unused variables, empty
formulas/clauses, contradictory units, signed cancellation, exact cap
boundaries, external-input changes with recomputed hashes, forged inverses,
port permutations, tensor/trace mutations and 15,001-bit rational inputs.

Saved examples include the original formulas and rational matrices, every
transformed entry and intermediate table, all completed contraction traces,
separate UNKNOWN outcomes, source hashes and source-stability evidence.
The low-degree 38-edge chain receives a checked local transformation while
the complete reference contraction refuses its exponential edge expansion.
The 256-unused-variable example is counted through degree-zero scalar factors,
without enumerating its 2^256 original assignments.

Run from this directory:

    python run_experiments.py
    python -m unittest discover -s . -p "test*.py" -v

No inference of general tractability is made from a successful finite batch
or from individually transformed local tensors. A useful holographic
algorithm would additionally require a jointly applicable exact evaluator
with verified global topology, arithmetic and complexity conditions.
