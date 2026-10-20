# Pinned Windows PySAT proof-stream exit control

Observed on 2026-10-20 with the existing CPython 3.10 Windows installation,
`python-sat==1.9.dev16`, and its Glucose3 backend. No installed package or
research production source was modified during these probes.

## Result

All five SAT inputs that failed in the pilot reproduced exit code
`3221226505` (`0xC0000409`) in three out of three runs with proof logging
enabled and its output unread. Each failed child printed both
`solver_deleted` and `normal_main_return` before exiting abnormally. Its
returned assignment had already been checked against every original clause.
This was a process-lifecycle failure, not grounds to accept that process.

Each of the same five inputs exited zero in three out of three runs with:

1. Proof logging disabled.
2. Proof logging enabled and the public `get_proof()` method called before
   leaving the solver context.
3. Proof logging enabled and the pinned extension's `flushpr(prfp)` called
   before leaving that context.

The contradictory-unit UNSAT and simple-unit SAT controls exited zero in all
four modes. Altogether this is **84 subprocess observations**:
7 originals × 4 modes × 3 repetitions. Every subprocess had a five-second
external timeout; none timed out. All recorded source hashes stayed unchanged.

| Original SAT input | Unread proof exits | Read proof exits | Flushed proof exits | No proof exits | Trace lines when read |
| --- | --- | --- | --- | --- | ---: |
| `unused_variables_sat` | abnormal ×3 | zero ×3 | zero ×3 | zero ×3 | 1 |
| `random3_20_86` | abnormal ×3 | zero ×3 | zero ×3 | zero ×3 | 8 |
| `planted3_20_86` | abnormal ×3 | zero ×3 | zero ×3 | zero ×3 | 11 |
| `random3_40_172` | abnormal ×3 | zero ×3 | zero ×3 | zero ×3 | 14 |
| `planted3_40_172` | abnormal ×3 | zero ×3 | zero ×3 | zero ×3 | 10 |

The two small controls had zero trace lines when read. The result establishes
the bounded workaround on these inputs; it does not establish universal
memory safety or diagnose a faulting native instruction.

## Source evidence

The installed wheel records SHA256
`c597c19c0588bb29ed78ca8e6bd6b580c72530e01f60ab20d9224406fd2adcaf`.
The corresponding source distribution was downloaded from the
[official PyPI release](https://pypi.org/project/python-sat/1.9.dev16/)
and checked against its published SHA256
`438798197dbaebfc7ccd729bd6df02addf892c4bd6df5e3919863f56f195c7c1`.
`SOURCE.json` retains the exact download URL and hashes of the extracted files.
The installed Python wrapper is byte-identical to the wrapper in that source
distribution.

Inspection of that pinned source found:

- `pysolvers.cc:9` disables `setlinebuf` under MSVC.
- `pysolvers.cc:8238` wraps Python's descriptor with a C `FILE*` for Glucose3
  proof output.
- `solvers.py:5315` implements public `get_proof()` by flushing that native
  stream before seeking and reading the Python file.
- `solvers.py:5175` deletes the solver and closes the Python file.
- `pysolvers.cc:8381` deletes the native solver without an explicit stream
  flush in that wrapper function.
- The bundled Glucose patch comments out its former proof-stream `fclose`.

Together with the read-versus-unread experiment, these facts support a
buffered proof-stream lifecycle explanation. No debugger trace was captured,
so the precise runtime fault path remains an inference.

## Reproduction and use

Run `python -B run_diagnosis.py` from this directory. The script imports only
the original case generator from the research repository, saves copies of
the seven original requests here, and starts separate probe processes.
`RESULTS.json` records every command, stdout, stderr, exit code, request hash,
source hash, and elapsed time.

For the benchmark adapter, the demonstrated public-API workaround is to call
`get_proof()` after every completed solve, including SAT, before closing the
solver context. A SAT trace is not an UNSAT proof. Keep independent original
model/proof verification and require a normal zero process exit. Do not
reinterpret the pilot's abnormal exits as successful runs.

For a small committed provenance record, copy only `DIAGNOSIS.md`,
`SOURCE.json`, `RESULTS.json`, `probe.py`, `run_diagnosis.py`, and the seven
original request JSON files. The local source archive, extracted upstream
files, installed wheel and binary extension need not be vendored.
