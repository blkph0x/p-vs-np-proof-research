# Reproducibility instructions

The repository is a research checkpoint. Run commands from the repository root
with Python 3.11 or newer. The checks use deterministic seeds and exact integer
or rational arithmetic where the report says so.

Install the pinned runtime dependencies before replaying the audit:

```powershell
python -m pip install -r requirements.txt
```

NetworkX is used for the blossom matching routine whose dual output is checked
by `matching_certificate.py`; SymPy is used only for the algebraic
corroboration suite.

All suites used by the full audit, including the proof-portfolio and charged
work controls, are vendored under this repository. A fresh checkout does not
depend on a neighboring checkpoint directory.

## Full audit

```powershell
python run_research_checks.py
```

The command regenerates `TEST_OUTPUT.txt` and `TEST_SUMMARY.json`, then checks
all registered suites. The current checkpoint passes 54 suites and 538 methods
with unchanged source hashes. A full run can take several
minutes because it includes exhaustive finite controls and native rank checks.

## Focused checks

```powershell
python fourier_spectrum_boundary_lab\run_experiments.py
python fourier_spectrum_boundary_lab\verify_fourier_boundary.py
python -m unittest -v test_fourier_spectrum_boundary_integration.py
Push-Location fourier_spectrum_boundary_lab
python run_fwht_cost.py
python review_fwht_cost.py
Pop-Location
Push-Location proof_motif_candidate_lab
python run_indirect_xor.py
python review_indirect_xor.py
Pop-Location
Push-Location proof_motif_candidate_lab
python run_indirect_ite.py
python review_indirect_ite.py
Pop-Location
Push-Location proof_motif_candidate_lab
python run_xor_closure.py
python review_xor_closure.py
Pop-Location
Push-Location proof_motif_candidate_lab
python run_sequential_counter.py
python review_sequential_counter.py
Pop-Location
python run_holographic_phase_checks.py
python verify_holographic_artifacts.py
python proof_complexity_scaling_lab\run_scaling.py
python proof_complexity_scaling_lab\review_scaling.py
Push-Location local_marginal_code_lab
python run_reed_muller_level_d_affine_overlap.py
python REED_MULLER_LEVEL_D_AFFINE_OVERLAP_INDEPENDENT_REVIEW.py
python -m unittest -v test_reed_muller_level_d_affine_overlap.py
Pop-Location
Push-Location local_marginal_code_lab
python run_reed_muller_level_d_full.py
python REED_MULLER_LEVEL_D_FULL_INDEPENDENT_REVIEW.py
python -m unittest -v test_reed_muller_level_d_full.py
Pop-Location
Push-Location local_marginal_code_lab
python run_reed_muller_sos_moment.py
python REED_MULLER_SOS_MOMENT_INDEPENDENT_REVIEW.py
python -m unittest -v test_reed_muller_sos_moment.py
Pop-Location
Push-Location local_marginal_code_lab
python run_reed_muller_sos_strengthened.py
python REED_MULLER_SOS_STRENGTHENED_INDEPENDENT_REVIEW.py
python -m unittest -v test_reed_muller_sos_strengthened.py
Pop-Location

Push-Location local_marginal_code_lab
python run_reed_muller_sos_two_cut.py
python REED_MULLER_SOS_TWO_CUT_INDEPENDENT_REVIEW.py
python -m unittest -v test_reed_muller_sos_two_cut.py
Pop-Location

Push-Location local_marginal_code_lab
python run_reed_muller_sos_three_cut.py
python REED_MULLER_SOS_THREE_CUT_INDEPENDENT_REVIEW.py
python -m unittest -v test_reed_muller_sos_three_cut.py
Pop-Location

Push-Location local_marginal_code_lab
python run_reed_muller_sos_four_cut.py
python REED_MULLER_SOS_FOUR_CUT_INDEPENDENT_REVIEW.py
python -m unittest -v test_reed_muller_sos_four_cut.py
Pop-Location

Push-Location local_marginal_code_lab
python run_reed_muller_sos_five_cut.py
python REED_MULLER_SOS_FIVE_CUT_INDEPENDENT_REVIEW.py
python -m unittest -v test_reed_muller_sos_five_cut.py
Pop-Location

Push-Location local_marginal_code_lab
python run_reed_muller_sos_six_cut.py
python REED_MULLER_SOS_SIX_CUT_INDEPENDENT_REVIEW.py
python -m unittest -v test_reed_muller_sos_six_cut.py
Pop-Location

The strengthened replay now reports `EXACT_OPTIMUM`: both saved certificates
equal `7037/1095`, the reduced-cost minimum is `0`, and the gap is `0`. The
certificate replay itself uses only the repository's exact arithmetic path;
the exploratory active-basis search used SciPy and FLINT to discover the saved
rational dual and is documented in
`local_marginal_code_lab/REED_MULLER_EXACT_DUAL_SEARCH_REPORT.md`.

The two-cut replay reports `EXACT_OPTIMUM`: both saved certificates equal
`367/57`, the reduced-cost minimum is `0`, and the gap is `0`. The added cut is
the valid integer-weight polynomial `(t-6)(t-7)`, and its exact dual multiplier
is `7/171`.

The three-cut replay reports `EXACT_OPTIMUM`: both saved certificates equal
`5231/801`, the reduced-cost minimum is `0`, and the gap is `0`. The added
integer-weight product is `(t-6)(t-7)(t-23)(t-24)` and its exact dual
multiplier is `7/9612`.

The four-cut replay reports `EXACT_OPTIMUM`: both saved certificates equal
`1219047171/184149541`, the reduced-cost minimum is `0`, and the gap is `0`.
The added integer-domain polynomial is
`t(31-t)(t-3)(t-4)(t+28)`, with exact dual multiplier
`4151/1657345869`.

The five-cut replay reports `EXACT_OPTIMUM`: both saved certificates equal
`324713143/48731153`, the reduced-cost minimum is `0`, and the gap is `0`.
The added core polynomial is `t(31-t)(t-3)(t-4)`, with exact dual multiplier
`178066/1315741131`; the earlier boundary product is slack in this optimum.

The six-cut replay reports `EXACT_OPTIMUM`: both saved certificates equal
`22465669893401/3255387995415`, the reduced-cost minimum is `0`, and the gap
is `0`. The added polynomial is
`(t-6)(t-7)(31-t)(t+32)^2`, with exact dual multiplier
`82328743/39064655944980`.
Push-Location resolution_width_lab
python run_indexed.py
python review_indexed.py
python run_bitset.py
python review_bitset.py
python run_pebble.py
python review_pebble.py
python run_php_width.py
python review_php_width_proof.py
Pop-Location
Push-Location proof_complexity_scaling_lab
python -m unittest -v test_scaling.py
Pop-Location
```

These commands cover the newest Fourier span result and the simultaneous-basis
certificate, plus the proof-producing CDCL scaling bridge. The GitHub Actions
workflow runs the focused set on every push.

The companion Pages workflow (`.github/workflows/pages.yml`) builds the Jekyll
site before deploying it. A deployment therefore cannot publish an artifact
that the site build itself rejected.

## Updating a result

1. Change the experiment and its theorem/report together.
2. Add or update an independent checker and a mutation or negative control when
   the method has a meaningful failure mode.
3. Run the focused checks, then the full audit.
4. Add public citations to the report and regenerate `PUBLIC_SOURCES.md`.
5. Regenerate `REPOSITORY_MANIFEST.json`, inspect the staged diff, and commit
   the code, artifact, report, test summary, and manifest as one logical update.

The large affine stress artifact is stored with Git LFS. A fresh checkout needs
Git LFS enabled so that its pointer is hydrated before running the full audit.
The generated native executable is intentionally excluded; its C++ source and
deterministic Python audit are tracked.

Push-Location local_marginal_code_lab
python run_reed_muller_sos_seven_cut.py
python REED_MULLER_SOS_SEVEN_CUT_INDEPENDENT_REVIEW.py
python -m unittest -v test_reed_muller_sos_seven_cut.py
Pop-Location

The seventh-cut replay reports `EXACT_OPTIMUM`: both saved certificates equal
`35873801083/5129253893`, the reduced-cost minimum is `0`, the positive minimum
is `154880840/165459803`, and the gap is `0`. The added polynomial is
`(t-6)(t-7)(31-t)`, with exact dual multiplier
`181738963/30775523358`; the earlier six-cut witness violates it by
`-3473117738496/217025866361`.
