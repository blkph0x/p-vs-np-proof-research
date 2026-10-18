# Independent threshold-control review

The OR construction, summed-budget counterexample and equal-mass feature-trade
proof are sound within their stated scopes. The four-point trade excludes
every real affine score on the supplied original features. It does not exclude
a SAT decision reduction with a different representation or decoder.

The entire physical OR signature is correctly characterized: invalid half-pairs
are infeasible, and a union of j whole pairs has cost k-j. This differs from a
common-minimum clause penalty and from an AND gate relation with an output.
The logical aggregation counterexample does not pretend to supply variable
wiring for matching gadgets; it grants consistency and still exposes the
particular sum rule's false positive.

Review found a valid-input handling defect in decimal JSON input hashing:
features with more than Python's permitted decimal digit count were rejected
despite being valid integers or rational values. The producer replaced the
hash with a versioned, signed, length-prefixed binary encoding. The mathematical
proof was unaffected. No process-wide interpreter guard was disabled.

After that repair, this review independently checked 200 affine rational
transformations of the four-bit features. Every transformed equal-mass trade
verified. Changing one feature and recomputing the input binding caused every
one of the 200 false trades to be rejected on mathematical grounds. Three
additional valid trades using positive and negative 2^15000 and denominator
2^15000 verified successfully. The unit tests separately cover these cases.

The verifier checks the original truth labels, nonempty equal mass and exact
feature sums independently of the hash. Its finite input and certificate caps
are explicit. No outstanding correctness issue was found. The all-size claims
come from the written proofs; finite experiments are supporting controls.
