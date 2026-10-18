# Independent review of counted residue certificates

Reviewed 2026-10-18. The theorem, producer, independent certificate checker, saved negative controls and resource qualifications are sound. No producer changes or mathematical corrections were requested. This is a proof/source audit with executable replay, not a proof-assistant formalization or a result resolving P versus NP.

## Algebra and quantifiers

The product expansion counts original binary choice vectors, including both choices when the two exponents coincide. The empty product and the q+1-bit coefficient bound are correct. Polynomial nonzeroness is consequently different from positivity of a selected coefficient.

Reduction modulo z^M−1 folds each original monomial into its exponent residue. The monic division argument gives the unique representative of degree less than M over the integers. Nonnegative coefficients make positivity equivalent to the existence of some original weight in that residue; they do not make it equivalent to the exact target weight. The exact complex root-of-unity average gives the same folded sum by geometric-series orthogonality, so it has the same aliasing. No floating-point root calculation is relied upon.

The simultaneous congruence condition is exactly divisibility of one fixed weight difference by the least common multiple. It is not the product for arbitrary non-coprime moduli. The empty list correctly means modulus one. Separate successful queries permit different choice vectors and cannot be combined into a common witness. A modulus larger than the degree isolates a target only when the target is also inside the original support range; the theorem's explicit 0≤W≤D qualification is necessary and correct.

The main gap expansion and every displayed count are correct. Its coefficient at 36 is zero, while the folded target counts for moduli 2,3,5,7 are respectively 8,8,2,4. Witness weight 6 works for the first two, and weight 1 for the last two. A common modulus 210 instead has target coefficient zero. This respects the Chinese remainder theorem because the separately chosen witnesses differ.

Integer-base packing of coefficients is also stated accurately. With an integer base B>2^q, coefficients fit within individual base-B digits, but the leading positive coefficient implies P(B)≥B^D. The resulting integer can have exponentially many binary digits. This diagnoses that explicit evaluation method; it is not a lower bound against all coefficient algorithms.

## Certificate and budget review

The certificate verifier receives the original ordered exponent pairs, target and modulus externally. The binary length-prefixed binding distinguishes exact and cyclic requests without decimal conversion. More importantly, the verifier recomputes every complete next layer from the original pairs, starting from exactly {0:1}. Thus it certifies missing target coefficients as well as positive ones. Sorted unique keys, positive counts, dimensions, mode, target count and original-choice witness are checked. The realizing witness backtracks through strictly decreasing factor indices and retains its actual integer sum rather than silently treating a residue witness as an exact-weight witness.

The producer and verifier have separate operational budgets. Producer UNKNOWN results contain no coefficient, attainability claim, witness or complete certificate. Verifier exhaustion returns UNKNOWN, and malformed or false evidence returns INVALID. The verifier checks the certificate, not the producer's outer timing/statistics fields; callers should use its returned coefficient when accepting a result.

Transition counts are not confused with total CPU time: input scanning, binary hashing, sorting, integer bit operations and witness work are explicitly additional. Verification retains parsed layers and reconstructs an additional bounded layer during recurrence checks. Nothing in the proof asserts a generally polynomial number of support states or constant-time operations on huge integers. Large exact or joint tables can exhaust a cap even on easy positive inputs.

## Independent replay

All 12 supplied tests passed in 0.597 seconds. The reviewer independently replayed all 59 saved EXACT certificates against their external original queries and checked that all eight UNKNOWN results leave every final-claim field empty. All recorded source hashes remained current.

For the saved small cases, independently enumerated all 741 original binary choice vectors and recomputed exact and folded target counts. For larger equal-choice and binary-power cases, independently checked their closed-form coefficient counts, including 2,705 stored layer entries. Equal-choice factors contribute one fixed exponent with multiplicity 2^i at prefix i. Binary-power prefixes have unit coefficients on every integer from zero through 2^i−1, giving each residue count directly by division. These checks agree with every saved exact query.

Directly checked 52 returned query witnesses using the original integer exponents, plus five separately saved exact-weight witnesses for positive controls. In particular, the eight UNKNOWN query outcomes are compatible with independently known positive answers and do not masquerade as zero coefficients.

The scoped conclusion is supported: separate residue positivity loses the common-witness requirement, and complete counted tables repair that issue with explicit state costs. No impossibility of a better joint-residue or coefficient-isolation algorithm follows.
