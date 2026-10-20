"""Fresh affine-overlap LP search with an optional SoPlex executable.

Default CI needs no external solver: --replay DIRECTORY reconstructs the
mathematical source independently before checking the stored candidate.
"""
from __future__ import annotations

import argparse
import ctypes
from ctypes import wintypes
import hashlib
import json
import os
from pathlib import Path
import platform
import subprocess
import sys
import time

HERE = Path(__file__).resolve().parent


def source_hashes():
    return {
        name: hashlib.sha256((HERE / name).read_text(encoding="utf-8").encode()).hexdigest()
        for name in ("exact_lp_model.py", "exact_lp_soplex.py", "exact_lp_verify.py",
                     "run_exact_lp_discovery.py", "reed_muller_affine_overlap.py",
                     "REED_MULLER_LEVEL_D_AFFINE_OVERLAP_INDEPENDENT_REVIEW.py")
    }


def write_json(path, value):
    Path(path).write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def rss_bytes(pid):
    """Sample current resident memory, not a guaranteed process peak."""
    if os.name == "nt":
        class Counters(ctypes.Structure):
            _fields_ = [
                ("cb", wintypes.DWORD), ("PageFaultCount", wintypes.DWORD),
                ("PeakWorkingSetSize", ctypes.c_size_t), ("WorkingSetSize", ctypes.c_size_t),
                ("QuotaPeakPagedPoolUsage", ctypes.c_size_t), ("QuotaPagedPoolUsage", ctypes.c_size_t),
                ("QuotaPeakNonPagedPoolUsage", ctypes.c_size_t), ("QuotaNonPagedPoolUsage", ctypes.c_size_t),
                ("PagefileUsage", ctypes.c_size_t), ("PeakPagefileUsage", ctypes.c_size_t),
            ]
        kernel = ctypes.WinDLL("kernel32", use_last_error=True)
        psapi = ctypes.WinDLL("psapi", use_last_error=True)
        kernel.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
        kernel.OpenProcess.restype = wintypes.HANDLE
        kernel.CloseHandle.argtypes = [wintypes.HANDLE]
        psapi.GetProcessMemoryInfo.argtypes = [wintypes.HANDLE, ctypes.POINTER(Counters), wintypes.DWORD]
        handle = kernel.OpenProcess(0x0410, False, pid)
        if not handle:
            return None
        try:
            counts = Counters()
            counts.cb = ctypes.sizeof(counts)
            if psapi.GetProcessMemoryInfo(handle, ctypes.byref(counts), counts.cb):
                return int(counts.WorkingSetSize)
            return None
        finally:
            kernel.CloseHandle(handle)
    try:
        for line in Path(f"/proc/{pid}/status").read_text().splitlines():
            if line.startswith("VmRSS:"):
                return int(line.split()[1]) * 1024
    except (OSError, ValueError):
        pass
    return None


def run_stage(label, command, directory, timeout):
    """No shell, no PIPE deadlock; preserve complete output even on timeout."""
    started = time.perf_counter()
    sampled_max = None
    samples = 0
    timed_out = False
    with (directory / (label + ".stdout.txt")).open("w", encoding="utf-8") as stdout:
        with (directory / (label + ".stderr.txt")).open("w", encoding="utf-8") as stderr:
            try:
                child = subprocess.Popen(command, cwd=directory, stdout=stdout, stderr=stderr)
            except OSError as exc:
                return {
                    "label": label, "wall_seconds": round(time.perf_counter() - started, 6),
                    "returncode": None, "timed_out": False, "launch_error": str(exc),
                    "max_sampled_rss_bytes": None, "rss_samples": 0,
                }
            try:
                while child.poll() is None:
                    rss = rss_bytes(child.pid)
                    if rss is not None:
                        sampled_max = max(sampled_max or 0, rss)
                        samples += 1
                    if time.perf_counter() - started > timeout:
                        timed_out = True
                        child.kill()
                        break
                    time.sleep(0.02)
                child.wait()
            finally:
                if child.poll() is None:
                    child.kill()
                    child.wait()
    return {
        "label": label, "wall_seconds": round(time.perf_counter() - started, 6),
        "returncode": child.returncode, "timed_out": timed_out,
        "max_sampled_rss_bytes": sampled_max, "rss_samples": samples,
        "memory_method": "20ms current-RSS samples; lower bound on true process peak; excludes parent",
    }


def worker(stage, directory):
    if stage == "construct":
        from exact_lp_model import build_affine_overlap_model, to_lp
        model = build_affine_overlap_model()
        write_json(directory / "model.json", model)
        (directory / "model.lp").write_text(to_lp(model), encoding="ascii")
        print(json.dumps({"variables": len(model["objective"]), "rows": len(model["rows"])}))
        return 0
    from exact_lp_verify import replay_affine_overlap
    model = json.loads((directory / "model.json").read_text(encoding="utf-8"))
    candidate = json.loads((directory / "candidate.json").read_text(encoding="utf-8"))
    result = replay_affine_overlap(model, candidate)
    write_json(directory / "replay.json", result)
    print(json.dumps(result, sort_keys=True))
    return 0 if result["valid"] else 1


def replay(directory):
    """Read committed evidence without overwriting its historical measurements."""
    from exact_lp_verify import replay_affine_overlap
    model = json.loads((directory / "model.json").read_text(encoding="utf-8"))
    candidate = json.loads((directory / "candidate.json").read_text(encoding="utf-8"))
    result = replay_affine_overlap(model, candidate)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["valid"] else 1


def discover(executable, directory, timeout):
    from exact_lp_soplex import candidate_from_output
    executable = executable.resolve()
    directory = directory.resolve()
    if directory.exists() and any(directory.iterdir()):
        raise ValueError("output directory must be new or empty; stale solver files are forbidden")
    directory.mkdir(parents=True, exist_ok=True)
    stages = []
    report = {
        "schema": "exact-lp-discovery-run-v1", "status": "UNKNOWN",
        "model": "rm25_affine_overlap", "historical_discovery": "UNRECORDED",
        "search_inputs": "source-rebuilt model only; no saved primal, dual, basis, or expected optimum",
        "solver": {"required_version": "8.1.0"},
        "environment": {"python": sys.version, "platform": platform.platform(),
                        "machine": platform.machine(), "logical_cpus": os.cpu_count()},
        "stages": stages,
        "source_sha256_lf": source_hashes(),
    }
    def finish(reason):
        report["source_after_sha256_lf"] = source_hashes()
        report["sources_unchanged"] = report["source_sha256_lf"] == report["source_after_sha256_lf"]
        if not report["sources_unchanged"]:
            report["status"] = "UNKNOWN"
            reason = "source changed during this run; rerun from an unchanged checkout"
        report["reason"] = reason
        # Preserve portable text evidence: normalize only newline encoding,
        # including native solver files, before hashing checked-in artifacts.
        for path in directory.iterdir():
            if path.is_file() and path.name != "discovery.json":
                path.write_text(path.read_text(encoding="utf-8"), encoding="utf-8", newline="\n")
        report["artifact_encoding"] = "UTF-8 text; newlines normalized to LF before SHA256"
        report["artifact_sha256"] = {p.name: sha256(p) for p in sorted(directory.iterdir())
                                    if p.is_file() and p.name != "discovery.json"}
        write_json(directory / "discovery.json", report)
        print(json.dumps({"status": report["status"], "reason": reason, "stages": stages}, indent=2))
        return 0 if report["status"] == "EXACT_OPTIMUM" else 2

    try:
        report["solver"]["executable_sha256"] = sha256(executable)
        version = subprocess.run([str(executable), "--version"], capture_output=True,
                                 text=True, timeout=30, check=True)
    except (OSError, subprocess.SubprocessError) as exc:
        return finish("solver version/launch unavailable: " + str(exc))
    (directory / "solver-version.txt").write_text(version.stdout + version.stderr, encoding="utf-8")
    if "SoPlex version 8.1.0 " not in version.stdout:
        return finish("unsupported solver version; this adapter requires SoPlex 8.1.0")
    report["solver"]["version"] = "8.1.0"
    command = [sys.executable, str(Path(__file__).resolve()), "--worker", "construct",
               "--output-dir", str(directory)]
    stages.append(run_stage("construct", command, directory, timeout))
    if stages[-1]["returncode"] != 0 or stages[-1]["timed_out"]:
        return finish("construction failed or exceeded the wall-clock limit")
    command = [str(executable), "--readmode=1", "--solvemode=2", "--int:syncmode=1",
               "--real:feastol=0", "--real:opttol=0", "--int:checkmode=2",
               "-X=primal.sol", "-Y=dual.sol", "-q", "-c", f"-t{timeout}", "model.lp"]
    report["solver"]["arguments"] = command[1:]
    stages.append(run_stage("search", command, directory, timeout + 5))
    if stages[-1]["returncode"] != 0 or stages[-1]["timed_out"]:
        return finish("search failed or exceeded the wall-clock limit")
    try:
        model = json.loads((directory / "model.json").read_text(encoding="utf-8"))
        candidate = candidate_from_output(
            model, (directory / "primal.sol").read_text(encoding="utf-8"),
            (directory / "dual.sol").read_text(encoding="utf-8"),
            (directory / "search.stdout.txt").read_text(encoding="utf-8"),
            stages[-1]["returncode"])
    except (ValueError, OSError) as exc:
        return finish("no usable exact candidate: " + str(exc))
    write_json(directory / "candidate.json", candidate)
    command = [sys.executable, str(Path(__file__).resolve()), "--worker", "verify",
               "--output-dir", str(directory)]
    stages.append(run_stage("verify", command, directory, timeout))
    if stages[-1]["returncode"] != 0 or stages[-1]["timed_out"]:
        return finish("independent source-bound verification failed or timed out")
    checked = json.loads((directory / "replay.json").read_text(encoding="utf-8"))
    if not checked["valid"]:
        return finish("independent source-bound verification rejected the candidate")
    report["status"] = "EXACT_OPTIMUM"
    report["reduced_objective"] = checked["reduced_objective"]
    report["total_objective"] = checked["total_objective"]
    return finish("fresh candidate passed independent model reconstruction and exact primal/dual checking")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--soplex", type=Path)
    parser.add_argument("--output-dir", type=Path)
    parser.add_argument("--replay", type=Path)
    parser.add_argument("--timeout", type=int, default=600)
    parser.add_argument("--worker", choices=("construct", "verify"), help=argparse.SUPPRESS)
    args = parser.parse_args()
    if args.replay is not None:
        return replay(args.replay.resolve())
    if args.output_dir is None:
        parser.error("--output-dir is required for discovery")
    if args.worker:
        return worker(args.worker, args.output_dir.resolve())
    if args.soplex is None or args.timeout <= 0:
        parser.error("--soplex and a positive --timeout are required")
    return discover(args.soplex, args.output_dir, args.timeout)


if __name__ == "__main__":
    raise SystemExit(main())
