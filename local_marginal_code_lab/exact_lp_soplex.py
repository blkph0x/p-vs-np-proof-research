"""Read SoPlex 8.1 rational candidates; independent verification decides truth."""
from __future__ import annotations

from fractions import Fraction
import re

from exact_lp_model import model_digest, parse_rational, rational_string, validate_model


def _lines(text: str) -> list[str]:
    if type(text) is not str:
        raise ValueError("solver output must be text")
    return [line.strip() for line in text.splitlines() if line.strip()]


def _entries(lines: list[str], names: list[str]) -> list[str]:
    result = ["0"] * len(names)
    positions = {name: index for index, name in enumerate(names)}
    seen = set()
    for line in lines:
        fields = line.split()
        if len(fields) != 2 or fields[0] not in positions:
            raise ValueError("unknown or malformed solver entry")
        name, value = fields
        if name in seen:
            raise ValueError("duplicate solver entry")
        seen.add(name)
        if parse_rational(value) == 0:
            raise ValueError("sparse solver entries must be nonzero")
        result[positions[name]] = value
    return result


def parse_primal(text: str, names: list[str]) -> list[str]:
    lines = _lines(text)
    if len(lines) < 2 or lines[0] != "Primal solution (name, value):":
        raise ValueError("missing rational primal header")
    footer = re.fullmatch(
        r"All other variables are zero\. Solution has ([0-9]+) nonzero entries\.", lines[-1])
    if footer is None or int(footer.group(1)) != len(lines) - 2:
        raise ValueError("missing or inconsistent primal completeness footer")
    return _entries(lines[1:-1], names)


def parse_dual(text: str, row_names: list[str], variable_names: list[str]) -> list[str]:
    lines = _lines(text)
    if not lines or lines[0] != "Dual solution (name, value):":
        raise ValueError("missing rational dual header")
    separator = "All other dual values are zero."
    if lines.count(separator) != 1:
        raise ValueError("missing or repeated dual completeness footer")
    split = lines.index(separator)
    dual = _entries(lines[1:split], row_names)
    remaining = lines[split + 1:]
    if (len(remaining) < 2
            or remaining[0] != "Reduced costs (name, value):"
            or remaining[-1] != "All other reduced costs are zero."):
        raise ValueError("missing reduced-cost section or footer")
    # Syntax-check this supplied section; the checker recomputes reduced costs.
    _entries(remaining[1:-1], variable_names)
    return dual


def candidate_from_output(model: dict, primal_text: str, dual_text: str,
                          stdout: str, returncode: int) -> dict:
    validate_model(model)
    if type(returncode) is not int or returncode != 0:
        raise ValueError("solver did not exit successfully")
    statuses = re.findall(r"^SoPlex status\s*:\s*(.+)$", stdout, flags=re.MULTILINE)
    if not statuses or any(status.strip() != "problem is solved [optimal]" for status in statuses):
        raise ValueError("solver did not report an optimal rational candidate")
    primal = parse_primal(primal_text, model["variable_ids"])
    dual = parse_dual(dual_text, model["row_ids"], model["variable_ids"])
    value = sum((parse_rational(c) * parse_rational(x)
                 for c, x in zip(model["objective"], primal)), Fraction())
    return {
        "schema": "exact-equality-lp-solution-v1",
        "model_sha256": model_digest(model),
        "primal": primal,
        "dual": dual,
        "claimed_objective": rational_string(value),
    }
