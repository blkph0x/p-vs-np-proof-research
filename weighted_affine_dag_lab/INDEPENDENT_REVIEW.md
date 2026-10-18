# Independent review of weighted affine message composition

Reviewed the frozen `dag.py`, `THEOREM.md`, tests and saved original requests.
No soundness defect or required source change was found. Only independent
review artifacts were added. This is a mathematical/source audit with independent bounded
and symbolic checks, not a proof-assistant formalization.

## Original factors and variable ownership

The boundary invariant is sufficient: a node owns a set S of original
factor occurrences and sums only variables in their normalized scopes that
appear nowhere outside S. Shared child variables therefore remain in both
child boundaries until their parent is entitled to sum them. Passing exactly
the union of child boundaries as the marginalizer's active set prevents
double counting an already eliminated variable, or accidentally counting
unrelated positions of the original universe.

The verifier reconstructs scopes and leaf decompositions from the external
original factors. Leaves own one factor occurrence; every product partitions
its ownership between disjoint children; the root covers every occurrence.
Topological child indices exclude cycles, and unused structural nodes are
rejected. A nonempty owned subtree cannot be shared by two eventual product
branches without violating disjoint ownership at their common ancestor.
The only empty ownership identity is permitted for the empty original input.
Arithmetic-request sharing is separate and safe because the complete derived
request, not merely its cache hash, is checked each time.

OR normalization preserves the original function, including duplicate
literals, tautologies and empty clauses. It does not reduce original n.
Variables disappearing from every normalized scope receive the final factor
two exactly once. Conversely, native affine scopes retain explicitly owned
variables even when their expressions are constant in those variables. Zero
children and signed cancellations remain zero; they do not authorize dropping
an original factor or interpreting a signed zero as a general SAT certificate.
Only the original CNF wrapper makes the nonnegative integer count claim.

## Products, canonical merging and dependency proofs

The checker enumerates every ordered pair of independently verified child
pieces. List length and full request equality detect missing, extra or
misbound terms. Each first reference to a marginal record invokes the affine
trace verifier and consumes its freshly reconstructed message. Saved
convenience keys and producer counters are not used as evidence.

Canonical support and phase descriptions make scalar-independent keys valid
for coefficient merging: equal keys denote the same function up to scalar.
Exact rational additions preserve negative coefficients and cancellations.
Removing a zero coefficient is valid. The method does not claim to find all
linear dependencies between different affine components; this limited merge
rule and the chosen structural plan can still expand exponentially.

All pre-merge pairs are charged before merging, including pairs that later
cancel or share a marginal request. Intermediate merge dictionaries obey the
term cap. Distinct verified marginal records and structural nodes obey their
node cap. A boundary subcall has its own caps; its measured work is charged
to the enclosing budget after the call. Thus the outer work cap is an
operation-accounting limit, not a preemptive wall-clock bound. The theorem
appropriately includes additional hashing, bookkeeping and bit costs, and
states no polynomial bound on the number of pieces or generated products.

## Independent checks

- All 14 supplied tests passed in 1.098 seconds, including every-message
  bounded oracles, typed/request/ownership mutations, product accounting,
  signed values, and UNKNOWN behavior.
- An additional 200 held-out mixed OR/affine requests were checked in random
  original factor orders. Direct evaluation enumerated 3,591 complete original
  assignments. Independently reconstructed intermediate supports were used
  to verify 4,306 structural boundary values. These include explicit native
  scopes, unused variables, repeated literals, tautologies, inconsistent
  equations, constant phases, and negative/rational/zero scalars.
- All 1,155 marginal records in those requests were independently recomputed
  and certified by `affine_boundary_reference` using block support
  parametrization, left-nullspace checks and internal quadratic-pair
  elimination. Their entire symbolic outputs agreed with the production
  messages, including support, phase on support and scalar sign.
- The saved 16 EXACT and two intentional UNKNOWN cases were replayed from
  their original requests. The wide analytic counts were checked against
  their stated identities. All 580 saved exact marginal records were also
  compared against the independent block reference; wide boundaries were compared
  symbolically, without expanding their truth tables.
- All saved source/dependency hashes remain current and no checked source
  changed during the review.

The independent production-boundary artifact cross-check is separately saved
as `../affine_boundary_reference/BOUNDARY_CROSSCHECK.json` and its accompanying
Markdown/script. It records 96 independently recomputed, reference-verified,
symbolically equal EXACT outputs, including 512 retained coordinates, with
six UNKNOWN controls and source/result hashes.

The additional weighted-DAG audit is replayable with
`python independent_review.py`. Its `INDEPENDENT_REVIEW.json` stores every
held-out original request, the fixed generator seed, oracle totals, all
1,735 marginal-check bindings and outcomes, saved-case indices, and exact
production/dependency/replay-script/result-file hashes. The run asserts the
reported 200/3,591/4,306/1,155 and 16/2/580 totals and that every hashed input
remains unchanged. Saved complete production certificates remain in the
hash-bound `RESULTS.json`; the replay recomputes held-out certificates from
their original requests.

The positive conclusion is correct weighted composition and compact affine
elimination under the declared scopes and caps. The documented original
formulas that exceed term/node caps remain unresolved by this implementation;
neither these failures nor the successful controls settle P versus NP.
