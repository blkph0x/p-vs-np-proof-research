"""Exact coefficient positivity by interval support; no polynomial general bound."""
import hashlib


def checked(choices, target):
    pairs = tuple(tuple(pair) for pair in choices)
    if type(target) is not int or target < 0:
        raise ValueError("target must be a nonnegative integer")
    if any(len(pair) != 2 or any(type(v) is not int or v < 0 for v in pair) for pair in pairs):
        raise ValueError("each choice must contain two nonnegative integer weights")
    return pairs


def request_hash(choices, target):
    digest = hashlib.sha256(b"interval-support-v1\0")
    for value in (len(choices), target, *(v for pair in choices for v in pair)):
        data = value.to_bytes(max(1, (value.bit_length()+7)//8), "big")
        digest.update(len(data).to_bytes(8, "big"))
        digest.update(data)
    return digest.hexdigest()


def contains(intervals, value):
    lo, hi = 0, len(intervals)
    while lo < hi:
        middle = (lo+hi)//2
        if intervals[middle][1] < value:
            lo = middle+1
        else:
            hi = middle
    return lo < len(intervals) and intervals[lo][0] <= value


def _merge(spans):
    result = []
    for left, right in sorted(spans):
        if result and left <= result[-1][1]+1:
            result[-1][1] = max(result[-1][1], right)
        else:
            result.append([left, right])
    return result


def solve(choices, target, *, max_intervals=4096, max_total_intervals=100000, max_spans=1000000):
    choices = checked(choices, target)
    if any(type(x) is not int or x < 0 for x in (max_intervals, max_total_intervals, max_spans)):
        raise ValueError("nonnegative integer budgets required")
    layers = [[[0, 0]]]
    total, peak, spans = 1, 1, 0
    binding = request_hash(choices, target)

    def unknown(reason):
        return {"status": "UNKNOWN", "request_sha256": binding, "reason": reason,
                "stats": {"completed_choices": len(layers)-1, "total_intervals": total,
                          "peak_intervals": peak, "generated_spans": spans}}

    if max_intervals < 1 or max_total_intervals < 1:
        return unknown("initial interval exceeds budget")
    for pair in choices:
        needed = 2*len(layers[-1])
        if spans+needed > max_spans:
            return unknown("span budget")
        shifted = [[left+w, min(right+w, target)] for left, right in layers[-1]
                   for w in pair if left+w <= target]
        spans += needed
        next_layer = _merge(shifted)
        peak = max(peak, len(next_layer))
        if len(next_layer) > max_intervals or total+len(next_layer) > max_total_intervals:
            return unknown("interval budget")
        layers.append(next_layer)
        total += len(next_layer)
    feasible = contains(layers[-1], target)
    bits = None
    if feasible:
        bits, remaining = [], target
        for i in range(len(choices)-1, -1, -1):
            bit = next(b for b in (0, 1) if contains(layers[i], remaining-choices[i][b]))
            bits.append(bit)
            remaining -= choices[i][bit]
        bits.reverse()
        assert remaining == 0
    return {"status": "EXACT", "request_sha256": binding, "feasible": feasible,
            "layers": layers, "witness": bits,
            "stats": {"completed_choices": len(choices), "total_intervals": total,
                      "peak_intervals": peak, "generated_spans": spans}}


def _event_union(previous, pair, target):
    """Independent recurrence check: sweep coverage events, not producer merging."""
    events = {}
    for weight in pair:
        for low, high in previous:
            start, stop = low+weight, min(high+weight, target)+1
            if start >= stop:
                continue
            events[start] = events.get(start, 0)+1
            events[stop] = events.get(stop, 0)-1
    result, coverage, opened = [], 0, None
    for point in sorted(events):
        old = coverage
        coverage += events[point]
        if old == 0 and coverage > 0:
            opened = point
        elif old > 0 and coverage == 0:
            result.append([opened, point-1])
    assert coverage == 0
    return result


def verify(choices, target, proof, *, max_total_intervals=200000, max_spans=2000000):
    """EXACT claims require all original-input recurrences; exhaustion is UNKNOWN."""
    try:
        choices = checked(choices, target)
        if any(type(x) is not int or x < 0 for x in (max_total_intervals, max_spans)):
            raise ValueError("invalid verifier budget")
        if proof.get("status") != "EXACT":
            return {"status": "UNKNOWN", "reason": "no exact proof supplied"}
        if proof["request_sha256"] != request_hash(choices, target):
            raise ValueError("wrong original input")
        layers = proof["layers"]
        if not isinstance(layers, list) or len(layers) != len(choices)+1:
            raise ValueError("missing layers")
        total = sum(len(layer) for layer in layers)
        spans = 2*sum(len(layer) for layer in layers[:-1])
        if total > max_total_intervals or spans > max_spans:
            return {"status": "UNKNOWN", "reason": "verification budget"}
        for layer in layers:
            previous = -2
            for interval in layer:
                if not isinstance(interval, list) or len(interval) != 2:
                    raise ValueError("malformed interval")
                low, high = interval
                if any(type(x) is not int for x in interval) or not 0 <= low <= high <= target or low <= previous+1:
                    raise ValueError("intervals not canonical")
                previous = high
        if layers[0] != [[0, 0]]:
            raise ValueError("wrong base")
        for i, pair in enumerate(choices):
            if _event_union(layers[i], pair, target) != layers[i+1]:
                raise ValueError("wrong recurrence")
        feasible = any(low <= target <= high for low, high in layers[-1])
        if type(proof["feasible"]) is not bool or proof["feasible"] != feasible:
            raise ValueError("wrong decision")
        bits = proof["witness"]
        if feasible:
            if not isinstance(bits, list) or len(bits) != len(choices) or any(type(b) is not int or b not in (0, 1) for b in bits):
                raise ValueError("invalid witness")
            if sum(pair[b] for pair, b in zip(choices, bits)) != target:
                raise ValueError("witness does not reach original target")
        elif bits is not None:
            raise ValueError("false decision has witness")
        stats = proof["stats"]
        wanted = {"completed_choices": len(choices), "total_intervals": total,
                  "peak_intervals": max(map(len, layers)), "generated_spans": spans}
        if stats != wanted or any(type(value) is not int for value in stats.values()):
            raise ValueError("wrong work counts")
        return {"status": "VERIFIED", "feasible": feasible,
                "support_size_at_most_target": sum(hi-lo+1 for lo, hi in layers[-1]), **wanted}
    except (ValueError, TypeError, KeyError, IndexError, AttributeError, OverflowError):
        return {"status": "INVALID"}


def separated_blocks(q):
    if type(q) is not int or q < 1:
        raise ValueError("positive q required")
    length = 1 << q
    return [[0, 1 << i] for i in range(q)] + [[0, 2*length]], length


def separated_block_modular_witness(q, modulus):
    """For every 1 <= M <= 2^q, one original choice word hits target mod M."""
    choices, target = separated_blocks(q)
    if type(modulus) is not int or not 1 <= modulus <= target:
        raise ValueError("modulus outside the proved range")
    weight = target % modulus
    bits = [(weight >> i) & 1 for i in range(q)] + [0]
    assert sum(pair[b] for pair, b in zip(choices, bits)) % modulus == target % modulus
    return bits
