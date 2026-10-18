"""Independent arithmetic for the random-code local-marginal bound."""

from math import comb


def bound(n):
    if type(n) is not int or n < 32 or n % 16:
        raise ValueError("invalid length")
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

