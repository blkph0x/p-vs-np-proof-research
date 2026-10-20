"""Normalize copied text artifacts and preserve both original and LF hashes."""
from pathlib import Path
import hashlib
import json

HERE = Path(__file__).resolve().parent


def main():
    report_path = HERE / "exact_run/RESULTS.json"
    report = json.loads(report_path.read_text())
    for label, entry in report["results"].items():
        if "original_artifact_sha256_before_lf_normalization" in entry:
            raise ValueError("evidence packaging already performed")
        old = dict(entry["artifact_sha256"])
        for name, expected in old.items():
            path = HERE / "exact_run" / label / name
            raw = path.read_bytes()
            if hashlib.sha256(raw).hexdigest() != expected:
                raise ValueError("search artifact changed before packaging: " + str(path))
            raw.decode("utf-8")
            path.write_bytes(raw.replace(b"\r\n", b"\n"))
        entry["original_artifact_sha256_before_lf_normalization"] = old
        entry["artifact_sha256"] = {
            name: hashlib.sha256((HERE / "exact_run" / label / name).read_bytes()).hexdigest()
            for name in old
        }
    report["artifact_encoding"] = (
        "UTF-8 text with CRLF normalized to LF after discovery; original byte hashes "
        "retained separately; no numeric token or model/certificate content changed."
    )
    report_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n",
                           encoding="utf-8", newline="\n")
    print("Packaged", sum(len(entry["artifact_sha256"]) for entry in report["results"].values()),
          "text artifacts; original hashes preserved.")


if __name__ == "__main__":
    main()
