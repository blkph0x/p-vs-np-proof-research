"""Fresh optional SoPlex search and independent replay for the nine-scope LP.

Discovery receives only a source-built model. Stored replay needs no solver.
The generic certificate proves this selected LP's optimum; the separately
written mathematical containment argument connects it to full locality nine.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import platform
import subprocess
import sys

from run_exact_lp_discovery import run_stage, sha256, write_json

HERE = Path(__file__).resolve().parent
SOURCES = (
    "run_rm2_nine_scope.py", "rm2_nine_scope.py", "review_rm2_nine_scope.py",
    "run_exact_lp_discovery.py", "exact_lp_model.py", "exact_lp_verify.py",
    "exact_lp_soplex.py", "reed_muller_affine_overlap.py",
    "REED_MULLER_LEVEL_D_AFFINE_OVERLAP_INDEPENDENT_REVIEW.py",
)


def source_hashes():
    return {name: hashlib.sha256((HERE / name).read_text(encoding="utf-8")
                                .encode("utf-8")).hexdigest() for name in SOURCES}


def replay(directory):
    from review_rm2_nine_scope import replay_nine_scope
    model = json.loads((directory / "model.json").read_text(encoding="utf-8"))
    candidate = json.loads((directory / "candidate.json").read_text(encoding="utf-8"))
    return replay_nine_scope(model, candidate)


def worker(stage, directory):
    if stage == "construct":
        from exact_lp_model import to_lp
        from rm2_nine_scope import build_details
        details = build_details()
        model = details.pop("model")
        write_json(directory / "model.json", model)
        write_json(directory / "model-details.json", details)
        (directory / "model.lp").write_text(to_lp(model), encoding="ascii", newline="\n")
        print(json.dumps({"variables": len(model["objective"]), "rows": len(model["rows"]),
                          "nonzeros": sum(map(len, model["rows"]))}))
        return 0
    result = replay(directory)
    write_json(directory / "replay.json", result)
    print(json.dumps(result, sort_keys=True))
    return 0 if result["valid"] else 1


def discover(executable, directory, timeout):
    from exact_lp_soplex import candidate_from_output
    executable, directory = executable.resolve(), directory.resolve()
    if directory.exists() and any(directory.iterdir()):
        raise ValueError("output directory must be new or empty")
    directory.mkdir(parents=True, exist_ok=True)
    report = {
        "schema": "rm2-nine-scope-discovery-v1", "status": "UNKNOWN",
        "model": "rm25_affine_plus_nine_scope",
        "search_inputs": "source-built LP only; no saved solution, basis, or expected optimum",
        "environment": {"python": sys.version, "platform": platform.platform(),
                        "machine": platform.machine(), "logical_cpus": os.cpu_count()},
        "source_sha256_lf": source_hashes(), "stages": [],
        "solver": {"required_version": "8.1.0"},
    }

    def finish(reason):
        report["source_after_sha256_lf"] = source_hashes()
        report["sources_unchanged"] = (
            report["source_sha256_lf"] == report["source_after_sha256_lf"])
        if not report["sources_unchanged"]:
            report["status"] = "UNKNOWN"
            reason = "source changed during this run"
        report["reason"] = reason
        for path in directory.iterdir():
            if path.is_file() and path.name != "discovery.json":
                path.write_text(path.read_text(encoding="utf-8"),
                                encoding="utf-8", newline="\n")
        report["artifact_encoding"] = "UTF-8; LF newlines before SHA256"
        report["artifact_sha256"] = {
            path.name: sha256(path) for path in sorted(directory.iterdir())
            if path.is_file() and path.name != "discovery.json"}
        write_json(directory / "discovery.json", report)
        print(json.dumps(report, indent=2, sort_keys=True))
        return 0 if report["status"] == "EXACT_OPTIMUM" else 2

    def stage(label, command, limit):
        result = run_stage(label, command, directory, limit)
        report["stages"].append(result)
        return result["returncode"] == 0 and not result["timed_out"]

    try:
        report["solver"]["executable_sha256"] = sha256(executable)
        version = subprocess.run([str(executable), "--version"], capture_output=True,
                                 text=True, timeout=30, check=True)
    except (OSError, subprocess.SubprocessError) as exc:
        return finish("solver unavailable: " + str(exc))
    (directory / "solver-version.txt").write_text(version.stdout + version.stderr,
                                                encoding="utf-8")
    if "SoPlex version 8.1.0 " not in version.stdout:
        return finish("unsupported solver version")
    report["solver"]["version"] = "8.1.0"
    command = [sys.executable, str(Path(__file__).resolve()), "--worker", "construct",
               "--output-dir", str(directory)]
    if not stage("construct", command, timeout):
        return finish("construction failed or timed out")
    command = [str(executable), "--readmode=1", "--solvemode=2", "--int:syncmode=1",
               "--real:feastol=0", "--real:opttol=0", "--int:checkmode=2",
               "-X=primal.sol", "-Y=dual.sol", "-q", "-c", f"-t{timeout}", "model.lp"]
    report["solver"]["arguments"] = command[1:]
    if not stage("search", command, timeout + 5):
        return finish("search failed or timed out")
    try:
        model = json.loads((directory / "model.json").read_text(encoding="utf-8"))
        candidate = candidate_from_output(
            model, (directory / "primal.sol").read_text(encoding="utf-8"),
            (directory / "dual.sol").read_text(encoding="utf-8"),
            (directory / "search.stdout.txt").read_text(encoding="utf-8"), 0)
    except (ValueError, OSError) as exc:
        return finish("candidate extraction failed: " + str(exc))
    write_json(directory / "candidate.json", candidate)
    command = [sys.executable, str(Path(__file__).resolve()), "--worker", "verify",
               "--output-dir", str(directory)]
    if not stage("verify", command, timeout):
        return finish("independent reconstruction/replay failed or timed out")
    checked = json.loads((directory / "replay.json").read_text(encoding="utf-8"))
    if not checked["valid"]:
        return finish("independent replay rejected the candidate")
    report["status"] = "EXACT_OPTIMUM"
    report["reduced_objective"] = checked["reduced_objective"]
    report["total_objective"] = checked["total_objective"]
    return finish("fresh discovery passed independent source reconstruction and exact primal/dual checks")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--soplex", type=Path)
    parser.add_argument("--output-dir", type=Path)
    parser.add_argument("--replay", type=Path)
    parser.add_argument("--timeout", type=int, default=600)
    parser.add_argument("--worker", choices=("construct", "verify"), help=argparse.SUPPRESS)
    args = parser.parse_args()
    if args.replay is not None:
        result = replay(args.replay.resolve())
        print(json.dumps(result, indent=2, sort_keys=True))
        return 0 if result["valid"] else 1
    if args.output_dir is None:
        parser.error("--output-dir is required")
    if args.worker:
        return worker(args.worker, args.output_dir.resolve())
    if args.soplex is None or args.timeout <= 0:
        parser.error("--soplex and a positive --timeout are required")
    return discover(args.soplex, args.output_dir, args.timeout)


if __name__ == "__main__":
    raise SystemExit(main())
