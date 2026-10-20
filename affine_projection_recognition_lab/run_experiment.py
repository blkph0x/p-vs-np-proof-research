"""Generate exact evidence for the affine-projection recognition reduction."""

from __future__ import annotations

import json
from pathlib import Path

from engine import build_artifact

HERE = Path(__file__).resolve().parent


def main():
    artifact = build_artifact()
    (HERE / "RESULTS.json").write_text(json.dumps(artifact, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": artifact["status"], "records": len(artifact["records"])}, sort_keys=True))


if __name__ == "__main__":
    main()

