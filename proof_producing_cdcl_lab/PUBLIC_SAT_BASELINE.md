# Public SAT discovery with original-formula certificate checking

20 October 2026. The final paired campaign verifies **114/114 runs** on
19 deterministic CNFs, two engines and three repetitions: 54 SAT models and
60 UNSAT certificates. All producer/checker source hashes remained unchanged.
The [complete run record](PUBLIC_SAT_BASELINE/benchmark.json) and
[replay result](PUBLIC_SAT_BASELINE/replay.json) are saved.

This adopts a public search implementation and proof format. It does not
introduce a new SAT algorithm, establish general performance superiority,
or resolve P versus NP. The Python reference checker is deliberately simple
and is the dominant cost on the largest proof in this small campaign.

## What is borrowed and what is checked

[PySAT](https://pysathq.github.io/docs/html/api/solvers.html) exposes the
Glucose3 search engine and DRUP proof logging through a Python interface.
This experiment pins `python-sat==1.9.dev16` and `six==1.16.0`, rather than
following the moving online documentation. The installed CPython 3.10 Windows
wheel is identified by its
[published PyPI release](https://pypi.org/project/python-sat/1.9.dev16/)
and SHA256:

```text
c597c19c0588bb29ed78ca8e6bd6b580c72530e01f60ab20d9224406fd2adcaf
```

The comparison engine is the repository's unchanged full-scan CDCL reference.
Both receive exactly the same original clauses, including their order,
duplicates and tautologies. The adapter retains the declared variable count;
PySAT infers variables from clauses, and the adapter fills unused model entries
before checking the complete original request. No transformed
formula or planted solution is substituted at acceptance.

The independent [acceptance module](sat_backend_certificate.py) checks:

- SAT: a full Boolean assignment satisfying every original clause.
- Public UNSAT: a hash-bound proposed trace, with every addition checked by
  [forward reverse-unit propagation](rup_verify.py) from the original CNF.
  This restricted checker has no RAT fallback or fresh-variable extensions.
- Native UNSAT: the existing original-bound explicit-resolution reviewer.
- Caps or abnormal child exits: `UNKNOWN`, never an inferred decision.

The RUP soundness argument is inductive. If unit propagation on the current
clauses together with the negation of a proposed clause reaches a conflict,
the current clauses entail that clause. Verified additions preserve the
models of the original formula; deletions only remove entailed constraints.
A verified empty clause therefore refutes the original formula. The parser,
propagation implementation and this argument are not a proof-assistant
certification. Small exhaustive and adversarial tests supplement them.

The adapter separately proposes the addition-only projection of the raw
solver log. It retains the raw log, omits deletion lines from the proposal,
and proposes a terminal empty clause if absent. **None of these operations
certifies UNSAT.** Every retained addition and the terminal empty clause
must pass the independent checker. Deletion removal is not claimed to
preserve arbitrary RAT proofs; no RAT proof is accepted by this checker.

For the 27 public UNSAT runs without an explicit original empty clause,
the same proposed proof also passed
[DRAT-trim](https://github.com/marijnheule/drat-trim), pinned to
[`2e3b2dc0`](https://github.com/marijnheule/drat-trim/tree/2e3b2dc0ecf938addbd779d42877b6ed69d9a985).
The other three public UNSAT runs contain an original empty clause, which
the independent checker directly validates. Native runs use their separate
resolution certificates.

## Measured comparison

The workload contains trivial controls, PHP(3,2) through
PHP(7,6), a renamed/reordered PHP instance, XOR chains with 16/64 input variables and
existential helper variables, and fixed-seed random/planted 3-CNFs.
The XOR CNFs contain 31/127 variables including helpers. Malformed-claim
controls belong to the separate test suite, not the timed workload.
“Random” rows here are deterministic generated samples, not an industrial
benchmark distribution. All four sampled random/planted formulas are SAT.

Each search runs in a new process with a five-second wall limit. The native
engine also receives a 5,000-decision cap. Its known resolution-step cap
defect is not used as a resource guarantee. Launch order alternates.
Windows 10 build 22631, CPython 3.10.10 and the exact extension hash are
recorded in the manifest. There is no CPU pinning or cgroup isolation.

Selected medians in seconds, from three repetitions:

| Original instance | Engine | Search process | Solve call only | Independent check | Public checker process | Combined measured stages |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| PHP(5,4) | Native | 0.1906 | 0.008886 | 0.0216 | — | 0.2128 |
| PHP(5,4) | Glucose3 | 0.2005 | 0.000090 | 0.0260 | 0.1489 | 0.3754 |
| PHP(7,6) | Native | 0.5072 | 0.279291 | 0.0857 | — | 0.5920 |
| PHP(7,6) | Glucose3 | 0.2249 | 0.004157 | 8.8725 | 0.1677 | 9.2634 |
| Shuffled PHP(6,5) | Native | 0.3740 | 0.157240 | 0.0530 | — | 0.4264 |
| Shuffled PHP(6,5) | Glucose3 | 0.1946 | 0.000712 | 0.3941 | 0.1542 | 0.7417 |
| XOR chain 64, SAT | Native | 0.1958 | 0.028167 | 0.0122 | — | 0.2080 |
| XOR chain 64, SAT | Glucose3 | 0.1910 | 0.000033 | 0.0021 | — | 0.1927 |

“Search process” includes imports, construction, solving, certificate export
and child startup/teardown. Construction and export also have separate
worker measurements. “Combined measured stages” is the median of each run's
search-process, independent-check and external-check sum, not the sum of
separate medians. It excludes case generation, final all-artifact replay,
manifest writing and parent orchestration. These are wall times, not CPU
measurements or a complete end-to-end application latency.

For PHP(7,6), the public candidate plus proposed proof uses **25,511 bytes**,
versus **1,251,467 bytes** for the native envelope, original clauses and
explicit resolution trace. These are different certificate formats; raw
logs and measurement metadata are excluded from that byte comparison.

Search-process totals over all 57 runs per engine are 11.9593 seconds native
and 11.7799 seconds Glucose3. Independent-check totals are 0.9689 and
28.9998 seconds respectively. Thus faster public search and smaller proofs
do **not** produce an overall win with this Python verifier.
The result supports an optional discovery adapter, not replacement of the
default verified path.

Memory records are 20 ms samples of child RSS, not guaranteed peaks and not
whole-process-tree measurements. Observed samples range from 17,149,952 to
26,521,600 bytes for native search and 20,520,960 to 25,309,184 for Glucose.
Parent and in-process independent-checker memory, and CPU time, were not
measured. External DRAT-trim checks have their own sampled RSS records.
Sub-millisecond solver
times on these small inputs should not be extrapolated into scaling laws.

## Failed pilot retained

The first campaign **failed**: 39 verified SAT, 57 verified UNSAT,
15 abnormal-process UNKNOWN outcomes and three rejected proof traces.
Its [full manifest](PUBLIC_SAT_PILOT_REJECTED/benchmark.json), frozen source
snapshots and first repetition of each affected case are retained.
This directory is explicitly an excerpt; it is not a complete replay bundle
for all 114 first-run attempts. Its historical artifact map describes the
full first run. [Evidence tests](test_public_sat_evidence.py) authenticate
the retained subset and preserve the rejection.

Two separate issues were established:

1. **Proof-stream lifecycle on the pinned Windows wheel.**
   Five SAT cases exited `0xC0000409` after writing candidate output.
   [Eighty-four controlled subprocess observations](PUBLIC_SAT_BACKEND_BUILD/pysat-crash/DIAGNOSIS.md)
   reproduce the failure with unread proof output and show successful
   exits when the public `get_proof()` method drains it before close.
   The adapter now drains the stream for SAT as well as UNSAT.
   Its SAT log is not a certificate. The exact native fault path remains
   an inference, not a debugger-confirmed diagnosis. Nonzero exits remain
   UNKNOWN even if a candidate file exists.
2. **Deletion semantics in the shuffled PHP proof.**
   After a learned unit, the raw log deletes 66 original and 75 learned
   clause occurrences. DRAT-trim ignores deletion of nine clauses that
   justify persistent top-level facts. Our fresh-database checker removes
   them and rejects line 262. The
   [saved diagnosis](PUBLIC_SAT_PILOT_REJECTED/php_6_5_shuffled/repeat_0/glucose3/diagnosis.json)
   records official acceptance with zero RAT lemmas and exact rejection by
   the narrower checker. The separate addition-only proposal passes all
   147 additions. The checker was **not weakened** to accept the raw log.

The failed first run is excluded from the final performance table and
reported separately; it has not been silently relabelled as successful.

## Reproduce

From this directory, committed evidence needs only Python's standard library:

```text
python run_public_sat.py --replay PUBLIC_SAT_BASELINE
python -m unittest -v test_rup_verify test_public_sat_certificate test_public_sat_evidence
python -O -m unittest -v test_rup_verify test_public_sat_certificate test_public_sat_evidence
```

Replay verifies the complete artifact map, current source hashes, original
CNFs, run coverage and certificates. It does not rerun the historical
timings or authenticate a past external process by executing it again.
After deliberately changing a bound source file, generate a fresh campaign
instead of editing hashes to claim an old run used new code.

Optional fresh discovery in a separate environment:

```text
python -m pip install -r requirements-public-sat.txt
python run_public_sat.py --output-dir NEW_OUTPUT_DIRECTORY --timeout 5 --repetitions 3
```

For the public second check, build the pinned source in a separate directory:

```text
git clone https://github.com/marijnheule/drat-trim.git
git -C drat-trim checkout --detach 2e3b2dc0ecf938addbd779d42877b6ed69d9a985
gcc drat-trim/drat-trim.c -std=c99 -O2 -o drat-trim-checker
```

On the recorded MinGW setup, add `-Dgetc_unlocked=getc` and use an `.exe`
output name. This maps an unavailable POSIX call to its standard locking
equivalent without changing the upstream source. Add
`--drat-trim PATH_TO_CHECKER` to the fresh campaign command. An optional
`--pysat-dir PATH` allows an isolated `pip --target` installation.
The output directory must be new or empty.

[Build provenance and eight CLI controls](PUBLIC_SAT_BACKEND_BUILD/drat-trim/BUILD_AND_TEST.json)
include the compiler, source hashes, executable hash, failed original
Windows build, successful portability build and MIT license. Archived
build/probe scripts end in `.py.txt`: they preserve the original local
commands and paths, not a portable installer. Use the commands above for a
clean checkout; adapt archived paths only when repeating those diagnostics.
No solver executable or third-party native source is vendored here.

DRAT-trim's exit code alone is insufficient: the adapter requires zero,
exactly one `s VERIFIED`, no timeout, and no error/competing status.
Controls show malformed input may exit zero and an original empty clause
may print VERIFIED but exit one. Original-empty-clause acceptance therefore
uses the independent checker directly.

## Next adoption gate

The next performance improvement is proof checking: evaluate watched-literal
propagation or a hinted, independently checked proof format against these
same originals, including the deleted-reason control. Public
[cake_lpr](https://github.com/marijnheule/cake_lpr) offers a stronger formal
assurance baseline than a second handwritten Python program.
Preserve the original-CNF binding and charge proof conversion and checking.
Keep this simple implementation as an adversarial/differential reference.

Modern CaDiCaL/Kissat, native XOR reasoning, larger public benchmarks,
Linux isolation, incremental-query proofs and certified compilation remain
separate comparison work. This small Glucose experiment cannot rank them.
