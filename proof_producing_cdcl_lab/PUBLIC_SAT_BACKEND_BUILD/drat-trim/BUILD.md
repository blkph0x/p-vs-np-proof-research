# Local Windows DRAT-trim baseline

Built and checked on 2026-10-20. This directory is a local tool cache; nothing was installed globally or added to the research repository.

The source is the official [marijnheule/drat-trim repository](https://github.com/marijnheule/drat-trim), pinned to commit [`2e3b2dc0ecf938addbd779d42877b6ed69d9a985`](https://github.com/marijnheule/drat-trim/tree/2e3b2dc0ecf938addbd779d42877b6ed69d9a985) (2024-11-25, commit message `long`). This is an exact source revision, not a claim that it is a tagged release. The observed official tag `v05.22.2023` points to a different revision. The upstream MIT license is retained in both `source/LICENSE` and `LICENSE`.

The checkout is detached and clean. The compiled `drat-trim.c` bytes were compared with the pinned Git blob. Source and binary SHA256 values, compiler version and target, complete command arguments, timings, stdout/stderr, and the original control inputs are recorded in `BUILD_AND_TEST.json`.

## Reproduction

The initial checkout used these commands from this directory:

```powershell
git -c core.autocrlf=false clone --depth 1 https://github.com/marijnheule/drat-trim.git source
git -C source checkout --detach 2e3b2dc0ecf938addbd779d42877b6ed69d9a985
```

For a future checkout after the upstream default branch has moved, fetch the pinned revision explicitly rather than assume it is in a shallow clone.

The compiler is `C:\Users\Blkph0x\gcc\bin\gcc.exe`, version GCC 11.3.0, target `x86_64-w64-mingw32`. The upstream Makefile-equivalent command failed because this MinGW installation does not supply `getc_unlocked`. The successful command substitutes standard `getc` at compile time and leaves upstream source unchanged:

```powershell
& 'C:\Users\Blkph0x\gcc\bin\gcc.exe' source/drat-trim.c -std=c99 -O2 -Dgetc_unlocked=getc -o drat-trim.exe
```

Run `python build_and_test.py` to repeat the builds and eight bounded controls. This overwrites the local binary, logs and JSON record; it may change the executable hash because bit-for-bit reproducible PE output was not established. The current executable SHA256 is:

```text
40cdaff2c2750417af420829d03d67e96fbf47150606f363f46afc820990cf0c
```

The compiled C source SHA256 is:

```text
d834b649f437e091597f5347f259b9f681087f89ca0844d0cee250a1a1a0c2ee
```

## Checked CLI behavior

Every control invokes `drat-trim.exe INPUT.cnf PROOF.drat -I -t 10`, with an independent 15-second subprocess timeout. `-I` forces ASCII proof input. Put the formula and proof paths before the options.

| Control | Exit code | Status |
| --- | ---: | --- |
| Contradictory original unit clauses, proof `0` | 0 | `s VERIFIED` |
| Four binary clauses with valid RUP proof `1 0; 0` | 0 | `s VERIFIED` |
| Same four clauses, forged proof containing only `0` | 1 | `s NOT VERIFIED` |
| Same four clauses, empty incomplete proof | 1 | `s NOT VERIFIED` |
| Original unit formula mutated to satisfiable | 1 | `s NOT VERIFIED` |
| Original binary formula mutated to satisfiable | 1 | `s NOT VERIFIED` |
| Missing DIMACS header | 0 | No status; error printed |
| Original formula already containing an empty clause | 1 | `s VERIFIED` |

The contradictory-unit case alone is insufficient to test rejection of forged proofs: that original formula is already refutable by unit propagation. The additional four-binary-clause control exercises a proof-dependent RUP step.

For ordinary externally checked proofs, a conservative adapter should require successful process completion, exit code 0, exactly one standalone `s VERIFIED` status, and no error or competing status. Validate the original DIMACS data independently; an original empty clause can be certified directly before invoking this CLI. Do not treat exit code 0 alone as verification.

Source inspection also found a native timeout path that prints `s TIMEOUT` and exits 0, plus parse/allocation error paths that exit 0. That timeout path was inspected, not triggered by these small controls. Native `-t` checks are not an encompassing wall-clock bound; retain an external subprocess deadline.

These results establish a working pinned public checker on this host and document its adapter contract. They are bounded CLI controls, not formal verification of DRAT-trim or evidence about performance on large proofs. No upstream source changes, research-source changes, commits or pushes were made.
