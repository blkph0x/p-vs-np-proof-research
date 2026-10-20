"""Normalize saved text artifacts for Git while preserving original byte hashes.

This is packaging, not a solver/proof rerun. Model/candidate JSON already use
LF. Existing source hashes are never rebound. Repeated calls are idempotent.
"""
from pathlib import Path
import hashlib
import json
import re

HERE = Path(__file__).resolve().parent


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write(path, value):
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n",
                    encoding="utf-8", newline="\n")


def main():
    before_decisions = {str(path.relative_to(HERE)): digest(path)
                        for path in HERE.rglob("candidate.json")}
    before_decisions.update({str(path.relative_to(HERE)): digest(path)
                             for path in HERE.rglob("model.json")})
    cases = [
        ("mixed_cut_run", "results", ("nine_control", "ten_cut")),
        ("ten_scope_run", "selected_result", ("selected_ten_scope",)),
        ("double_external_run", "results", ("compact", "combined")),
        ("compact_combined_run", "selected_result", ("compact_combined",)),
    ]
    for run, field, labels in cases:
        path = HERE / run / "RESULTS.json"
        report = json.loads(path.read_text())
        for label in labels:
            result = report[field][label] if field == "results" else report[field]
            result.setdefault("artifact_raw_sha256_before_lf", result["artifact_sha256"])
            directory = HERE / run / label
            for artifact in directory.iterdir():
                if artifact.is_file():
                    raw = artifact.read_bytes()
                    normalized = raw.replace(b"\r\n", b"\n")
                    normalized.decode("utf-8", errors="strict")
                    if raw != normalized:
                        artifact.write_bytes(normalized)
            result["artifact_sha256"] = {artifact.name: digest(artifact)
                                         for artifact in sorted(directory.iterdir())
                                         if artifact.is_file()}
            result["artifact_encoding"] = "UTF-8, LF; raw pre-normalization hashes retained separately"
        report["packaging"] = {
            "operation": "Lossless text newline normalization after discovery; no proof rerun",
            "script_sha256": digest(Path(__file__)),
        }
        write(path, report)
    for name in ("TESTS_NORMAL.txt", "TESTS_OPTIMIZED.txt", "TESTS_STALE_DOCUMENT_REJECTED.txt"):
        path = HERE / name
        path.write_bytes(path.read_bytes().replace(b"\r\n", b"\n"))
    for relative, expected in before_decisions.items():
        if digest(HERE / relative) != expected:
            raise ValueError("unexpected mathematical artifact mutation")
    records = []
    for filename, optimized in (
        ("TESTS_NORMAL.txt", False),
        ("TESTS_OPTIMIZED.txt", True),
    ):
        text = (HERE / filename).read_text()
        match = re.search(r"Ran 10 tests in ([0-9.]+)s", text)
        if match is None or not text.rstrip().endswith("OK"):
            raise ValueError("missing successful final test transcript")
        records.append({"command": "python -B " + ("-O " if optimized else "") +
                        "-m unittest test_exploration -v",
                        "tests": 10, "exit_code": 0, "seconds": match.group(1),
                        "transcript": filename, "sha256": digest(HERE / filename)})
    write(HERE / "TEST_SUMMARY.json", {
        "schema": "rm2-level10-exploration-tests-v1", "status": "PASS",
        "tests": records,
        "test_source_sha256": digest(HERE / "test_exploration.py"),
        "reviewer_source_sha256": digest(HERE / "review_level10.py"),
        "final_review_sha256": digest(HERE / "FINAL_REVIEW.json"),
        "stale_document_control": {
            "status": "REJECTED_AS_EXPECTED",
            "explanation": "An external edit changed a recorded dependency; it was restored before final passing runs.",
            "transcript": "TESTS_STALE_DOCUMENT_REJECTED.txt",
            "sha256": digest(HERE / "TESTS_STALE_DOCUMENT_REJECTED.txt"),
        },
        "packaging_scope": "Newlines only; all model and candidate bytes unchanged.",
    })
    print("PACKAGED: six candidate/model pairs unchanged; text hashes portable; 10+10 tests PASS")


if __name__ == "__main__":
    main()
