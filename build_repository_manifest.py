"""Write a SHA-256 manifest for the committed repository tree."""

from __future__ import annotations

import hashlib
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "REPOSITORY_MANIFEST.json"


def git_files() -> list[str]:
    result = subprocess.run(
        ["git", "ls-files", "-z"], cwd=ROOT, check=True, capture_output=True
    )
    return [item for item in result.stdout.decode("utf-8").split("\0") if item]


def main() -> None:
    files: dict[str, dict[str, int | str]] = {}
    for relative in git_files():
        if relative == OUT.name:
            continue
        path = ROOT / relative
        if not path.is_file():
            continue
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        files[relative] = {"bytes": path.stat().st_size, "sha256": digest}
    commit = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=ROOT, check=True, capture_output=True, text=True
    ).stdout.strip()
    payload = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "source_commit": commit,
        "file_count": len(files),
        "files": files,
    }
    OUT.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"manifested {len(files)} tracked files into {OUT.name}")


if __name__ == "__main__":
    main()
