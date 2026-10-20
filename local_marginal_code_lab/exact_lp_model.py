"""Canonical equality LPs for reproducible rational RM discovery.

The mathematical solver problem is min c*x, subject to A*x=b and x>=0.
``objective_offset`` is reporting metadata: total pinned weight is the
reduced solver objective plus this offset.  It is not put in the LP objective.

Builders use the original model construction code, never a saved solution.
This module validates serialization and exports a model; it does not establish
the RM quotient theorem or verify a solver's primal/dual certificate.
"""
from __future__ import annotations

from fractions import Fraction
import hashlib
import importlib.util
import json
import math
from pathlib import Path
import re
import sys


SCHEMA = "exact-equality-lp-v1"
FIELDS = {
    "schema", "name", "variable_ids", "row_ids", "rows", "rhs",
    "objective", "objective_offset",
}
_NAME = re.compile(r"[A-Za-z][A-Za-z0-9_]*", re.ASCII)
_RATIONAL = re.compile(r"-?(?:0|[1-9][0-9]*)(?:/[1-9][0-9]*)?", re.ASCII)


def _decimal_integer(digits: str) -> int:
    """Read unsigned decimal digits without changing Python's global guard."""
    number = 0
    for start in range(0, len(digits), 9):
        chunk = digits[start:start + 9]
        number = number * (10 ** len(chunk)) + int(chunk)
    return number


def _integer_string(number: int) -> str:
    """Format an integer without the interpreter's decimal-digit limit."""
    if number == 0:
        return "0"
    sign = "-" if number < 0 else ""
    number = abs(number)
    pieces = []
    while number:
        number, remainder = divmod(number, 1_000_000_000)
        pieces.append(remainder)
    return sign + str(pieces[-1]) + "".join(f"{part:09d}" for part in reversed(pieces[:-1]))


def rational_string(value: int | Fraction) -> str:
    """Return a reduced rational string; reject bool, floats and other types."""
    if type(value) not in (int, Fraction):
        raise ValueError("rational value must be an exact integer or Fraction")
    value = Fraction(value)
    numerator = _integer_string(value.numerator)
    if value.denominator == 1:
        return numerator
    return numerator + "/" + _integer_string(value.denominator)


def parse_rational(value: str) -> Fraction:
    """Parse only canonical strings: integers or coprime p/q with q>1."""
    if type(value) is not str or _RATIONAL.fullmatch(value) is None:
        raise ValueError("expected a canonical rational string")
    numerator_text, separator, denominator_text = value.partition("/")
    negative = numerator_text.startswith("-")
    numerator = _decimal_integer(numerator_text[1:] if negative else numerator_text)
    if negative and numerator == 0:
        raise ValueError("negative zero is not canonical")
    denominator = _decimal_integer(denominator_text) if separator else 1
    if separator and (denominator == 1 or math.gcd(numerator, denominator) != 1):
        raise ValueError("rational string is not in lowest canonical terms")
    return Fraction(-numerator if negative else numerator, denominator)


def validate_model(model: dict) -> None:
    """Reject malformed/noncanonical models without coercing input types.

    Zero rows are represented by empty dictionaries.  Stored coefficients
    must be nonzero; redundant equalities are retained.  Validation is linear
    in the serialized entries apart from exact integer parsing and gcd work.
    No wall-clock, allocation or arithmetic-bit cap is implied.
    """
    if type(model) is not dict or set(model) != FIELDS:
        raise ValueError("model must contain exactly the equality-LP schema fields")
    if type(model["schema"]) is not str or model["schema"] != SCHEMA:
        raise ValueError("unsupported model schema")
    if type(model["name"]) is not str or _NAME.fullmatch(model["name"]) is None:
        raise ValueError("model name must be an ASCII letter followed by letters, digits or underscores")
    for key in ("variable_ids", "row_ids", "rows", "rhs", "objective"):
        if type(model[key]) is not list:
            raise ValueError(f"{key} must be a list")
    n = len(model["variable_ids"])
    m = len(model["row_ids"])
    if any(type(value) is not str for value in model["variable_ids"]) or model["variable_ids"] != [f"x{index:06d}" for index in range(n)]:
        raise ValueError("variable IDs must be consecutive canonical x IDs")
    if any(type(value) is not str for value in model["row_ids"]) or model["row_ids"] != [f"r{index:06d}" for index in range(m)]:
        raise ValueError("row IDs must be consecutive canonical r IDs")
    if len(model["objective"]) != n or len(model["rows"]) != m or len(model["rhs"]) != m:
        raise ValueError("model dimensions disagree")
    for row in model["rows"]:
        if type(row) is not dict:
            raise ValueError("each sparse row must be a dictionary")
        for index_text, coefficient in row.items():
            if type(index_text) is not str or re.fullmatch(r"0|[1-9][0-9]*", index_text, re.ASCII) is None:
                raise ValueError("column index must be a canonical decimal string")
            # Reject impossible indices before converting arbitrarily long text.
            if len(index_text) > len(str(n)):
                raise ValueError("column index out of range")
            index = int(index_text)
            if index >= n:
                raise ValueError("column index out of range")
            if parse_rational(coefficient) == 0:
                raise ValueError("explicit zero sparse coefficients are not canonical")
    for value in model["rhs"] + model["objective"] + [model["objective_offset"]]:
        parse_rational(value)


def model_digest(model: dict) -> str:
    """Hash the complete canonical model, including its reporting offset."""
    validate_model(model)
    encoded = json.dumps(model, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _linear_expression(entries, variable_ids) -> str:
    terms = []
    for index, value in entries:
        if value == 0:
            continue
        magnitude = rational_string(abs(value))
        if not terms:
            terms.append(("- " if value < 0 else "") + magnitude + " " + variable_ids[index])
        else:
            terms.append((" - " if value < 0 else " + ") + magnitude + " " + variable_ids[index])
    if terms:
        return "".join(terms)
    return "0 " + variable_ids[0] if variable_ids else "0"


def to_lp(model: dict) -> str:
    """Export stable SoPlex LP text with exact rational literals.

    All variables have explicit zero lower bounds and no upper bound.
    Objective offsets are intentionally excluded from the solver expression.
    """
    validate_model(model)
    variables = model["variable_ids"]
    objective = _linear_expression(
        ((i, parse_rational(value)) for i, value in enumerate(model["objective"])), variables)
    lines = [
        "\\ " + SCHEMA + " " + model["name"],
        "\\ model_sha256 " + model_digest(model),
        "\\ reporting_objective_offset " + model["objective_offset"],
        "Minimize", " obj: " + objective, "Subject To",
    ]
    for row_id, row, rhs in zip(model["row_ids"], model["rows"], model["rhs"]):
        expression = _linear_expression(
            ((int(index), parse_rational(value))
             for index, value in sorted(row.items(), key=lambda item: int(item[0]))), variables)
        lines.append(" " + row_id + ": " + expression + " = " + rhs)
    lines.append("Bounds")
    lines.extend(" 0 <= " + variable for variable in variables)
    lines.extend(["End", ""])
    return "\n".join(lines)


def _load_sibling(filename: str):
    """Avoid accidentally importing a same-named module from another lab."""
    path = Path(__file__).resolve().with_name(filename)
    module_name = "_exact_lp_model_" + path.stem
    if module_name in sys.modules:
        module = sys.modules[module_name]
        if Path(module.__file__).resolve() != path:
            raise RuntimeError("model-builder module path collision")
        return module
    spec = importlib.util.spec_from_file_location(module_name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load the model builder")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    try:
        spec.loader.exec_module(module)
    except BaseException:
        del sys.modules[module_name]
        raise
    return module


def _from_matrix(name, matrix, rhs, objective) -> dict:
    n, m = len(objective), len(matrix)
    result = {
        "schema": SCHEMA, "name": name,
        "variable_ids": [f"x{index:06d}" for index in range(n)],
        "row_ids": [f"r{index:06d}" for index in range(m)],
        "rows": [
            {str(index): rational_string(value)
             for index, value in sorted(((int(i), v) for i, v in row.items()))
             if value != 0}
            for row in matrix
        ],
        "rhs": [rational_string(value) for value in rhs],
        "objective": [rational_string(value) for value in objective],
        "objective_offset": "1",
    }
    validate_model(result)
    return result


def build_affine_overlap_model() -> dict:
    """Build the 28-variable, 53-equality affine-scope quotient from source."""
    source = _load_sibling("reed_muller_affine_overlap.py").build_quotient()
    return _from_matrix("rm25_affine_overlap", source["matrix"], source["rhs"], source["objective"])


def build_full_level8_model() -> dict:
    """Build the full 2,174-variable quotient; construction is intentionally explicit."""
    source = _load_sibling("reed_muller_full_level8.py").build_model()
    return _from_matrix("rm25_full_level8", source["matrix"], source["rhs"], source["objective"])
