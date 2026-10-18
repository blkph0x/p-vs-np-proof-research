# Independent frozen-boundary artifact cross-check

All 96 saved EXACT production messages were independently recomputed by the block support-parametrization/internal-pair algorithm, checked by its left-nullspace and pair-identity verifier, and compared symbolically with the production messages. All agree, including a 512-coordinate retained boundary. No boundary truth table was expanded for those wide cases.

The six production UNKNOWN records contain no message or certificate. Each exact case used a separate reference work cap of 20,000,000; this validates the function and does not assert identical cost or success under the production caps.

BOUNDARY_CROSSCHECK.json records the source/result hashes, original-case indices, reference input bindings, recomputed messages and verification outcomes. The original requests remain in the hash-bound production RESULTS.json. The replay script is crosscheck_boundary.py. All hashed inputs were unchanged during the run. This is a reproducible validation report, not a proof-assistant formalization.
