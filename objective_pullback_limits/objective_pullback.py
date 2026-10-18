"""Exact test for additive nonnegative Hamming costs under a binary linear map.

Rows are m-bit integers. Complexity is polynomial in the explicit n-by-m
matrix size. This deliberately concerns all z, not a constrained subset.
"""
import hashlib


def checked(rows, m, weights):
    if type(m) is not int or m < 0:
        raise ValueError("invalid input dimension")
    rows, weights = tuple(rows), tuple(weights)
    if len(rows) != len(weights):
        raise ValueError("one cost per output coordinate required")
    if any(type(r) is not int or r < 0 or r.bit_length() > m for r in rows):
        raise ValueError("invalid binary row")
    if any(type(w) is not int or w < 0 for w in weights):
        raise ValueError("nonnegative integer output costs required")
    return rows, weights


def objective(rows, weights, z):
    return sum(w * ((r & z).bit_count() & 1) for r, w in zip(rows, weights))


def request_hash(rows, m, weights):
    # Binary encoding avoids Python's decimal-conversion digit limit.
    digest = hashlib.sha256(b"linear_cost_pullback_input_v1\0")
    for value in (m, len(rows), len(weights), *rows, *weights):
        data = value.to_bytes(max(1, (value.bit_length() + 7) // 8), "little")
        digest.update(len(data).to_bytes(8, "little"))
        digest.update(data)
    return digest.hexdigest()


def classify(rows, m, weights, *, max_columns=100000):
    rows, weights = checked(rows, m, weights)
    if type(max_columns) is not int or max_columns < 0:
        raise ValueError("invalid column budget")
    if m > max_columns:
        return {"status": "UNKNOWN", "reason": "column budget"}
    common = {"status": "EXACT", "format": "linear_cost_pullback_v1",
              "input_hash": request_hash(rows, m, weights)}
    for r, w in zip(rows, weights):
        if w and r.bit_count() >= 2:
            a = r & -r
            b = (r ^ a) & -(r ^ a)
            values = [objective(rows, weights, z) for z in (a, b, a ^ b)]
            return dict(common, additive=False,
                        pair=[a.bit_length()-1, b.bit_length()-1],
                        values=values, defect=values[0]+values[1]-values[2])
    costs = [0] * m
    for r, w in zip(rows, weights):
        if r and w:
            costs[r.bit_length()-1] += w
    return dict(common, additive=True, constant=0, unary_costs=costs)


def verify(rows, m, weights, certificate, *, max_columns=100000):
    """Verify with the original map and costs; no call to the classifier."""
    try:
        rows, weights = checked(rows, m, weights)
        if type(max_columns) is not int or max_columns < 0:
            raise ValueError("invalid column budget")
        if m > max_columns:
            return {"status": "UNKNOWN", "valid": False}
        c = certificate
        if not isinstance(c, dict) or c.get("status") != "EXACT":
            raise ValueError("no exact evidence")
        common = {"status", "format", "input_hash", "additive"}
        if c.get("format") != "linear_cost_pullback_v1":
            raise ValueError("wrong format")
        if c.get("input_hash") != request_hash(rows, m, weights):
            raise ValueError("wrong original input")
        if type(c.get("additive")) is not bool:
            raise ValueError("invalid classification")
        if c["additive"]:
            if set(c) != common | {"constant", "unary_costs"}:
                raise ValueError("wrong additive schema")
            if type(c["constant"]) is not int or c["constant"] != 0:
                raise ValueError("nonzero constant")
            costs = c["unary_costs"]
            if not isinstance(costs, list) or len(costs) != m:
                raise ValueError("wrong unary cost shape")
            if any(type(v) is not int or v < 0 for v in costs):
                raise ValueError("invalid unary cost")
            if any(w and r.bit_count() > 1 for r, w in zip(rows, weights)):
                raise ValueError("positive-cost overlapping output")
            for j, value in enumerate(costs):
                if value != sum(w for r, w in zip(rows, weights) if r & (1 << j)):
                    raise ValueError("wrong unary cost")
        else:
            if set(c) != common | {"pair", "values", "defect"}:
                raise ValueError("wrong obstruction schema")
            pair = c["pair"]
            if not isinstance(pair, list) or len(pair) != 2:
                raise ValueError("wrong pair shape")
            j, k = pair
            if any(type(v) is not int or not 0 <= v < m for v in pair) or j == k:
                raise ValueError("invalid pair")
            expected = [objective(rows, weights, z)
                        for z in (1 << j, 1 << k, (1 << j) | (1 << k))]
            if not isinstance(c["values"], list) or len(c["values"]) != 3:
                raise ValueError("wrong values shape")
            if any(type(v) is not int for v in c["values"]) or c["values"] != expected:
                raise ValueError("wrong original objective values")
            defect = expected[0] + expected[1] - expected[2]
            if type(c["defect"]) is not int or c["defect"] != defect or defect <= 0:
                raise ValueError("no obstruction")
        return {"status": "EXACT", "valid": True}
    except (TypeError, ValueError, KeyError):
        return {"status": "INVALID", "valid": False}
