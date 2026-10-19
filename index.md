---
layout: default
title: P versus NP Research
description: A public, reproducible research notebook for exact algorithms, certificates, and scoped barriers.
---

<div class="hero">
  <p class="eyebrow">PUBLIC RESEARCH CHECKPOINT · 20 OCTOBER 2026</p>
  <h1>Can computation settle P versus NP?</h1>
  <p class="lede">This project tests proposed algorithms and proof ideas with exact arithmetic, saved certificates, independent checkers, and explicit complexity accounting.</p>
  <p>
    <a class="button" href="METHOD_INDEX.md">Explore the methods</a>
    <a class="button secondary" href="REPRODUCIBILITY.md">Run the audit</a>
  </p>
</div>

## Current result

**P versus NP remains unresolved.** The repository contains exact algorithms for
stated structural families, finite exhaustive controls, certificate verifiers,
and scoped counterexamples. It does not claim a solver for every SAT instance
or a lower bound against every polynomial algorithm.

The latest recorded full audit passed **54 suites and 539 test methods** with
unchanged source hashes. These are reproducibility results for the checked
finite cases, not a solution to the open problem.

The [peer-audit response](PEER_AUDIT_RESPONSE_2026_10_19.md) records what is
borrowed from neighboring proof-complexity, SAT, hierarchy, and coding
literatures, what this repository actually certifies, and which claims remain
outside its scope.

The newest finite proof-complexity checkpoint settles the standard PHP(5,4)
encoding's minimum resolution width at **4**. An exhaustive five-pebble game
fixed point certifies the width-4 upper bound, while the complete width-3
closure has no empty clause. See the [pebble-game report](resolution_width_lab/PEBBLE_REPORT.md)
and its [independent replay](resolution_width_lab/PEBBLE_REVIEW.json).
The accompanying [uniform PHP width certificate](resolution_width_lab/PHP_WIDTH_REPORT.md)
proves the exact ordinary-resolution width `n` for every PHP(n+1,n) with
`n >= 2`, with an explicit width-two PHP(2,1) edge case. This is a
proof-complexity result, not a general SAT algorithm. The saved replay now
extends through the complete PHP(7,6) certificate.

The [odd-charge Tseitin expander campaign](tseitin_expander_lab/REPORT.md)
adds four named connected cubic graph contradictions and a deterministic
Möbius-ladder sweep from 6 through 20 vertices. An exact parity certificate
proves each CNF unsatisfiable, and an independent checker rebuilds the local
3-CNF encoding and replays every CDCL resolution step. These are finite
controls against the cited expansion-based resolution literature, not a new
all-size lower bound or a P-versus-NP result.

The [hidden-XOR pair audit](proof_motif_candidate_lab/INDIRECT_XOR_REPORT.md)
also certifies one bounded auxiliary-variable step: two exact parity blocks
sharing one variable are combined into a four-variable XOR relation, while a
mutated block and a disjoint pair are rejected. This strengthens the scoped
motif miner but does not provide complete auxiliary elimination or a general
SAT algorithm.

The [compact ITE audit](proof_motif_candidate_lab/INDIRECT_ITE_REPORT.md)
recognizes the exact four-clause 3-CNF encoding of ITE gates and rejects
mutated and same-support decoys through independent truth-table replay. This is
another bounded motif result, not a complete circuit solver.

The [bounded XOR-chain audit](proof_motif_candidate_lab/XOR_CLOSURE_REPORT.md)
composes a capped five-block chain with proof IDs on each derived relation. The
mutation and `UNKNOWN_CAP` controls make the boundary explicit: this is a
proof-language experiment, not a complete parity or SAT solver.

The [prefix-threshold sequential-counter audit](proof_motif_candidate_lab/SEQUENTIAL_COUNTER_REPORT.md)
adds an exact cardinality primitive beyond AMO. A supplied role map is checked
by clause reconstruction and exhaustive projection on a five-input,
threshold-two instance; missing clauses, literal mutations, and a wrong
threshold are rejected by an independent replay. A capped signed incidence-graph
search also recovers a renamed role map; unrestricted discovery remains explicit
and unresolved.

The [deterministic Reed--Muller local-marginal audit](local_marginal_code_lab/REED_MULLER_THEOREM.md)
adds an explicit self-dual binary-code family to the relaxation barrier. Its
proved distance `2^(s+1)` leaves a unit-vector local witness through level
`2^(s+1)-2`, while the pinned integer optimum is `2^(s+1)`. The saved controls
include exact RM(1,3) scope replay, full RM(2,5) word enumeration, and an
independently checked theorem-backed RM(3,7) certificate. This remains a
limitation of the stated relaxation, not a general SAT lower bound.

The companion [all-redundant-parity replay](local_marginal_code_lab/REED_MULLER_ALL_DUAL_REPORT.md)
adds every dual parity check analytically. Its exact rational certificate still
leaves integer/fractional ratios `6/5`, `28/19`, and `120/71` on the saved
family, so redundant XOR checks tighten the relaxation without closing it.

The [combined all-dual/local replay](local_marginal_code_lab/REED_MULLER_ALL_DUAL_LOCAL_REPORT.md)
adds all pinned-code projection marginals through the boundary level `d-1` at
the same time. Exact sparse one-hot tables remain feasible at the all-dual
optimum, leaving the same ratios on the three saved Reed--Muller controls.

The [level-`d` RM(1,3) certificate](local_marginal_code_lab/REED_MULLER_LEVEL_D_REPORT.md)
checks the next finite boundary with an exact integer dual certificate. All
982 supported local atoms are covered, and the level-four optimum is exactly
four, matching a pinned weight-four codeword. This closes the smallest saved
gap only; it is not a general SAT or P-versus-NP result.

The [RM(2,5) affine-flat star control](local_marginal_code_lab/REED_MULLER_LEVEL_D_FLAT_STAR_REPORT.md)
tests a weaker level-eight construction. Its 620 affine-flat tables retain the
exact `38/7` fractional optimum; the full replay below supplies the missing
overlap-consistent finite result while preserving this weaker control.

The stronger [RM(2,5) affine-overlap replay](local_marginal_code_lab/REED_MULLER_LEVEL_D_AFFINE_OVERLAP_REPORT.md)
shares all affine four-point, line, and singleton marginals among those flats.
An exact 28-orbit primal/dual certificate raises the selected-model optimum to
`31/5`, proving the same lower bound for the full level-eight relaxation by
projection. The [full level-eight replay](local_marginal_code_lab/REED_MULLER_LEVEL_D_FULL_REPORT.md)
then includes every scope through size eight and exact pinned-code support.
Its independently checked 2,174-orbit quotient has the matching optimum
`31/5`; the pinned integer optimum is eight. This closes the finite value of
the stated RM(2,5) relaxation while leaving general SAT and P versus NP
unresolved.

The [SOS moment audit](local_marginal_code_lab/REED_MULLER_SOS_MOMENT_INDEPENDENT_REVIEW.md)
then supplies an exact finite separation: the valid Boolean square
`(5t-31)^2`, with `t` the nonpin Hamming weight, evaluates to `-992/7` on
the fractional witness. This identifies a missing global moment constraint;
it is not a general SAT or P-versus-NP result.

Adding that cut to the full level-eight model now has the exact finite optimum
`7037/1095`. The [SOS-strengthened replay](local_marginal_code_lab/REED_MULLER_SOS_STRENGTHENED_REPORT.md)
checks matching rational primal and dual certificates, all reduced costs, and
zero gap. It closes this finite relaxation without making a general SAT or
P-versus-NP claim.

The next [two-cut replay](local_marginal_code_lab/REED_MULLER_SOS_TWO_CUT_REPORT.md)
adds the valid integer-weight polynomial `(t-6)(t-7)`. It closes the resulting
finite relaxation exactly at `367/57`, with a matching rational primal and dual,
zero gap, and an independently replayed reduced-cost certificate. This remains
a representation-specific hierarchy result, not a P-versus-NP result.

The [three-cut replay](local_marginal_code_lab/REED_MULLER_SOS_THREE_CUT_REPORT.md)
adds the valid integer-weight product `(t-6)(t-7)(t-23)(t-24)`, which the
two-cut witness violates by `-2400/19`. The strengthened finite relaxation is
closed exactly at `5231/801`, with a matching rational primal and dual,
zero gap, and an independent pure-stdlib replay. This is still a
representation-specific certificate, not a P-versus-NP result.

The [four-cut replay](local_marginal_code_lab/REED_MULLER_SOS_FOUR_CUT_REPORT.md)
adds `t(31-t)(t-3)(t-4)(t+28) >= 0`, a valid integer-domain inequality that
the three-cut witness violates by `-3248000/89`. It closes the next finite
relaxation exactly at `1219047171/184149541`, with matching rational
certificates, nonnegative reduced costs, and independent replay. This is
still a representation-specific certificate, not a P-versus-NP result.

The [fifth-cut replay](local_marginal_code_lab/REED_MULLER_SOS_FIVE_CUT_REPORT.md)
adds the valid core inequality `t(31-t)(t-3)(t-4) >= 0`. The four-cut witness
violates it by `-61440933600/184149541`; the next finite relaxation closes
exactly at `324713143/48731153`, with matching rational certificates,
nonnegative reduced costs, and independent replay. This remains a
representation-specific certificate, not a P-versus-NP result.

The [sixth-cut replay](local_marginal_code_lab/REED_MULLER_SOS_SIX_CUT_REPORT.md)
adds the valid integer-domain inequality
`(t-6)(t-7)(31-t)(t+32)^2 >= 0`. The fifth-cut witness violates it by
`-6759234824400/48731153`; the next finite relaxation closes exactly at
`22465669893401/3255387995415`, with matching rational certificates,
nonnegative reduced costs, and independent replay. This remains a
representation-specific certificate, not a P-versus-NP result.

## Runtime scaling notebook

{% include runtime-chart.html data_url='/assets/data/scaling-runtime.json' %}
<script src="{{ '/assets/js/scaling-chart.js?v=2' | relative_url }}" defer></script>

The chart is a measurement view, not a complexity claim. Exact family and
capped archive points use different symbols; an UNKNOWN point records work
spent before a branch cap, not a solved instance or a lower bound. The CDCL
series are resolution-based proof traces and do not lower-bound every SAT
algorithm.

## Start here

<div class="cards">
  <a class="card" href="RESOLUTION_STANDARD.md">
    <strong>Acceptance standard</strong>
    <span>What a valid P=NP or P≠NP result would have to prove.</span>
  </a>
  <a class="card" href="METHOD_INDEX.md">
    <strong>Method index</strong>
    <span>Every active algorithm, theorem, boundary result, and write-up.</span>
  </a>
  <a class="card" href="CITATIONS.md">
    <strong>Sources and claims</strong>
    <span>Public references, provenance, and the project's citation rules.</span>
  </a>
  <a class="card" href="TEST_SUMMARY.json">
    <strong>Audit record</strong>
    <span>Machine-readable suite outcomes, timings, and source hashes.</span>
  </a>
</div>

## What is being tested

- **Native exact solvers:** graph-plus-exception and rank-compressed minimum
  distance routines with independently checked matching dual certificates.
- **Structural boundaries:** degree-two distance algorithms, Fourier span
  obstructions, holographic basis limits, and regular-LDPC hardness scope.
- **Proof-producing experiments:** every result keeps the input, certificate,
  checker, negative control, and a report of what the result does and does not
  establish.
- **Open proposals:** unresolved ideas remain labeled as proposals until their
  correctness and fixed polynomial bit-complexity bounds are proved.

## Reproduce it

From a fresh checkout with Git LFS enabled:

```text
python -m pip install -r requirements.txt
python run_research_checks.py
```

The audit writes `TEST_OUTPUT.txt` and `TEST_SUMMARY.json`. The workflow in
`.github/workflows/research-checks.yml` runs the focused checks and the same
self-contained full audit on every push and pull request.

The public site is built and deployed by
`.github/workflows/pages.yml` after every push to `main`. The workflow first
builds the Jekyll source and uploads the exact artifact it deploys, so a broken
page build fails before publication.

## Public record

The source repository is [blkph0x/p-vs-np-proof-research on GitHub](https://github.com/blkph0x/p-vs-np-proof-research).
The [external status audit](EXTERNAL_STATUS_AUDIT_2026_10_18.md) records the
official public status and keeps an unverified recent P=NP claim separate from
the project's own evidence.

The [seventh-cut replay](local_marginal_code_lab/REED_MULLER_SOS_SEVEN_CUT_REPORT.md) adds the valid integer-domain inequality `(t-6)(t-7)(31-t) >= 0`. The exact six-cut witness violates it by `-3473117738496/217025866361`; the next finite relaxation closes exactly at `35873801083/5129253893`, with matching rational certificates and independent replay. This remains representation-specific and does not resolve P versus NP.
