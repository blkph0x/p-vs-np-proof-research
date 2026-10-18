# Non-graphic core experiment — 18 October 2026

The six stored v17 random codes now have explicit certificates excluding graphic
and cographic matroid representations. An exact coordinate-conditioning solver
also reproduces all six minimum distances. On these inputs, conditioning reduces
peak syndrome tables but increases transitions across all branches.

This is a finite research increment, not a P-versus-NP result or a new hardness proof.

## What changed

The previous complete-graph control showed that high connectivity and high trellis
width can coexist with polynomial native minimum-weight algorithms. The next step
was to exclude those particular graph representations from the stored random codes,
then test another exact route while accounting for discovery and reconstruction.

For each matrix, bounded seeded search finds an F7 minor. A separate verifier
checks the certificate using rank identities on original columns: after contraction,
the retained seven columns are the seven nonzero points of a binary rank-three
space. F7 is a nonregular minor and rules out both graphic and cographic matroids.
See `FANO_NOTES.md` for the proof and primary-source cross-check. This obstruction
does not rule out every graph-based algorithm or an extended representation.

| Length | Dimension | Fano search trials | Prior internal-4 audit | Prior middle-cut width lower bound | Exact minimum distance |
| --- | --- | --- | --- | --- | --- |
| 18 | 9 | 14 | all cuts | 4 | 3 |
| 20 | 10 | 15 | all cuts | 5 | 3 |
| 22 | 11 | 1 | all cuts | 6 | 4 |
| 24 | 12 | 1 | all cuts | 6 | 4 |
| 26 | 13 | 1 | all cuts | 7 | 4 |
| 28 | 14 | 2 | **not established** | 8 | 4 |

The prior cut bounds and internal-4 claims come from v17's saved exhaustive audits.
This increment checks input rank and the saved minimizing-cut witness but does not
rerun those scans. The source artifact's SHA-256 is recorded in `results.json`.
The new Fano certificates do not close the length-28 internal-4-connectivity gap.

## Exact conditioning, including the deleted bits

For a code `C = ker H`, choose coordinates `D` to fix and retain the rest `R`.
For every assignment `b` on `D`, solve the affine system

    H_R x = H_D b

and minimize `weight(x) + weight(b)`, excluding the all-zero full word. This is
different from freely puncturing coordinates, which can change the distance.
The solver checks every reconstructed word against the original parity constraints.

The residual solver tracks a syndrome and a nonzero flag. It discards a partial
syndrome only when the remaining suffix cannot reach the branch target. Every
feasible branch is an affine translate of the same shortened code, so its distinct
syndrome-state profile is computable by ranks before running the solver.

Candidate selection exhausts every one- or two-coordinate set for the supplied
greedy order, choosing the smallest peak profile, then smallest summed profile,
then lexicographic indices. It does not optimize the order globally. The experiment
records candidate counts, profile-rank evaluations and discovery time separately.

## Measurements

All 24 default solver runs finish exactly. Their distances agree with two existing
reference methods: generator enumeration and the v17 syndrome trellis.

| Length | Greedy peak states | Fix one peak | Fix two peak | Greedy transitions | Fix one transitions | Fix two transitions |
| --- | --- | --- | --- | --- | --- | --- |
| 18 | 128 | 64 | 32 | 1,488 | 1,674 | 2,106 |
| 20 | 128 | 64 | 32 | 1,726 | 1,832 | 2,236 |
| 22 | 256 | 128 | 64 | 2,772 | 2,894 | 3,714 |
| 24 | 512 | 256 | 128 | 5,844 | 5,966 | 6,274 |
| 26 | 1,024 | 512 | 256 | 16,918 | 17,424 | 18,948 |
| 28 | 2,048 | 1,024 | 512 | 26,138 | 28,692 | 30,728 |

Peak counts refer to distinct syndromes in one branch. Actual dictionary entries
also include the nonzero flag: the length-28 run goes from 2,049 to 513 entries.
Two current/next dictionaries and polynomial setup storage are also needed; these
counts are not a measurement of process memory in bytes. Transition counts include
both possible bit extensions, including rejected ones, across all branches.

For length 28, selecting a two-coordinate set inspects 378 candidates and performs
20,790 profile-rank evaluations. These are additional to solving. All four branch
assignments are feasible. Generator enumeration visits only 16,384 codewords for
this small dimension, so the experiment does not establish a speed advantage over
the simple generator method. Timings in the raw results are observations only;
different operation counts are not interchangeable runtime units.

## Why the table reduction has a limit

Let `w` be the original fixed-order syndrome width, `w_D` the residual width, and
`q` the dimension of the code's projection onto the fixed coordinates. There are
exactly `2^q` feasible affine branches, and

    w - q <= w_D <= w
    2^q * 2^w_D >= 2^w.

Thus branching cannot reduce this particular product of feasible branch count and
peak syndrome states. It can still reduce peak per-branch tables. This elementary
bound makes no claim about total transitions, parallel execution, or wall time.
The proof is in `THEOREMS.md`. A useful next algorithm must exploit more than
smaller explicit tables, such as decomposed residuals or a stronger native coset solver.

The charged-work replay closes the accounting gap for the implemented
fixed-order solver. Charging both deleted-assignment attempts and residual
transition attempts gives at least `2^w` operations for every exact run, where
`w` is the original order width. All 24 saved exact runs satisfy this bound in
`CHARGED_WORK_REVIEW.json`. This is a statement about this conditioning
architecture; it is not a lower bound for other algorithms.

## Checks and limits

The new lab has 21 passing tests. Independent set-based enumeration checks all 91
binary subspaces through four coordinates and all coordinate-fixing subsets:
1,225 complete solver cases. Other checks cover affine branch optima, directly
enumerated extension classes, exact work-limit boundaries, invalid inputs,
corrupted Fano certificates, and known graphic negative controls.

The experimental solver has explicit limits on branch assignments and transition
attempts. If either limit is reached before completion, it returns `UNKNOWN` with
no exact distance. A completed branch may supply a feasible upper-bound witness.
Polynomial validation/elimination/setup work is separate from those counters.
Candidate discovery has its own cap and reports incomplete selection explicitly.
The reference solvers still run to completion on these small stored inputs.

The v17 high-width suite also passes all nine tests after fixing its dimension
metadata for dependent generator rows. Its general cut-code/mincut wording now
requires a connected graph with at least one edge; complete-graph results are unchanged.

The saved certificates exclude two native representation classes, not all efficient
algorithms. No all-size explicit hard family, average-case hardness result, or
polynomial general minimum-distance/SAT algorithm has been obtained.
