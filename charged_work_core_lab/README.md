# Non-graphic cores and exact coordinate conditioning

Read `REPORT.md` for measurements, `THEOREMS.md` for the conditioning proof, and
`FANO_NOTES.md` for the graph obstruction certificates and primary reference.

```powershell
python -m unittest discover -v
python run_lab.py
```

Both commands use only Python's standard library. The runner also imports the
sibling `high_width_core_stress_lab` reference algorithms and saved matrices.
It works from any current directory and writes `results.json` and `results.csv`
beside the script. Timings vary across runs; mathematical results and work counts
are deterministic for the saved inputs and seed.

Files:

- `fano_certificate.py`: bounded discovery and independent verification of F7 minors.
- `deletion_solver.py`: exact affine-coset trellis, bounded coordinate selection,
  and `EXACT`/`UNKNOWN` result semantics.
- `run_lab.py`: six stored samples, 24 solver comparisons, graphic and budget controls.
- `charged_work_review.py`: independent replay of the `2^w` charged-work bound
  for every completed conditioning run.
- `test_*.py`: independent finite checks, malformed certificates and interrupted search.
- `results.json`: complete witnesses, certificates, profiles, work counters and provenance.
- `results.csv`: compact comparison table.
- `CHARGED_WORK_REVIEW.json`: source-bound charged-work replay for all 24 exact cases.

Limits are configurable: `--max-transitions`, `--max-candidates`, `--fano-trials`.
Reducing limits can produce `UNKNOWN` or incomplete candidate selection. A lack of
certificate is never interpreted as a graph recognition or hardness result. The
unbudgeted reference enumeration/trellis runs are restricted by the six small saved inputs.
