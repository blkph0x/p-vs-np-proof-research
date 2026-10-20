"""Independent truth-table and adversarial controls for the strict RUP checker.

Run with both python -B -m unittest test_rup_verify and python -B -O -m unittest
test_rup_verify. No SAT producer or other proof checker is imported.
"""
from __future__ import annotations

import copy
import itertools
import unittest

from rup_verify import verify_rup


def models(nvars, clauses):
    """Small independent semantic oracle, deliberately unrelated to propagation."""
    return [
        bits for bits in itertools.product((False, True), repeat=nvars)
        if all(any(bits[abs(lit) - 1] == (lit > 0) for lit in clause)
               for clause in clauses)
    ]


def exhaustive_cube_proof(nvars):
    """Refute by complete assignments then paired prefix clauses.

    On an unsatisfiable formula each full blocking clause is RUP; once all
    length-k prefixes exist, each length-(k-1) prefix follows by opposite units.
    On a satisfiable formula a full model's blocking clause cannot be RUP.
    This exponential test producer is not a claimed solver improvement.
    """
    lines = []
    for length in range(nvars, -1, -1):
        for bits in itertools.product((False, True), repeat=length):
            clause = [-(i + 1) if bit else i + 1 for i, bit in enumerate(bits)]
            lines.append(" ".join(map(str, clause + [0])))
    return "\n".join(lines) + "\n"


class RUPTests(unittest.TestCase):
    def check_status(self, expected, nvars, clauses, text, **caps):
        result = verify_rup(nvars, clauses, text, **caps)
        self.assertEqual(result["status"], expected, result)
        self.assertEqual(result["valid"], expected == "VERIFIED", result)
        self.assertEqual(result["claim"], "UNSAT" if expected == "VERIFIED" else None)
        self.assertEqual(bool(result["errors"]), expected != "VERIFIED")
        return result

    def test_exhaustive_all_two_variable_cnfs(self):
        possible = [
            tuple((index + 1) * sign for index, sign in enumerate(signs) if sign)
            for signs in itertools.product((0, 1, -1), repeat=2)
        ]
        proof = exhaustive_cube_proof(2)
        unsat_count = 0
        for subset in range(1 << len(possible)):
            clauses = [clause for i, clause in enumerate(possible) if subset >> i & 1]
            unsat = not models(2, clauses)
            unsat_count += unsat
            with self.subTest(subset=subset):
                self.check_status("VERIFIED" if unsat else "INVALID", 2, clauses, proof)
        self.assertEqual(unsat_count, 417)

    def test_exhaustive_short_one_variable_traces_are_sound(self):
        possible = [(), (1,), (-1,)]
        operations = [
            prefix + " ".join(map(str, clause + (0,))) + "\n"
            for prefix in ("", "d ") for clause in possible
        ]
        checked = 0
        for subset in range(8):
            clauses = [clause for i, clause in enumerate(possible) if subset >> i & 1]
            satisfiable = bool(models(1, clauses))
            for length in range(4):
                for steps in itertools.product(operations, repeat=length):
                    result = verify_rup(1, clauses, "".join(steps))
                    self.assertNotEqual(result["status"], "UNKNOWN")
                    if result["valid"]:
                        self.assertFalse(satisfiable, (clauses, steps, result))
                        self.assertEqual(result["claim"], "UNSAT")
                    checked += 1
        self.assertEqual(checked, 2072)

    def test_explicit_completion_and_zero_variables(self):
        self.check_status("INVALID", 1, [[1], [-1]], "")
        self.check_status("VERIFIED", 1, [[1], [-1]], "0\n")
        self.check_status("INVALID", 0, [], "")
        self.check_status("INVALID", 0, [], "0\n")
        original = self.check_status("VERIFIED", 0, [[]], b"")
        self.assertEqual(original["completion"], "original_empty_clause")
        self.check_status("VERIFIED", 0, [[]], "0\n")

    def test_duplicate_literals_and_tautologies(self):
        self.check_status("VERIFIED", 1, [[1, 1], [-1, -1]], "1 1 0\n0\n")
        self.check_status("INVALID", 1, [[1, -1]], "0\n")
        self.check_status("INVALID", 1, [], "1 -1 0\n")
        result = self.check_status("VERIFIED", 1, [[1], [-1]], "1 -1 1 0\n0\n")
        self.assertEqual(result["stats"]["additions"], 2)

    def test_deletion_removes_one_multiset_occurrence(self):
        clauses = [[1], [1], [-1]]
        result = self.check_status("VERIFIED", 1, clauses, "d 1 0\n0\n")
        self.assertEqual(result["stats"]["active_clauses"], 3)
        self.check_status("INVALID", 1, clauses, "d 1 0\nd 1 0\n0\n")
        self.check_status("INVALID", 1, [[1], [-1]], "d 1 0\n0\n")
        result = self.check_status("VERIFIED", 2, [[1], [-1]], "d 2 0\n0\n")
        self.assertEqual(result["stats"]["absent_deletions"], 1)

    def test_deletion_canonicalization_and_added_copies(self):
        clauses = [[2, 1, 2], [1, 2], [-1], [-2]]
        self.check_status("VERIFIED", 2, clauses, "d 2 1 1 0\n0\n")
        self.check_status("INVALID", 2, clauses, "d 2 1 0\nd 1 2 0\n0\n")
        self.check_status("VERIFIED", 1, [[1], [-1]], "1 0\nd 1 1 0\n0\n")
        self.check_status("INVALID", 1, [[1], [-1]], "1 0\nd 1 0\nd 1 0\n0\n")

    def test_input_binding_and_no_rat_fallback(self):
        proof = "0\n"
        self.check_status("VERIFIED", 2, [[1], [-1]], proof)
        self.check_status("INVALID", 2, [[1], [2]], proof)
        # A pure-pivot unit is RAT for an empty formula, but is not RUP.
        result = self.check_status("INVALID", 1, [], "1 0\n0\n")
        self.assertIn("not RUP", result["errors"][0])

    def test_no_early_return_after_empty_clause(self):
        self.check_status("INVALID", 1, [[1], [-1]], "0\njunk\n")
        self.check_status("INVALID", 1, [[1], [-1]], "0\n2 0\n")
        self.check_status("VERIFIED", 1, [[1], [-1]], "0\n1 0\n")
        self.check_status("INVALID", 1, [[1], [-1]], "0\nd 0\nd -1 0\n-1 0\n")
        # Deleting a proved contradiction does not erase its earlier proof.
        self.check_status("VERIFIED", 1, [[1], [-1]], "0\nd 0\n")
        self.check_status("INVALID", 0, [[]], "malformed\n")
        self.check_status("INVALID", 0, [[]], "c unterminated")

    def test_all_original_clauses_are_validated(self):
        for clauses in ([[], [True]], [[], [0]], [[], [2]], [[], False]):
            with self.subTest(clauses=clauses):
                self.check_status("INVALID", 1, clauses, "")

    def test_strict_original_types_and_bounds(self):
        for nvars in (True, False, -1, 1.0, "1", None):
            with self.subTest(nvars=nvars):
                self.check_status("INVALID", nvars, [[]], "")
        for clauses in ({}, {()}, None, iter([[]]), [set()], [1], [False]):
            with self.subTest(clauses=repr(clauses)):
                self.check_status("INVALID", 1, clauses, "0\n")
        for literal in (True, False, 0, 2, -2, 1.0, "1", None):
            with self.subTest(literal=literal):
                self.check_status("INVALID", 1, [[literal]], "0\n")
        self.check_status("VERIFIED", 1, ((1,), (-1,)), b"0\n")

    def test_strict_proof_encoding_and_termination(self):
        for text in (
            b"\xff\n", b"\xc0\x80\n", "\ud800\n", "0", "c comment",
            b"\x000\n", "0\x0b\n", "0\r", "0\r \n", "\ufeff0\n",
            None, [], bytearray(b"0\n"), True,
        ):
            with self.subTest(text=repr(text)):
                self.check_status("INVALID", 1, [[1], [-1]], text)
        self.check_status("VERIFIED", 1, [[1], [-1]],
                          " \t\r\nc UTF-8 comment \u03bb\r\nc\r\n\t0\t\r\n")

    def test_strict_proof_literal_syntax(self):
        for text in (
            "1 0 0\n", "-0\n", "+1 0\n", "01 0\n", "-01 0\n", "1.0 0\n",
            "1e0 0\n", "True 0\n", "d0\n", "d\n", "a 1 0\n", "p cnf 1 1\n",
            "2 0\n", "-2 0\n", "1\n", "1\u00a00\n", "\u0661 0\n",
            "0 junk\n", "d 0 0\n", "cc comment\n",
        ):
            with self.subTest(text=text):
                self.check_status("INVALID", 1, [[1], [-1]], text)

    def test_step_byte_literal_and_work_caps(self):
        source, proof = [[1], [-1]], "0\n"
        self.check_status("UNKNOWN", 1, source, proof, max_steps=0)
        self.check_status("UNKNOWN", 1, source, proof, max_proof_bytes=1)
        self.check_status("UNKNOWN", 1, source, proof, max_literal_inspections=0)
        self.check_status("UNKNOWN", 1, source, proof, max_work=0)
        baseline = self.check_status("VERIFIED", 1, source, proof)
        for counter, cap in (("steps", "max_steps"), ("proof_bytes", "max_proof_bytes"),
                             ("literal_inspections", "max_literal_inspections"),
                             ("work", "max_work")):
            value = baseline["stats"][counter]
            self.check_status("VERIFIED", 1, source, proof, **{cap: value})
            result = self.check_status("UNKNOWN", 1, source, proof, **{cap: value - 1})
            if counter != "proof_bytes":
                self.assertLessEqual(result["stats"][counter], value - 1)

    def test_caps_are_strict_and_comments_are_metered(self):
        for name in ("max_steps", "max_proof_bytes", "max_literal_inspections", "max_work"):
            for cap in (True, -1, 1.5, None, "10"):
                with self.subTest(name=name, cap=cap):
                    self.check_status("INVALID", 0, [[]], "", **{name: cap})
        result = self.check_status("VERIFIED", 0, [[]], "c comment\n\n", max_steps=0)
        self.assertEqual(result["stats"]["steps"], 0)
        self.assertEqual(result["stats"]["proof_lines"], 2)
        self.check_status("UNKNOWN", 0, [[]], "c comment\n\n", max_work=2)
        result = self.check_status("UNKNOWN", 0, [[]], "c \u03bb\n", max_proof_bytes=4)
        self.assertEqual(result["stats"]["proof_bytes"], 5)

    def test_no_input_mutation_or_variable_universe_allocation(self):
        original = [[1, 1], [-1], [1, -1]]
        before = copy.deepcopy(original)
        self.check_status("VERIFIED", 10**50, original, "0\n")
        self.assertEqual(original, before)
        literal = 10**100
        self.check_status("VERIFIED", literal, [[literal], [-literal]], "0\n")
        self.check_status("INVALID", 1, [[1], [-1]], "9" * 10000 + " 0\n")

    def test_nontrivial_refutation_requires_derived_units(self):
        clauses = [[1, 2], [1, -2], [-1, 2], [-1, -2]]
        self.check_status("INVALID", 2, clauses, "0\n")
        result = self.check_status("VERIFIED", 2, clauses, "1 0\n0\n")
        self.assertEqual(result["stats"]["rup_checks"], 2)
        self.assertGreater(result["stats"]["propagations"], 0)

    def test_deleted_reason_for_previously_propagated_unit(self):
        # Before deletion, root-level propagation derives 2 from 1 and (-1,2).
        # Some public checkers retain such forced facts/reason clauses. Our
        # strict fresh-database semantics really delete the sole reason, so
        # the subsequent addition (2) must fail. The remaining binary core
        # is UNSAT but is deliberately not unit-refutable without a new lemma.
        clauses = [[1], [-1, 2], [3, 4], [3, -4], [-3, 4], [-3, -4]]
        raw = "d -1 2 0\n2 0\n3 0\n0\n"
        failed = self.check_status("INVALID", 4, clauses, raw)
        self.assertIn("line 2 is not RUP", failed["errors"][0])
        # A separately proposed addition-only proof retains the original
        # reason and is sound ONLY because its entire proof is freshly checked.
        proposed = "2 0\n3 0\n0\n"
        self.check_status("VERIFIED", 4, clauses, proposed)
        self.check_status("INVALID", 4, clauses[:-1], proposed)
        self.check_status("INVALID", 4, clauses, "2 0\n")
        self.assertFalse(models(4, clauses))
        self.assertTrue(models(4, clauses[:-1]))


if __name__ == "__main__":
    unittest.main()
