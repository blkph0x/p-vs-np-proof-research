"""Exact equality-LP tests; no solver or exporter is imported."""
from copy import deepcopy
from fractions import Fraction
import json
from pathlib import Path
import subprocess
import sys
import unittest

from exact_lp_verify import model_digest, replay_affine_overlap, verify_solution


HERE = Path(__file__).resolve().parent


def model(rows, rhs, objective, offset="0", name="test_lp"):
    return {
        "schema": "exact-equality-lp-v1", "name": name,
        "variable_ids": [f"x{i:06d}" for i in range(len(objective))],
        "row_ids": [f"r{i:06d}" for i in range(len(rows))],
        "rows": rows, "rhs": rhs, "objective": objective, "objective_offset": offset,
    }


def certificate(source, primal, dual, objective):
    return {"schema": "exact-equality-lp-solution-v1",
            "model_sha256": model_digest(source), "primal": primal,
            "dual": dual, "claimed_objective": objective}


def mapping_control():
    source = model([{"0": "1", "1": "1"}, {"0": "1", "1": "2"}],
                   ["3", "5"], ["2", "1"], "1")
    return source, certificate(source, ["1", "2"], ["3", "-1"], "4")


def rejected_controls():
    source, proof = mapping_control()
    tests = []
    for key, value in (
        ("primal", ["2", "1"]), ("primal", ["-1", "4"]),
        ("primal", ["1"]), ("primal", ["1", "2", "0"]),
        ("primal", [1.0, "2"]), ("primal", [True, "2"]),
        ("primal", ["1.0", "2"]), ("primal", ["01", "2"]),
        ("primal", ["1/1", "2"]), ("primal", ["2/2", "2"]),
        ("primal", ["+1", "2"]), ("primal", ["NaN", "2"]),
        ("dual", ["-3", "1"]), ("dual", ["-1", "3"]), ("dual", ["3"]),
        ("claimed_objective", "5"), ("claimed_objective", 4),
        ("model_sha256", "0" * 64), ("schema", "FLOAT_OPTIMAL"),
    ):
        mutated = deepcopy(proof)
        mutated[key] = value
        tests.append((source, mutated))
    for mutate in (
        lambda m: m.update(rows=m["rows"][:-1]),
        lambda m: m.update(rhs=m["rhs"][:-1]),
        lambda m: m.update(objective=m["objective"][:-1]),
        lambda m: m["row_ids"].reverse(),
        lambda m: m["variable_ids"].reverse(),
        lambda m: m["rows"][0].update({"01": "1"}),
        lambda m: m["rows"][0].update({"2": "1"}),
        lambda m: m["rows"][0].update({"0": "0"}),
        lambda m: m["rows"][0].update({"0": True}),
        lambda m: m.update(objective_offset="1.0"),
        lambda m: m.update(name="bad\nsubject to"),
        lambda m: m.update(extra="unbound"),
        lambda m: m.update(schema=True),
    ):
        mutated = deepcopy(source)
        mutate(mutated)
        tests.append((mutated, proof))
    return tests


class ExactLPVerificationTests(unittest.TestCase):
    def test_valid_row_mapping_and_signed_equality_dual(self):
        source, proof = mapping_control()
        result = verify_solution(source, proof)
        self.assertTrue(result["valid"], result)
        self.assertEqual(result["reduced_objective"], "4")
        self.assertEqual(result["total_objective"], "5")
        negative = model([{"0": "-1"}], ["-1"], ["1"])
        self.assertTrue(verify_solution(negative, certificate(negative, ["1"], ["-1"], "1"))["valid"])

    def test_all_adversarial_controls(self):
        for source, proof in rejected_controls():
            result = verify_solution(source, proof)
            self.assertFalse(result["valid"], (source, proof))
            self.assertEqual(result["status"], "INVALID")

    def test_no_primal_feasible_certificate_for_infeasible_lp(self):
        source = model([{"0": "1"}, {"0": "1"}], ["0", "1"], ["1"])
        self.assertFalse(verify_solution(source, certificate(source, ["0"], ["1", "0"], "0"))["valid"])

    def test_dual_feasibility_and_gap_are_separate(self):
        source = model([{"0": "1", "1": "1"}], ["1"], ["0", "1"])
        # Feasible primal/dual with a gap do not prove optimality.
        self.assertFalse(verify_solution(source, certificate(source, ["0", "1"], ["0"], "1"))["valid"])
        # Matching objectives alone do not suffice when a reduced cost is negative.
        self.assertFalse(verify_solution(source, certificate(source, ["0", "1"], ["1"], "1"))["valid"])

    def test_alternative_optimal_vectors_are_allowed(self):
        source = model([{"0": "1", "1": "1"}], ["1"], ["0", "0"])
        for primal in (["1", "0"], ["0", "1"], ["1/3", "2/3"]):
            self.assertTrue(verify_solution(source, certificate(source, primal, ["0"], "0"))["valid"])

    def test_rational_row_scaling_requires_dual_remap(self):
        source = model([{"0": "1/3"}], ["1/2"], ["1"])
        self.assertTrue(verify_solution(source, certificate(source, ["3/2"], ["3"], "3/2"))["valid"])
        self.assertFalse(verify_solution(source, certificate(source, ["3/2"], ["1/2"], "3/2"))["valid"])

    def test_hash_and_mathematics_both_checked(self):
        source, proof = mapping_control()
        changed = deepcopy(source)
        changed["rows"][1]["1"] = "3"
        self.assertFalse(verify_solution(changed, proof)["valid"])
        rebound = deepcopy(proof)
        rebound["model_sha256"] = model_digest(changed)
        self.assertFalse(verify_solution(changed, rebound)["valid"])

    def test_offset_is_reporting_metadata_for_generic_lp(self):
        source, proof = mapping_control()
        changed = deepcopy(source)
        changed["objective_offset"] = "7/3"
        self.assertFalse(verify_solution(changed, proof)["valid"])
        rebound = deepcopy(proof)
        rebound["model_sha256"] = model_digest(changed)
        result = verify_solution(changed, rebound)
        self.assertTrue(result["valid"], result)
        self.assertEqual(result["reduced_objective"], "4")
        self.assertEqual(result["total_objective"], "19/3")

    def test_large_exact_rational_strings(self):
        # More than Python's usual decimal conversion limit; no global setting changed.
        enormous = "1" + "0" * 5000
        source = model([{"0": "1"}], [enormous], ["1"])
        result = verify_solution(source, certificate(source, [enormous], ["1"], enormous))
        self.assertTrue(result["valid"], result)
        self.assertEqual(result["total_objective"], enormous)

    def test_zero_dimension_cases(self):
        empty = model([], [], [])
        self.assertTrue(verify_solution(empty, certificate(empty, [], [], "0"))["valid"])
        inconsistent = model([{}], ["1"], [])
        self.assertFalse(verify_solution(inconsistent, certificate(inconsistent, [], ["0"], "0"))["valid"])

    def test_optimized_python_rejects_forged_certificates(self):
        script = (
            "from test_exact_lp_verify import rejected_controls, mapping_control; "
            "from exact_lp_verify import verify_solution; "
            "bad = sum(verify_solution(m,c)['valid'] for m,c in rejected_controls()); "
            "good = verify_solution(*mapping_control())['valid']; "
            "print(bad,good); raise SystemExit(0 if bad == 0 and good else 1)"
        )
        run = subprocess.run([sys.executable, "-B", "-O", "-c", script],
                             cwd=HERE, capture_output=True, text=True, timeout=30)
        self.assertEqual(run.returncode, 0, run.stdout + run.stderr)
        self.assertEqual(run.stdout.strip(), "0 True")

    def test_affine_source_binding_and_source_mutations(self):
        saved = json.loads((HERE / "REED_MULLER_LEVEL_D_AFFINE_OVERLAP_RESULTS.json").read_text())
        source = model(
            [{key: str(Fraction(value)) for key, value in row.items() if value != 0}
             for row in saved["quotient_matrix"]],
            saved["rhs"], saved["objective"], "1", "rm25_affine_overlap")
        proof = certificate(source, saved["primal_orbit_masses"],
                            saved["dual_row_values"], saved["selected_model_optimum"])
        result = replay_affine_overlap(source, proof)
        self.assertTrue(result["valid"], result)
        self.assertEqual(result["reduced_objective"], "31/5")
        self.assertEqual(result["total_objective"], "36/5")
        for key, value in (("objective_offset", "0"), ("name", "unrelated_model")):
            changed = deepcopy(source)
            changed[key] = value
            rebound = deepcopy(proof)
            rebound["model_sha256"] = model_digest(changed)
            # A self-consistent digest/math certificate still is not source binding.
            self.assertTrue(verify_solution(changed, rebound)["valid"])
            self.assertFalse(replay_affine_overlap(changed, rebound)["valid"])
        changed = deepcopy(source)
        changed["rows"][0] = {key: str(Fraction(value) * 2)
                              for key, value in changed["rows"][0].items()}
        changed["rhs"][0] = str(Fraction(changed["rhs"][0]) * 2)
        rebound = deepcopy(proof)
        rebound["dual"][0] = str(Fraction(rebound["dual"][0]) / 2)
        rebound["model_sha256"] = model_digest(changed)
        self.assertTrue(verify_solution(changed, rebound)["valid"])
        self.assertFalse(replay_affine_overlap(changed, rebound)["valid"])


if __name__ == "__main__":
    unittest.main()
