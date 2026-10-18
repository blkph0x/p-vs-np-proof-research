# Rank-compressed native affine experiments

This is a deterministic exact experiment on a supplied-basis family. It establishes agreement with an independent closed-form optimum for these instances. It does not settle P versus NP, establish a general polynomial algorithm, or establish a new complexity theorem.

## Construction and original request

For each p from 1 through 8, take r=3p non-ground vertices and one ground vertex. The graph columns are the reduced incidence columns of the complete graph K_(3p+1). For j=0,...,p-1 let g_j have ones exactly at row positions 3j, 3j+1, 3j+2. Append every nonzero combination of the g_j, in increasing combination-bitmask order. These q=2^p-1 columns are distinct and each has weight at least three; their binary rank is p. The graph columns have weight one or two, and the supplied row transform is the identity.

The exact problem is min |x| subject to Hx=s over GF(2), with `require_nonzero=False`. Primary targets have block weights 1,2,3,1,2,3,...; in each block the first a_j row bits are one. The JSON preserves H in both row and column form, each target, each identity transform, the original solver request and its hash. Its `research_request_summary` records the larger research objective; `experiment_request` records this bounded test.

## Independent closed-form proof

First consider only the complete graph. If a reduced syndrome has w one bits, each selected edge can account for at most two of them, so at least ceil(w/2) edges are necessary. Pair the marked vertices by graph edges; when w is odd, join the remaining vertex to ground. This attains ceil(w/2), proving the exact graph cost for every syndrome.

Write a_j in {0,1,2,3} for the target weight in block j. A zero exceptional syndrome is cheapest with no exceptional coordinates, and has total cost C0=ceil((sum_j a_j)/2). Every nonzero exceptional syndrome is itself one appended column, so its minimum exceptional cost is exactly one. Using any larger subset with that same syndrome cannot improve the graph part or its total cost. Selecting block j in that syndrome replaces a_j by 3-a_j in the residual graph target.

Without the requirement to select a nonempty set of blocks, the minimum residual weight is R0=sum_j min(a_j,3-a_j). If any a_j is at least two, this minimum already selects a nonempty block set. Otherwise every a_j is zero or one, every toggle strictly raises the residual weight, and the cheapest nonempty set is a single block with smallest increase min_j(3-2a_j). Thus set R=R0 in the first case and R=R0+min_j(3-2a_j) in the second. Since ceil(w/2) is nondecreasing, the best cost with nonzero exceptional syndrome is C1=1+ceil(R/2). The exact affine optimum is min(C0,C1). This proof applies to all targets and every positive p, including the zero target where C0=0.

## Primary results

Every row below completed with status EXACT, passed the independent certificate replay, matched the formula, and had its returned word checked directly against the original affine equations. The JSON retains all eight full certificates, including all DP layers, final exceptional witnesses and graph optimality evidence.

| p | n | Graph columns | Exceptional columns q | Rank states | Graph calls | DP transitions | Affine optimum | Produce (s) | Replay (s) |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | 7 | 6 | 1 | 2 | 2 | 1 | 1 | 0.454452 | 0.000114 |
| 2 | 24 | 21 | 3 | 4 | 4 | 7 | 2 | 0.070727 | 0.000426 |
| 3 | 52 | 45 | 7 | 8 | 8 | 39 | 2 | 0.143697 | 0.001440 |
| 4 | 93 | 78 | 15 | 16 | 16 | 167 | 3 | 0.294526 | 0.004804 |
| 5 | 151 | 120 | 31 | 32 | 32 | 679 | 3 | 0.615462 | 0.014941 |
| 6 | 234 | 171 | 63 | 64 | 64 | 2727 | 3 | 1.288301 | 0.046484 |
| 7 | 358 | 231 | 127 | 128 | 128 | 10919 | 4 | 3.260753 | 0.138101 |
| 8 | 555 | 300 | 255 | 256 | 256 | 43687 | 4 | 5.850304 | 0.392407 |

`Produce` is the solver's reported construction time before its own verification. `Replay` is the runner's additional certificate check. The JSON also records the solver's own verification time and total time for construction plus both checks. Timings are single measurements in the local environment and are not comparative benchmarks; other work may have been running. Timing is never used to establish correctness.

At p=8 there are 555 coordinates, including 255 distinct exceptional columns of rank eight. The solver covers all 256 syndrome cases. A coordinate-assignment enumeration would contain 2^255 assignments; that count is a combinatorial comparison, not an executed baseline or a measured speedup. The experiment's state, transition and graph-call caps are respectively 256, 1,000,000 and 257. For this explicit family q=2^p-1, so the general O(q 2^p) DP bound is polynomial in the explicit family input size. This property does not hold for arbitrary matrices.

## Small exhaustive controls

The runner solves all 8 targets for p=1 and all 64 targets for p=2, including zero, with the same affine semantics and budgets. Each certificate is replayed and each answer compared to the closed form. It additionally enumerates every exceptional-coordinate subset (two and eight subsets per target respectively), using the independently proved complete-graph cost. For p=1 it independently enumerates all 128 full coordinate words once and compares the minimum for each target. No full-coordinate enumeration is used for p=2 or larger.

| p | Targets | All checks agree | Full words enumerated | Exceptional subsets checked | Seconds |
|---:|---:|:---:|---:|---:|---:|
| 1 | 8 | Yes | 128 | 16 | 0.264310 |
| 2 | 64 | Yes | 0 | 512 | 4.485750 |

For these 72 checks the JSON stores compact target/optimum/word outcomes and their hash, rather than duplicating all certificates. The runner reconstructs and checks them on rerun.

## Archived best-found transforms: counts only

The six previously saved row transforms were read from `ROW_BASIS_RESULTS.json`, their row operations checked directly, and the exceptional-column ranks recomputed. No new optimization or archived solve was run, and no global optimality of these transforms is asserted.

| n | Exceptional columns q | Exception rank p | Coordinate assignments | Syndrome states | State-count improvement |
|---:|---:|---:|---:|---:|:---:|
| 18 | 3 | 3 | 8 | 8 | No |
| 20 | 4 | 4 | 16 | 16 | No |
| 22 | 6 | 6 | 64 | 64 | No |
| 24 | 7 | 7 | 128 | 128 | No |
| 26 | 9 | 9 | 512 | 512 | No |
| 28 | 12 | 12 | 4096 | 4096 | No |

These archived transforms all have p=q, so rank compression does not reduce their state counts. In particular, this method has not closed the previously recorded gaps on the larger archived cases.

## Reproduction and limits

Run `python run_rank_experiments.py` from this directory to reproduce both result files. Source files are hashed before and after the experiments; the runner refuses to publish if a source changes during the run. `RANK_NATIVE_RESULTS.json` records these SHA256 hashes, its Python and NetworkX versions, the archived-input hash, per-case inputs and certificates. Matrix and request hashes use compact UTF-8 JSON; dictionary keys are sorted. File hashes use their exact stored bytes.

Recorded environment: Python 3.10.10, NetworkX 3.2.1. Run started at 2026-10-17T13:45:31.560991+00:00; total measured experiment time before output serialization was 18.000147 seconds.

The certified class consists of graph coordinates and disjoint exceptional coordinates in a supplied row basis. It is not an arbitrary low-rank perturbation on the same graph coordinates. The exactness claim relies on complete syndrome DP and complete graph-case coverage; arbitrary rank p still produces exponentially many states. These examples supply the basis directly and provide no general basis-finding algorithm. The analytic optimum and successful finite checks validate this implementation route; they do not prove unrestricted tractability or either answer to P versus NP.
