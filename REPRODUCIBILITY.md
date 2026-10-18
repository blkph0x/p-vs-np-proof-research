# Reproducibility instructions

The repository is a research checkpoint. Run commands from the repository root
with Python 3.11 or newer. The checks use deterministic seeds and exact integer
or rational arithmetic where the report says so.

## Full audit

```powershell
python run_research_checks.py
```

The command regenerates `TEST_OUTPUT.txt` and `TEST_SUMMARY.json`, then checks
all registered suites. The frozen checkpoint on 18 October 2026 passed 31
suites and 260 methods with unchanged source hashes. A full run can take several
minutes because it includes exhaustive finite controls and native rank checks.

## Focused checks

```powershell
python fourier_spectrum_boundary_lab\run_experiments.py
python fourier_spectrum_boundary_lab\verify_fourier_boundary.py
python -m unittest -v test_fourier_spectrum_boundary_integration.py
python run_holographic_phase_checks.py
python verify_holographic_artifacts.py
```

These commands cover the newest Fourier span result and the simultaneous-basis
certificate. The GitHub Actions workflow runs this focused set on every push.

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
