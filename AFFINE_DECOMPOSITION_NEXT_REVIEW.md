# Next route: certified sums of affine networks

The new exact affine/quadratic-phase evaluator extends to every SAT instance
by an explicit signed decomposition. The useful parameter is the number of
terms actually generated, not the fact that each term is easy. The read-only
checkpoint audit below changes the implementation recommendation: **do not
build another unit-residual/backdoor solver**. Reuse the existing discovery
and boundary machinery, with the now-reviewed certificate repair below, and add
weighted affine boundary messages plus a checked decomposition DAG. A small
branching set is a baseline, not a new project capability or a general bound.

These are applications of elementary inclusion-exclusion and the established
backdoor approach, not novelty claims. Williams, Gomes and Selman define a
strong backdoor by requiring every assignment to the selected variables to
enter the tractable class; see [Definitions 2.2–2.4](https://www.ijcai.org/Proceedings/03/Papers/168.pdf).
Affine holographic target classes on general graphs are also established;
see Cai, Guo and Williams, [Holographic Algorithms Beyond Matchgates](https://arxiv.org/abs/1307.7430).
The proposal below uses the narrower exact real-affine evaluator implemented
here, not every transformation covered by that literature.

## Read-only checkpoint audit: reuse and limits

The following paths are relative to the canonical checkpoint. These are
observations from the actual code, not just the lab names.

| Existing artifact | Reuse | What it does not already supply |
|---|---|---|
| `polymorphism_backdoor_lab` | Its macro/Schaefer conclusions and adversarial examples. | This directory contains documentation and measurements, with no current Python engine or test file despite its README command. Do not treat it as an executable backdoor API. |
| `proof_motif_candidate_lab/miner.py`: `detect_parity_blocks`, `verify_parity_block`, equality detectors/verifiers | Actual fixed-arity XOR and equality discovery from original clauses; retain source clause IDs and replay semantic checks. | Signed quadratic phases, weighted projection and counting multiplicities. Replacing a verified block by the same Boolean relation preserves counts only while retaining its variables or accounting for their extensions. |
| `automatic_parameter_discovery_lab/engine.py`: `simplify`, `incidence_components`, `normalize_variables`, `_horn_depth_norm`, `verify_horn_depth_certificate` | Existing normalized cached branch/component search and structural certificate design. | Search is worst-case exponential; the leaf solver is Boolean Horn SAT, not exact counting or a signed sum. Variable renaming drops absent variables, so a counting adapter needs explicit maps and free-variable multiplicities. |
| `parameter_reduction_engine_lab/engine.py`: `affine_propagate`, `cross_theory_fixpoint` | Existing native GF(2)/CNF propagation and its mixed fixtures. | Phase-sensitive weighted counts or a complete polynomial discovery theorem. |
| `semantic_branch_dp_lab/engine.py`: boundary annotation, `leaf_message`, `merge_messages`, `canonical_tt` | Region ownership, ordered boundaries and the join/project recurrence, as bounded reference oracles. | Messages are existential Boolean bits. `canonical_tt` records recurring types after computing them; it does not avoid those computations. Its indexing is MSB-first, unlike the new LSB tensor modules. |
| `symbolic_projection_portfolio_lab/engine.py::affine_project` and `automatic_region_abstraction_lab/region_dp.py::AffineRegion` | Symbolic affine support projection and native extendability controls. | The former returns support equations, the latter a Boolean answer; neither retains extension counts or signed phases. |
| `overnight_research_2026_10_18/holographic_tractability_lab/affine_holant.py` | The newly audited local affine certificates, exact phase algebra and closed-network evaluator/verifier. | Its public result is a scalar contraction. The proposed addition is a reusable **open-boundary weighted** summary and a DAG of sums of such summaries. |

The two-variable branching example below already falls within the historical
Horn branch/component design for decision. A new implementation resolving
only that example would duplicate the old route. It is useful only as a
small count-preservation/regression test of a more capable interface.

### Historical verifier gap: repaired and independently reviewed

The historical `semantic_branch_dp_lab/engine.py::verify_dp_certificate`
recomputes listed node boundaries and tables but does not require the root
to own every original clause, or children to partition their parent's clause
IDs. The following actual read-only execution was accepted:

```python
sat, root, _, _ = solve_branch_dp([(1,)])
original = [(1,), ()]  # x AND the empty clause: UNSAT
assert sat is True and root.clause_ids == (0,)
assert verify_dp_certificate(root, original) is True
assert brute_sat(original) is False
```

The returned acceptance is wrong as a certificate for the external original
formula: it omits the empty clause. Before reusing this verifier, require
root ownership of all original clause IDs exactly once, valid IDs, and
disjoint exhaustive child partitions at every internal node, in addition
to boundary/table checks. Add this exact regression and mutation tests.
For a future shared DAG, distinguish sharing computed messages from silently
dropping original factors; edge references still require verified ownership
and variable maps. No historical code was changed by this review. The
baseline reviewer implemented the historical repair; its final source and
provenance are frozen in the [repair record](SEMANTIC_CERTIFICATE_REPAIR.md)
and [machine-readable record](SEMANTIC_CERTIFICATE_REPAIR.json). The
reproduction above describes the pre-repair source; the repaired verifier
rejects it.

Independent review found no correction needed: all 16 repaired tests passed,
and 400 additional original formulas checked all 2,884 boundary messages
against direct assignment projection. All 2,884 single-table-bit mutations
and all 400 additions of an omitted original empty clause were rejected.
The independent seed was 2026101847. Before/after source hashes agreed:
`engine.py=f17f0380015652d9f4a3d7ffd452de70c4e71f9eb5c85f5f4d22d916b1af41aa`
and `test_lab.py=18a3e87ecd6be99c1a6d9a1853f85341a4b915e1c3dbe41b495c7c464dc7bc36`.
This review note is now frozen for the parent manifest refresh as well.

This defect concerns the **historical semantic-branch verifier only**. It is
not a defect found in the four newly audited holographic-phase labs
(`tensor_basis_lab`, `simultaneous_basis_lab`, `crossing_sign_lab`, and
`holographic_tractability_lab`); their current phase remains frozen.

## Complete exact decomposition

For a clause C with literal truth values `l_1,...,l_k`, let
`V_C=product_j [l_j=0]`. Then, pointwise,

`OR_C = 1 - V_C`.

Both 1 and V_C are affine-support tensors with constant phase. Negated
literals just change the pinned bits. After deleting tautological clauses
and duplicate literals, these identities include units and the empty clause
(whose violation indicator is 1). They preserve ordinary SAT counts; the
slack factor `[0,1,2,1]` must not be substituted for OR without changing the
claimed count.

Suppose d remaining OR clauses multiply an already certified affine core
in the same Boolean coordinates. Combining its local constraints and signs
gives a core of the form

`H_0(x)=lambda * [A x=b] * (-1)^q(x)`,

where q has degree at most two over GF(2). Its variables may be tensor-edge
bits, with copy equalities among the linear constraints. Distributivity gives

`Z = sum_{S subseteq [d]} (-1)^|S| * sum_x H_0(x) product_{i in S} V_i(x)`.

Every inner expression adds only linear pins to the core, so the affine
evaluator applies on arbitrary topology. This covers ordinary CNF completely:
use the equality core, identity basis, `lambda=1`, `q=0`, and take d to be
the number of clauses not already incorporated as affine constraints. There
is no assertion that a generic CNF has a large affine core automatically.
If a different basis has changed the clause tables, its actual transformed
tables require their own checked decomposition; the OR identity cannot be
silently applied to those changed tables.

For pure CNF each inner value is 0 or `2^(n-rank)` after consistent pins.
Nevertheless its signed contribution can cancel another term. For example,
`(x) AND (not x)` gives `2-1-1+0=0`. A positive partial sum is not a
satisfiability certificate, and a zero individual affine value is not an
unsatisfiability certificate for the whole formula. Complete exact summation
recovers the original nonnegative integer #SAT; positivity then decides SAT.

With evaluator cost `T_aff(N)` on a polynomial-size affine description, this
method costs `2^d * (T_aff(poly(N))+poly(N))`. In the unweighted CNF case
each summand has magnitude at most `2^n`, so partial sums need at most
`n+d+O(1)` bits. A common rational core scale lambda adds its numerator and
denominator bit lengths. Streamed enumeration needs polynomial workspace;
storing a table of all distinct terms can take exponential space. Explicit
certificates for every leaf have corresponding exponential total size.

Avoid an accidental `2^(variable degree)` input expansion: encode copy
constraints as linear equations or bounded-arity equality trees, with a
unique auxiliary extension for each assignment. Here n is the number of
actual variables being counted, not an unchecked compressed header value.

## A stronger implementable parameter: a supplied affine backdoor

For a supplied variable set B of size b, use the exact, disjoint identity

`1_F(x) = sum_{beta in {0,1}^B} [x_B=beta] * 1_(F restricted by beta)(x_not_B)`.

If every restricted tensor network is certified affine, this is a sum of
`2^b` affine networks and is evaluated in `2^b poly(N)` time. It counts each
original assignment once. Pinning a pre-existing quadratic phase leaves
degree at most two, so affine cores remain in the class. Every leaf, its
restriction map and its affine certificate must be checked; an unverified or
capped leaf makes the aggregate UNKNOWN.

There is a particularly simple sufficient criterion that can also be found
constructively: require B to contain all but at most one distinct variable
of every residual OR clause. After assignment, each clause is either true,
false or a unary pin. Build the clause primal graph, connecting every pair
of variables appearing in a residual clause. Exactly this sufficient
condition says that B is a vertex cover of that graph. To find a cover of
size at most b, choose an uncovered edge uv and recurse on including u or
including v; any cover must do one of these. The complete search has at
most `2^b` leaves and polynomial work per node. Thus discovery as well as
evaluation has a proved `2^b poly(N)` bound for this specified criterion.
It does not recognize every possible small affine backdoor.

## Exact counterfamily for naive identical-term merging

Consider the connected ternary formula

`F_m = AND_{i=1}^m (x OR y OR z_i)`.

Expand the two-term clause identity, and merge only terms having identical
canonical affine supports and phases (RREF and a restricted quadratic phase
are possible keys). The empty subset contributes the unrestricted support.
Every nonempty subset S contributes

`(-1)^|S| * [x=0,y=0,z_i=0 for i in S]`.

All these `2^m` supports are distinct and nonempty; all phases are zero and
all coefficients are nonzero. To distinguish two nonempty supports, choose
an index in their symmetric difference, set its z-bit to one, set all other
required z-bits to zero, and set x=y=0. The unrestricted support also differs
from every pinned support. Therefore this particular expansion-and-equality-
merging algorithm has exactly `2^m` surviving terms, even though the
incidence graph is connected.

This is **not** a lower bound on affine decomposition size or on SAT
algorithms. Indeed B={x,y} satisfies the criterion above. Its four branches
have counts `1,2^m,2^m,2^m`, so

`#F_m = 3*2^m+1`.

The same follows directly from the signed expansion:
`2^(m+2) + sum_{nonempty S} (-1)^|S| 2^(m-|S|)=3*2^m+1`.
Independent enumeration for m=1,...,8 checked the distinct-term counts
`2,4,...,256`, the four branch counts, and original truth-table counts
`7,13,25,49,97,193,385,769`. The displayed proofs establish the all-m claim.
Factoring or a better decomposition defeats this example; that is the
intended distinction between a bad merge rule and a general lower bound.

## Additional executable capability worth building

The first real extension should export the weighted boundary function

`M(b)=sum_internal lambda*[A(b,x)=c]*(-1)^q(b,x)`

as a compressed affine-support/quadratic-phase object, rather than a scalar
or a `2^|boundary|` Boolean table. There is a direct closure proof, suitable
for a short step certificate. Eliminate one internal bit t at a time:

- If a support equation fixes `t=a(x)` for an affine function a, substitute
  in every remaining equation and in q. Each permitted remaining assignment
  has one extension, and substituting an affine function into a quadratic
  preserves degree at most two.
- Otherwise t occurs in no support equation. Write
  `q(t,x)=q0(x)+t*L(x)` with L affine. Then its exact sum is
  `2*lambda*[A x=c]*[L(x)=0]*(-1)^q0(x)`. Add that linear equation and
  multiply the scalar by two; inconsistent constraints yield zero.

Repeating these steps gives another object of the same form, with polynomial
description size and arithmetic cost for **one** affine term. It retains
signs and multiplicities that the historical existential projection erases.
The necessary new verifier checks each substitution or summation identity
symbolically; it must not enumerate a large boundary truth table. The
existing closed-network evaluator is the zero-boundary regression oracle.
The independently written [boundary design](AFFINE_BOUNDARY_DESIGN.md)
also derives closure by block parametrization and internal quadratic pairs,
and specifies bit costs and certificate fields for this primitive.

Two exact controls distinguish this new output from Boolean projection:
`sum_t (-1)^(t*b)=2*[b=0]`, although every boundary value has internal
assignments; and `sum_(s,t) (-1)^(s*t+s*a+t*b)=2*(-1)^(a*b)`, whose
boundary support is full but whose sign varies. Independent products of k
copies give compact outputs `2^k*[b=0]` and
`2^k*(-1)^sum_i(a_i*b_i)` on k and 2k boundary bits, respectively. Their
symbolic descriptions grow linearly while full tables grow exponentially.
These are exact primitive tests, not hard SAT benchmarks or new complexity
claims.

Then extend the old boundary recurrence to **sums** of these objects.
Multiply child sums, add support equations and phases, eliminate only truly
internal variables, and combine equal weighted functions. Fix the ordered
boundary variable IDs; canonicalize the support by full RREF, choose its
canonical free-variable coordinates, restrict q to those coordinates, and
absorb its constant sign into the rational coefficient. Equal canonical
keys may safely combine coefficients, including cancellation to zero.
Arbitrary renaming requires an explicit checked interface map. This adds
dynamic merging of signed residual functions, rather than merely counting
equal truth-table types after computation.

A source-bound arithmetic DAG should record original clause identities,
verified macro replacements, product/join nodes, exact projection steps,
branch sums and reuse edges. Start with the two-term clause identity and
reuse the existing backdoor/component planner as one strategy; do not make
a new unit-only solver the headline. A shared subproblem is evaluated and
certified once. However, product nodes can create `K_left*K_right` terms;
canonical merging, DAG sharing and scalar cancellation do not prove a
polynomial bound. Charge discovery, pre-merge products, retained terms,
coefficient bits and verification separately, with UNKNOWN on exhaustion.

## Tests beyond the current 40-formula batch

Keep the current same-input comparison as regression only. Before claiming
an extension, serialize and hash original instances from existing larger
sources, including all variables, original clauses, modes and any native
equations. Do not choose a renamed easy instance after a capped run.

1. Reuse the original clauses stored in
   `coefficient_structure_lab/RESULTS.json` for the connected 40-clause
   chain, the bad/good-order star, complete interaction at 16 variables,
   and the planted 24/96 and 32/128 mixed 3CNFs. The saved exact coefficient
   references are **slack counts**; ordinary SAT counts need separate
   original-assignment or exact count references. A planted witness proves
   SAT but does not supply the exact count. Preserve UNKNOWN where no full
   count is certified, and compare to prior method/status on the same input.
2. Reuse `mixed_family(..., connect=True/False)`, `sliding_cnf`, and the
   XOR/equality fixtures from the historical modules above. Include missing
   parity clauses and flipped RHS controls. Already-solved propagation or
   component cases must be reported as baselines, not newly solved SAT.
3. Test the new boundary capability itself: large signed quadratic-phase
   regions with small OR defects, contradictory pins, zero and negative
   conditional sums, overlapping supports, disappearing free variables and
   renamed interfaces. Small originals must agree on **every** boundary
   assignment with direct summation. Large runs need symbolic step replay
   and closed-contraction cross-checks under independently chosen boundary
   pins, not just membership tests.
4. Include `F_m` for the proved `2^m` versus four-branch distinction, but
   require at least one count/weighted-boundary capability absent from the
   old Boolean solver and test actual unresolved original requests. Record
   no improvement if the larger hard cases still cap. This is an outcome,
   not permission to silently shrink the benchmark.

No larger benchmark or new capability has been executed in this review;
these are acceptance criteria for the next implementation, not results.

## Unresolved theorem

The missing result is a **uniformly constructible, polynomial-total-size
decomposition or evaluation DAG for every SAT instance**, together with
polynomial-bit coefficients and a polynomially checkable preservation
argument. Existentially small sums, guessed small backdoors, or many easy
leaves do not establish it. A constructive polynomial sum evaluated by this
method would compute exact #SAT in polynomial time, a stronger objective
than merely deciding SAT. That observation neither proves such sums
impossible nor replaces the need to discover and verify them. A different
decision-only route remains open even if this exact-count route stalls.
