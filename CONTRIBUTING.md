# Contribution and update rules

Keep mathematical claims narrower than the evidence. Every new algorithm must
state its input promise, output, correctness argument, and encoded bit-cost.
Every negative result must name the representation or assumption it excludes.

Use the evidence labels in [`RESOLUTION_STANDARD.md`](RESOLUTION_STANDARD.md),
cite public sources in the local report, and add a reproducible checker. Do not
describe a finite experiment as an asymptotic theorem, and do not describe an
unverified external claim as a result.

Before opening a change for review, run the focused checks and then
`python run_research_checks.py`. Update the method ledger, source index, test
summary, and repository manifest in the same commit. Keep generated artifacts
small enough for normal Git or explicitly add large deterministic artifacts to
Git LFS.
