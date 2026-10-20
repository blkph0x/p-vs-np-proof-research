"""Replay committed evidence without importing a public solver."""
from collections import Counter
import hashlib
from pathlib import Path
import unittest

import run_public_sat as runner
from sat_backend_certificate import proof_digest, verify_candidate


HERE = Path(__file__).resolve().parent
PILOT = HERE / "PUBLIC_SAT_PILOT_REJECTED"


class PublicSatEvidenceTests(unittest.TestCase):
    def test_complete_paired_campaign(self):
        checked = runner.replay(HERE / "PUBLIC_SAT_BASELINE")
        self.assertEqual(checked["status"], "PASS")
        self.assertEqual(checked["runs"], 114)
        self.assertEqual(checked["statuses"], {
            "VERIFIED_SAT": 54, "VERIFIED_UNSAT": 60})

    def test_rejected_pilot_is_retained_as_failed_evidence(self):
        manifest = runner.read_json(PILOT / "benchmark.json")
        self.assertEqual(manifest["status"], "FAILED")
        counts = dict(Counter(row["status"] for row in manifest["runs"]))
        self.assertEqual(counts, manifest["status_counts"])
        self.assertEqual(counts, {
            "VERIFIED_SAT": 39, "VERIFIED_UNSAT": 57,
            "UNKNOWN_PROCESS": 15, "INVALID": 3})
        self.assertEqual(runner.read_json(PILOT / "replay.json")["status"], "NOT_ACCEPTED")
        # This directory is an explicit excerpt, not the complete first run.
        # Bind every retained original run artifact to that run's full manifest.
        retained = 0
        for name, digest in manifest["artifact_sha256"].items():
            path = PILOT / name
            if path.is_file():
                self.assertEqual(runner.sha256(path), digest, name)
                retained += 1
        self.assertGreater(retained, 30)
        for name, digest in manifest["source_sha256_lf"].items():
            snapshot = PILOT / "sources" / (name + ".txt")
            text = snapshot.read_text(encoding="utf-8")
            self.assertEqual(hashlib.sha256(text.encode()).hexdigest(), digest, name)

    def test_failed_raw_trace_and_checked_separate_proposal(self):
        case = PILOT / "php_6_5_shuffled"
        out = case / "repeat_0/glucose3"
        original = runner.read_json(case / "request.json")
        candidate = runner.read_json(out / "candidate.json")
        raw = (out / "proof.drup").read_bytes()
        failed = verify_candidate(original, candidate, raw, **runner.RUP_LIMITS)
        self.assertEqual(failed["status"], "INVALID")
        self.assertIn("line 262", failed["errors"][0])
        _, proposed, metadata = runner.propose_rup(
            (out / "raw-proof.drup").read_text(encoding="utf-8").splitlines())
        self.assertGreater(metadata["removed_deletion_lines"], 0)
        candidate["proof_sha256"] = proof_digest(proposed)
        checked = verify_candidate(original, candidate, proposed, **runner.RUP_LIMITS)
        self.assertEqual(checked["status"], "VERIFIED_UNSAT")
        self.assertEqual(checked["stats"]["additions"], 147)

    def test_nonzero_children_are_not_promoted_from_partial_output(self):
        manifest = runner.read_json(PILOT / "benchmark.json")
        failures = [row for row in manifest["runs"]
                    if row["status"] == "UNKNOWN_PROCESS"]
        self.assertEqual(len(failures), 15)
        for row in failures:
            self.assertEqual(row["backend"], "glucose3")
            self.assertEqual(row["process"]["returncode"], 0xC0000409)
            self.assertFalse(row["process"]["timed_out"])
            self.assertNotIn("verification", row)


if __name__ == "__main__":
    unittest.main()
