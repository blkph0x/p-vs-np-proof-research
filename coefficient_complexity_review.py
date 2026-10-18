"""Independent replay of the exact-coefficient X3C reduction."""
from __future__ import annotations

import hashlib
import importlib.util
import json
from itertools import combinations, product
from pathlib import Path
import random
import sys


ROOT = Path(__file__).resolve().parent
SOURCE = ROOT / "coefficient_complexity_barrier.py"
spec = importlib.util.spec_from_file_location("coefficient_complexity_barrier_review", SOURCE)
module = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = module
spec.loader.exec_module(module)


def independent_exact_cover(instance, selection):
    counts = [0] * instance.universe_size
    for index, triple in enumerate(instance.triples):
        if (selection >> index) & 1:
            for element in triple:
                counts[element] += 1
    return all(value == 1 for value in counts)


def independent_coefficient(instance):
    # Work in base-B digit vectors instead of using encoded integer exponents.
    count = 0
    for selection in range(1 << len(instance.triples)):
        digits = [0] * instance.universe_size
        for index, triple in enumerate(instance.triples):
            if (selection >> index) & 1:
                for element in triple:
                    digits[element] += 1
        if all(value == 1 for value in digits):
            count += 1
    return count


def check(instance):
    expected = sum(independent_exact_cover(instance, selection)
                   for selection in range(1 << len(instance.triples)))
    return (expected == independent_coefficient(instance) ==
            module.encoded_coefficient(instance))


def main():
    before_source = hashlib.sha256(SOURCE.read_bytes()).hexdigest()
    possible = tuple((a, 2 + b, 4 + c) for a, b, c in product(range(2), repeat=3))
    families = selections = positive = 0
    for mask in range(1 << len(possible)):
        triples = [triple for i, triple in enumerate(possible) if mask >> i & 1]
        instance = module.encode_x3c(6, triples)
        if not check(instance):
            raise AssertionError(("tripartite family", triples))
        families += 1
        selections += 1 << len(triples)
        positive += independent_coefficient(instance) > 0

    rng = random.Random(2026101919)
    random_cases = 0
    possible6 = tuple(combinations(range(6), 3))
    for _ in range(400):
        triples = tuple(rng.sample(possible6, rng.randrange(0, 7)))
        if not check(module.encode_x3c(6, triples)):
            raise AssertionError(("seeded family", triples))
        random_cases += 1

    malformed = 0
    for universe, triples in [(-3, ()), (1, ()), (4, ()), (True, ()),
                              (6, ((0, 1),)), (6, ((0, 1, 6),)),
                              (6, ((0, 1, 1),))]:
        try:
            module.encode_x3c(universe, triples)
        except ValueError:
            malformed += 1

    after_source = hashlib.sha256(SOURCE.read_bytes()).hexdigest()
    result = {
        "theorem": "parsimonious X3C reduction to a binary-exponent coefficient",
        "tripartite_families": families,
        "tripartite_selections": selections,
        "tripartite_positive_families": positive,
        "seeded_general_families": random_cases,
        "malformed_cases_rejected": malformed,
        "source_sha256": after_source,
        "source_unchanged_during_run": before_source == after_source,
        "all_checks_passed": (families == 256 and selections == 6561 and positive == 175
                              and random_cases == 400 and malformed == 7
                              and before_source == after_source),
    }
    (ROOT / "COEFFICIENT_COMPLEXITY_REVIEW.json").write_text(
        json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))
    return 0 if result["all_checks_passed"] else 1


if __name__ == "__main__":
    sys.exit(main())
