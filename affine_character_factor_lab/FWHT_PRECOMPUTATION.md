# Local FWHT precomputation: method and measured controls

20 October 2026. This is a borrowed arithmetic improvement to the declared
integer-table character solver, not a new transform or a general SAT algorithm.

[SymPy's FWHT documentation](https://docs.sympy.org/latest/modules/discrete.html)
specifies the familiar butterfly transform. The character interpretation is
[normal-factor-graph Fourier duality](https://arxiv.org/abs/1102.0316).
For each block, the producer chooses between repeated direct sums and
precomputing its whole exact spectrum. With width k, N=2^k entries and C=2^r
characters, its compared work charges are C*N and N+k*N+C. Precompute only
on strict improvement; ties and C<=2 retain the original direct path.
The [theorem](THEOREM.md) gives the identity and limits.

The integer-only input and certificate formats are unchanged. Each character,
mask, local value and final normalization is still checked using **direct**
local sums. The checker does not import the new transform helpers or trust
the producer's work statistics.

## Saved paired measurement

[FWHT_BENCHMARK.json](FWHT_BENCHMARK.json) retains original requests, input
hashes, source hashes, all five paired times, exact values, charged work,
certificate equality and direct checker results. The run was on the local
Windows workstation with Python 3.10.10. It was an ordinary process, without
CPU affinity or process-tree resource isolation. Peak memory was not measured.

| Control | Direct median | Adaptive median | Direct/adaptive work units |
| --- | ---: | ---: | ---: |
| Tiny rank, 64 OR blocks | 2.674 ms | 2.704 ms | 512 / 512 |
| Connected rank 10 | 148.426 ms | 46.068 ms | 40,960 / 10,360 |
| Signed six-bit block | 15.317 ms | 1.028 ms | 4,096 / 512 |

Timings include producer parsing, arithmetic and certificate construction.
They exclude interpreter startup and the separate direct verification step.
Order alternated between paired repetitions, after untimed validation.
The baseline is the current solver with the new selector disabled, retaining
the unchanged original direct local-sum method; it is not a separately built
historical executable. This is not an external-tool comparison.

The connected control showed about 3.2x lower producer time; the six-bit
control about 14.9x. The tiny-rank result provides no improvement evidence.
These are finite observations, not a speed guarantee, asymptotic improvement
of the exponential rank term, or end-to-end proof-checking speedup.

## Correctness and budget tests

All 33 local tests pass, including 10 new tests. They cover all 81 signed
two-bit tables with all eight full-rank right sides, 180 seeded requests,
repeated factors, scalar/zero blocks, inconsistent rows, original-source
and certificate mutation, normalization, spectrum masks, and cap boundaries.
Independent review also compared 5,100 coefficients across 160 signed tables
of widths zero through seven. The saved original campaign still has 21
exact rows, one UNKNOWN and one rejected mutation, plus its 220-case replay.

Two tradeoffs matter:

- Direct verification can need a larger work budget than the optimized producer.
- An unused full-spectrum coefficient can exceed a tight integer-bit cap even
  when direct requested sums would cancel. The adaptive run then returns
  UNKNOWN; identical caps need not preserve the completion status.

Signed **integers** remain the input contract. Fraction, float and Boolean
table entries are rejected; the output fraction pair does not extend that
contract to rational input tables. Costs count the documented work units;
they do not fully count factor indexing, multiplication bit costs, or memory.

## Reproduction and provenance

From this directory:

```text
python -m unittest discover -v
python INDEPENDENT_REVIEW.py
python test_fwht_precomputation.py --benchmark
```

The benchmark prints a fresh observation; it does not overwrite the saved
measurement. Compare values and certificates, not exact elapsed times.

[PRE_FWHT_RESULTS.json](PRE_FWHT_RESULTS.json) preserves the original
measurements from commit
[914f2e0c](https://github.com/blkph0x/p-vs-np-proof-research/tree/914f2e0c283b6440159d3495ececffd83d42dc30/affine_character_factor_lab),
where the previous review is also retained. The current RESULTS.json and
independent replay were regenerated against the changed producer. No older
measurement was relabelled with the new source hash.
