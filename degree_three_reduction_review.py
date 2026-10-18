"""Independent replay for the degree-three affine-decoding theorem."""
from __future__ import annotations

import hashlib
import importlib.util
import json
from itertools import combinations, product
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parent
SOURCE = ROOT / "degree_three_barrier.py"
spec = importlib.util.spec_from_file_location("degree_three_barrier_review", SOURCE)
module = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = module
spec.loader.exec_module(module)


def check_instance(instance):
    for selection in range(1 << len(instance.columns)):
        exact = module.is_exact_cover(instance, selection)
        encoded = module.satisfies_coset_bound(instance, selection)
        if exact != encoded or (module.decode_cover(instance, selection) is not None) != exact:
            return False
    return True


def main():
    possible = tuple((a, 2 + b, 4 + c) for a, b, c in product(range(2), repeat=3))
    families = selections = positive = 0
    for family_mask in range(1 << len(possible)):
        triples = [triple for i, triple in enumerate(possible) if family_mask >> i & 1]
        instance = module.encode_exact_cover(6, triples)
        if not check_instance(instance):
            raise AssertionError(("tripartite family", triples))
        families += 1
        selections += 1 << len(triples)
        positive += any(module.is_exact_cover(instance, selection)
                        for selection in range(1 << len(triples)))

    possible6 = tuple(combinations(range(6), 3))
    small_families = 0
    for size in range(4):
        for triples in combinations(possible6, size):
            instance = module.encode_exact_cover(6, triples)
            if not check_instance(instance):
                raise AssertionError(("six-element family", triples))
            small_families += 1

    malformed_rejected = 0
    for universe_size in (-3, 1, 4, True, 6.0):
        try:
            module.encode_exact_cover(universe_size, ())
        except ValueError:
            malformed_rejected += 1
    for triples in (((0, 1),), ((0, 1, 1),), ((0, 1, 6),),
                    ((0, 1, -1),), ((0, 1, True),), ((0, 1, 2.0),)):
        try:
            module.encode_exact_cover(6, triples)
        except ValueError:
            malformed_rejected += 1

    counterexample = module.naive_homogenization_counterexample()
    homogenization_warning_verified = (
        not counterexample["has_exact_cover"]
        and counterexample["kernel_syndrome"] == 0
        and counterexample["kernel_weight"] <= counterexample["naive_homogeneous_threshold"]
        and counterexample["appended_target_weight"] > counterexample["naive_homogeneous_threshold"]
    )

    result = {
        "theorem": "X3C -> binary affine decoding with column weight three",
        "tripartite_families": families,
        "tripartite_selections": selections,
        "tripartite_positive_families": positive,
        "six_element_families_at_most_three_sets": small_families,
        "malformed_cases_rejected": malformed_rejected,
        "naive_homogenization_warning_verified": homogenization_warning_verified,
        "source_sha256": hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
        "all_checks_passed": (families == 256 and selections == 6561 and positive == 175 and
                              small_families == 1351 and malformed_rejected == 11 and
                              homogenization_warning_verified),
    }
    (ROOT / "DEGREE_THREE_REDUCTION_REVIEW.json").write_text(
        json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))
    return 0 if result["all_checks_passed"] else 1


if __name__ == "__main__":
    sys.exit(main())
