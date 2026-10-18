# Exact coefficient queries: working compression and verified limits

**P versus NP remains unresolved.** The new work goes beyond merely storing
the SAT encoding: it supplies several exact query methods, checks their
costs, and demonstrates a concrete improvement on identical original inputs.
It does not give a polynomial bound for arbitrary SAT formulas.

## What now works

The strongest result in this phase retains the original clause structure.
For a fixed logical assignment, a clause of size k with c false literals has
exactly binomial(k-1,k-1-c) admissible slack choices. Thus the requested
coefficient equals a sum over one shared original assignment of the product
of these local counts. Exact variable elimination computes that sum with
tables exponential in the supplied elimination width, while each integer
count needs at most q+1 bits for q original binary choices.

This gives a polynomial algorithm when the supplied order has logarithmic
width. It is not a claim that every formula admits such an order. The
[structure proof and implementation](coefficient_structure_lab/THEOREM.md)
check the original formula, packed exponents, target and order separately.
Repeated clauses and unused variables preserve their multiplicities.

On 24 disjoint ternary clauses, the method certifies coefficient 10^24 with
only eight assignments in the largest bucket. The packed polynomial supports
every exponent from zero through 6^24-1; explicitly listing reachable costs
would be enormous. A connected 40-clause chain also has width two, and its
exact count agrees with an independent transfer-matrix recurrence.
These coefficients count logical assignments AND their slack extensions:
one ternary clause has coefficient ten but only seven satisfying assignments.

The [comparison on identical original requests](ALGEBRAIC_CROSSCHECK.json)
checks all 34 SAT encodings from the interval experiment. It produces
34 verified exact counts: 23 positive and 11 zero. In particular it resolves
all six requests on which the interval method returned UNKNOWN. Original
Boolean/slack enumeration or explicitly checked disjoint components provide
separate reference counts. This is finite evidence of complementary methods,
not a general performance or complexity claim.

## Two other exact query methods

The [interval method](interval_coefficient_lab/THEOREM.md) stores entire runs
of reachable weights, with independently checked recurrence certificates.
For q binary powers followed by a choice of weight 2L, where L=2^q, the
support is [0,L-1] union [2L,3L-1]. Target L is absent. With target truncation,
one interval per layer proves this even at q=256, representing 2^256 reachable
values without enumerating them. Its 45 saved requests finish 37 exact
proofs and return eight UNKNOWN results at the configured limits.

The [integer-digit method](coefficient_isolation_lab/THEOREM.md) first removes
mandatory weight, divides by a gcd and reflects the target toward the nearer
endpoint. For reduced target h and r positive differences, it packs exact
coefficients into (r+1)(h+1) retained bits. This is useful when h is small,
but remains pseudopolynomial in that numerical target. Temporary shifted
integers and arithmetic costs are charged explicitly. A separately checked
binary-ladder identity solves a 40-factor case where the generic packed and
sparse methods exhaust their caps.

## Algebraic shortcuts that fail

The [residue audit](coefficient_residue_lab/THEOREM.md) proves that reduction
modulo z^M-1 sums coefficients whose exponents share a residue. Different
moduli may be satisfied by different original choices. In the saved UNSAT
gap, separate moduli 2,3,5,7 all accept although their product exceeds the
entire degree. A single common-witness query correctly rejects.

The interval family gives an all-size version: EVERY separate modulus
M<=2^q accepts its missing target. The family itself is easy by the interval
algorithm, so this excludes only the stated separate-test rule and its dense
implementation, not all algebraic methods.

Even after removing exponent aliasing, finite-field cancellation remains.
For P=(1+z)^5(1+z^2)^2, the coefficient at degree four is 26. An alias-free
order-twelve filter over the field with 13 elements returns zero. A second
verified residue and a sufficient coefficient bound recover 26 by CRT.
Residues must concern the SAME original coefficient; the arithmetic CRT
helper cannot establish that premise from fabricated residues.

Whole-polynomial identity testing also answers a different question: the
integer product is nonzero whether or not one chosen coefficient is zero.
Exact evaluation, numerical precision, root order, characteristic, and
integer size are separate obligations. No floating-point value is used as
proof of a zero or positive coefficient.

## The limits are tested on actual original formulas

The structure lab includes a complete-interaction formula with width n-1
under EVERY order, despite being easy SAT, and planted mixed-polarity
3CNFs with 24 and 32 variables. Their original satisfying assignments and
exact-weight matching extensions verify, while the table method honestly
returns UNKNOWN. A bad and a good order for the same star formula expose
ordering dependence. The small eight-clause UNSAT control receives a full
zero-coefficient proof.

The interval representation likewise fragments into 2^(q-1) intervals for
base-four digit choices, although membership in that family is easy by
digit inspection. These examples prevent any one compression scheme's
failure or success from being mistaken for a universal complexity result.

## Evidence and reproducibility

All **44 new tests across four suites pass** on frozen sources. These are
separate from the previous phase's 37 tests and earlier checkpoint suites.
See [ALGEBRAIC_TEST_SUMMARY.json](ALGEBRAIC_TEST_SUMMARY.json).

The [artifact audit](ALGEBRAIC_ARTIFACT_AUDIT.json) matches 21 source references
and independently replays 59 sparse/cyclic coefficient proofs, 37 interval
proofs, 11 named structure proofs and 34 further structure proofs in the
same-request comparison. It also checks 87 finite-field requests using 613
saved evaluation rows, three integer-packing controls, the binary-ladder
identity, the same-coefficient CRT premises, and original matching/residue
witnesses. UNKNOWN records remain explicitly undecided.

The structure experiment additionally checks 630 generated small formulas;
those individual certificates are reproducible from its frozen runner rather
than all serialized in RESULTS.json. Its 15 named controls are serialized.
The isolation experiment compares 5,740 target queries with full original
choice enumeration. Separate reviewers checked the mathematical arguments,
source scope, mutations and additional independently generated examples.
The proofs are written mathematical arguments, not proof-assistant formalizations.

Run `python run_algebraic_phase_checks.py`, `python run_algebraic_crosscheck.py`
and `python verify_algebraic_artifacts.py` here. Each lab has its own experiment
runner and independent review. No additional package installation was needed.

The [primary-source check](ALGEBRAIC_LITERATURE_CHECK.md) records recent
pseudopolynomial algorithms and excludes a withdrawn claim. This work makes
no novelty claim for variable elimination or established coefficient methods.

## Next question

Our exact methods still depend on width, interval count, numerical target or
support size. The next investigation is whether an exact change of tensor
basis can make the original constraints jointly tractable while preserving
their contraction, including signed or complex cancellations. The
[next brief](NEXT_HOLOGRAPHIC_BRIEF.md) requires explicit global consistency,
planarity conditions, algebraic certificates and bit accounting. Failure of
a restricted basis search will not be treated as P!=NP; a successful local
transform alone will not be treated as a SAT solver. The goal remains active.
