# Exact discovery with a nine-coordinate distribution

The optional public SoPlex backend now discovers an exact reduced optimum
of **7**, total pinned weight **8**, for a source-built extension of the
RM(2,5) affine-overlap LP. The independent checker reconstructs every row,
column, support atom and objective before checking exact primal and dual
feasibility. No saved solution, basis or expected optimum was supplied to
this fresh search.

This is a finite LP certificate, with a separate mathematical consequence:
every full level-nine solution projects to this selected model after symmetry
averaging, and a genuine pinned weight-eight codeword supplies the opposite
bound. Therefore the full RM(2,5) level-nine optimum is reduced 7 / total 8.
The [family proof](REED_MULLER_QUADRATIC_LEVEL9_THEOREM.md) supplies the additional
argument for all dimensions. The LP checker alone does not prove that argument.
Novelty is **UNKNOWN**, and P versus NP is unchanged.

## What changed in the model

Start with the original 28-variable, 53-row affine-overlap quotient. Add a
probability table on the nine nonpin coordinates
`S={16,17,...,24}` of `GF(2)^5`. The first eight form an affine three-flat;
the ninth is outside its linear span.

The producer evaluates the pinned quadratic monomials and spans their local
evaluation vectors. The reviewer independently enumerates all 32,768 settings
of the fifteen nonconstant coefficients. Both obtain the same 256 allowed
atoms. New variables are their individual probabilities, with normalization.

For **every** nonempty `A ⊆ S` whose affine closure has at most eight points,
equate its all-ones moment to the corresponding moment of the original
selected-flat table on that closure. There are 362 such equations, including
98 whose closure extends outside `S`. Omitting those cross-boundary equations
would change the model. Quotient variables are common per-atom probabilities,
so the equations retain atom multiplicities.

The final LP has **284 variables, 416 equality rows and 10,089 nonzeros**.
This is a necessary selected model for full level nine, not an enumeration
of the full all-scope level-nine quotient. Its exact optimum is enough for the
lower bound; a separate upper-bound construction is essential.

## Fresh discovery and verification costs

The [run record](RM2_NINE_SCOPE_DISCOVERY/discovery.json) pins the environment,
solver executable hash, arguments, source hashes before and after the run,
and all artifact hashes. The source remained unchanged.

| Stage | Wall time | Maximum sampled resident memory |
| --- | ---: | ---: |
| Source model construction | 44.732151 s | 109,998,080 bytes |
| SoPlex search | 0.231767 s | 18,202,624 bytes |
| Independent reconstruction and exact replay | 45.930733 s | 114,417,664 bytes |

Memory uses 20 ms samples of the child process. These are lower bounds on
true peak memory, exclude the parent, and are not process-tree isolation.
The timings are one workstation run, not a comparative performance claim.

The canonical model JSON is 201,854 bytes; the primal/dual candidate JSON is
7,226 bytes. Its 93 nonzero primal and 202 nonzero dual entries have maximum
absolute numerator and denominator bit lengths 9 and 8 respectively.
These are finite measurements, not polynomial bounds in the ambient dimension.

## Reproduce

From this directory, replay without an external solver:

```text
python run_rm2_nine_scope.py --replay RM2_NINE_SCOPE_DISCOVERY
python -m unittest -v test_rm2_nine_scope test_rm2_level9_family
python -O -m unittest -v test_rm2_nine_scope test_rm2_level9_family
```

The [focused validation record](RM2_NINE_SCOPE_VALIDATION.json) binds
20 passing test methods under normal Python and the same 20 under `-O`.
The [upper-table review](RM2_LEVEL9_FAMILY_REVIEW.json) checks 168 specified
or seeded scopes, 59,221 moments, and 3,193 complete proper marginals.
It does **not** enumerate every nine-point configuration; the written proof
provides the all-size argument. Current-commit whole-repository CI is a
separate check.

For a fresh search, use the SoPlex 8.1.0 executable from the pinned release
documented in [EXACT_LP_DISCOVERY.md](EXACT_LP_DISCOVERY.md), with a new directory:

```text
python run_rm2_nine_scope.py --soplex PATH_TO_SOPLEX --output-dir fresh-nine-scope --timeout 600
```

Exact reading/solving, synchronized rational input and zero feasibility and
optimality tolerances are explicit. A failed launch, timeout, changed source,
unusable solver output or rejected certificate produces `UNKNOWN`.
The independent mathematical checker requires nonnegative primal entries,
every equality, nonnegative recomputed dual reduced costs, and matching exact
objectives. It imports neither this model producer nor the solver/exporter.
It does share the original independent affine reconstruction and generic
rational-checking infrastructure; this is not proof-assistant independence.

## Retained intermediate failure

Before adding an actual nine-point table, the weaker experiment added only
`p - 8q + 28r >= 0`. It follows from nonnegativity of
`t(t-2)(t-3)/2` on integer weights, since the nine-point scope has no
zero-sum triples. This is a valid integer polynomial cut; no bounded-degree
SOS representation is claimed.

The [intermediate control](RM2_NINE_POINT_CUT_CONTROL/control.json) preserves
an exact selected-model optimum `1147/184`, total `1331/184`, and the original
solver logs. Separate stage timing and source snapshots were not recorded
for that preliminary probe. Its model and certificate can still be rebuilt
and checked independently:

```text
python review_rm2_nine_scope.py --cut RM2_NINE_POINT_CUT_CONTROL
```

The saved primal is a mixture of the previous witness and the all-one word.
The cut is tight, forcing any proposed nine-point extension to have weight
only 0, 2 or 3. But its four-point moment is `1/736`, which would force positive
mass on weights at least four. That particular primal therefore cannot extend.
The stored selected-model optimum must not be reported as a full-L9 optimum.
The later explicit distribution model resolves this issue by imposing the
missing moment compatibility.

## Sources and scope

Exact LP discovery uses public methods documented by
[SoPlex](https://soplex.zib.de/doc/html/EXACT.php) and its
[source repository](https://github.com/scipopt/soplex); the binary comes from
[SCIP Optimization Suite 10.1.0](https://github.com/scipopt/scip/releases/tag/v10.1.0).
The precise pinned tool and the earlier rejected numerical-tolerance control
are recorded in the existing discovery instructions.

Code parameters and minimum-weight parity-check geometry are inherited from
the coding literature cited in the family proofs. Symmetry averaging,
Boolean moments and LP weak duality are established methods. The finite
certificate, explicit model and written family argument are the repository's
current objects of study; their novelty remains unestablished.
