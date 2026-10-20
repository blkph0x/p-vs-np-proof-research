"""Independent original-CNF and candidate acceptance controls.

No public solver or downloaded executable is needed. Small direct assignment
oracles check semantics; native resolution proofs exercise the other envelope.
"""
from copy import deepcopy
from contextlib import redirect_stdout
import io
from itertools import product
import json
from pathlib import Path
import subprocess
import sys
import tempfile
from types import ModuleType, SimpleNamespace
import unittest
from unittest.mock import patch

from cdcl import CDCL
import public_sat_cases as cases
import run_public_sat as runner
import sat_backend_certificate as certificate


HERE = Path(__file__).resolve().parent
XOR_UNSAT = [[1, 2], [1, -2], [-1, 2], [-1, -2]]
RUP = "1 0\n0\n"


def holds(clauses, model):
    return all(any(model[abs(lit) - 1] == (lit > 0) for lit in clause)
               for clause in clauses)


def candidate(request, status, **data):
    return {"schema": "public-sat-candidate-v1",
            "request_sha256": certificate.request_digest(request),
            "status": status, **data}


def native_envelope(request, result):
    return {"schema": "native-cdcl-candidate-v1",
            "request_sha256": certificate.request_digest(request),
            "result": result}


def original_two_variable_families():
    # All 3^2 non-tautological clauses, including the empty clause.
    pool = [[(index + 1) * sign for index, sign in enumerate(signs) if sign]
            for signs in product((0, 1, -1), repeat=2)]
    for selected in range(1 << len(pool)):
        yield [clause for index, clause in enumerate(pool) if selected >> index & 1]


def assert_rebound_false_claims():
    original = cases.request(1, [[1]])
    sat = candidate(original, "SAT", model=[True])
    changed = cases.request(1, [[-1]])
    sat["request_sha256"] = certificate.request_digest(changed)
    if certificate.verify_candidate(changed, sat)["status"] != "INVALID":
        raise RuntimeError("rebound false SAT claim accepted")
    original = cases.request(2, XOR_UNSAT)
    unsat = candidate(original, "UNSAT", proof_sha256=certificate.proof_digest(RUP))
    changed = cases.request(2, XOR_UNSAT[:-1])
    unsat["request_sha256"] = certificate.request_digest(changed)
    if certificate.verify_candidate(changed, unsat, RUP)["status"] != "INVALID":
        raise RuntimeError("rebound false UNSAT claim accepted")


class PublicSatCertificateTests(unittest.TestCase):
    def invalid(self, checked):
        self.assertFalse(checked["valid"])
        self.assertEqual(checked["status"], "INVALID")
        self.assertTrue(checked["errors"])

    def test_all_two_variable_formulas_and_models(self):
        count = 0
        for clauses in original_two_variable_families():
            request = cases.request(2, clauses)
            for values in product((False, True), repeat=2):
                checked = certificate.verify_candidate(
                    request, candidate(request, "SAT", model=list(values)))
                self.assertEqual(checked["valid"], holds(clauses, values))
                self.assertEqual(checked["status"],
                                 "VERIFIED_SAT" if holds(clauses, values) else "INVALID")
            count += 1
        self.assertEqual(count, 512)

    def test_original_hash_binding_does_not_replace_mathematics(self):
        request = cases.request(1, [[1]])
        saved = candidate(request, "SAT", model=[True])
        changed = cases.request(1, [[-1]])
        self.invalid(certificate.verify_candidate(changed, saved))
        assert_rebound_false_claims()

    def test_complete_strict_boolean_models_and_unused_variables(self):
        request = cases.request(4, [[1], [-2]])
        good = candidate(request, "SAT", model=[True, False, True, False])
        self.assertTrue(certificate.verify_candidate(request, good)["valid"])
        for model in ([True, False], [True, False, False, False, False],
                      [1, False, False, False], [True, 0, False, False],
                      [True, False, None, False], {0: True, 1: False},
                      (True, False, False, False), None):
            with self.subTest(model=model):
                self.invalid(certificate.verify_candidate(
                    request, candidate(request, "SAT", model=model)))
        for width in (0, 5):
            empty = cases.request(width, [])
            self.assertTrue(certificate.verify_candidate(
                empty, candidate(empty, "SAT", model=[False] * width))["valid"])
        empty_clause = cases.request(0, [[]])
        self.invalid(certificate.verify_candidate(
            empty_clause, candidate(empty_clause, "SAT", model=[])))

    def test_original_request_strict_fields_and_literals(self):
        valid = cases.request(1, [[1]])
        saved = candidate(valid, "SAT", model=[True])
        malformed = [
            None, [], {"schema": "wrong", "nvars": 1, "clauses": [[1]]},
            {**valid, "extra": 1}, {**valid, "nvars": True},
            {**valid, "nvars": -1}, {**valid, "nvars": 1.0},
            {**valid, "clauses": ((1,),)}, {**valid, "clauses": [(1,)]},
        ]
        malformed += [{**valid, "clauses": [[lit]]}
                      for lit in (True, False, 0, 2, -2, "1", 1.0, None)]
        for request in malformed:
            with self.subTest(request=request):
                self.invalid(certificate.verify_candidate(request, saved))
                with self.assertRaises((ValueError, TypeError)):
                    certificate.dimacs(request)

    def test_candidate_fields_are_strict(self):
        request = cases.request(1, [[1]])
        good = candidate(request, "SAT", model=[True])
        malformed = [None, [], {}, {**good, "extra": 1},
                     {**good, "schema": "other"}, {**good, "status": "VERIFIED_SAT"},
                     {**good, "request_sha256": None},
                     {key: value for key, value in good.items() if key != "model"}]
        for value in malformed:
            self.invalid(certificate.verify_candidate(request, value))
        unsat_request = cases.request(1, [[1], [-1]])
        unsat = candidate(unsat_request, "UNSAT",
                          proof_sha256=certificate.proof_digest("0\n"))
        self.invalid(certificate.verify_candidate(
            unsat_request, {**unsat, "model": None}, "0\n"))

    def test_text_and_bytes_proof_binding_and_complete_replay(self):
        request = cases.request(2, XOR_UNSAT)
        saved = candidate(request, "UNSAT", proof_sha256=certificate.proof_digest(RUP))
        for proof in (RUP, RUP.encode("ascii")):
            checked = certificate.verify_candidate(request, saved, proof)
            self.assertTrue(checked["valid"], checked)
            self.assertEqual(checked["status"], "VERIFIED_UNSAT")
            self.assertEqual(checked["claim"], "UNSAT")
        for proof in (None, "0\n", "", RUP + "c altered bytes\n"):
            self.invalid(certificate.verify_candidate(request, saved, proof))
        for proof in ("0\n", "", RUP + "not a proof\n"):
            rebound = candidate(request, "UNSAT",
                                proof_sha256=certificate.proof_digest(proof))
            self.invalid(certificate.verify_candidate(request, rebound, proof))

    def test_units_original_empty_clause_and_tautologies(self):
        for request, proof in (
            (cases.request(1, [[1], [-1]]), "0\n"),
            (cases.request(0, [[]]), ""),
            (cases.request(3, [[1, -1], [2, 2], [-2]]), "0\n"),
        ):
            checked = certificate.verify_candidate(
                request, candidate(request, "UNSAT",
                                   proof_sha256=certificate.proof_digest(proof)), proof)
            self.assertEqual(checked["status"], "VERIFIED_UNSAT", checked)
        request = cases.request(0, [])
        self.invalid(certificate.verify_candidate(
            request, candidate(request, "UNSAT",
                               proof_sha256=certificate.proof_digest("0\n")), "0\n"))

    def test_resource_unknown_is_not_a_decision(self):
        request = cases.request(2, XOR_UNSAT)
        saved = candidate(request, "UNSAT", proof_sha256=certificate.proof_digest(RUP))
        baseline = certificate.verify_candidate(request, saved, RUP)
        fields = {"max_steps": "steps", "max_work": "work",
                  "max_literal_inspections": "literal_inspections",
                  "max_proof_bytes": "proof_bytes"}
        exact_limits = {limit: baseline["stats"][field] for limit, field in fields.items()}
        self.assertTrue(certificate.verify_candidate(request, saved, RUP, **exact_limits)["valid"])
        for limit in fields:
            caps = {**exact_limits, limit: exact_limits[limit] - 1}
            checked = certificate.verify_candidate(request, saved, RUP, **caps)
            self.assertFalse(checked["valid"])
            self.assertEqual(checked["status"], "UNKNOWN", checked)
            self.assertIsNone(checked["claim"])
        self.invalid(certificate.verify_candidate(request, saved, RUP, max_steps=True))
        self.invalid(certificate.verify_candidate(request, saved, RUP, not_a_cap=10))

    def test_reported_unknown_is_strict_and_has_no_decision(self):
        request = cases.request(2, [[1, 2]])
        good = candidate(request, "UNKNOWN", reason="time cap")
        checked = certificate.verify_candidate(request, good)
        self.assertFalse(checked["valid"])
        self.assertEqual(checked["status"], "UNKNOWN")
        for altered in ({**good, "model": [True, True]},
                        {**good, "proof_sha256": "0" * 64},
                        {**good, "reason": ""}, {**good, "reason": 5}):
            self.invalid(certificate.verify_candidate(request, altered))

    def test_dimacs_exact_original_and_input_not_mutated(self):
        request = cases.request(4, [[2, 2], [-1, 1], []])
        original = deepcopy(request)
        self.assertEqual(certificate.dimacs(request),
                         "p cnf 4 3\n2 2 0\n-1 1 0\n0\n")
        saved = candidate(request, "UNSAT", proof_sha256=certificate.proof_digest(""))
        frozen = deepcopy(saved)
        self.assertTrue(certificate.verify_candidate(request, saved, "")["valid"])
        self.assertEqual(request, original)
        self.assertEqual(saved, frozen)
        reordered = {**request, "clauses": list(reversed(request["clauses"]))}
        self.assertNotEqual(certificate.request_digest(request),
                            certificate.request_digest(reordered))
        self.assertEqual(certificate.request_digest(request),
                         certificate.request_digest(json.loads(json.dumps(request))))

    def test_native_envelopes_all_two_variable_originals(self):
        for clauses in original_two_variable_families():
            request = cases.request(2, clauses)
            result = CDCL(2, clauses).solve()
            expected = any(holds(clauses, values)
                           for values in product((False, True), repeat=2))
            checked = certificate.verify_native_candidate(
                request, native_envelope(request, json.loads(json.dumps(result))))
            self.assertTrue(checked["valid"], checked)
            self.assertEqual(checked["status"], "VERIFIED_SAT" if expected else "VERIFIED_UNSAT")
        for width, clauses in ((0, []), (0, [[]]), (5, [[1]])):
            request = cases.request(width, clauses)
            self.assertTrue(certificate.verify_native_candidate(
                request, native_envelope(request, CDCL(width, clauses).solve()))["valid"])

    def test_native_original_binding_even_with_rebound_hash(self):
        request = cases.request(1, [[1], [-1]])
        envelope = native_envelope(request, CDCL(1, request["clauses"]).solve())
        changed = cases.request(1, [[1]])
        self.invalid(certificate.verify_native_candidate(changed, envelope))
        envelope["request_sha256"] = certificate.request_digest(changed)
        self.invalid(certificate.verify_native_candidate(changed, envelope))
        request = cases.request(1, [[1]])
        envelope = native_envelope(request, CDCL(1, request["clauses"]).solve())
        changed = cases.request(1, [[-1]])
        envelope["request_sha256"] = certificate.request_digest(changed)
        envelope["result"]["clauses"] = [[-1]]
        self.invalid(certificate.verify_native_candidate(changed, envelope))

    def test_native_tampered_proof_model_and_envelope(self):
        request = cases.request(1, [[1], [-1]])
        good = native_envelope(request, CDCL(1, request["clauses"]).solve())
        for mutate in (
            lambda value: value.update(extra=1),
            lambda value: value.update(schema="other"),
            lambda value: value["result"].update(proof=[]),
            lambda value: value["result"].update(clauses=[]),
            lambda value: value["result"]["proof"][0].update(from_conflict=[]),
            lambda value: value["result"]["proof"][0]["derivation"][0].update(pivot=True),
            lambda value: value["result"].update(model={0: True}),
        ):
            altered = deepcopy(good)
            mutate(altered)
            self.invalid(certificate.verify_native_candidate(request, altered))
        sat_request = cases.request(3, [[1]])
        sat = native_envelope(sat_request, CDCL(3, [[1]]).solve())
        for model in ({0: True}, {0: 1, 1: False, 2: False},
                      {0: True, "0": True, 1: False, 2: False}):
            altered = deepcopy(sat)
            altered["result"]["model"] = model
            self.invalid(certificate.verify_native_candidate(sat_request, altered))

    def test_native_unknown_and_no_enumeration_dependency(self):
        request = cases.request(2, [[1, 2]])
        result = CDCL(2, request["clauses"], max_decisions=0).solve()
        checked = certificate.verify_native_candidate(request, native_envelope(request, result))
        self.assertFalse(checked["valid"])
        self.assertEqual(checked["status"], "UNKNOWN")
        with patch.object(certificate.sibling("review"), "direct",
                          side_effect=RuntimeError("truth-table oracle forbidden")):
            request = cases.request(1, [[1], [-1]])
            checked = certificate.verify_native_candidate(
                request, native_envelope(request, CDCL(1, request["clauses"]).solve()))
            self.assertTrue(checked["valid"])

    def test_bare_module_names_cannot_replace_the_checkers(self):
        wrong_review = ModuleType("review")
        wrong_review.replay = lambda *args: True
        wrong_rup = ModuleType("rup_verify")
        wrong_rup.verify_rup = lambda *args, **kwargs: {"valid": True, "status": "VERIFIED"}
        request = cases.request(1, [[1]])
        public = candidate(request, "UNSAT", proof_sha256=certificate.proof_digest("0\n"))
        result = CDCL(1, [[1]]).solve()
        result.update(status="UNSAT", model=None, proof=[])
        with patch.dict(sys.modules, {"review": wrong_review, "rup_verify": wrong_rup}):
            self.invalid(certificate.verify_candidate(request, public, "0\n"))
            self.invalid(certificate.verify_native_candidate(
                request, native_envelope(request, result)))

    def test_case_generators_match_independent_small_truth_tables(self):
        for size in range(1, 5):
            for contradiction in (False, True):
                request = cases.xor_chain(size, contradiction)
                models = [values for values in product((False, True), repeat=request["nvars"])
                          if holds(request["clauses"], values)]
                self.assertEqual(len(models), 0 if contradiction else 1 << (size - 1))
                for values in models:
                    self.assertEqual(sum(values[:size]) % 2, 0)
                    for variable in range(2, size + 1):
                        self.assertEqual(values[size + variable - 2],
                                         bool(sum(values[:variable]) % 2))
        for holes in (0, 1, 2):
            request = cases.php(holes)
            self.assertFalse(any(holds(request["clauses"], values)
                                 for values in product((False, True), repeat=request["nvars"])))
        original = cases.request(4, [[1, -2], [2, 3], [-3, 4], [1, 1]])
        saved = deepcopy(original)
        relabelled = cases.shuffled(original, 53)
        self.assertEqual(original, saved)
        self.assertEqual(relabelled, cases.shuffled(original, 53))
        model_count = lambda request: sum(
            holds(request["clauses"], values)
            for values in product((False, True), repeat=request["nvars"]))
        self.assertEqual(model_count(original), model_count(relabelled))

    def test_saved_case_family_requests_and_planted_witnesses(self):
        first = cases.cases()
        self.assertEqual(first, cases.cases())
        self.assertEqual(len(first), 19)
        self.assertEqual(len({value["name"] for value in first}), len(first))
        for value in first:
            request = value["request"]
            certificate.validate_request(request)
            self.assertTrue(certificate.dimacs(request).startswith(
                f'p cnf {request["nvars"]} {len(request["clauses"])}\n'))
            if value["name"].startswith("planted3_"):
                self.assertTrue(holds(request["clauses"], [True] * request["nvars"]))
                self.assertTrue(all(len(clause) == 3 and
                                    len({abs(lit) for lit in clause}) == 3
                                    for clause in request["clauses"]))

    def test_rebound_adversaries_survive_python_optimization(self):
        completed = subprocess.run(
            [sys.executable, "-B", "-O", "-c",
             "from test_public_sat_certificate import assert_rebound_false_claims; "
             "assert_rebound_false_claims()"],
            cwd=HERE, capture_output=True, text=True, timeout=30)
        self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)

    def test_external_checker_status_contract(self):
        self.assertTrue(runner.check_external_output(0, "c information\ns VERIFIED\n"))
        for code, text in (
            (1, "s VERIFIED\n"), (0, ""), (0, "c ERROR: bad header\n"),
            (0, "s TIMEOUT\n"), (0, "s NOT VERIFIED\n"),
            (0, "s VERIFIED\ns VERIFIED\n"), (0, "s VERIFIED\ns UNKNOWN\n"),
            (0, "s VERIFIED\nc ERROR in stderr\n"),
            (0, "prefix s VERIFIED suffix\n"),
        ):
            with self.subTest(code=code, text=text):
                self.assertFalse(runner.check_external_output(code, text))

    def test_rup_proposal_preserves_raw_and_requires_original_replay(self):
        raw = ["1 0", "d -1 2 0", "0"]
        raw_text, proof, metadata = runner.propose_rup(raw)
        self.assertEqual(raw_text, "1 0\nd -1 2 0\n0\n")
        self.assertEqual(proof, RUP)
        self.assertEqual(metadata["removed_deletion_lines"], 1)
        self.assertFalse(metadata["appended_terminal_rup_proposal"])
        self.assertEqual(metadata["raw_proof_sha256"], certificate.proof_digest(raw_text))
        request = cases.request(2, XOR_UNSAT)
        self.assertEqual(certificate.verify_candidate(
            request, candidate(request, "UNSAT",
                               proof_sha256=certificate.proof_digest(proof)), proof)["status"],
                         "VERIFIED_UNSAT")
        raw_text, proof, metadata = runner.propose_rup([])
        self.assertEqual(raw_text, "")
        self.assertEqual(proof, "0\n")
        self.assertTrue(metadata["appended_terminal_rup_proposal"])
        units = cases.request(1, [[1], [-1]])
        self.assertTrue(certificate.verify_candidate(
            units, candidate(units, "UNSAT",
                             proof_sha256=certificate.proof_digest(proof)), proof)["valid"])
        # Proposing a terminal clause is not evidence of its validity.
        self.invalid(certificate.verify_candidate(
            request, candidate(request, "UNSAT",
                               proof_sha256=certificate.proof_digest(proof)), proof))
        sat = cases.request(1, [[1]])
        self.invalid(certificate.verify_candidate(
            sat, candidate(sat, "UNSAT", proof_sha256=certificate.proof_digest(proof)), proof))

    def test_rup_proposal_bad_shapes_and_forged_additions(self):
        for raw in (None, (), "0", [0], [b"0"], [False]):
            with self.assertRaises(ValueError):
                runner.propose_rup(raw)
        request = cases.request(2, XOR_UNSAT)
        for raw in (["garbage"], ["3 0"], ["0"], ["1 0", "0", "trailing garbage"]):
            _, proof, _ = runner.propose_rup(raw)
            self.invalid(certificate.verify_candidate(
                request, candidate(request, "UNSAT",
                                   proof_sha256=certificate.proof_digest(proof)), proof))
        # A fabricated intermediate lemma cannot turn a SAT original UNSAT.
        request = cases.request(2, [[1, 2]])
        _, proof, _ = runner.propose_rup(["1 0", "-1 0"])
        self.invalid(certificate.verify_candidate(
            request, candidate(request, "UNSAT",
                               proof_sha256=certificate.proof_digest(proof)), proof))

    def test_public_worker_drains_proof_before_close_for_every_status(self):
        # Protocol test, independent of the optional wheel. The real Windows
        # reproduction is separately saved under .research-tools.
        for solver_result in (True, False, None):
            events = []
            original = cases.request(3, [[1]] if solver_result is not False else [[1], [-1]])
            raw = ["d 1 0"] if solver_result is True else []

            class FakeGlucose:
                def __init__(self, *, bootstrap_with, with_proof):
                    self.drained = False
                    if bootstrap_with != original["clauses"] or with_proof is not True:
                        raise RuntimeError("worker changed original input/proof mode")
                    events.append("construct")

                def __enter__(self):
                    return self

                def __exit__(self, *exc):
                    if not self.drained:
                        raise RuntimeError("closed without draining the proof stream")
                    events.append("close")

                def solve(self):
                    events.append("solve")
                    return solver_result

                def accum_stats(self):
                    return {"decisions": 0}

                def get_proof(self):
                    self.drained = True
                    events.append("proof")
                    return list(raw)

                def get_model(self):
                    events.append("model")
                    return [1]  # Unused declared variables must be filled.

            package = ModuleType("pysat")
            package.__version__ = "1.9.dev16"
            extension = ModuleType("pysolvers")
            extension.__file__ = __file__
            six = ModuleType("six")
            six.__version__ = "1.16.0"
            solvers = ModuleType("pysat.solvers")
            solvers.__file__ = __file__
            solvers.Glucose3 = FakeGlucose
            with tempfile.TemporaryDirectory() as temp:
                directory = Path(temp)
                request_path = directory / "request.json"
                runner.write_json(request_path, original)
                args = SimpleNamespace(request=request_path, backend="glucose3",
                                       pysat_dir=None, output_dir=directory)
                with patch.dict(sys.modules, {"pysat": package, "pysolvers": extension,
                                              "six": six, "pysat.solvers": solvers}):
                    with redirect_stdout(io.StringIO()):
                        self.assertEqual(runner.worker(args), 0)
                self.assertLess(events.index("proof"), events.index("close"))
                self.assertEqual(events[-1], "close")
                self.assertEqual((directory / "raw-proof.drup").read_text(),
                                 "".join(line + "\n" for line in raw))
                metadata = runner.read_json(directory / "worker.json")
                self.assertIs(metadata["proof_stream_drained_before_close"], True)
                checked = runner.check_candidate(original, directory, "glucose3")
                self.assertEqual(checked["status"],
                                 {True: "VERIFIED_SAT", False: "VERIFIED_UNSAT",
                                  None: "UNKNOWN"}[solver_result])
                if solver_result is True:
                    self.assertEqual(runner.read_json(directory / "candidate.json")["model"],
                                     [True, False, False])
                    self.assertFalse((directory / "proof.drup").exists())

    def test_native_worker_subprocess_preserves_original(self):
        with tempfile.TemporaryDirectory() as temp:
            directory = Path(temp)
            request = cases.request(4, [[1], [-2]])
            request_path = directory / "original.json"
            runner.write_json(request_path, request)
            completed = subprocess.run(
                [sys.executable, "-B", str(HERE / "run_public_sat.py"), "--worker",
                 "--backend", "native", "--request", str(request_path),
                 "--output-dir", str(directory), "--native-decisions", "100"],
                cwd=HERE, capture_output=True, text=True, timeout=30)
            self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)
            checked = runner.check_candidate(request, directory, "native")
            self.assertEqual(checked["status"], "VERIFIED_SAT")
            self.assertEqual(runner.read_json(request_path), request)
            stored = runner.read_json(directory / "candidate.json")
            altered_request = cases.request(4, [[-1], [-2]])
            stored["request_sha256"] = certificate.request_digest(altered_request)
            stored["result"]["clauses"] = [[-1], [-2]]
            runner.write_json(directory / "candidate.json", stored)
            self.invalid(runner.check_candidate(altered_request, directory, "native"))

    def campaign_fixture(self, directory):
        """Create fresh valid evidence without either public solver or timing claims."""
        originals = [{"name": "sat", "request": cases.request(1, [[1]])},
                     {"name": "unsat", "request": cases.request(1, [[1], [-1]])}]
        runner.write_json(directory / "requests.json", originals)
        rows = []
        for item in originals:
            name, request = item["name"], item["request"]
            case_dir = directory / name
            case_dir.mkdir()
            runner.write_json(case_dir / "request.json", request)
            (case_dir / "input.cnf").write_text(certificate.dimacs(request), encoding="ascii")
            for backend in ("native", "glucose3"):
                out = case_dir / "repeat_0" / backend
                out.mkdir(parents=True)
                if backend == "native":
                    saved = native_envelope(request, CDCL(1, request["clauses"]).solve())
                elif name == "sat":
                    saved = candidate(request, "SAT", model=[True])
                else:
                    saved = candidate(request, "UNSAT",
                                      proof_sha256=certificate.proof_digest("0\n"))
                    (out / "proof.drup").write_bytes(b"0\n")
                runner.write_json(out / "candidate.json", saved)
                status = "VERIFIED_SAT" if name == "sat" else "VERIFIED_UNSAT"
                rows.append({"case": name, "backend": backend, "repetition": 0,
                             "request_sha256": certificate.request_digest(request),
                             "status": status})
        sources = runner.source_hashes()
        manifest = {
            "schema": "public-sat-benchmark-v1", "status": "PASS",
            "sources_unchanged": True, "source_sha256_lf": sources,
            "source_after_sha256_lf": dict(sources),
            "repetitions": 1, "rup_limits": dict(runner.RUP_LIMITS),
            "runs": rows, "disagreements": [],
            "status_counts": {"VERIFIED_SAT": 2, "VERIFIED_UNSAT": 2},
            "artifact_sha256": {path.relative_to(directory).as_posix(): runner.sha256(path)
                                for path in directory.rglob("*") if path.is_file()},
        }
        runner.write_json(directory / "benchmark.json", manifest)
        return manifest

    def test_replay_complete_original_proofs_and_pair_coverage(self):
        with tempfile.TemporaryDirectory() as temp:
            directory = Path(temp)
            manifest = self.campaign_fixture(directory)
            checked = runner.replay(directory)
            self.assertEqual(checked["status"], "PASS")
            self.assertEqual(checked["runs"], 4)
            self.assertEqual(checked["statuses"], {"VERIFIED_SAT": 2, "VERIFIED_UNSAT": 2})
            for mutate in (
                lambda value: value["runs"].pop(),
                lambda value: value["runs"].append(deepcopy(value["runs"][0])),
                lambda value: value["runs"][0].update(status="VERIFIED_UNSAT"),
                lambda value: value["runs"][0].update(request_sha256="0" * 64),
                lambda value: value["runs"][0].update(repetition=True),
                lambda value: value.update(repetitions=2),
            ):
                altered = deepcopy(manifest)
                mutate(altered)
                runner.write_json(directory / "benchmark.json", altered)
                with self.assertRaises(ValueError):
                    runner.replay(directory)

    def test_replay_artifact_and_source_declarations_are_complete(self):
        with tempfile.TemporaryDirectory() as temp:
            directory = Path(temp)
            manifest = self.campaign_fixture(directory)
            for mutate in (
                lambda value: value.update(artifact_sha256={}),
                lambda value: value["artifact_sha256"].pop("requests.json"),
                lambda value: value["artifact_sha256"].update({"../outside": "0" * 64}),
                lambda value: value.update(source_sha256_lf={}),
                lambda value: value.update(source_after_sha256_lf={}),
                lambda value: value["source_sha256_lf"].update(
                    {runner.SOURCES[0]: "0" * 64}),
                lambda value: value["source_after_sha256_lf"].update(
                    {runner.SOURCES[0]: "0" * 64}),
            ):
                altered = deepcopy(manifest)
                mutate(altered)
                runner.write_json(directory / "benchmark.json", altered)
                with self.assertRaises(ValueError):
                    runner.replay(directory)

    def test_replay_rejects_changed_evidence_and_rebound_false_proof(self):
        with tempfile.TemporaryDirectory() as temp:
            directory = Path(temp)
            manifest = self.campaign_fixture(directory)
            path = directory / "unsat" / "repeat_0" / "glucose3" / "proof.drup"
            path.write_bytes(b"")
            with self.assertRaises(ValueError):
                runner.replay(directory)
            candidate_path = path.with_name("candidate.json")
            saved = runner.read_json(candidate_path)
            saved["proof_sha256"] = certificate.proof_digest("")
            runner.write_json(candidate_path, saved)
            for changed in (path, candidate_path):
                manifest["artifact_sha256"][changed.relative_to(directory).as_posix()] = (
                    runner.sha256(changed))
            runner.write_json(directory / "benchmark.json", manifest)
            with self.assertRaises(ValueError):
                runner.replay(directory)


if __name__ == "__main__":
    unittest.main()
