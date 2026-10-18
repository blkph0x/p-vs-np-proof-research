---
layout: default
title: P versus NP Research
description: A public, reproducible research notebook for exact algorithms, certificates, and scoped barriers.
---

<div class="hero">
  <p class="eyebrow">PUBLIC RESEARCH CHECKPOINT · 18 OCTOBER 2026</p>
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

The latest recorded full audit passed **42 suites and 409 test methods** with
unchanged source hashes. These are reproducibility results for the checked
finite cases, not a solution to the open problem.

The newest finite proof-complexity checkpoint settles the standard PHP(5,4)
encoding's minimum resolution width at **4**. An exhaustive five-pebble game
fixed point certifies the width-4 upper bound, while the complete width-3
closure has no empty clause. See the [pebble-game report](resolution_width_lab/PEBBLE_REPORT.md)
and its [independent replay](resolution_width_lab/PEBBLE_REVIEW.json).
The accompanying [uniform PHP width certificate](resolution_width_lab/PHP_WIDTH_REPORT.md)
proves the exact ordinary-resolution width `n` for every PHP(n+1,n) with
`n >= 2`, with an explicit width-two PHP(2,1) edge case. This is a
proof-complexity result, not a general SAT algorithm.

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

## Runtime scaling notebook

{% include runtime-chart.html data_url='/assets/data/scaling-runtime.json' %}
<script src="{{ '/assets/js/scaling-chart.js' | relative_url }}" defer></script>

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
