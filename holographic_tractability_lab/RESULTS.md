# Saved real-affine evaluation results

42 saved original requests: {'EXACT': 15, 'UNSUPPORTED': 26, 'UNKNOWN': 1}.

Every EXACT result has been checked from its external original network or formula. The transformed K3,3 and 120-edge equality-family controls both evaluate to 2. The latter avoids enumeration of 2^120 assignments.

Single/repeated ternary Boolean counts are 7/7; the corresponding slack counts are 10/16. The all-eight-polarity formula is independently UNSAT. The 24-variable/96-clause controls retain a satisfying original assignment, but their tested local tensors remain unsupported. Neither unsupported cases nor the interrupted case contain a value claim.

The test suite covers all 1,099 quadratic phases through four variables, 240 seeded full-contraction comparisons, inverse nonsymmetric rational bases, external request mutations, malformed proofs, signed cancellation, exact rational/big-integer arithmetic, and budget interruptions. Source hashes and complete replay inputs are in RESULTS.json.
