# Coefficient-isolation results

All 5,740 exhaustive coefficient queries agreed between independent choice enumeration, sparse counting and carry-free integer digits. All 87 exact prime-field filter cases were serialized and replayed, including complete saved modular evaluation tables.

The alias-free characteristic-13 filter returns zero for the positive coefficient 26. A large characteristic or verified same-count CRT recovers 26 exactly. The saved missing-target example returns a positive folded residue when exponent aliasing is allowed. Separate residue tests use different witnesses and do not establish one exact matching.

A 40-factor binary-ladder product has an exact coefficient of one at the saved target. The generic packed and sparse methods return UNKNOWN under their explicit caps, while the proved binary-ladder identity returns the count immediately. This distinguishes a method limitation from inherent difficulty of that family.

The results include normalization, zero-factor multiplicities, whole-product identity-test and finite-field evaluation counterexamples, the CRT binding caveat, and an exact precision calculation for near-zero evaluation. No floating-point result is used as a certificate.

Run `python -m unittest -v test_coefficient` and `python run_experiments.py` here. Original requests and before/after source hashes are saved in RESULTS.json. Measured experiment time: 0.133816s. No novelty or P-versus-NP resolution is claimed.
