"""Run fresh source-bound replay and normal/optimized adversarial tests."""
from pathlib import Path
import hashlib
import json
import subprocess
import sys
import time

HERE = Path(__file__).resolve().parent


def hashes():
    return {path.name: hashlib.sha256(path.read_bytes().replace(b"\r\n", b"\n")).hexdigest()
            for path in sorted(HERE.iterdir()) if path.suffix in (".py", ".md")}


def main():
    before, started = hashes(), time.perf_counter()
    records = []
    stages = [
        ("REPLAY_OUTPUT.txt", [sys.executable, "-B", "replay.py"]),
        ("TESTS_NORMAL.txt", [sys.executable, "-B", "-m", "unittest", "test_conditioning", "-v"]),
        ("TESTS_OPTIMIZED.txt", [sys.executable, "-B", "-O", "-m", "unittest", "test_conditioning", "-v"]),
    ]
    for filename, command in stages:
        start = time.perf_counter()
        completed = subprocess.run(command, cwd=HERE, capture_output=True, text=True,
                                   encoding="utf-8")
        output = completed.stdout + completed.stderr
        (HERE / filename).write_text(output, encoding="utf-8", newline="\n")
        records.append({"command": command, "returncode": completed.returncode,
                        "log": filename, "elapsed_seconds": time.perf_counter() - start})
        print(filename, completed.returncode, records[-1]["elapsed_seconds"], flush=True)
        if completed.returncode:
            break
    after = hashes()
    passed = len(records) == 3 and all(row["returncode"] == 0 for row in records) and before == after
    artifacts = ["exact_run/RESULTS.json", "REPLAY.json"] + [row["log"] for row in records]
    report = {
        "status": "PASS" if passed else "FAIL",
        "source_sha256_lf": before, "source_after_sha256_lf": after,
        "sources_unchanged": before == after, "stages": records,
        "tests_each_mode": 9 if passed else None,
        "elapsed_seconds": time.perf_counter() - started,
        "artifact_sha256_lf": {name: hashlib.sha256(
            (HERE / name).read_bytes().replace(b"\r\n", b"\n")).hexdigest()
            for name in artifacts if (HERE / name).is_file()},
    }
    (HERE / "TEST_SUMMARY.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n",
                                          encoding="utf-8", newline="\n")
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
