# Bounded whole-sum recognition inside the affine DAG

**P versus NP remains unresolved.** This phase tests whether the complete
explicit-sum recognizer can help after the existing greedy affine DAG has
already produced a valid output. It is a bounded integration experiment, not
a polynomial SAT algorithm.

## Fixed policy

The policy was frozen in `globally_compressed_affine_dag_lab/POLICY.md` before
the original-formula comparison. Recognition is attempted only after a
successful mandatory greedy stage, for 2--16 nonzero output pieces, retained
width at most 12 and original dimension at most 256. Each attempt has caps of
50,000 work units, 64 norm queries, 2,048 pair contractions, 128 point
evaluations and 2,048 certificate products. The fast rejection probe is capped
at 64 samples, 16 cubes and 20,000 probe work units inside the same attempt.

Aggregate recognition limits are 1,024 attempts, 1,000,000 work units, 4,096
norm queries, 65,536 pair contractions, 8,192 point evaluations and 65,536
certificate products. Recognition work is also charged to the unchanged
3,000,000-work DAG limit.

An exact one-piece result replaces the derived list only after fresh equality
verification. A certified rejection, or a local UNKNOWN, keeps the valid greedy
list and records the consumed work. If the mandatory greedy stage fails first,
recognition is never called. Verification derives every recognition input from
freshly checked original factors and ignores producer counters.

## Results on the frozen original formulas

The runner uses original clause occurrence order and reads the same 22 stress
and 58 earlier requests used by the compression comparisons.

| Dataset | Previous exact | Integrated exact | Previous UNKNOWN | Integrated UNKNOWN |
|---|---:|---:|---:|---:|
| 22 stress requests | 11 | 11 | 11 | 11 |
| Earlier 58 requests | 54 | 54 | 4 | 4 |

There were 3,509 recognition attempts. The fast stage produced 3,453
source-bound one-piece rejections and 55 local UNKNOWN identity events; no
attempt produced an exact one-piece replacement. The run evaluated 28,860
probe samples, 5,455 cubes, 23,660 pair contractions and 4,769 norm queries.
Recognition consumed 6,053,821 recorded work units within the separate
per-formula aggregate limits, and the complete solver work across the 80 fresh
runs was 39,816,725 units. These counters are operation conventions, not
runtime or asymptotic bounds. The recognition stage increased cost on this
benchmark without improving coverage.

This is a useful negative result: the complete one-piece primitive does not
rescue the known greedy failures, and the optional adapter does not turn a
representation test into a general SAT method.

## Independent checks

The adapter's 30 tests pass. They cover signed and zero replacements, source
binding, certificate mutation, aggregate and local cap behavior, skipped
triggers, failed mandatory compression, untrusted statistics and sparse or
wide coordinates. The fast recognizer has nine tests, including all three
cheap obstructions and strict resource behavior.

The independent fast-wrapper review replays all 494 saved explicit-sum
requests. It checks all 464 requests with at most three coordinates against a
separate direct truth-table and quadratic-sign oracle, rejects 12 rebinding
mutations, and finds no false UNSUPPORTED or false EXACT result. Larger cases
receive fresh certificate replay; UNKNOWN remains unclaimed.

The comparison audit binds the current source hashes, fixed policy and all 80
rows. It confirms the post-run exact counts only after each fresh result is
computed; it does not provide expected answers to the solver. The audit and
comparison are in `globally_compressed_affine_dag_lab/COMPARISON_AUDIT.json`
and `COMPARISON_RESULTS.json`.

The follow-up reproduction script passes **43 unit tests** across the fast,
integrated-DAG and positive-cover suites, then rechecks the gram-conditioning,
fast-wrapper and comparison audits. `FOLLOWUP_ARTIFACT_AUDIT.json` binds the
resulting 16 evidence, runner and report files. Its scope is fresh hashes and saved
arithmetic consistency; the expensive formula run is represented by its
source-bound comparison record rather than silently rerun during the audit.

The integration does not search all proper subsets, does not handle a retained
size overflow before the greedy stage emits an output, and does not establish
P=NP or P!=NP.
