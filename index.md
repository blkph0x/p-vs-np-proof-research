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

The latest recorded full audit passed **37 suites and 383 test methods** with
unchanged source hashes. These are reproducibility results for the checked
finite cases, not a solution to the open problem.

## Runtime scaling notebook

<section class="scaling-panel" data-runtime-chart data-runtime-source="{{ '/assets/data/scaling-runtime.json' | relative_url }}">
  <p class="chart-note">Recorded producer solve times from the native binary-code and proof-producing SAT experiments. Select the horizontal measure, include capped UNKNOWN runs, or switch to a logarithmic vertical scale.</p>
  <div class="chart-toolbar">
    <label>Horizontal axis <select data-chart-axis aria-label="Horizontal chart axis"></select></label>
    <label><input type="checkbox" data-chart-unknown> Include UNKNOWN runs</label>
    <label><input type="checkbox" data-chart-log> Logarithmic runtime</label>
    <button type="button" data-chart-reset>Reset view</button>
  </div>
  <div class="chart-layout">
    <svg class="runtime-chart" data-chart-svg role="img" aria-label="Solver runtime scaling chart" viewBox="0 0 760 390"></svg>
  </div>
  <div class="chart-legend" data-chart-legend aria-label="Chart series"></div>
  <p class="chart-detail" data-chart-details aria-live="polite">Hover or focus a point for details.</p>
  <p class="chart-note" data-chart-status>Loading recorded measurements…</p>
  <details>
    <summary>Accessible data table</summary>
    <table class="chart-table">
      <thead><tr><th>Series</th><th>Selected x</th><th>Seconds</th><th>Status</th></tr></thead>
      <tbody data-chart-table-body></tbody>
    </table>
  </details>
</section>
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

## Public record

The source repository is [blkph0x/p-vs-np-proof-research on GitHub](https://github.com/blkph0x/p-vs-np-proof-research).
The [external status audit](EXTERNAL_STATUS_AUDIT_2026_10_18.md) records the
official public status and keeps an unverified recent P=NP claim separate from
the project's own evidence.
