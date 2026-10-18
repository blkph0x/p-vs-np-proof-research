"""Independent replay for the random affine isolation theorem."""
from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
import random
import sys


ROOT = Path(__file__).resolve().parent
SOURCE = ROOT / "randomized_isolation.py"
spec = importlib.util.spec_from_file_location("randomized_isolation_review_impl", SOURCE)
module = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = module
spec.loader.exec_module(module)


def direct_hash(rows, x):
    value = 0
    for i, row in enumerate(rows):
        bit = 0
        for j in range(max(row.bit_length(), x.bit_length())):
            bit ^= ((row >> j) & 1) & ((x >> j) & 1)
        value |= bit << i
    return value


def direct_survivors(assignments, rows, target):
    return tuple(x for x in assignments if direct_hash(rows, x) == target)


def main():
    before = hashlib.sha256(SOURCE.read_bytes()).hexdigest()
    uniformity_checks = 0
    n, r = 3, 2
    for difference in range(1, 1 << n):
        counts = [0] * (1 << r)
        for rows in module.all_matrices(n, r):
            counts[direct_hash(rows, difference)] += 1
        if counts != [2 ** (n * r - r)] * (1 << r):
            raise AssertionError((difference, counts))
        uniformity_checks += 1

    probability_sets = 0
    minimum_probability = 1.0
    for n in range(1, 4):
        # Precompute each hash bucket as an assignment bit mask.  This is an
        # independent direct-parity replay, but avoids recomputing the same
        # row products once per solution set.
        buckets_by_rank = {}
        for r in range(1, module.choose_rank(1 << n) + 1):
            buckets = []
            for rows in module.all_matrices(n, r):
                values = [direct_hash(rows, assignment) for assignment in range(1 << n)]
                for target in module.all_targets(r):
                    bucket = sum(1 << assignment for assignment, value in enumerate(values)
                                 if value == target)
                    buckets.append(bucket)
            buckets_by_rank[r] = buckets
        for mask in range(1, 1 << (1 << n)):
            assignments = tuple(x for x in range(1 << n) if mask >> x & 1)
            r = module.choose_rank(len(assignments))
            buckets = buckets_by_rank[r]
            successes = sum((bucket & mask).bit_count() == 1 for bucket in buckets)
            total = len(buckets)
            probability = successes / total
            mu, lower = module.second_moment_bound(len(assignments), r)
            if probability + 1e-15 < lower or probability + 1e-15 < 3 / 16:
                raise AssertionError((n, assignments, probability, lower))
            minimum_probability = min(minimum_probability, probability)
            probability_sets += 1

    rng = random.Random(2026101921)
    seeded_replays = 0
    for n in range(1, 8):
        for _ in range(100):
            assignments = tuple(x for x in range(1 << n) if rng.randrange(2))
            if not assignments:
                assignments = (rng.randrange(1 << n),)
            r = module.choose_rank(len(assignments))
            rows = tuple(rng.randrange(1 << n) for _ in range(r))
            target = rng.randrange(1 << r)
            if module.survivors(assignments, rows, target) != direct_survivors(assignments, rows, target):
                raise AssertionError((n, assignments, rows, target))
            seeded_replays += 1

    after = hashlib.sha256(SOURCE.read_bytes()).hexdigest()
    result = {
        "theorem": "random affine isolation with a second-moment lower bound",
        "uniformity_checks": uniformity_checks,
        "exhaustive_probability_sets": probability_sets,
        "minimum_exhaustive_probability": minimum_probability,
        "seeded_replays": seeded_replays,
        "source_sha256": after,
        "source_unchanged_during_run": before == after,
        "all_checks_passed": (uniformity_checks == 7 and probability_sets == 273
                              and seeded_replays == 700 and before == after
                              and minimum_probability >= 3 / 16 - 1e-15),
    }
    (ROOT / "RANDOMIZED_ISOLATION_REVIEW.json").write_text(
        json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))
    return 0 if result["all_checks_passed"] else 1


if __name__ == "__main__":
    sys.exit(main())
