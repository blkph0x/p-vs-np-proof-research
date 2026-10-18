# Independent review of interval coefficient positivity

**Conclusion:** no mathematical or implementation correctness defect found in the reviewed files. The solver gives exact coefficient-positivity decisions when its complete interval certificate fits the stated budgets, and otherwise returns UNKNOWN. Its compact modular-test obstruction and its exponentially fragmented control are correctly limited to the particular representations and test rules described. No polynomial general algorithm or complexity-class separation follows.

Only this review file was written. All nine current unit tests passed. The additional independent enumeration and saved-result replay below also passed.

## Proof audit

The support recurrence is exact because the product has nonnegative integer coefficients: an exponent is present precisely when at least one choice word reaches it. Discarding prefix weights greater than W is valid because all future weights are nonnegative. Shifts of maximal closed integer intervals, followed by clipping and merging adjacent or overlapping intervals, therefore preserve the support exactly. This method decides positivity; it does not recover coefficient multiplicities.

The producer's sorting/merging routine and the verifier's event sweep implement the same recurrence differently. In the sweep, a shifted interval [l,h] contributes +1 at l and −1 at h+1. Adjacent intervals remain connected because the net event leaves positive coverage, so the sweep gives maximal integer intervals. The verifier checks the initial singleton, canonical disjoint intervals, every original-input recurrence, the final decision and any original choice witness. Its input hash uses length-prefixed binary integer encodings, so large values do not depend on decimal formatting.

For the separated-block family, binary expansion gives exactly [0,L−1] before the last choice, with L=2^q. The final choice adds a copy shifted by 2L, leaving L absent. For every 1<=M<=L, s=L mod M satisfies 0<=s<L and is therefore a real attainable original weight with the requested residue. Its binary expansion plus final bit zero supplies the witness. This proves the all-size failure of the stated separate-residue rejection rule, including adaptive selection of bounded moduli. It does not imply failure of every algorithm using residues or algebra: different residue tests may have different witnesses, while a simultaneous test has a stronger contract.

The input lists q exponents of increasing bit length and one larger exponent, using O(q^2) bits. A rejecting modulus for that separate-test rule must exceed 2^q; a dense scan of all its residues is consequently superpolynomial in the explicit input length. The theorem correctly says superpolynomial rather than asserting a general complexity lower bound. The interval algorithm retains one interval per layer after truncating at L and solves this easy family with a compact certificate.

For powers of four, the lowest digit 0/1 creates one consecutive pair for each assignment to the higher q−1 digits. Different higher-digit assignments leave at least two missing integers between these pairs. Thus the exact canonical interval count is **2^(q−1)**, not 2^q. The target is the sum of all weights, so no support is removed by truncation. A separate base-four digit test decides this family efficiently; its fragmentation is specific to interval representation.

## Code, complexity and cap audit

The stated operation bound charges sorting at most twice the previous layer's interval count and uses endpoint bit lengths, rather than treating exponentially large integers as fixed-size machine words. The candidate layer may temporarily contain up to twice the previous interval count before the interval cap is checked; this is documented. The updated UNKNOWN peak includes the rejected candidate, while the retained-total count and completed-choice count exclude that unfinished layer.

The `generated_spans` budget charges two potential shifted spans per prior interval, including shifts later clipped away. The verifier reconstructs that same work convention. These counters are algorithmic controls, not exact elapsed-time, total process-memory or bit-operation budgets. Empty subsequent layers can still require a scan of the remaining input, which the theorem separately charges.

Backward witness selection is justified by the verified recurrence: each present target has at least one predecessor under one of the two original weights. Subtracting a weight may produce a negative candidate, which correctly fails the interval-membership test. Zero weights, duplicate choices, empty products, empty reachable layers and very large integers are handled consistently.

For SAT-derived controls, the saved experiment first binds the graph and costs to the external original formula through `packing.verify_encoding`. Replayed interval choices and targets were checked to equal that encoding. Thus the certificate cannot silently refer to a different packed request. Larger controls use explicit original satisfying assignments rather than claiming an exhaustive truth table over all their variables.

## Independent verification results

With seed 971913, the reviewer generated **800 products** with zero through ten choice pairs, each exponent in [0,30], and target in [0,150]. For every prefix, direct enumeration of all original choice words was compared against the expanded saved interval layer. Every decision and every layer agreed. The independent event verifier accepted all completed certificates.

For each such certificate, verifier budgets set exactly to its retained-interval and generated-span counts accepted it. Reducing the retained count by one, or a positive span count by one, returned UNKNOWN. Random smaller solver caps produced **328 correct EXACT results and 472 UNKNOWN results**, all without a feasibility claim when incomplete. This checks that exhaustion does not masquerade as a negative decision.

The saved RESULTS.json was then loaded from disk and bound to the current source hashes. The reviewer replayed:

* **45 saved requests:** 37 complete exact proofs and eight UNKNOWN records.
* **34 modular witnesses:** every supplied original bit vector had the recorded cost, differed from the exact target, and reached its claimed residue.
* **34 original SAT references:** every small truth table was recomputed independently, and every larger explicit assignment was checked clause by clause.
* **41 graph matching witnesses:** all passed the original graph and formula checks after external-formula binding.

The base-four interval counts were checked against 2^(q−1), including exact saved layers where available. Every saved separated-block exact certificate had peak interval count one. Source files were not modified during these checks.

## Source snapshot

| File | SHA-256 |
|:---|:---|
| intervals.py | b62036e069238d7dc92a1119b108814034b3090e7ec98fc673d1d70cb673140a |
| test_intervals.py | 1ff4735fb28fdec5e9405c06b71844bf5fbae1b00975bedc34919946d8a5c9ab |
| THEOREM.md | a4f07544d435534db139827fe2114891d666259d2ac541f1cf73583e942e206f |
| run_experiments.py | 70e9ce822c32ddfc103cb20166d32fdb852f428e473500bd85e77b2c3b10f4b7 |
| ../packed_cost_exact_matching/packing.py | 1d60ffd5bf25a2cacdb08e5cf0287432135fe8134c6ca531c497e054ede30fbe |

These results support the elementary proofs and implementation. The interval representation can be highly effective on appropriate inputs, but the exponential fragmentation family rules out an unrestricted polynomial bound on its number of intervals; it does not rule out other representations or a future general algorithm.
