"""Ordered crossing controls and exact, certified rational Pfaffians.

This computes a SIGNED pairing sum. Zero does not certify no perfect matching.
Ports use little-endian bit masks; vertex order is part of every request.
"""
from fractions import Fraction as F
import hashlib


def q(value):
    if type(value) is int or isinstance(value, F):
        return F(value)
    if (isinstance(value, (list, tuple)) and len(value) == 2
            and all(type(x) is int for x in value) and value[1] > 0):
        return F(*value)
    raise ValueError("exact integer, Fraction or [numerator, positive denominator] required")


def enc(value):
    value = q(value)
    return [value.numerator, value.denominator]


def matrix(value):
    a = [[q(x) for x in row] for row in value]
    n = len(a)
    if any(len(row) != n for row in a):
        raise ValueError("square matrix required")
    if any(a[i][j] != -a[j][i] for i in range(n) for j in range(n)):
        raise ValueError("skew-symmetric matrix required")
    return a


def encode_matrix(a):
    return [[enc(x) for x in row] for row in a]


def request_hash(a):
    a = matrix(a)
    h = hashlib.sha256(b"ordered-rational-pfaffian-v1\0")
    for x in [len(a)] + [v for row in a for x in row for v in (x.numerator, x.denominator)]:
        data = abs(x).to_bytes(max(1, (abs(x).bit_length()+7)//8), "big")
        h.update(bytes([int(x < 0)]))
        h.update(len(data).to_bytes(8, "big"))
        h.update(data)
    return h.hexdigest()


def ordinary_crossing():
    return [F(int(((s >> 0) & 1) == ((s >> 2) & 1)
                  and ((s >> 1) & 1) == ((s >> 3) & 1))) for s in range(16)]


def signed_crossing():
    result = ordinary_crossing()
    result[15] = F(-1)
    return result


def four_port_identity(f):
    if len(f) != 16:
        raise ValueError("four ports required")
    f = list(map(q, f))
    return f[0]*f[15] - f[3]*f[12] + f[5]*f[10] - f[9]*f[6]


def matchgate_violations(f):
    """All necessary matchgate identities, exponentially many in port count."""
    f = list(map(q, f))
    k = (len(f)-1).bit_length()
    if len(f) != 1 << k:
        raise ValueError("truth table length must be a power of two")
    bad = []
    for alpha in range(1 << k):
        for beta in range(1 << k):
            ports = [j for j in range(k) if (alpha ^ beta) >> j & 1]
            value = sum(((-1)**(i+1))*f[alpha ^ (1 << p)]*f[beta ^ (1 << p)]
                        for i, p in enumerate(ports))
            if value:
                bad.append({"alpha": alpha, "beta": beta, "residual": enc(value)})
    return bad


def crossover_graph():
    """Cai--Gorenstein Figure 6; exterior 0,1,2,3 clockwise, interior 4,5."""
    return 6, [(0, 1, 1), (0, 4, 1), (4, 3, 1), (1, 5, 1),
               (5, 2, 1), (3, 2, 1), (4, 5, -1)]


def deletion_signature(n, edges, ports):
    """Small exhaustive graph control, including every matching and signed weight."""
    if type(n) is not int or not 0 <= n <= 16:
        raise ValueError("small graph control supports at most 16 vertices")
    if len(set(ports)) != len(ports) or any(type(v) is not int or not 0 <= v < n for v in ports):
        raise ValueError("distinct valid ordered ports required")
    adjacency = {}
    for u, v, w in edges:
        if type(u) is not int or type(v) is not int or not 0 <= u < n or not 0 <= v < n or u == v:
            raise ValueError("invalid edge")
        edge = tuple(sorted((u, v)))
        if edge in adjacency:
            raise ValueError("parallel edge not supported by this control")
        adjacency[edge] = q(w)

    def enumerate_matchings(remaining):
        if not remaining:
            return [(F(1), [])]
        u, *rest = remaining
        result = []
        for v in rest:
            edge = (u, v)
            if edge not in adjacency:
                continue
            for weight, chosen in enumerate_matchings([x for x in rest if x != v]):
                result.append((adjacency[edge]*weight, [list(edge)] + chosen))
        return result

    rows = []
    for mask in range(1 << len(ports)):
        deleted = {v for i, v in enumerate(ports) if mask >> i & 1}
        matchings = enumerate_matchings([v for v in range(n) if v not in deleted])
        rows.append({"mask": mask, "value": enc(sum((w for w, _ in matchings), F(0))),
                     "matchings": [{"edges": e, "weight": enc(w)} for w, e in matchings]})
    return rows


def pairing_expansion(a):
    """Independent factorial-time reference, never an advertised efficient solver."""
    a = matrix(a)
    n = len(a)
    if n > 12:
        raise ValueError("reference expansion is limited to 12 vertices")

    def go(vertices):
        if not vertices:
            return [(F(1), [])]
        if len(vertices) % 2:
            return []
        u, *rest = vertices
        rows = []
        for i, v in enumerate(rest):
            if not a[u][v]:
                continue
            for w, pairs in go([x for x in rest if x != v]):
                rows.append(((-1)**i*a[u][v]*w, [(u, v)] + pairs))
        return rows

    result = []
    for value, pairs in go(list(range(n))):
        crossings = sum(int(a0 < c < b < d or c < a0 < d < b)
                        for i, (a0, b) in enumerate(pairs) for c, d in pairs[i+1:])
        unsigned = F(1)
        for u, v in pairs:
            unsigned *= a[u][v]
        assert value == (-1)**crossings*unsigned
        result.append({"pairs": [list(p) for p in pairs], "crossings": crossings,
                       "edge_product": enc(unsigned), "signed_product": enc(value)})
    return result


def _size(a):
    return max((max(abs(v.numerator).bit_length(), v.denominator.bit_length())
                for row in a for v in row), default=0)


def solve_pfaffian(a, *, max_vertices=128, max_entry_bits=100000):
    a = matrix(a)
    if any(type(v) is not int or v < 0 for v in (max_vertices, max_entry_bits)):
        raise ValueError("nonnegative integer caps required")
    binding, n = request_hash(a), len(a)
    steps, value = [], F(1)
    peak = _size(a)

    def unknown(reason):
        return {"status": "UNKNOWN", "request_sha256": binding, "reason": reason,
                "stats": {"completed_steps": len(steps), "peak_entry_bits": peak}}

    if n > max_vertices or peak > max_entry_bits:
        return unknown("input cap")
    if n % 2:
        return {"status": "EXACT", "request_sha256": binding, "value": enc(0),
                "steps": [], "termination": "odd_dimension", "stats": {"peak_entry_bits": peak}}
    while a:
        p = next((j for j in range(1, len(a)) if a[0][j]), None)
        if p is None:
            return {"status": "EXACT", "request_sha256": binding, "value": enc(0),
                    "steps": steps, "termination": "zero_row", "stats": {"peak_entry_bits": peak}}
        if p != 1:
            a[1], a[p] = a[p], a[1]
            for row in a:
                row[1], row[p] = row[p], row[1]
            value = -value
        pivot = a[0][1]
        tail = [[a[i][j] + (a[1][i]*a[0][j]-a[0][i]*a[1][j])/pivot
                 for j in range(2, len(a))] for i in range(2, len(a))]
        value *= pivot
        peak = max(peak, _size(tail), abs(value.numerator).bit_length(), value.denominator.bit_length())
        if peak > max_entry_bits:
            return unknown("arithmetic cap")
        steps.append({"swap_with": p, "pivot": enc(pivot), "tail": encode_matrix(tail)})
        a = tail
    return {"status": "EXACT", "request_sha256": binding, "value": enc(value),
            "steps": steps, "termination": "empty", "stats": {"peak_entry_bits": peak}}


def verify_pfaffian(original, proof, *, max_vertices=128, max_entry_bits=100000):
    """Independently check each reduction by S^T A S, not the producer formula."""
    try:
        if any(type(v) is not int or v < 0 for v in (max_vertices, max_entry_bits)):
            raise ValueError("invalid verifier caps")
        a = matrix(original)
        if len(a) > max_vertices or _size(a) > max_entry_bits:
            return {"status": "UNKNOWN", "reason": "verifier input cap"}
        if proof.get("status") != "EXACT":
            return {"status": "UNKNOWN", "reason": "no exact proof"}
        if proof["request_sha256"] != request_hash(a):
            raise ValueError("wrong original ordered matrix")
        steps = proof["steps"]
        if not isinstance(steps, list) or len(steps) > len(a)//2:
            raise ValueError("invalid number of reduction steps")
        total = F(1)
        for step in steps:
            n = len(a)
            if n < 2 or n % 2:
                raise ValueError("invalid reduction dimension")
            p = step["swap_with"]
            if type(p) is not int or not 1 <= p < n:
                raise ValueError("invalid pivot permutation")
            order = list(range(n))
            order[1], order[p] = order[p], order[1]
            a = [[a[i][j] for j in order] for i in order]
            pivot = q(step["pivot"])
            if not pivot or pivot != a[0][1]:
                raise ValueError("incorrect nonzero pivot")
            tail = matrix(step["tail"])
            if len(tail) != n-2:
                raise ValueError("incorrect tail dimension")
            if _size(tail) > max_entry_bits:
                return {"status": "UNKNOWN", "reason": "verifier arithmetic cap"}
            s = [[F(int(i == j)) for j in range(n)] for i in range(n)]
            for j in range(2, n):
                s[0][j] = a[1][j]/pivot
                s[1][j] = -a[0][j]/pivot
            product = [[sum((a[i][k]*s[k][j] for k in range(n)), F(0))
                        for j in range(n)] for i in range(n)]
            transformed = [[sum((s[k][i]*product[k][j] for k in range(n)), F(0))
                            for j in range(n)] for i in range(n)]
            expected = [[F(0) for _ in range(n)] for _ in range(n)]
            expected[0][1], expected[1][0] = pivot, -pivot
            for i in range(n-2):
                for j in range(n-2):
                    expected[i+2][j+2] = tail[i][j]
            if transformed != expected:
                raise ValueError("congruence identity fails")
            total *= pivot * (-1 if p != 1 else 1)
            a = tail
        reason = proof["termination"]
        if reason == "empty" and not a:
            result = total
        elif reason == "zero_row" and a and len(a) % 2 == 0 and all(v == 0 for v in a[0]):
            result = F(0)
        elif reason == "odd_dimension" and len(a) % 2 == 1 and not steps:
            result = F(0)
        else:
            raise ValueError("incorrect terminal justification")
        if q(proof["value"]) != result:
            raise ValueError("incorrect final Pfaffian")
        return {"status": "VERIFIED", "value": enc(result)}
    except (ValueError, KeyError, TypeError, IndexError, ZeroDivisionError) as exc:
        return {"status": "REJECTED", "reason": str(exc)}
