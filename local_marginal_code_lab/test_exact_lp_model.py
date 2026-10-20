"""Independent small algebra and strict serialization checks for LP export."""
from copy import deepcopy
from fractions import Fraction
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import unittest
from unittest.mock import patch


_SPEC = importlib.util.spec_from_file_location(
    "_tested_exact_lp_model", Path(__file__).with_name("exact_lp_model.py"))
model_api = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(model_api)


def control_model():
    # Feasible at (1,2,3), with both negative coefficients and a redundant row.
    return {
        "schema": "exact-equality-lp-v1",
        "name": "signed_control",
        "variable_ids": ["x000000", "x000001", "x000002"],
        "row_ids": ["r000000", "r000001", "r000002", "r000003"],
        "rows": [
            {"0": "1", "1": "1"},
            {"0": "-1/2", "1": "2/3", "2": "1"},
            {"0": "-2", "1": "1"},
            {},
        ],
        "rhs": ["3", "23/6", "0", "0"],
        "objective": ["-3/2", "0", "5/7"],
        "objective_offset": "1",
    }


def independently_read_lp(text):
    """Read only the emitted LP subset, without using any exporter parser."""
    section = None
    objective = None
    rows = {}
    bounds = []

    def terms(expression):
        if expression.strip() == "0":
            return {}
        tokens = expression.split()
        result = {}
        position = 0
        while position < len(tokens):
            sign = 1
            if tokens[position] in ("+", "-"):
                sign = -1 if tokens[position] == "-" else 1
                position += 1
            value = sign * Fraction(tokens[position])
            variable = tokens[position + 1]
            if re.fullmatch(r"x[0-9]{6,}", variable) is None:
                raise ValueError("invalid variable in LP")
            if variable in result:
                raise ValueError("duplicate LP term")
            result[variable] = value
            position += 2
        return {key: value for key, value in result.items() if value}

    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith("\\"):
            continue
        if line in ("Minimize", "Subject To", "Bounds", "End"):
            section = line
        elif section == "Minimize":
            label, expression = line.split(":", 1)
            if label != "obj" or objective is not None:
                raise ValueError("duplicate or wrong objective")
            objective = terms(expression)
        elif section == "Subject To":
            label, expression = line.split(":", 1)
            lhs, rhs = expression.split("=", 1)
            if label in rows:
                raise ValueError("duplicate row")
            rows[label] = (terms(lhs), Fraction(rhs.strip()))
        elif section == "Bounds":
            zero, relation, variable = line.split()
            if zero != "0" or relation != "<=" or variable in bounds:
                raise ValueError("invalid nonnegative bound")
            bounds.append(variable)
        else:
            raise ValueError("unexpected LP content")
    if section != "End" or objective is None:
        raise ValueError("unfinished LP")
    return objective, rows, bounds


class ModelExportTests(unittest.TestCase):
    def test_signed_fractional_equations_and_reduced_objective(self):
        model = control_model()
        model_api.validate_model(model)
        objective, rows, bounds = independently_read_lp(model_api.to_lp(model))
        point = dict(zip(model["variable_ids"], map(Fraction, (1, 2, 3))))
        self.assertEqual(bounds, model["variable_ids"])
        self.assertEqual(list(rows), model["row_ids"])
        for lhs, rhs in rows.values():
            self.assertEqual(sum(value * point[key] for key, value in lhs.items()), rhs)
        reduced = sum(value * point[key] for key, value in objective.items())
        self.assertEqual(reduced, Fraction(9, 14))
        self.assertEqual(reduced + Fraction(model["objective_offset"]), Fraction(23, 14))
        # The offset is not silently included in the solver expression.
        self.assertEqual(objective, {"x000000": Fraction(-3, 2), "x000002": Fraction(5, 7)})
        self.assertEqual(rows["r000003"], ({}, Fraction(0)))

    def test_digest_is_canonical_and_covers_all_model_data(self):
        model = control_model()
        expected = hashlib.sha256(json.dumps(
            model, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()
        self.assertEqual(model_api.model_digest(model), expected)
        reordered = dict(reversed(list(model.items())))
        reordered["rows"] = [dict(reversed(list(row.items()))) for row in model["rows"]]
        self.assertEqual(model_api.model_digest(reordered), expected)
        mutations = [
            ("name", "other"), ("objective_offset", "-2/3"),
            ("rhs", ["4", "23/6", "0", "0"]),
            ("objective", ["-3/2", "1", "5/7"]),
            ("rows", [{"0": "2", "1": "1"}] + model["rows"][1:]),
        ]
        for key, value in mutations:
            with self.subTest(key=key):
                changed = deepcopy(model)
                changed[key] = value
                self.assertNotEqual(model_api.model_digest(changed), expected)
        self.assertEqual(model_api.to_lp(model), model_api.to_lp(reordered))

    def test_canonical_rationals_and_large_exact_values(self):
        values = [0, -7, Fraction(14, 35), Fraction(-13, 11),
                  (1 << 15000) + 1, Fraction(1, 1 << 15000)]
        for value in values:
            with self.subTest(bits=Fraction(value).numerator.bit_length()):
                encoded = model_api.rational_string(value)
                self.assertEqual(model_api.parse_rational(encoded), value)
                model = control_model()
                model["objective_offset"] = encoded
                self.assertEqual(len(model_api.model_digest(model)), 64)
                self.assertIn("\\ reporting_objective_offset " + encoded, model_api.to_lp(model))
        for value in [True, False, 1.0, "1", None, [1, 2]]:
            with self.subTest(value=value):
                with self.assertRaises(ValueError):
                    model_api.rational_string(value)

    def test_reject_noncanonical_rationals(self):
        for value in [True, 1, 0.5, None, "", " 1", "1 ", "+1", "-0", "00", "01",
                      "1/0", "1/1", "2/4", "0/2", "1/-2", "-0/3", "1/02",
                      "1e3", "NaN", "\u0661", "1\n", "1//2"]:
            with self.subTest(value=value):
                with self.assertRaises(ValueError):
                    model_api.parse_rational(value)

    def test_reject_schema_dimensions_and_duplicate_ids(self):
        mutations = [
            ("schema", "other"), ("name", ""), ("name", "a\nBounds"), ("name", "1bad"),
            ("name", "\u00e9"), ("name", True), ("variable_ids", ["x000000"] * 3),
            ("variable_ids", ["x000000", "x000002", "x000001"]),
            ("variable_ids", [0, 1, 2]), ("row_ids", ["r000000"] * 4),
            ("row_ids", ["r000000"]), ("objective", ["1"]),
            ("rhs", ["1"]), ("rows", []), ("rows", tuple(control_model()["rows"])),
            ("objective_offset", 1), ("objective_offset", False),
        ]
        for key, value in mutations:
            with self.subTest(key=key, value=value):
                model = control_model()
                model[key] = value
                with self.assertRaises(ValueError):
                    model_api.validate_model(model)
        for modify in ("remove", "add"):
            model = control_model()
            if modify == "remove":
                del model["name"]
            else:
                model["extra"] = 0
            with self.assertRaises(ValueError):
                model_api.validate_model(model)

    def test_reject_sparse_zeros_bad_indexes_and_inexact_values(self):
        bad_rows = [
            {"0": "0"}, {"0": "-0"}, {"0": 1}, {"0": 1.0}, {"0": True},
            {0: "1"}, {True: "1"}, {"01": "1"}, {"-1": "1"}, {"3": "1"},
            {"9" * 5000: "1"}, {"1.0": "1"}, {"0": "2/4"}, [], None,
        ]
        for row in bad_rows:
            with self.subTest(row_type=type(row).__name__):
                model = control_model()
                model["rows"][0] = row
                with self.assertRaises(ValueError):
                    model_api.validate_model(model)

    def test_zero_objective_and_zero_dimensional_serialization(self):
        model = control_model()
        model["objective"] = ["0"] * 3
        self.assertEqual(independently_read_lp(model_api.to_lp(model))[0], {})
        empty = {
            "schema": "exact-equality-lp-v1", "name": "empty",
            "variable_ids": [], "row_ids": ["r000000"],
            "rows": [{}], "rhs": ["1"], "objective": [], "objective_offset": "0",
        }
        model_api.validate_model(empty)
        # An inconsistent zero row is preserved; export never silently drops it.
        objective, rows, bounds = independently_read_lp(model_api.to_lp(empty))
        self.assertEqual((objective, rows, bounds), ({}, {"r000000": ({}, Fraction(1))}, []))


class AffineModelTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.builder = model_api._load_sibling("reed_muller_affine_overlap.py")
        # A new LP must not be manufactured from stored primal or dual values.
        with patch.object(cls.builder, "exact_certificate_values",
                          side_effect=AssertionError("solution-dependent builder")):
            cls.model = model_api.build_affine_overlap_model()

    def test_original_quotient_dimensions_and_representative_equation(self):
        model = self.model
        self.assertEqual(model["name"], "rm25_affine_overlap")
        self.assertEqual(len(model["variable_ids"]), 28)
        self.assertEqual(len(model["rows"]), 53)
        self.assertEqual(sum(map(len, model["rows"])), 215)
        self.assertEqual(model["objective"], ["0"] * 27 + ["31"])
        self.assertEqual(model["objective_offset"], "1")
        self.assertEqual(model["rows"][0], {"0": "7", "1": "7", "2": "28", "3": "21", "4": "1"})
        self.assertEqual(model["rhs"][0], "1")

    def test_exported_lp_accepts_an_exact_feasible_primal_dual_pair(self):
        objective, rows, bounds = independently_read_lp(model_api.to_lp(self.model))
        primal, dual = self.builder.exact_certificate_values()
        point = dict(zip(bounds, primal))
        for lhs, rhs in rows.values():
            self.assertEqual(sum(value * point[key] for key, value in lhs.items()), rhs)
        self.assertTrue(all(value >= 0 for value in primal))
        for variable in bounds:
            dual_column = sum(dual[index] * rows[row_id][0].get(variable, 0)
                              for index, row_id in enumerate(self.model["row_ids"]))
            self.assertLessEqual(dual_column, objective.get(variable, 0))
        primal_objective = sum(value * point[key] for key, value in objective.items())
        dual_objective = sum(dual[i] * rows[row_id][1]
                             for i, row_id in enumerate(self.model["row_ids"]))
        self.assertEqual(primal_objective, dual_objective)
        self.assertEqual(primal_objective, Fraction(31, 5))
        self.assertEqual(primal_objective + Fraction(self.model["objective_offset"]), Fraction(36, 5))


if __name__ == "__main__":
    unittest.main()
