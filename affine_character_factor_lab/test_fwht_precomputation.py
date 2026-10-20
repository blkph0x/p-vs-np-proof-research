"""Exact FWHT/direct regression tests and an optional paired finite benchmark.

Run all local tests with ``python -m unittest discover -p "test_*.py"``.
Run the benchmark with ``python test_fwht_precomputation.py --benchmark``.
The latter prints JSON and writes no artifacts.  Its direct baseline disables
only the new selector; _block_transform is the original direct implementation.
Timings are measurements of these named controls, not a general speed claim.
"""

import copy
from contextlib import nullcontext
from fractions import Fraction
import hashlib
import itertools
import json
from pathlib import Path
import random
import statistics
import sys
import time
import unittest
from unittest.mock import patch

import engine


def block(identifier, scope, table):
    return {"id": "b-" + identifier, "scope": list(scope),
            "factors": [{"id": "f-" + identifier, "scope": list(scope),
                         "table": list(table)}]}


def original_sum(n, blocks, rows, rhs):
    """Enumerate original global words; no producer mask/table helper."""
    total = 0
    for word in range(1 << n):
        bits = [(word >> i) & 1 for i in range(n)]
        if any(sum(bits[i] for i in range(n) if row & (1 << i)) % 2 != bit
               for row, bit in zip(rows, rhs)):
            continue
        product = 1
        for owned in blocks:
            for factor in owned["factors"]:
                index = sum(bits[var] * (2 ** j)
                            for j, var in enumerate(factor["scope"]))
                product *= factor["table"][index]
        total += product
    return total


def direct_result(request, caps=None):
    with patch.object(engine, "_use_precomputed_spectrum", return_value=False):
        return engine.solve(*request, caps=caps)


def without_stats(result):
    return {key: value for key, value in result.items() if key != "stats"}


def mixed_request(seed):
    rng = random.Random(seed)
    n = rng.randrange(9)
    variables = list(range(n))
    rng.shuffle(variables)
    blocks = []
    while variables:
        width = rng.randrange(1, min(4, len(variables)) + 1)
        scope, variables = variables[:width], variables[width:]
        factors = []
        for j in range(rng.randrange(1, 4)):
            local_scope = rng.sample(scope, rng.randrange(width + 1))
            factors.append({
                "id": f"f{len(blocks)}-{j}", "scope": local_scope,
                "table": [rng.randrange(-3, 4)
                          for _ in range(1 << len(local_scope))]})
        blocks.append({"id": f"b{len(blocks)}", "scope": scope, "factors": factors})
    if seed % 3 == 0:
        blocks.append(block("scalar", [], [rng.randrange(-2, 3)]))
    rows = [rng.randrange(1 << n) for _ in range(rng.randrange(n + 3))]
    rhs = [rng.randrange(2) for _ in rows]
    return n, blocks, rows, rhs


class FWHTPrecomputationTests(unittest.TestCase):
    def check_request(self, request, exhaustive=True):
        fast = engine.solve(*request)
        direct = direct_result(request)
        self.assertEqual(fast["status"], "EXACT", fast)
        self.assertEqual(without_stats(fast), without_stats(direct))
        self.assertTrue(engine.verify(*request, fast)["valid"])
        if exhaustive:
            self.assertEqual(fast["value"], [original_sum(*request), 1])
        return fast, direct

    def test_all_two_bit_signed_tables_all_full_rhs(self):
        # All 81 ternary-valued tables, including zero and signed cancellation.
        # A reordered scope also checks that LSB tensor order is not variable ID.
        for table in itertools.product((-1, 0, 1), repeat=4):
            blocks = [block("main", [2, 0], table), block("other", [1], [-2, 1])]
            for rhs in itertools.product((0, 1), repeat=3):
                fast, direct = self.check_request((3, blocks, [1, 2, 4], rhs))
                self.assertLess(fast["stats"]["work"], direct["stats"]["work"])

    def test_seeded_scopes_repeated_factors_and_affine_rows(self):
        for seed in range(180):
            self.check_request(mixed_request(seed))
        request = (4, [
            {"id": "a", "scope": [3, 1], "factors": [
                {"id": "a0", "scope": [1, 3], "table": [0, -2, 3, 1]},
                {"id": "a1", "scope": [1, 3], "table": [0, -2, 3, 1]}]},
            block("b", [2, 0], [1, -1, -2, 2])],
            [5, 3, 12, 10], [1, 0, 1, 0])
        self.check_request(request)

    def test_empty_scalar_zero_and_free_variable_controls(self):
        for request in [
            (0, [], [], []),
            (0, [block("s", [], [-3])], [], []),
            (0, [block("s", [], [0])], [], []),
            (0, [], [0], [1]),
            (4, [block("z", [0, 1], [0] * 4),
                 block("s", [2, 3], [-2, 1, 0, 3])], [1, 2, 4, 8], [1] * 4),
            (3, [block("free", [0, 1, 2], [1] * 8)], [], []),
        ]:
            self.check_request(request)

    def test_strategy_uses_dimensions_only_tiny_rank_and_ties_direct(self):
        for width in range(8):
            owned = block("x", range(width), [0] * (1 << width))
            for characters in (1, 2):
                self.assertFalse(engine._use_precomputed_spectrum(owned, characters))
        # C=4,k=2 ties at 16 charged units and must stay direct.
        request = (2, [block("x", [0, 1], [3, -2, 1, 0])], [1, 2], [0, 1])
        with patch.object(engine, "_block_spectrum", side_effect=AssertionError):
            fast = engine.solve(*request)
        self.assertEqual(fast["stats"]["work"], 16)
        self.assertEqual(fast["stats"]["local_evaluations"], 16)
        # C=8,k=2 charges 4 evaluations+8 butterfly operations+8 lookups.
        request = (3, [block("x", [0, 1], [0] * 4), block("y", [2], [1, 1])],
                   [1, 2, 4], [0, 0, 0])
        fast = engine.solve(*request)
        self.assertEqual(fast["stats"]["work"], 20 + 12)
        self.assertEqual(fast["stats"]["local_evaluations"], 4 + 2)

    def test_checker_is_direct_and_ignores_producer_work(self):
        request = engine.paired_or_blocks(7, "connected")
        fast = engine.solve(*request)
        fast["stats"] = {"work": -1}
        with patch.object(engine, "_block_spectrum", side_effect=AssertionError), \
                patch.object(engine, "_spectrum_lookup", side_effect=AssertionError), \
                patch.object(engine, "_use_precomputed_spectrum", side_effect=AssertionError):
            checked = engine.verify(*request, fast)
        self.assertTrue(checked["valid"], checked)

    def test_work_boundary_and_independent_verification_budget(self):
        request = engine.paired_or_blocks(8, "connected")
        fast, direct = self.check_request(request, exhaustive=False)
        fast_work = fast["stats"]["work"]
        direct_work = direct["stats"]["work"]
        self.assertLess(fast_work, direct_work)
        at_limit = engine.solve(*request, caps={"max_work": fast_work})
        self.assertEqual(at_limit["status"], "EXACT")
        capped = engine.solve(*request, caps={"max_work": fast_work - 1})
        self.assertEqual(capped["status"], "UNKNOWN")
        self.assertNotIn("value", capped)
        self.assertNotIn("characters", capped)
        self.assertEqual(engine.verify(*request, at_limit,
                                      caps={"max_work": fast_work})["status"], "UNKNOWN")
        self.assertTrue(engine.verify(*request, at_limit,
                                      caps={"max_work": direct_work})["valid"])
        component = engine.solve_components(*request, caps={"max_work": fast_work})
        self.assertEqual(component["status"], "EXACT")
        self.assertTrue(engine.verify_components(
            *request, component, caps={"max_work": direct_work})["valid"])

    def test_precomputation_interruption_and_bit_cap(self):
        request = (3, [block("x", [0, 1], [1, 2, 3, 4]),
                       block("y", [2], [1, -1])], [1, 2, 4], [0, 0, 0])
        for cap in (0, 3, 5):
            result = engine.solve(*request, caps={"max_work": cap})
            self.assertEqual(result["status"], "UNKNOWN")
            self.assertNotIn("value", result)
        self.assertEqual(engine.solve(*request, caps={"max_work": 3})
                         ["stats"]["local_evaluations"], 3)
        self.assertEqual(engine.solve(*request, caps={"max_work": 5})
                         ["stats"]["local_evaluations"], 4)
        self.assertEqual(engine.solve(*request, caps={"max_integer_bits": 2})
                         ["status"], "UNKNOWN")
        for caps in ({"max_rank": 2}, {"max_characters": 4},
                     {"max_block_variables": 1}):
            result = engine.solve(*request, caps=caps)
            self.assertEqual(result["status"], "UNKNOWN")
            self.assertNotIn("value", result)

    def test_unused_spectrum_bit_cap_can_differ_from_direct(self):
        # Explicit cap limitation: all requested masks of x are zero, but its
        # full spectrum has an unused coefficient of magnitude 32.  A tiny
        # bit cap can reject precomputation even though direct sums cancel.
        blocks = [block("x", [0, 1, 2], [-4, 4] * 4)]
        blocks += [block(str(i), [i], [1, 1]) for i in range(3, 7)]
        request = (7, blocks, [1 << i for i in range(3, 7)], [0] * 4)
        self.assertEqual(direct_result(request, {"max_integer_bits": 3})
                         ["status"], "EXACT")
        fast = engine.solve(*request, caps={"max_integer_bits": 3})
        self.assertEqual(fast["status"], "UNKNOWN")
        self.assertNotIn("value", fast)
        self.check_request(request)

    def test_certificate_and_original_request_mutations(self):
        request = engine.paired_or_blocks(5, "connected")
        result = engine.solve(*request)
        for location in ("mask", "value", "block_id"):
            bad = copy.deepcopy(result)
            if location == "block_id":
                bad["characters"][1]["local"][0][location] = "wrong"
            else:
                bad["characters"][1]["local"][0][location] += 1
            self.assertEqual(engine.verify(*request, bad)["status"], "INVALID")
        for key in ("sign", "product", "term", "character"):
            bad = copy.deepcopy(result)
            bad["characters"][1][key] += 1
            self.assertEqual(engine.verify(*request, bad)["status"], "INVALID")
        changed = copy.deepcopy(request)
        changed[1][0]["factors"][0]["table"][0] = -1
        self.assertEqual(engine.verify(*changed, result)["status"], "INVALID")
        bad = copy.deepcopy(result)
        bad["characters"].pop()
        self.assertEqual(engine.verify(*request, bad)["status"], "INVALID")

    def test_integer_only_contract_rejects_rationals_floats_and_bool(self):
        # Do not silently broaden the original integer-table API.
        for value in (Fraction(1, 2), Fraction(2, 1), 0.5, True):
            with self.assertRaises(ValueError):
                engine.solve(1, [block("x", [0], [value, 1])], [1], [0])
        for caps in ({"max_work": True}, {"max_work": -1}, {"unknown": 1}):
            with self.assertRaises(ValueError):
                engine.solve(0, [], [], [], caps=caps)


def benchmark(repeats=5):
    """Paired timings on fixed original inputs, with full proof equality."""
    cases = [
        ("tiny-rank-direct", engine.paired_or_blocks(64, "global")),
        ("connected-rank-10", engine.paired_or_blocks(10, "connected")),
        ("single-six-bit-block", (6, [block("dense", list(reversed(range(6))),
             [((i * 7) % 11) - 5 for i in range(64)])],
             [1 << i for i in range(6)], [1, 0, 1, 0, 1, 0])),
    ]
    rows = []
    for name, request in cases:
        optimized = engine.solve(*request)
        original = direct_result(request)
        if without_stats(optimized) != without_stats(original):
            raise AssertionError("baseline certificate disagreement")
        checked = engine.verify(*request, optimized)
        if not checked["valid"]:
            raise AssertionError(checked)
        timings = {"direct": [], "adaptive": []}
        # Alternate execution order to reduce a systematic first-run bias.
        for repeat in range(repeats):
            order = ("direct", "adaptive") if repeat % 2 else ("adaptive", "direct")
            for strategy in order:
                # Patch installation is outside the timed region on both paths.
                context = (patch.object(engine, "_use_precomputed_spectrum",
                                        new=lambda owned, count: False)
                           if strategy == "direct" else nullcontext())
                with context:
                    start = time.perf_counter()
                    result = engine.solve(*request)
                    timings[strategy].append(time.perf_counter() - start)
                if result["value"] != optimized["value"]:
                    raise AssertionError("timed result changed")
        rows.append({
            "name": name, "original_request": {
                "n": request[0], "blocks": request[1],
                "equations": request[2], "rhs": request[3]},
            "source_hash": optimized["source_hash"], "value": optimized["value"],
            "direct_stats": original["stats"], "adaptive_stats": optimized["stats"],
            "direct_seconds": timings["direct"], "adaptive_seconds": timings["adaptive"],
            "direct_median_seconds": statistics.median(timings["direct"]),
            "adaptive_median_seconds": statistics.median(timings["adaptive"]),
            "certificate_equal_except_stats": True, "verification": checked,
        })
    return {"kind": "paired-fwht-local-benchmark-v1", "repeats": repeats,
            "scope": "Finite named controls; timing is not a universal speed claim.",
            "baseline": "Current solve with the selector disabled and its unchanged "
                        "original direct local-sum path; not a separate historical binary.",
            "source_sha256": {
                path.name: hashlib.sha256(path.read_bytes()).hexdigest()
                for path in (Path(engine.__file__), Path(__file__))},
            "cases": rows}


if __name__ == "__main__":
    if sys.argv[1:] == ["--benchmark"]:
        print(json.dumps(benchmark(), indent=2))
    else:
        unittest.main()
