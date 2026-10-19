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
all registered suites. The current checkpoint passes 44 suites and 452 methods
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
