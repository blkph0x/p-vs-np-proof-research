"""Adversarial proof validation, including an optimized Python subprocess."""
from copy import deepcopy
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from cdcl import CDCL
import review


HERE = Path(__file__).resolve().parent


def bad_certificates():
    sat = CDCL(1, [[1]]).solve()
    unsat = CDCL(1, [[1], [-1]]).solve()
    cases = []
    forged = deepcopy(sat)
    forged.update(status="UNSAT", model=None, proof=[])
    cases.append((1, [[1]], forged))
    for mutate in (
        lambda r: r["model"].update({0: False}),
        lambda r: r["model"].clear(),
        lambda r: r["model"].update({0: 1}),
        lambda r: r["model"].update({"0": True}),
        lambda r: r.update(status="UNRECOGNIZED"),
    ):
        result = deepcopy(sat)
        mutate(result)
        cases.append((1, [[1]], result))
    for mutate in (
        lambda r: r["proof"][0].update(from_conflict=[]),
        lambda r: r["proof"][0]["derivation"][0].update(right=[]),
        lambda r: r["proof"][0]["derivation"][0].update(left=[1]),
        lambda r: r["proof"][0]["derivation"][0].update(pivot=True),
        lambda r: r["proof"][0]["derivation"][0].update(result=[1]),
        lambda r: r["proof"][0].update(derivation=[]),
        lambda r: r["proof"].append(deepcopy(r["proof"][0])),
        lambda r: r.update(clauses=[]),
        lambda r: r.update(status="UNKNOWN", reason="DECISION_CAP"),
    ):
        result = deepcopy(unsat)
        mutate(result)
        cases.append((1, [[1], [-1]], result))
    return cases


def check_rejections():
    for nvars, clauses, result in bad_certificates():
        try:
            review.replay(nvars, clauses, result)
        except review.VerificationError:
            continue
        raise RuntimeError("forged certificate was accepted")
    return len(bad_certificates())


def check_main_rejection():
    # Main must invoke replay even when Python eliminates assert statements.
    with tempfile.TemporaryDirectory() as folder:
        root = Path(folder)
        (root / "RESULTS.json").write_text(json.dumps({
            "all_cases_match_direct": True, "source_sha256": {}}), encoding="utf-8")
        nvars, clauses, result = bad_certificates()[0]
        (root / "CERTIFICATES.json").write_text(json.dumps([{
            "nvars": nvars, "clauses": clauses, "result": result}]), encoding="utf-8")
        with patch.object(review, "HERE", root):
            try:
                review.main()
            except review.VerificationError:
                return
        raise RuntimeError("main accepted the forged UNSAT certificate")


class ReviewValidationTests(unittest.TestCase):
    def test_adversarial_certificates(self):
        self.assertEqual(check_rejections(), 15)

    def test_main_invokes_replay(self):
        check_main_rejection()

    def test_optimized_mode_adversaries_and_main(self):
        code = (
            "from test_review_validation import check_rejections, check_main_rejection; "
            "print(check_rejections()); check_main_rejection()"
        )
        result = subprocess.run([sys.executable, "-B", "-O", "-c", code],
                                cwd=HERE, capture_output=True, text=True, timeout=30)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(result.stdout.strip(), "15")

    def test_existing_saved_certificates(self):
        for saved in json.loads((HERE / "CERTIFICATES.json").read_text(encoding="utf-8")):
            self.assertTrue(review.replay(saved["nvars"], saved["clauses"], saved["result"]))

    def test_no_exhaustive_oracle_is_needed(self):
        with patch.object(review, "direct", side_effect=RuntimeError("enumeration forbidden")):
            self.assertTrue(review.replay(1, [[1]], CDCL(1, [[1]]).solve()))
            clauses = [[1], [-1]]
            self.assertTrue(review.replay(1, clauses, CDCL(1, clauses).solve()))

    def test_strict_original_and_model_types(self):
        for nvars, clauses in ((True, [[1]]), (1, [[True]]),
                               (1, [[0]]), (1, [[2]]), (1, [["1"]])):
            with self.assertRaises(review.VerificationError):
                review.replay(nvars, clauses, CDCL(1, [[1]]).solve())

    def test_empty_formula_and_empty_clause(self):
        for nvars, clauses in ((0, []), (0, [[]]), (2, [[1, -1]])):
            result = CDCL(nvars, clauses).solve()
            self.assertTrue(review.replay(nvars, clauses, result))
            self.assertTrue(review.replay(nvars, clauses, json.loads(json.dumps(result))))


if __name__ == "__main__":
    unittest.main()
