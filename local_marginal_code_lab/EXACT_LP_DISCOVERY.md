# Reproducible exact LP discovery with SoPlex

Status: fresh affine-overlap optimum independently reproduced, reduced objective
**31/5**, total pinned weight **36/5**. This reproduces the existing 28-variable,
53-equality, 215-nonzero finite result. It is not a new optimum or a complexity
separation. The historical discovery process remains unrecorded; this is a new
search with preserved inputs, outputs, settings, and verification.

## Public method adopted

[SoPlex](https://github.com/scipopt/soplex) provides revised simplex, presolving,
scaling, iterative refinement, precision boosting, and rational reconstruction.
Those are established solver methods. Our addition is the source-bound adapter
and reproducibility record, not a new LP algorithm. Follow its
[exact-solver instructions](https://soplex.zib.de/doc/html/EXACT.php), including
zero primal and dual tolerances: requesting rational output alone is insufficient.

Credit: Gleixner, Steffy and Wolter, *Iterative Refinement for Linear Programming*,
INFORMS Journal on Computing 28(3), 449–464 (2016)
([author preprint](https://optimization-online.org/wp-content/uploads/2015/06/4948.pdf));
Gleixner and Steffy, *Linear Programming using Limited-Precision Oracles*,
Mathematical Programming 183, 525–554 (2020)
([author preprint](https://arxiv.org/abs/1912.12820)).
These references explain the borrowed numerical/exact methods, not the
Reed–Muller model or its novelty.

## Acceptance and trust

1. The producer reconstructs the affine geometry and equality quotient from
   source. It reads no saved primal vector, dual vector, basis, or expected
   optimum. Stable original row/column labels survive export.
2. The mathematical solver input is min c*x with A*x=b and x>=0. Coordinates
   are common per-atom masses, not total orbit masses. The reporting offset 1
   never enters c*x. Equality dual multipliers may have either sign.
3. SoPlex proposes named rational primal and dual vectors. Omitted zeros are
   accepted only in a complete recognized sparse-output section. Unknown names,
   duplicates, decimals, truncated sections, and nonoptimal statuses fail.
4. The generic independent checker requires exact nonnegativity, Ax=b,
   c-A^T*y>=0, and c*x=b*y. It imports neither the exporter nor the solver.
   A hash alone binds a supplied LP; it does not prove that LP encodes RM(2,5).
5. The source-bound wrapper independently reconstructs A,b,c from affine
   geometry using the existing separate reviewer and compares the entire
   canonical model, including labels and offset, before accepting the candidate.
   The mathematical quotient-equivalence theorem remains a separate dependency.

An exact optimum is accepted for this affine-overlap model. The existing
full-level-eight primal certificate and model-containment proof are still
needed for the corresponding full-model result. This run does not rediscover
the 2,174-variable full-model certificate or any polynomial-cut certificate.

Failure, timeout, unsupported solver output, source changes during a run, and
unverified infeasible/unbounded reports produce UNKNOWN. No Farkas or unbounded
ray checker is provided. INVALID means a certificate failed checking, not that
the LP is infeasible. This is a modular Python verification chain, not formal
verification of the mathematical definitions or the implementation.

## A real negative control

The first trial enabled rational reading, solving, output and checking, but
left feasibility/optimality tolerances at their defaults. SoPlex reported
optimality and printed a rational objective
55844635379394169/9007199254740992. The row-zero equality residual was
23/288230376151711744, not zero. The independent checker rejected it.

[EXACT_LP_TOLERANCE_CONTROL](EXACT_LP_TOLERANCE_CONTROL/discovery.json)
preserves the rejected candidate, model, command arguments and raw textual
solver diagnostics. Its UNKNOWN is an observed outcome. It is not evidence
that SoPlex is mathematically incorrect: its stated tolerance contract was
weaker than this repository's exact acceptance contract. Regression tests
replay this failure alongside a signed-dual control whose optimum is four.

## Reproduce verification without SoPlex

From this directory, with Python 3.10 or newer:

    python run_exact_lp_discovery.py --replay EXACT_LP_DISCOVERY
    python -m unittest -v test_exact_lp_model test_exact_lp_verify test_exact_lp_soplex
    python -O -m unittest -v test_exact_lp_verify test_exact_lp_soplex

The replay reads committed evidence and does not overwrite historical
measurements. Tests include malformed rational data, objective/source changes,
wrong dual signs, alternative valid optima, parser truncation, timeouts,
launch failures, and acceptance under optimized Python.

The combined [focused validation record](EXACT_LP_FAMILY_VALIDATION.json)
passes 54 tests covering the adapter, checker, exporter and quadratic-family
controls, plus 45 repeated tests under optimized Python. Source hashes stayed
unchanged during those runs. This is not the full repository test suite.

## Reproduce fresh discovery

Use SoPlex **8.1.0**, built with GMP. The measured Windows binary is distributed
in the official [SCIP Optimization Suite 10.1.0 release](https://github.com/scipopt/scip/releases/tag/v10.1.0),
asset scipoptsuite-10.1.0-win-x64.zip. Its published archive SHA256 is
e71bafb8ce3c26386ae0d93cdd51867f21eb74b70986bbd696b7b864a3c355ff.
The measured soplex.exe SHA256 is
8a18cfe1f6c5b844d79afea179aacb755b1ee1e63a3bb0b07dd661ad22eaaf26.
Keep its required runtime DLLs and upstream licenses together. No vendor
binary is committed or installed into the system environment.

    python run_exact_lp_discovery.py --soplex /path/to/soplex --output-dir /path/to/new-run --timeout 600

The output directory must be new or empty. Other platform builds of 8.1.0
may return another optimal solution or basis; exact feasibility and matching
primal/dual values are the acceptance condition. The adapter rejects other
versions until their formats/settings have been explicitly checked.

The preserved arguments use rational input, forced rational solving,
synchronized rational data, zero feasibility/optimality tolerances, rational
final checks, and separate rational primal/dual outputs. Neither an expected
objective nor a warm-start basis is supplied.

## Costs and limitations

[discovery.json](EXACT_LP_DISCOVERY/discovery.json) records construction,
search, and independent reconstruction/checking as separate fresh processes.
Wall time includes process startup and output. Search time excludes model
construction and verification. RSS is sampled approximately every 20 ms and
is explicitly a lower bound on the true process peak, especially for the
short solver run; it is not a guaranteed peak-memory measurement.

The recorded Windows/Python 3.10.10 run measured:

| Stage | Wall seconds |
| --- | ---: |
| Source model construction and export | 46.230238 |
| Fresh SoPlex search and output | 0.076472 |
| Independent source reconstruction and exact verification | 47.378427 |

For this fixed small quotient, rebuilding geometry dominates solver time.
This observation does not imply the same cost balance for larger quotients.

The record includes Python/platform details, solver version/binary digest,
complete logs, artifact hashes after LF normalization, and source hashes
before and after the run. It is one finite workload, not a benchmark proving
SoPlex is faster than another exact solver or that this model scales well.
The exporter also exposes a full-level-eight builder, but that larger search
has not been executed by this recorded workflow.
