"""Measure finite RM(2,5) construction and replay costs.

The measurement runs in a temporary copy so generated review artifacts cannot
silently change the checked-in certificate. RSS is sampled from the child
process (Windows working-set API or /proc on Linux). Certificate discovery is
reported as UNRECORDED because the historical search process is not part of
the repository; regenerating a saved witness is measured separately.
"""
from __future__ import annotations

import ctypes
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import time


HERE = Path(__file__).resolve().parent
OUT = HERE / "REED_MULLER_COST_MEASUREMENTS.json"


def _rss_bytes(pid: int) -> int:
    if os.name == "nt":
        class Counters(ctypes.Structure):
            _fields_ = [
                ("cb", ctypes.c_ulong),
                ("PageFaultCount", ctypes.c_ulong),
                ("PeakWorkingSetSize", ctypes.c_size_t),
                ("WorkingSetSize", ctypes.c_size_t),
                ("QuotaPeakPagedPoolUsage", ctypes.c_size_t),
                ("QuotaPagedPoolUsage", ctypes.c_size_t),
                ("QuotaPeakNonPagedPoolUsage", ctypes.c_size_t),
                ("QuotaNonPagedPoolUsage", ctypes.c_size_t),
                ("PagefileUsage", ctypes.c_size_t),
                ("PeakPagefileUsage", ctypes.c_size_t),
            ]

        process = ctypes.windll.kernel32.OpenProcess(0x0410, False, pid)
        if not process:
            return 0
        try:
            counters = Counters()
            counters.cb = ctypes.sizeof(counters)
            ok = ctypes.windll.psapi.GetProcessMemoryInfo(
                process, ctypes.byref(counters), counters.cb
            )
            return int(counters.WorkingSetSize) if ok else 0
        finally:
            ctypes.windll.kernel32.CloseHandle(process)
    status = Path(f"/proc/{pid}/status")
    try:
        for line in status.read_text(encoding="utf-8").splitlines():
            if line.startswith("VmRSS:"):
                return int(line.split()[1]) * 1024
    except (FileNotFoundError, OSError, ValueError):
        pass
    return 0


def _run(label: str, command: list[str], cwd: Path) -> dict[str, object]:
    started = time.perf_counter()
    child = subprocess.Popen(
        command,
        cwd=cwd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )
    peak = 0
    while child.poll() is None:
        peak = max(peak, _rss_bytes(child.pid))
        time.sleep(0.1)
    output = child.stdout.read() if child.stdout is not None else ""
    elapsed = time.perf_counter() - started
    peak = max(peak, _rss_bytes(child.pid))
    if child.returncode:
        raise RuntimeError(f"{label} failed with {child.returncode}:\n{output[-4000:]}")
    return {
        "label": label,
        "seconds": round(elapsed, 3),
        "peak_rss_bytes": peak,
        "peak_rss_mib": round(peak / (1024 * 1024), 3),
        "returncode": child.returncode,
        "stdout_tail": output[-1000:],
    }


def main() -> None:
    with tempfile.TemporaryDirectory(prefix="rm25-cost-") as raw:
        temp_root = Path(raw) / "local_marginal_code_lab"
        shutil.copytree(
            HERE,
            temp_root,
            ignore=shutil.ignore_patterns("__pycache__", "*.pyc"),
        )
        commands = [
            (
                "construct_full_level8_model",
                [
                    sys.executable,
                    "-c",
                    "from reed_muller_full_level8 import build_model; "
                    "m=build_model(); print(m['variable_orbit_count'], m['row_orbit_count'])",
                ],
            ),
            (
                "regenerate_saved_primal",
                [sys.executable, "run_reed_muller_level_d_full.py"],
            ),
            (
                "independent_full_level8_replay",
                [sys.executable, "REED_MULLER_LEVEL_D_FULL_INDEPENDENT_REVIEW.py"],
            ),
        ]
        measurements = [_run(label, command, temp_root) for label, command in commands]
    result = {
        "schema": "rm25_cost_measurements_v1",
        "family": "RM(2,5)",
        "python": sys.version,
        "platform": sys.platform,
        "measurements": measurements,
        "discovery": {
            "status": "UNRECORDED",
            "reason": "The historical certificate-search process is not retained in this repository.",
        },
    }
    OUT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
