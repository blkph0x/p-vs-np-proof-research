"""Solver-free tests of captured SoPlex text and the exact acceptance boundary.

The tiny signed-dual strings were copied from the real SoPlex 8.1.0
pnp-exact-{primal,dual}.sol control.  Derived malformed strings are synthetic.
No installed SoPlex executable is needed by this module.
"""
from copy import deepcopy
from contextlib import redirect_stdout
from fractions import Fraction
import hashlib
import io
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from exact_lp_soplex import candidate_from_output, parse_dual, parse_primal
from exact_lp_verify import verify_solution
import run_exact_lp_discovery as discovery


HERE = Path(__file__).resolve().parent
OPTIMAL = "SoPlex status       : problem is solved [optimal]\n"
CAPTURED_PRIMAL = """
Primal solution (name, value):
x000000\t1
x000001\t2
All other variables are zero. Solution has 2 nonzero entries.
"""
CAPTURED_DUAL = """
Dual solution (name, value):
r000000\t3
r000001\t-1
All other dual values are zero.

Reduced costs (name, value):
All other reduced costs are zero.
"""


def model(rows, rhs, objective, offset="0"):
    return {
        "schema": "exact-equality-lp-v1", "name": "soplex_test",
        "variable_ids": [f"x{i:06d}" for i in range(len(objective))],
        "row_ids": [f"r{i:06d}" for i in range(len(rows))],
        "rows": rows, "rhs": rhs, "objective": objective,
        "objective_offset": offset,
    }


def signed_model():
    return model([{"0": "1", "1": "1"}, {"0": "1", "1": "2"}],
                 ["3", "5"], ["2", "1"], "1")


def primal_text(entries):
    return ("Primal solution (name, value):\n"
            + "".join(f"{name}\t{value}\n" for name, value in entries)
            + f"All other variables are zero. Solution has {len(entries)} nonzero entries.\n")


def dual_text(entries, reduced=()):
    return ("Dual solution (name, value):\n"
            + "".join(f"{name}\t{value}\n" for name, value in entries)
            + "All other dual values are zero.\nReduced costs (name, value):\n"
            + "".join(f"{name}\t{value}\n" for name, value in reduced)
            + "All other reduced costs are zero.\n")


def parsed(model_value, primal=CAPTURED_PRIMAL, dual=CAPTURED_DUAL,
           stdout=OPTIMAL, returncode=0):
    return candidate_from_output(model_value, primal, dual, stdout, returncode)


def optimized_checks():
    """Use explicit exceptions/returns so this control remains meaningful under -O."""
    source = signed_model()
    if not verify_solution(source, parsed(source))["valid"]:
        return False
    for text in (CAPTURED_PRIMAL.replace("2 nonzero", "1 nonzero"),
                 CAPTURED_PRIMAL.replace("x000001\t2", "x999999\t2"),
                 CAPTURED_PRIMAL.replace("x000000\t1", "x000000\t1.0")):
        try:
            parsed(source, primal=text)
        except ValueError:
            continue
        return False
    wrong_dual = dual_text([("r000000", "-3"), ("r000001", "1")])
    if verify_solution(source, parsed(source, dual=wrong_dual))["valid"]:
        return False
    try:
        parsed(source, stdout="SoPlex status : unknown\n")
    except ValueError:
        return True
    return False


class SoPlexCandidateTests(unittest.TestCase):
    def test_captured_signed_equality_dual_and_reporting_offset(self):
        source = signed_model()
        candidate = parsed(source)
        self.assertEqual(candidate["primal"], ["1", "2"])
        self.assertEqual(candidate["dual"], ["3", "-1"])
        self.assertEqual(candidate["claimed_objective"], "4")
        checked = verify_solution(source, candidate)
        self.assertTrue(checked["valid"], checked)
        self.assertEqual(checked["total_objective"], "5")

    def test_mapping_is_by_exact_name_not_printed_order(self):
        source = signed_model()
        candidate = parsed(
            source, primal_text([("x000001", "2"), ("x000000", "1")]),
            dual_text([("r000001", "-1"), ("r000000", "3")]))
        self.assertEqual(candidate["primal"], ["1", "2"])
        self.assertEqual(candidate["dual"], ["3", "-1"])
        self.assertTrue(verify_solution(source, candidate)["valid"])
        # Swapping values while preserving names is a different mathematical claim.
        bad = parsed(source, dual=dual_text([("r000000", "-1"), ("r000001", "3")]))
        self.assertFalse(verify_solution(source, bad)["valid"])

    def test_omitted_zero_entries_and_positive_reduced_cost(self):
        source = model([{"0": "1"}, {"1": "1"}], ["1", "0"], ["1", "2"])
        candidate = parsed(source, primal_text([("x000000", "1")]),
                           dual_text([("r000000", "1")], [("x000001", "2")]))
        self.assertEqual(candidate["primal"], ["1", "0"])
        self.assertEqual(candidate["dual"], ["1", "0"])
        self.assertTrue(verify_solution(source, candidate)["valid"])
        # All-zero solutions have headers and completeness footers but no entries.
        zero = model([{"0": "1"}], ["0"], ["0"])
        self.assertTrue(verify_solution(
            zero, parsed(zero, primal_text([]), dual_text([])))["valid"])

    def test_exact_fraction_and_negative_objective(self):
        source = model([{"0": "2"}], ["1"], ["-3"], "1/7")
        candidate = parsed(source, primal_text([("x000000", "1/2")]),
                           dual_text([("r000000", "-3/2")]))
        self.assertEqual(candidate["claimed_objective"], "-3/2")
        checked = verify_solution(source, candidate)
        self.assertTrue(checked["valid"], checked)
        self.assertEqual(checked["total_objective"], "-19/14")

    def test_primal_missing_truncated_or_inconsistent_completeness(self):
        bad = [
            "", "Primal solution (name, value):",
            CAPTURED_PRIMAL.replace("All other variables are zero.", ""),
            CAPTURED_PRIMAL.replace("2 nonzero", "1 nonzero"),
            CAPTURED_PRIMAL.replace("2 nonzero", "3 nonzero"),
            CAPTURED_PRIMAL.replace("entries.", "entries"),
            CAPTURED_PRIMAL + "x000000 1\n",
            CAPTURED_PRIMAL.replace("Primal solution", "Approximate primal solution"),
        ]
        for text in bad:
            with self.subTest(text=text), self.assertRaises(ValueError):
                parse_primal(text, signed_model()["variable_ids"])

    def test_dual_and_reduced_cost_sections_must_be_complete(self):
        bad = [
            "", "Dual solution (name, value):",
            CAPTURED_DUAL.replace("All other dual values are zero.", ""),
            CAPTURED_DUAL.replace("All other dual values are zero.",
                                  "All other dual values are zero.\nAll other dual values are zero."),
            CAPTURED_DUAL.split("Reduced costs")[0],
            CAPTURED_DUAL.replace("All other reduced costs are zero.", ""),
            CAPTURED_DUAL.replace("Reduced costs (name, value):", "Reduced costs:"),
            CAPTURED_DUAL + "r000000 3\n",
        ]
        for text in bad:
            with self.subTest(text=text), self.assertRaises(ValueError):
                parse_dual(text, signed_model()["row_ids"], signed_model()["variable_ids"])

    def test_unknown_duplicate_and_cross_section_ids_rejected(self):
        for entries in (
            [("x999999", "1")], [("x0", "1")], [("r000000", "1")],
            [("x000000", "1"), ("x000000", "1")],
            [("x000000 extra", "1")],
        ):
            with self.subTest(entries=entries), self.assertRaises(ValueError):
                parse_primal(primal_text(entries), signed_model()["variable_ids"])
        for entries, reduced in (
            ([("r999999", "1")], []),
            ([("x000000", "1")], []),
            ([("r000000", "1"), ("r000000", "2")], []),
            ([], [("r000000", "1")]),
            ([], [("x000001", "1"), ("x000001", "2")]),
        ):
            with self.subTest(entries=entries, reduced=reduced), self.assertRaises(ValueError):
                parse_dual(dual_text(entries, reduced), signed_model()["row_ids"],
                           signed_model()["variable_ids"])

    def test_sparse_entries_require_canonical_nonzero_exact_rationals(self):
        for value in ("0", "-0", "0/2", "1.0", "1e0", "NaN", "inf",
                      "+1", "01", "1/1", "2/2", "1/-2", "True"):
            with self.subTest(value=value):
                with self.assertRaises(ValueError):
                    parse_primal(primal_text([("x000000", value)]), ["x000000"])
                with self.assertRaises(ValueError):
                    parse_dual(dual_text([("r000000", value)]), ["r000000"], ["x000000"])
                with self.assertRaises(ValueError):
                    parse_dual(dual_text([], [("x000000", value)]), [], ["x000000"])
        for value in (1.0, True, None, b"Primal solution", []):
            with self.subTest(value=value), self.assertRaises(ValueError):
                parse_primal(value, ["x000000"])

    def test_nonoptimal_unknown_missing_or_conflicting_status_rejected(self):
        for stdout in (
            "", "problem is solved [optimal]\n",
            "SoPlex status : unknown\n", "SoPlex status : problem is infeasible\n",
            "SoPlex status : solving aborted [time limit]\n",
            "SoPlex status : problem is solved [optimal] maybe\n",
            OPTIMAL + "SoPlex status : unknown\n",
        ):
            with self.subTest(stdout=stdout), self.assertRaises(ValueError):
                parsed(signed_model(), stdout=stdout)
        for code in (1, -1, True, False, 0.0, "0", None):
            with self.subTest(code=code), self.assertRaises(ValueError):
                parsed(signed_model(), returncode=code)

    def test_optimal_stdout_and_supplied_reduced_costs_do_not_prove_truth(self):
        # This candidate is primal feasible and has matching objective, but its
        # real first reduced cost is -1. An invented reduced-cost section cannot help.
        source = model([{"0": "1", "1": "1"}], ["1"], ["0", "1"])
        candidate = parsed(source, primal_text([("x000001", "1")]),
                           dual_text([("r000000", "1")], [("x000000", "999")]))
        self.assertFalse(verify_solution(source, candidate)["valid"])
        # The parser deliberately does not authenticate reduced-cost claims:
        # a valid primal/dual pair is checked from A,b,c even with that field wrong.
        source = model([{"0": "1"}], ["1"], ["1", "2"])
        candidate = parsed(source, primal_text([("x000000", "1")]),
                           dual_text([("r000000", "1")], [("x000001", "999")]))
        self.assertTrue(verify_solution(source, candidate)["valid"])

    def test_missing_nonzero_entry_and_wrong_signed_dual_fail_exact_replay(self):
        source = signed_model()
        for primal, dual in (
            (primal_text([("x000000", "1")]), CAPTURED_DUAL),
            (CAPTURED_PRIMAL, dual_text([("r000000", "3")])),
            (CAPTURED_PRIMAL, dual_text([("r000000", "-3"), ("r000001", "1")])),
        ):
            self.assertFalse(verify_solution(source, parsed(source, primal, dual))["valid"])

    def test_model_types_and_digest_bind_the_candidate(self):
        source = signed_model()
        for mutation in (
            lambda m: m["rows"][0].update({"0": 1.0}),
            lambda m: m["objective"].__setitem__(0, True),
            lambda m: m["row_ids"].reverse(),
            lambda m: m["variable_ids"].reverse(),
        ):
            bad = deepcopy(source)
            mutation(bad)
            with self.assertRaises(ValueError):
                parsed(bad)
        candidate = parsed(source)
        source["objective_offset"] = "2"
        self.assertFalse(verify_solution(source, candidate)["valid"])

    def test_captured_default_tolerance_candidate_is_rejected(self):
        # This real run reported optimal rational output, but did not use zero
        # tolerances. Do not turn a solver status or decimal-sized residual into truth.
        directory = HERE / "EXACT_LP_TOLERANCE_CONTROL"
        source = json.loads((directory / "model.json").read_text(encoding="utf-8"))
        candidate = parsed(
            source, (directory / "primal.sol").read_text(encoding="utf-8"),
            (directory / "dual.sol").read_text(encoding="utf-8"),
            (directory / "search.stdout.txt").read_text(encoding="utf-8"))
        saved = json.loads((directory / "candidate.json").read_text(encoding="utf-8"))
        self.assertEqual(candidate, saved)
        row_value = sum((Fraction(coefficient) * Fraction(candidate["primal"][int(column)])
                         for column, coefficient in source["rows"][0].items()), Fraction())
        self.assertEqual(row_value - Fraction(source["rhs"][0]),
                         Fraction(23, 288230376151711744))
        self.assertEqual(candidate["claimed_objective"],
                         "55844635379394169/9007199254740992")
        checked = verify_solution(source, candidate)
        self.assertFalse(checked["valid"])
        self.assertEqual(checked["status"], "INVALID")
        self.assertEqual(checked["errors"], ["primal equality failure at row 0"])

    def test_optimized_mode_has_the_same_acceptance_boundary(self):
        run = subprocess.run(
            [sys.executable, "-B", "-O", "-c",
             "from test_exact_lp_soplex import optimized_checks; "
             "raise SystemExit(0 if optimized_checks() else 1)"],
            cwd=HERE, capture_output=True, text=True, timeout=30)
        self.assertEqual(run.returncode, 0, run.stdout + run.stderr)


class DiscoveryProcessTests(unittest.TestCase):
    def test_success_and_nonzero_exit_preserve_separate_outputs(self):
        with tempfile.TemporaryDirectory(prefix="pnp-soplex-stage-") as temporary:
            directory = Path(temporary)
            for code in (0, 3):
                label = "stage" + str(code)
                result = discovery.run_stage(
                    label, [sys.executable, "-B", "-c",
                            f"import sys; print('stdout control'); "
                            f"print('stderr control',file=sys.stderr); raise SystemExit({code})"],
                    directory, 10)
                self.assertEqual(result["returncode"], code)
                self.assertFalse(result["timed_out"])
                self.assertIn("stdout control", (directory / (label + ".stdout.txt")).read_text())
                self.assertIn("stderr control", (directory / (label + ".stderr.txt")).read_text())
                self.assertGreaterEqual(result["wall_seconds"], 0)
                self.assertIn("lower bound", result["memory_method"])

    def test_wall_timeout_preserves_partial_output_and_reaps_child(self):
        with tempfile.TemporaryDirectory(prefix="pnp-soplex-timeout-") as temporary:
            directory = Path(temporary)
            # Record the actual child object, so this tests termination rather
            # than inferring it only from a producer-supplied flag.
            children = []
            real_popen = subprocess.Popen

            def record_child(*args, **kwargs):
                child = real_popen(*args, **kwargs)
                children.append(child)
                return child

            with patch.object(discovery.subprocess, "Popen", side_effect=record_child):
                result = discovery.run_stage(
                    "timeout", [sys.executable, "-B", "-c",
                                "import time; print('before sleep',flush=True); time.sleep(30)"],
                    directory, 0.5)
            self.assertTrue(result["timed_out"], result)
            self.assertNotEqual(result["returncode"], 0)
            self.assertEqual(len(children), 1)
            self.assertIsNotNone(children[0].poll())
            self.assertIn("before sleep", (directory / "timeout.stdout.txt").read_text())

    def test_existing_artifacts_are_rejected_before_any_solver_call(self):
        with tempfile.TemporaryDirectory(prefix="pnp-soplex-stale-") as temporary:
            directory = Path(temporary)
            marker = directory / "primal.sol"
            marker.write_text("untrusted stale solution", encoding="utf-8")
            with patch.object(discovery.subprocess, "run") as run:
                with self.assertRaisesRegex(ValueError, "stale solver files"):
                    discovery.discover(Path(sys.executable), directory, 1)
                run.assert_not_called()
            self.assertEqual(marker.read_text(), "untrusted stale solution")

    def test_launch_failure_has_structured_non_success_result(self):
        with tempfile.TemporaryDirectory(prefix="pnp-soplex-launch-") as temporary:
            directory = Path(temporary)
            with patch.object(discovery.subprocess, "Popen",
                              side_effect=OSError("controlled launch failure")):
                result = discovery.run_stage("launch", ["unused"], directory, 1)
            self.assertIsNone(result["returncode"])
            self.assertFalse(result["timed_out"])
            self.assertEqual(result["launch_error"], "controlled launch failure")
            self.assertIsNone(result["max_sampled_rss_bytes"])
            self.assertEqual(result["rss_samples"], 0)
            self.assertTrue((directory / "launch.stdout.txt").is_file())
            self.assertTrue((directory / "launch.stderr.txt").is_file())

    def test_version_error_timeout_and_unsupported_version_are_unknown(self):
        failures = [
            OSError("controlled version launch failure"),
            subprocess.CalledProcessError(3, ["solver", "--version"]),
            subprocess.TimeoutExpired(["solver", "--version"], 30),
            subprocess.CompletedProcess([], 0, "SoPlex version 99.0.0 control\n", ""),
        ]
        for failure in failures:
            with self.subTest(failure=str(failure)):
                with tempfile.TemporaryDirectory(prefix="pnp-soplex-version-") as temporary:
                    directory = Path(temporary)
                    kwargs = ({"side_effect": failure} if isinstance(failure, Exception)
                              else {"return_value": failure})
                    with patch.object(discovery.subprocess, "run", **kwargs), \
                            patch.object(discovery.platform, "platform", return_value="test-platform"), \
                            patch.object(discovery.platform, "machine", return_value="test-machine"), \
                            patch.object(discovery, "run_stage") as stages, \
                            redirect_stdout(io.StringIO()):
                        code = discovery.discover(Path(sys.executable), directory, 1)
                    self.assertEqual(code, 2)
                    stages.assert_not_called()
                    report = json.loads((directory / "discovery.json").read_text())
                    self.assertEqual(report["status"], "UNKNOWN")
                    self.assertTrue(report["sources_unchanged"])
                    self.assertEqual(report["stages"], [])
                    self.assertNotIn("reduced_objective", report)

    def test_missing_solver_is_unknown_without_launch(self):
        with tempfile.TemporaryDirectory(prefix="pnp-soplex-missing-") as temporary:
            directory = Path(temporary) / "output"
            with patch.object(discovery.subprocess, "run") as launch, \
                    patch.object(discovery.platform, "platform", return_value="test-platform"), \
                    patch.object(discovery.platform, "machine", return_value="test-machine"), \
                    redirect_stdout(io.StringIO()):
                code = discovery.discover(Path(temporary) / "missing.exe", directory, 1)
            launch.assert_not_called()
            self.assertEqual(code, 2)
            report = json.loads((directory / "discovery.json").read_text())
            self.assertEqual(report["status"], "UNKNOWN")
            self.assertIn("version/launch unavailable", report["reason"])

    def test_source_drift_prevents_exact_run_and_stable_run_binds_lf_artifacts(self):
        # Stage execution is replaced only in this orchestration test. It uses a
        # tiny exact LP, not the expensive source-bound affine-overlap worker.
        # Mathematical/source reconstruction has its own separate checker tests.
        for changed in (False, True):
            with self.subTest(changed=changed):
                with tempfile.TemporaryDirectory(prefix="pnp-soplex-provenance-") as temporary:
                    directory = Path(temporary)
                    seen_commands = {}
                    source = signed_model()

                    def stage(label, command, path, timeout):
                        seen_commands[label] = command
                        if label == "construct":
                            discovery.write_json(path / "model.json", source)
                        elif label == "search":
                            (path / "primal.sol").write_bytes(
                                CAPTURED_PRIMAL.replace("\n", "\r\n").encode())
                            (path / "dual.sol").write_bytes(
                                CAPTURED_DUAL.replace("\n", "\r\n").encode())
                            (path / "search.stdout.txt").write_bytes(OPTIMAL.encode())
                        elif label == "verify":
                            candidate = json.loads((path / "candidate.json").read_text())
                            discovery.write_json(path / "replay.json",
                                                 verify_solution(source, candidate))
                        else:
                            raise RuntimeError("unexpected stage")
                        return {"label": label, "returncode": 0, "timed_out": False}

                    before = {"test_source.py": "0" * 64}
                    after = {"test_source.py": ("1" if changed else "0") * 64}
                    version = subprocess.CompletedProcess(
                        [], 0, "SoPlex version 8.1.0 captured-format control\n", "")
                    with patch.object(discovery.subprocess, "run", return_value=version), \
                            patch.object(discovery.platform, "platform", return_value="test-platform"), \
                            patch.object(discovery.platform, "machine", return_value="test-machine"), \
                            patch.object(discovery, "run_stage", side_effect=stage), \
                            patch.object(discovery, "source_hashes", side_effect=[before, after]), \
                            redirect_stdout(io.StringIO()):
                        code = discovery.discover(Path(sys.executable), directory, 10)
                    report = json.loads((directory / "discovery.json").read_text())
                    self.assertEqual(code, 2 if changed else 0)
                    self.assertEqual(report["status"], "UNKNOWN" if changed else "EXACT_OPTIMUM")
                    self.assertEqual(report["sources_unchanged"], not changed)
                    self.assertEqual(report["source_sha256_lf"], before)
                    self.assertEqual(report["source_after_sha256_lf"], after)
                    if changed:
                        self.assertIn("source changed", report["reason"])
                    else:
                        self.assertEqual(report["reduced_objective"], "4")
                        self.assertEqual(report["total_objective"], "5")
                    for flag in ("--readmode=1", "--solvemode=2", "--int:syncmode=1",
                                 "--real:feastol=0", "--real:opttol=0", "--int:checkmode=2"):
                        self.assertIn(flag, seen_commands["search"])
                    self.assertEqual(set(report["artifact_sha256"]),
                                     {p.name for p in directory.iterdir()
                                      if p.name != "discovery.json"})
                    for name, digest in report["artifact_sha256"].items():
                        artifact = (directory / name).read_bytes()
                        self.assertNotIn(b"\r", artifact)
                        self.assertEqual(hashlib.sha256(artifact).hexdigest(), digest)


if __name__ == "__main__":
    unittest.main()
