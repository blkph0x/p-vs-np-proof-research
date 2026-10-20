"""Regenerate finite evidence and source-bound normal/optimized test records."""
from __future__ import annotations

import gzip
import hashlib
import json
from pathlib import Path
import platform
import re
import subprocess
import sys
from time import perf_counter

import chain
import verify

HERE = Path(__file__).resolve().parent


def source_hashes():
    # Separate implementation of the documented UTF-8/LF normalization.
    answer = {}
    for name in ("chain.py", "verify.py", "test_hierarchy.py", "run_experiments.py", "THEOREM.md"):
        text = (HERE/name).read_bytes().decode("utf-8")
        text = text.replace("\r\n", "\n").replace("\r", "\n")
        answer[name] = hashlib.sha256(text.encode("utf-8")).hexdigest()
    return answer


def main():
    before = source_hashes()
    start = perf_counter()
    artifact = chain.build_artifact()
    checked = verify.verify_artifact(artifact)
    if not checked["valid"]:
        raise ValueError(checked)
    payload = json.dumps(artifact, sort_keys=True, separators=(",", ":")).encode("utf-8")
    compressed = gzip.compress(payload, mtime=0)
    (HERE/"CERTIFICATE.json.gz").write_bytes(compressed)
    evidence_seconds = perf_counter()-start
    tests = []
    for optimized in (False, True):
        command = [sys.executable, "-B"] + (["-O"] if optimized else [])
        command += ["-m", "unittest", "-v", "test_hierarchy"]
        started = perf_counter()
        run = subprocess.run(command, cwd=HERE, stdout=subprocess.PIPE,
                             stderr=subprocess.STDOUT, timeout=60)
        text = run.stdout.decode("utf-8", errors="strict").replace("\r\n", "\n")
        name = "TESTS_OPTIMIZED.txt" if optimized else "TESTS_NORMAL.txt"
        (HERE/name).write_text(text, encoding="utf-8", newline="\n")
        matches = re.findall(r"Ran (\d+) tests? in", text)
        tests.append({"optimized": optimized, "command": command,
                      "exit_code": run.returncode, "tests": int(matches[-1]) if matches else None,
                      "wall_seconds": perf_counter()-started, "transcript": name,
                      "sha256_lf": hashlib.sha256(text.encode("utf-8")).hexdigest()})
        if run.returncode:
            raise RuntimeError(text)
    after = source_hashes()
    result = {"schema": "fixed-width-affine-hierarchy-results-v1",
              "status": "PASS" if before == after else "SOURCE_CHANGED",
              "python": platform.python_version(), "platform": platform.platform(),
              "source_sha256_lf": before, "source_after_sha256_lf": after,
              "sources_unchanged": before == after,
              "certificate_sha256": hashlib.sha256(compressed).hexdigest(),
              "certificate_bytes": len(compressed), "independent_replay": checked,
              "evidence_seconds": evidence_seconds, "tests": tests,
              "scope": "Fixed finite controls; the all-input fixed-k classification rests on THEOREM.md. No SAT speed, proof-assistant, novelty, or complexity separation claim."}
    (HERE/"RESULTS.json").write_text(json.dumps(result, indent=2, sort_keys=True)+"\n",
                                   encoding="utf-8", newline="\n")
    if before != after:
        raise RuntimeError("source changed during the experiment")
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
