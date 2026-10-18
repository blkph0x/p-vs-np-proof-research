# Independent architecture audit — 18 October 2026

**Status: no proof of P=NP or P!=NP.** This audit adds two explicit obstructions,
one classification safeguard, and a concrete boundary for the native graph
route. The new observations do not establish general computational lower bounds.

## 1. The remaining theorem must be constructive and uniform

The native-region branch-DP theorem is sound under its stated assumptions:
polynomial-time extension oracles, a supplied decomposition, and bounded shared
boundary. The conditioning theorem also correctly charges feasible cosets and
only claims a fixed-order state-count product bound. Neither theorem guarantees
that the prerequisites can be found on arbitrary inputs.

A sufficient universal theorem can be stated without hiding the missing work.
There must exist a single deterministic compiler A, evaluator E, and fixed
constant c such that, for every CNF F of bit length N:

1. A(F) terminates in at most N^c operations and outputs an exact typed plan.
2. Its complete encodings, private variables, certificates, intermediate messages,
   discovery logs actually needed for verification, and shared DAG descriptions
   have polynomial total length.
3. E executes every required pinned extension, conjunction, projection, quotient
   transition, and reconstruction operation within polynomial total bit cost.
4. The root result is SAT exactly when F is satisfiable.

These hypotheses directly yield SAT in P. They are not currently established.
The exponent must be fixed independently of F; allowing a different polynomial
for each input makes the condition vacuous. A polynomial state count does not
bound state construction or transition cost, and a growing native vocabulary
must come with uniform algorithms rather than implicit semantic oracles.

By contrast, suppose every UNSAT input merely has a polynomial-size plan whose
soundness a polynomial verifier can check. Guessing and checking that plan puts
UNSAT in NP, hence implies NP=coNP. That implication alone does not supply a
deterministic polynomial search algorithm or establish P=NP. This is precisely
the proof-size versus proof-search distinction formalized by
[Cook and Reckhow, Propositions 1.1 and 1.4](https://www.cs.toronto.edu/~sacook/homepage/cook_reckhow.pdf).

Bare semantic checks are not automatically efficient: checking F implies false
is UNSAT itself. A fast checker for a supplied implication certificate is useful,
but certificate length and construction time still need separate bounds.

## 2. A one-bit interface can hide NP-complete extension work

The smallest elementary counterexample uses

    R(a,b,c) iff a+b=c over Boolean values using integer addition,
    R = {000,011,101}.

R has precisely the ZERO-valid Schaefer signature. Its AND, OR, majority, and
minority closure failures are respectively 001, 111, 001, and 110, obtained from
011, 101, and, for the ternary operations, 000. Its complement has precisely the
ONE-valid signature.

Replace each positive exactly-one clause on a,b,c by

    R(a,b,s_j) AND R(s_j,c,t),

where s_j is fresh and all clauses share one t. Existentially eliminating s_j
gives a+b+c=t. At t=0 the whole formula has the all-zero solution. At t=1 it
expresses the original positive 1-in-3 SAT instance. Thus its exact projection
onto t is either {0} or {0,1}, depending on an NP-complete decision.

There are at most two boundary assignments in either case. The failure is the
cost of computing which assignments survive, even though the region is
trivially satisfiable before it is pinned. This defeats the inference that
small semantic messages plus unpinned tractability suffice.

The gadget is minimal in both arity and relation cardinality. All Boolean
relations of arity <=2 are majority-closed; every relation with <=2 tuples is
minority-closed. The complete arguments are now in
`../typed_merge_planner_lab/THEOREMS.md`.

Schaefer's original theorem explicitly distinguishes ordinary SAT from SAT with
constants: the latter permits only the four operation-preserved tractable cases,
not ZERO/ONE validity. See
[Schaefer, Section 2](https://www.khoury.northeastern.edu/home/lieber/courses/csg260/f06/materials/papers/max-sat/p216-schaefer.pdf).

### Implementation consequence

The existing native planner already used only AND, OR, MAJ, MIN, so this audit
found no earlier executed native-plan result that relied on the unsafe inference.
The unpinned relation-pair classifier was correct for its stated problem.

The API now explicitly supports `schaefer_pair_status(..., allow_pins=True)`.
For that query, shared ZERO/ONE validity no longer yields a polynomial claim.
Boundary merges also filter their tags through the four pin-preserving
operations. Existing unpinned classifications remain unchanged.

This matters if relation invention feeds its full six-tag signature back into
the planner: constant-validity tags cannot then accidentally authorize an
unbounded conditional merge.

## 3. Horn closure is safe only with an explicit representation contract

For boundary variables a_i,b_i,z and private y_i, consider

    F_m = AND_i ((a_i -> y_i) AND (b_i -> y_i))
          AND ((y_1 AND ... AND y_m) -> z).

F_m has 2m+1 Horn clauses and linear literal count. Its projection is

    P_m = ((AND_i (a_i OR b_i)) -> z).

An auxiliary-free CNF for P_m needs at least 2^m clauses. Here is a complete
counting witness. Take all 2^m assignments with z=0 and exactly one true bit
per pair (a_i,b_i); each falsifies P_m. A clause false on two such assignments
is also false on their coordinatewise meet. Their meet has a pair 00 and
therefore satisfies P_m. Consequently no valid clause can reject two members
of this family. The 2^m distributed Horn implications supply a matching upper
bound.

This does not obstruct a polynomial native Horn solver. Retain the compact
existential Horn formula, keep private variable names disjoint across children,
and answer boundary assignments by Horn satisfiability with unit pins. Native
conjunction merely combines the formulas after renaming; representation size
is additive. What fails is requiring every projection to be flattened into
polynomial-size Horn CNF over only boundary variables.

The typed planner currently models such merges rather than emitting the native
symbolic messages. A future implementation must preserve this auxiliary-bearing
representation, or account for any expansion explicitly.

## 4. A sharp adversarial family for graph-based coset solving

The native graph route exploits columns that can be interpreted as graph edges.
The immediate extension to arbitrary three-element columns already encounters
NP-completeness.

Start with a 3-dimensional matching instance with three parts of q elements
and a family of permitted triples. Let H have 3q rows and one binary column
per permitted triple, with exactly three ones indicating its three elements.
Let the target syndrome be the all-ones vector. Then

    exists x: Hx = 1 over GF(2), |x| <= q

holds exactly when the triples have a perfect 3-dimensional matching.

Proof: write c_i for the integer number of selected triples containing row i.
The syndrome condition makes every c_i odd, so c_i>=1. Hence

    3q <= sum_i c_i = 3|x| <= 3q.

Equality holds throughout: |x|=q and every c_i=1. The selected triples form a
perfect matching. The reverse implication is immediate. Construction is
polynomial and a proposed selection is easy to check. The starting problem is
one of Karp's NP-complete problems; see
[Karp, Reducibility Among Combinatorial Problems](https://www2.seas.gwu.edu/~simhaweb/champalg/tsp/papers/KarpOriginal.pdf).

This is a statement about arbitrary affine cosets, not homogeneous minimum
distance. It proves that a polynomial extension from graph-incidence decoding
to all three-element columns would resolve P=NP. Sparsity by itself cannot be
used as a substitute for a graph representation certificate.

Finite audit: all 256 subfamilies of the eight possible triples for q=2 were
checked, including all 6,561 family/selected-subfamily combinations. The two
predicates agreed in every case; 175 families have a perfect matching and 81
do not. The all-size proof above supplies the conclusion; these calculations
only check the implementation of the reduction on the small family.

## 5. Concrete next constructive attack

Keep the graph-plus-exception route as an exact parameterized algorithm and
make the difficult part an explicit discovery problem:

    Find a certified row-equivalent representation of H
    whose non-graph portion admits a small exact interaction interface.

The certificate should provide the row transformation, graph incidence map,
exception columns, and affine target transformation. Every branch must retain
the original weight accounting and the distinction between ordinary coset
optimization and exclusion of the zero word.

Measure the full cost of discovering that representation, local native solves,
cross-interface messages, and final witness reconstruction. More importantly,
formulate an all-size theorem for a specific nontrivial family where discovery
and the remaining interface complexity are provably bounded. Such a theorem is
stronger progress than another collection of random successes.

Use the three-element incidence family above as a mandatory boundary control.
Any claimed polynomial generalization must explain precisely how it decides
those instances. If it merely places all three-element columns in an exception
set, then exponential dependence on that set is expected and must be reported.
No theorem here guarantees logarithmically many exceptions on arbitrary inputs.

## 6. Verification and edited artifacts

Only the following source files were edited by this audit:

- `../typed_merge_planner_lab/engine.py`
- `../typed_merge_planner_lab/test_lab.py`
- `../typed_merge_planner_lab/THEOREMS.md`

`python -m unittest -v test_lab` in that lab passes **10 tests**, comprising
the four existing tests and six new tests. New checks cover the minimal
ZERO/ONE obstructions, pin-preserving classifications, minimality on all
Boolean relations through arity two and small-cardinality ternary relations,
all 16 positive 1-in-3 formulas on the four distinct triples of four variables,
rejection of unsafe constant-validity merge tags, and the Horn projection
family through m=4.

The Horn checks independently quantify local variables, compare the explicit
projection, and verify the pairwise-meet lower-bound witness. The mathematical
proofs hold for all sizes; the tests only validate their finite instances.

The historical lab manifest and recorded old test transcript were not rewritten;
they describe the earlier checkpoint, not this modified source snapshot.

## 7. Follow-up: executable reduction and all-redundant-check counterexample

The exact-cover reduction now has a standalone implementation in
`degree_three_barrier.py` with tests in `test_degree_three_barrier.py`. Besides
the 256 complete two-by-two-by-two matching families, tests cover all 1,351
arbitrary six-element families of at most three triples, duplicate sets,
malformed inputs, empty universes, and the necessity of the weight bound.

The same module has a supplied-row LP negative control on the [8,4,4] extended
Hamming code: pin x_7=1, set x_3=x_5=x_6=1/2, and set the rest to zero. Explicit
rational mixtures satisfy its four chosen parity checks with weight 5/2 even
though its true distance is four. This example is deliberately labeled as
supplied-row only: XORing the three index checks gives support {1,2,4,7} and
immediately excludes the point. A regression test verifies that repair.

A stronger exact control is in `all_dual_lp_barrier.py`. It verifies a
self-dual [24,12,8] code by its entire 4,096-word span. Pin any coordinate to one
and set all other coordinates to 1/7. The point has weight 30/7<=5, while every
pinned integer solution has weight at least eight. Exact rational subset
mixtures certify membership in **all 4,095 nonzero dual-check polytopes**.
Consequently even adding every redundant XOR check leaves an integer-threshold
false positive. In fact the fractional optimum is exactly 30/7: the 253
weight-eight checks through the pin contain each other coordinate 77 times,
so summing their singleton inequalities gives the matching lower bound.
Those incidence counts are checked for all 24 pins. No floating-point solver
is needed for this certificate.

`ALL_DUAL_LP_THEOREM.md` proves the general analytic witness for every code whose
dual distance delta is at least three: one coordinate equals one, all others
equal 1/(delta-1). It also proves, by a random-subspace union bound, existence
of code families with primal and dual linear distance. The pinned all-dual LP
then has an Omega(n) integrality gap. This is a lower bound on the accuracy of
this particular relaxation, not on general algorithms. It does not exclude
stronger cuts, extended formulations, branching, or native methods.

The nine degree-three/supplied-row tests and six all-dual tests pass. Together
with the ten typed-planner tests, this audit owns 25 passing tests. The extra
source artifacts are the two reduction/certificate modules and their two test
files. SciPy was used only for an intermediate small numerical search; all
delivered certificates and tests depend only on Python's standard library.
