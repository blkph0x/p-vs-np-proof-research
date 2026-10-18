# Checked pairwise compression of real-affine sums

This lab implements four exact local sum identities. It does not claim a canonical smallest sum, a confluent rewrite system, or a polynomial algorithm for arbitrary SAT. Input order can change the final number of pieces. The reviewed design is [AFFINE_SUM_COMPRESSION_NEXT.md](../AFFINE_SUM_COMPRESSION_NEXT.md); this implementation preserves its finite scope.

## Functions and original coordinates

A nonzero message represents

`f(x) = c * 1[A x = b] * (-1)^q(x)`.

Coordinates keep their original IDs in `0,...,n-1`; `retained` is an externally supplied ordered subset. All equations and monomials use only retained IDs. `c` is an exact nonzero rational. `A x=b` is consistent and in the canonical RREF order of retained IDs. Its free IDs are explicitly recorded. The phase is a Boolean polynomial of degree at most two in those common free coordinates, with no constant term; its constant sign has been absorbed into `c`. The canonical zero has empty equations, phase and free IDs and scalar `[0,1]`.

Every incoming message must already have this complete canonical shape. The producer re-normalizes and compares every field, and the checker independently verifies that normalization against the external incoming equations, phase and scalar. In particular, misleading zero/free-coordinate metadata is rejected, rather than ignored. Canonicalization uses the frozen [affine boundary producer and verifier](../affine_boundary_lab/boundary.py), with active and retained coordinates equal and an empty elimination order. No inactive coordinate contributes a factor of two.

## Exact identities

All polynomial arithmetic below is in the Boolean ring over GF(2), so repeated monomials cancel and `x_i^2=x_i`.

1. **Identical normalized functions.** Equal support and phase allow replacing coefficients `c,d` by `c+d`, including exact cancellation to zero.

2. **Same support and affine phase difference.** Let the magnitudes agree, write `d=(-1)^sigma c`, and let `ell=q0+q1` be affine in the same canonical free coordinates. Then

   `c 1_A (-1)^q0 + d 1_A (-1)^q1 = 2c 1_{A and ell=sigma} (-1)^q0`.

   Canonical phases have no constant, so the implementation adds the corresponding linear row with right-hand side `sigma`. Identical phases are handled by rule 1 first. The new support may be empty.

3. **Distinct parallel affine cosets.** Suppose the two canonical supports have the same matrix `A`, different right-hand sides `b0,b1`, and equal coefficient magnitudes. Put `delta=b0+b1` and choose `j` with `delta_j=1`. Their union is the affine support consisting of the rows

   `(A_i + delta_i A_j)x = b0_i + delta_i b0_j`, for `i != j`.

   These rows have rank `rank(A)-1`; on the union, `t=A_j x+b0_j` selects the original coset. If `q0+q1` is affine in their common canonical free coordinates, the union phase

   `Q = q0 + t*(q0+q1+sigma)`

   has degree at most two and realizes both original summands, with scalar `c`. The common-coordinate condition is essential. When the phase difference has a nonzero quadratic part, this rule refuses the merge. Refusal makes no claim about other multi-piece representations or other algorithms.

4. **Nested codimension-one subtraction.** Suppose nonempty affine supports `B` and `A` obey `B subset A`, with `rank(B)=rank(A)+1`. If `qA+qB` restricted to `B` is the constant `epsilon` and `cB=(-1)^(epsilon+1)cA`, the two contributions cancel exactly on `B`. Choose an additional equation `h x=e` of `B` independent of `A`; the remaining function is `cA 1_{A and hx=e+1} (-1)^qA`. The producer checks containment by row reduction and restriction by sequential substitution. The checker instead uses augmented-row ranks for containment and generic polynomial substitution for phase restriction. Rank difference one and the effective sign after restriction are both required. Merely having opposite raw coefficients or syntactically different phases is insufficient.

For canonical consistent supports the augmented rows `(mask,rhs)` are independent. Therefore `rank(rows(B) union rows(A))=rank(B)` is exactly the implication of every equation of `A` by `B`. This also handles redundant equations in an original normalization proof; live canonical messages themselves contain no redundant rows.

Each rule is followed by checked canonical normalization. By induction over the event stream, applying these pointwise identities preserves the entire original sum on every retained assignment, including signed rational cancellation. A zero drop preserves the sum only when its current message was independently derived to be canonical zero.

## Certificate and independent replay

`compress(n, retained, messages, **caps)` returns `EXACT` with `messages`, `certificate`, and producer `stats`. `reduce_sum` is an alias. `verify_compression(n, retained, original_messages, result, **caps)` (alias `verify_sum`) returns `valid`, `status`, independently derived `messages`, `errors` and fresh verifier `stats`.

The certificate contains an ordered event list, the hash of the complete external original request, and final live IDs. Input and generated IDs are fresh consecutive integers. Every input index is consumed once in order. Each rewrite requires two distinct currently live nonzero source IDs, consumes both exactly once, and creates one fresh output. Every untouched ID remains live. The checker rejects omitted, invented or reordered external inputs, reused or absent source IDs, invalid rules, forged normalizations, wrong final IDs, and wrong final messages. A length-prefixed signed-binary encoding binds the external dimension, ordered boundary, and every original piece and metadata field; it does not depend on Python's decimal-integer conversion limit. SHA-256 binding is supplemented by algebraic replay against each supplied original, not used as a substitute for it.

`failed_pair` events are no-ops that preserve both sources. The producer records and charges all attempted pairs and all failed identity tests. The verifier checks that both IDs are currently live but deliberately does not repeat unsuccessful discovery. These events do **not** certify irreducibility, optimal piece count, or completeness of the heuristic. The verifier ignores producer statistics and reports its own verification work separately; its failed-test counters need not equal the producer's. It invokes neither producer discovery nor producer normalization.

Malformed producer requests raise `ValueError` (or the usual iterable/type error for an object that is not iterable); malformed certificates fail closed as `INVALID`. A reached resource cap returns `UNKNOWN`, with no accepted output sum. Verification exhaustion is `valid:false,status:UNKNOWN,messages:null`; it is not mathematical rejection. Producers return neither a partial sum nor a partial certificate on exhaustion.

## Streaming, counters and finite costs

The greedy producer inserts each canonical incoming piece, repeatedly tries it against other live IDs in increasing-ID order, and retries any replacement against the remaining IDs. Old unchanged pairs are not revisited. A merge reduces the number of live pieces by one; no rewrite splits a piece. Empty sums and zero inputs are explicitly supported.

`max_live_pieces` bounds the **settled retained set between arrivals**, including the final set. It is not a peak-memory cap. The arrival is inserted before merging, so an exact run may have `max_live_pieces+1` actual live IDs temporarily. Statistics report both `peak_retained_pieces` and the true `peak_live_pieces`. Before original normalization there is also a pending input object; before source consumption a successful rewrite has a pending generated object. Their individual peaks and `peak_live_plus_pending_objects` are recorded separately. Two identical pieces under settled cap one therefore report retained peak one, actual-live peak two, and live-plus-pending peak three. The caps and counters count mathematical message objects, not bytes or copies inside Python, the normalization checker, the retained proof trace, or a caller-owned input list.

`max_inputs`, `max_generated`, `max_pairs` and `max_steps` bound incoming pieces, successful candidate outputs (including zeros), attempted pairs, and proof events. A budget-rejected reservation is recorded as the attempted count beyond its limit. Every original and generated message is normalized and counted. `max_work` bounds charged algebra operations, including nested normalization work; `max_scalar_bits`, `max_rows`, `max_terms` and `max_variables` bound coefficient bits and individual representations. Dimension is guarded before large bit shifts. These named operation counters are **not total setup CPU**: validation, binary hashing, list/set operations, sorting, RREF pivot metadata construction, copying and serialization still take time polynomial in the explicitly bounded data sizes. Producer and verifier have separate work accounting and potentially different thresholds.

For fixed boundary size, coefficient bit limit, row/term limits and finite event/input/pair bounds, each implemented row, polynomial, rational and normalization operation has polynomial bit cost in those bounds. Integer masks have at most `n+1` bits; ordinary rational addition uses products of bounded-bit numerators/denominators before checking the resulting bit bound. Phase substitution is at most quadratic and operation-capped. There is no `2^|retained|` truth-table expansion in production or verification. Certificate storage includes all input and output normalization proofs and all no-op attempts, so it grows with the charged events and their explicit message sizes. A caller that materializes exponentially many input pieces has already paid that cost; streaming does not remove it. No theorem bounds the retained piece count, total arrivals, failed searches or DAG generation polynomially for arbitrary formulas.

The tests and saved controls separately use bounded original-assignment enumeration. Wide controls have explicit algebraic expected messages. The same eight singleton pins can greedily produce one piece in natural order and four pieces in order `[0,1,4,6,3,7,2,5]`. Both outputs are exact; this is direct evidence against conflating verified local compression with a canonical or optimal representation.

## Reproduction

From this directory, run `python -m unittest -v test_compression` and `python run_experiments.py`. The experiment stores original canonical messages, complete certificates, independently replayed verification counters, bounded original-assignment checks or explicit wide algebraic expected outputs, source hashes and an unchanged-source flag. The prior frozen boundary implementation and reviewed design are included in the source provenance map.
