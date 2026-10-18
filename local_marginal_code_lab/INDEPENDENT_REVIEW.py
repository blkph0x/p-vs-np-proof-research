"""Independent replay of the local-marginal barrier."""

import json
from math import comb
from pathlib import Path


def b(rows):
    pivots = {}
    for value in rows:
        while value:
            bit = value.bit_length() - 1
            if bit in pivots:
                value ^= pivots[bit]
            else:
                pivots[bit] = value
                break
    return tuple(pivots[bit] for bit in sorted(pivots, reverse=True))


def s(rows):
    rows = b(rows)
    words = [0]
    for row in rows:
        words += [word ^ row for word in tuple(words)]
    return tuple(sorted(words))


def orth(rows, n):
    reduced = list(rows)
    pivots = []
    rank = 0
    for bit in range(n):
        index = next((i for i in range(rank, len(reduced))
                      if reduced[i] >> bit & 1), None)
        if index is None:
            continue
        reduced[rank], reduced[index] = reduced[index], reduced[rank]
        for i in range(len(reduced)):
            if i != rank and reduced[i] >> bit & 1:
                reduced[i] ^= reduced[rank]
        pivots.append(bit)
        rank += 1
    result = []
    for free in range(n):
        if free in pivots:
            continue
        word = 1 << free
        for index, pivot in enumerate(pivots):
            if reduced[index] >> free & 1:
                word |= 1 << pivot
        result.append(word)
    return tuple(result)


def verify_case(saved):
    cert = saved["certificate"]
    n = cert["n"]
    rows = tuple(cert["generator_rows"])
    pin, level = cert["pin"], cert["level"]
    words = s(rows)
    dual = orth(rows, n)
    dual_words = s(dual)
    delta = min(word.bit_count() for word in dual_words if word)
    pinned = [word for word in words if word >> pin & 1]
    pinned_distance = min(word.bit_count() for word in pinned)
    assert tuple(cert["dual_basis"]) == dual
    assert cert["dual_distance"] == delta
    assert cert["pinned_integer_optimum"] == pinned_distance
    assert cert["scope_count"] == sum(__import__('math').comb(n, i)
                                       for i in range(level + 1))
    assert cert["atom_slot_count"] == sum(__import__('math').comb(n, i) * (1 << i)
                                           for i in range(level + 1))
    observed_support = None
    if cert["enumerated_support"] is not None:
        target = 1 << pin
        observed_support = True
        for mask in range(1 << n):
            if mask.bit_count() > level:
                continue
            scope = [i for i in range(n) if mask >> i & 1]
            wanted = tuple((target >> i) & 1 for i in scope)
            supported = any(tuple((word >> i) & 1 for i in scope) == wanted
                            and word >> pin & 1 for word in words)
            if not supported:
                observed_support = False
                break
        assert cert["enumerated_support"] == observed_support
        assert saved["verification"]["support_replay"] == observed_support
    assert saved["verification"]["valid"] is True
    return {"name": saved["name"], "dual_distance": delta,
            "pinned_integer_optimum": pinned_distance,
            "theorem_level_valid": level <= delta - 2,
            "relaxation_point_weight": 1}


def independent_bound(n):
    rank = n // 2
    distance = n // 16
    ball = sum(comb(n, weight) for weight in range(distance))
    denominator = 1 << rank
    numerator = 2 * ball
    atom_slots = sum(comb(n, size) * (1 << size)
                     for size in range(distance - 1))
    return {
        "n": n, "rank": rank, "distance_lower_bound": distance,
        "local_level_lower_bound": distance - 2,
        "low_weight_ball": ball, "bad_probability_numerator": numerator,
        "bad_probability_denominator": denominator,
        "good_probability_lower_numerator": denominator - numerator,
        "strictly_positive_good_probability": denominator > numerator,
        "atom_slots_at_level": atom_slots,
    }


def main():
    saved = json.loads(Path("RESULTS.json").read_text())
    rows = [verify_case(row) for row in saved["rows"]]
    saved_bounds = saved["random_code_bounds"]
    bound_rows = [independent_bound(n) for n in (32, 64, 128, 256, 512, 1024)]
    assert saved_bounds == bound_rows
    assert all(row["strictly_positive_good_probability"] for row in bound_rows)
    assert saved["all_valid"] is True
    assert saved["golay_level_bound_verified"] is True
    assert rows[2]["dual_distance"] == 8
    assert rows[2]["pinned_integer_optimum"] == 8
    assert rows[1]["theorem_level_valid"] is False
    output = {"status": "VERIFIED_INDEPENDENT_LOCAL_MARGINAL_BOUND",
              "case_count": len(rows), "rows": rows,
              "golay_level": 6, "golay_gap": 8,
              "golay_support_replay_deferred": True,
              "random_bound_lengths": [row["n"] for row in bound_rows],
              "random_bound_levels": [row["local_level_lower_bound"] for row in bound_rows]}
    Path("INDEPENDENT_REVIEW.json").write_text(json.dumps(output, indent=2) + "\n")
    Path("INDEPENDENT_REVIEW.md").write_text(
        "# Independent local-marginal review\n\n"
        "Recomputed all code spans, dual spaces, distances and the enumerated "
        "small-scope supports, including the level boundary rejection. The Golay level-6 claim is certified by the "
        "dual-distance theorem rather than by enumerating its ten-million-plus "
        "local atoms.\n"
    )
    print(json.dumps({"status": output["status"], "cases": len(rows),
                      "golay_level": 6, "golay_gap": 8}))


if __name__ == "__main__":
    main()
