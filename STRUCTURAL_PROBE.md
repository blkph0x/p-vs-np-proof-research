# Conditioning and direct-sum decomposition probe

Date: 2026-10-18. This is a finite structural result, with a polynomial decomposition algorithm and independently checked certificates. It is not a complexity lower bound or a resolution of P versus NP.

## Result

Every choice of zero, one, or two conditioned coordinates was checked for each of the six stored binary codes in `../high_width_core_stress_lab/random_code_audits.json`. For each code generator G, the probe constructs a parity-check matrix H and decomposes the column matroid of H_R, where R contains the unconditioned coordinates.

**None of the 1,697 residual matrices has more than one nontrivial direct-sum component.** Here a nontrivial component has at least two coordinates; singleton loops and coloops are counted separately.

| Code length n | Dimension k | Cases with zero deletions | Cases with one deletion | Cases with two deletions | Split residuals | Residuals with two nontrivial components |
| --- | --- | --- | --- | --- | --- | --- |
| 18 | 9 | 1 | 18 | 153 | 0 | 0 |
| 20 | 10 | 1 | 20 | 190 | 0 | 0 |
| 22 | 11 | 1 | 22 | 231 | 3 | 0 |
| 24 | 12 | 1 | 24 | 276 | 3 | 0 |
| 26 | 13 | 1 | 26 | 325 | 0 | 0 |
| 28 | 14 | 1 | 28 | 378 | 0 | 0 |

All six splits occur after deleting a pair from T = {6, 13, 20}, with **zero-based original coordinate labels**, for n=22 or n=24:

| Deleted D | Singleton coloop | Other component |
| --- | --- | --- |
| {6, 13} | {20} | All coordinates outside T |
| {6, 20} | {13} | All coordinates outside T |
| {13, 20} | {6} | All coordinates outside T |

For n=22 the component ranks are 10 and 1, adding to total rank 11; the large component has 19 coordinates. For n=24 the ranks are 11 and 1, adding to total rank 12; the large component has 21 coordinates. These are complete coordinate descriptions of all split witnesses. No probe produces a loop.

A singleton coloop has its coordinate fixed to zero in the homogeneous kernel. Its value in a feasible affine coset is fixed by that coset's target syndrome. Removing such a coordinate does not decompose the remaining large component into smaller blocks.

## Algorithm and certificate

`decompose_columns(columns, basis_indices=None)` represents each binary column by a nonnegative integer. It selects a basis by elimination unless the caller supplies any independent spanning basis, in any order. Each nonbasis column has a unique expression in that basis. Its support together with the nonbasis coordinate is its fundamental circuit. Union-find joins the coordinates in each such circuit. Zero columns produce singleton circuits and remain singleton loops; basis elements in no circuit remain singleton coloops.

The result records the basis, every fundamental circuit, the component partition, loops and coloops, and work counts. `validate_partition(columns, components)` independently checks exact coverage and

    rank(all columns) = sum(rank(component columns)).

Its elimination uses least-significant pivots, separately from the decomposition's most-significant-pivot elimination. The rank test proves that the blocks form a direct sum. It deliberately accepts coarsenings too; it does not alone prove that the partition is finest.

The fundamental circuits establish fineness as follows. Every column in a component is a combination of the basis columns in that same component. The global basis is independent, so the spans of the component basis sets form a direct sum. Conversely, a direct-sum partition cannot split a circuit: its two nonempty sides would give an equal nonzero vector in two independent spans, contradicting directness. Every edge of the recorded fundamental-circuit graph must therefore remain within any direct-sum component. Its connected components are exactly the finest blocks.

This argument applies to any supplied basis. It uses no enumeration of coordinate cuts. With m columns, rank r, and maximum column bit length L, the elimination work is O(mr) integer XOR reductions, each on polynomially sized integers. The explicit circuit lists and union operations are O(mr); rank-additivity verification is polynomial as well. The probe enumerates only O(n²) choices of D because |D|≤2 is fixed.

## Independent verification and measured work

`python -m unittest -v test_structural_probe` passes all 9 tests. The tests include:

- All 1,365 representations with up to five columns over GF(2)^2, compared with an independent oracle that enumerates minimal zero-sum circuits on these tiny instances.
- 100 additional seeded representations with up to eight columns over GF(2)^4.
- All 168 orders of every basis of the seven nonzero vectors in GF(2)^3, plus a loop.
- Circuit validity and minimality, rank-additivity rejection cases, arbitrary coordinate permutations and invertible row operations, loops, coloops, empty matrices, high bit positions, malformed inputs, and original coordinate mapping after conditioning.

The production probe performs 436,158 integer XOR reductions, including its independent partition verification; 3,400 verification rank evaluations; 103,013 union attempts; and 35,729 successful unions. One run took about 0.40 seconds on the current host. The counts omit loading the fixtures and constructing their six parity-check matrices. They count integer operations, not bit operations. Runtime is descriptive evidence only.

## API and reproduction

- `decompose_columns(columns, basis_indices=None)` returns local-index components, basis and circuit certificates, singleton classifications, and work counts.
- `validate_partition(columns, components)` independently checks a proposed direct-sum partition by coverage and rank additivity.
- `conditioned_components(generator, n, deleted=())` builds H_R and returns both local components and original coordinate labels, including original basis, loops and coloops.
- `probe_stored_codes(max_delete=2)` returns the full aggregate results and every split witness. This bounded entry point accepts only 0, 1, or 2.

Run `python structural_probe.py` from this directory to print the full results. It does not overwrite existing artifacts.

The result rules out a useful direct-sum split after at most two conditioned coordinates **for these six stored instances**. It says nothing about other instances, larger conditioning sets, 2-sums or 3-sums, a different native theory, or general hardness. A decomposition of H_R alone is also not a complete affine-coset solver: target-syndrome compatibility and local minimum-weight computations must still be handled correctly.
