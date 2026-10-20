"""Exact factorized counting under affine coupling.

The input is a product of local factors on disjoint variable blocks together
with an affine system over GF(2).  Fourier/character expansion of the affine
indicator gives an exact solver parameterized by the independent affine rank.
Every character term is produced before any coefficient is merged, and the
certificate records all local transforms.  This is a deliberately narrow
family: it is a compactness experiment, not a general SAT solver.

The producer chooses independently for each block between direct local sums
and one exact, unnormalised Walsh--Hadamard transform.  For k block variables,
N=2**k assignments and C characters, the charged costs are C*N for direct
evaluation and N+k*N+C for precomputation: N local product evaluations, k*N
butterfly additions/subtractions, and C lookups.  Strict improvement is
required; ties and C<=2 retain the direct method.  These work units preserve
the original local-evaluation convention, not a claim about total CPU cost:
factor indexing/multiplications, character masks, parsing, and row reduction
still have their existing polynomial overhead.  No factor values inform this
choice.  The independent verifier deliberately retains direct local sums,
so verification can require a larger work budget than production.
"""

from __future__ import annotations

from fractions import Fraction
from hashlib import sha256
import json
from typing import Any


DEFAULT_CAPS = {
    "max_variables": 256,
    "max_blocks": 256,
    "max_factors": 1024,
    "max_block_variables": 12,
    "max_rank": 20,
    "max_characters": 1 << 20,
    "max_work": 10_000_000,
    "max_integer_bits": 100_000,
}


class Exhausted(Exception):
    pass


class Budget:
    def __init__(self, caps=None):
        caps = {} if caps is None else dict(caps)
        unknown = set(caps) - set(DEFAULT_CAPS)
        if unknown:
            raise ValueError(f"unknown cap(s): {sorted(unknown)}")
        self.caps = {**DEFAULT_CAPS, **caps}
        if any(type(v) is not int or v < 0 for v in self.caps.values()):
            raise ValueError("caps must be nonnegative exact integers")
        self.work = 0
        self.local_evaluations = 0

    def tick(self, amount=1):
        if type(amount) is not int or amount < 0:
            raise ValueError("work amount must be a nonnegative integer")
        self.work += amount
        if self.work > self.caps["max_work"]:
            raise Exhausted("work cap")

    def check_integer(self, value):
        if type(value) is bool or type(value) is not int:
            return
        if abs(value).bit_length() > self.caps["max_integer_bits"]:
            raise Exhausted("integer bit cap")


def _exact_int(value, label):
    if type(value) is bool or type(value) is not int:
        raise ValueError(f"{label} must be an integer")
    return value


def _canonical_request(n, blocks, equations, rhs):
    n = _exact_int(n, "n")
    if n < 0:
        raise ValueError("n must be nonnegative")
    if type(blocks) not in (list, tuple):
        raise ValueError("blocks must be a list")
    if type(equations) not in (list, tuple) or type(rhs) not in (list, tuple):
        raise ValueError("equations and rhs must be lists")
    if len(equations) != len(rhs):
        raise ValueError("equations/rhs length mismatch")
    out_blocks = []
    seen_vars = set()
    seen_ids = set()
    factor_count = 0
    for bi, block in enumerate(blocks):
        if type(block) is not dict or set(block) != {"id", "scope", "factors"}:
            raise ValueError("block schema is id/scope/factors")
        bid = block["id"]
        if type(bid) is not str or not bid or bid in seen_ids:
            raise ValueError("block IDs must be distinct nonempty strings")
        seen_ids.add(bid)
        scope = list(block["scope"])
        if (type(block["scope"]) not in (list, tuple)
                or any(type(v) is not int or v < 0 or v >= n for v in scope)
                or len(set(scope)) != len(scope)
                or set(scope) & seen_vars):
            raise ValueError("block scopes must partition distinct valid variables")
        seen_vars.update(scope)
        if len(scope) > 0 and len(scope) > 64:
            raise ValueError("block scope too large")
        factors = block["factors"]
        if type(factors) not in (list, tuple) or not factors:
            raise ValueError("each block needs at least one factor")
        out_factors = []
        block_var_set = set(scope)
        factor_ids = set()
        for factor in factors:
            if (type(factor) is not dict
                    or set(factor) != {"id", "scope", "table"}):
                raise ValueError("factor schema is id/scope/table")
            fid = factor["id"]
            if type(fid) is not str or not fid or fid in seen_ids or fid in factor_ids:
                raise ValueError("factor IDs must be distinct nonempty strings")
            seen_ids.add(fid); factor_ids.add(fid)
            fscope = list(factor["scope"])
            if (type(factor["scope"]) not in (list, tuple)
                    or any(type(v) is not int or v not in block_var_set for v in fscope)
                    or len(set(fscope)) != len(fscope)):
                raise ValueError("factor scope must be a distinct subset of its block")
            table = list(factor["table"])
            if len(table) != 1 << len(fscope):
                raise ValueError("factor table length does not match its scope")
            table = [_exact_int(x, "factor table entry") for x in table]
            out_factors.append({"id": fid, "scope": fscope, "table": table})
            factor_count += 1
        out_blocks.append({"id": bid, "scope": scope, "factors": out_factors})
    if seen_vars != set(range(n)):
        raise ValueError("block scopes must cover every original variable exactly once")
    out_equations = []
    for row, bit in zip(equations, rhs):
        row = _exact_int(row, "equation mask")
        bit = _exact_int(bit, "equation rhs")
        if row < 0 or row >> n or bit not in (0, 1):
            raise ValueError("invalid affine equation")
        out_equations.append(row)
    return {"n": n, "blocks": out_blocks, "equations": out_equations,
            "rhs": [_exact_int(x, "rhs") for x in rhs],
            "factor_count": factor_count}


def canonical_request(n, blocks, equations, rhs):
    req = _canonical_request(n, blocks, equations, rhs)
    return {k: v for k, v in req.items() if k != "factor_count"}


def request_hash(req):
    raw = json.dumps(req, sort_keys=True, separators=(",", ":")).encode()
    return sha256(b"affine-character-factor-v1\0" + raw).hexdigest()


def _rref(rows, n):
    """Return independent rows in full RREF and inconsistency flag."""
    work = [[int(mask), int(bit)] for mask, bit in rows]
    pivot = 0
    for col in range(n):
        found = next((i for i in range(pivot, len(work))
                      if (work[i][0] >> col) & 1), None)
        if found is None:
            continue
        work[pivot], work[found] = work[found], work[pivot]
        pmask, pbit = work[pivot]
        for i in range(len(work)):
            if i != pivot and ((work[i][0] >> col) & 1):
                work[i][0] ^= pmask
                work[i][1] ^= pbit
        pivot += 1
        if pivot == len(work):
            break
    nonzero = [row for row in work if row[0]]
    inconsistent = any(mask == 0 and bit for mask, bit in work)
    if inconsistent:
        return [], True
    # Sort by pivot for a stable character coordinate system.
    nonzero.sort(key=lambda row: (row[0] & -row[0]).bit_length())
    return nonzero, False


def _assignment_table(block, assignment):
    value = 1
    for factor in block["factors"]:
        idx = 0
        for j, variable in enumerate(factor["scope"]):
            idx |= ((assignment >> block["scope"].index(variable)) & 1) << j
        value *= factor["table"][idx]
    return value


def _block_transform(block, character_mask, row_masks, budget):
    scope = block["scope"]
    local_mask = 0
    for j, row in enumerate(row_masks):
        if (character_mask >> j) & 1:
            for pos, variable in enumerate(scope):
                if (row >> variable) & 1:
                    # Characters add exponents in GF(2); overlapping rows
                    # cancel by XOR rather than accumulating with OR.
                    local_mask ^= 1 << pos
    total = 0
    for assignment in range(1 << len(scope)):
        budget.tick()
        value = _assignment_table(block, assignment)
        if value:
            total += (-value if (local_mask & assignment).bit_count() & 1 else value)
        budget.check_integer(total)
    budget.local_evaluations += 1 << len(scope)
    return total, local_mask


def _use_precomputed_spectrum(block, characters):
    """Select by charged work, with a direct tiny-rank/tie fallback."""
    width = len(block["scope"])
    assignments = 1 << width
    return (characters > 2
            and (width + 1) * assignments + characters < characters * assignments)


def _block_spectrum(block, budget):
    """Return every unnormalised local Walsh coefficient in LSB mask order.

    Each stage replaces (a,b) by (a+b,a-b); after k stages, entry u is
    sum_x f(x)*(-1)**parity(u&x).  Only integer addition/subtraction is used.
    Work and integer caps apply before each allocation-producing evaluation
    and before each butterfly's results are retained.  Exhaustion propagates
    to solve as UNKNOWN without a value or partial certificate.
    """
    spectrum = []
    for assignment in range(1 << len(block["scope"])):
        budget.tick()
        value = _assignment_table(block, assignment)
        budget.local_evaluations += 1
        budget.check_integer(value)
        spectrum.append(value)
    stride = 1
    while stride < len(spectrum):
        for start in range(0, len(spectrum), stride * 2):
            for offset in range(stride):
                left = start + offset
                right = left + stride
                a, b = spectrum[left], spectrum[right]
                budget.tick(2)
                plus, minus = a + b, a - b
                budget.check_integer(plus)
                budget.check_integer(minus)
                spectrum[left], spectrum[right] = plus, minus
        stride *= 2
    return spectrum


def _spectrum_lookup(block, character, row_masks, spectrum, budget):
    """Project the global character onto a block; overlapping rows XOR."""
    mask = 0
    for index, row in enumerate(row_masks):
        if (character >> index) & 1:
            mask ^= row
    local_mask = sum(((mask >> variable) & 1) << index
                     for index, variable in enumerate(block["scope"]))
    budget.tick()
    return spectrum[local_mask], local_mask


def solve(n, blocks, equations, rhs, caps=None):
    req = _canonical_request(n, blocks, equations, rhs)
    budget = Budget(caps)
    if req["n"] > budget.caps["max_variables"]:
        return {"status": "UNKNOWN", "reason": "variable cap"}
    if len(req["blocks"]) > budget.caps["max_blocks"]:
        return {"status": "UNKNOWN", "reason": "block cap"}
    if req["factor_count"] > budget.caps["max_factors"]:
        return {"status": "UNKNOWN", "reason": "factor cap"}
    if any(len(b["scope"]) > budget.caps["max_block_variables"] for b in req["blocks"]):
        return {"status": "UNKNOWN", "reason": "block-variable cap"}
    rows = list(zip(req["equations"], req["rhs"]))
    rref, inconsistent = _rref(rows, req["n"])
    if inconsistent:
        return {"status": "EXACT", "value": [0, 1], "rank": None,
                "inconsistent": True, "source_hash": request_hash(canonical_request(n, blocks, equations, rhs))}
    rank = len(rref)
    if rank > budget.caps["max_rank"]:
        return {"status": "UNKNOWN", "reason": "affine-rank cap"}
    characters = 1 << rank
    if characters > budget.caps["max_characters"]:
        return {"status": "UNKNOWN", "reason": "character cap"}
    row_masks = [mask for mask, _ in rref]
    row_rhs = [bit for _, bit in rref]
    records = []
    numerator = 0
    rhs_mask = sum(bit << j for j, bit in enumerate(row_rhs))
    try:
        # Precomputation leaves the existing character certificate unchanged.
        # The direct checker never calls these helpers or trusts this choice.
        spectra = [
            _block_spectrum(block, budget)
            if _use_precomputed_spectrum(block, characters) else None
            for block in req["blocks"]
        ]
        for character in range(characters):
            sign = -1 if (character & rhs_mask).bit_count() & 1 else 1
            product = 1
            local = []
            for block, spectrum in zip(req["blocks"], spectra):
                if spectrum is None:
                    value, local_mask = _block_transform(block, character, row_masks, budget)
                else:
                    value, local_mask = _spectrum_lookup(
                        block, character, row_masks, spectrum, budget)
                local.append({"block_id": block["id"], "mask": local_mask, "value": value})
                product *= value
                budget.check_integer(product)
            term = sign * product
            numerator += term
            budget.check_integer(numerator)
            records.append({"character": character, "sign": sign,
                            "local": local, "product": product, "term": term})
    except Exhausted as exc:
        return {"status": "UNKNOWN", "reason": str(exc),
                "stats": {"work": budget.work, "local_evaluations": budget.local_evaluations,
                           "characters": characters, "rank": rank}}
    value = Fraction(numerator, characters)
    if value.denominator != 1:
        # A valid integer-table count must be integral; retaining this check
        # catches a broken affine normalization rather than rounding.
        raise AssertionError("character projection produced a non-integer")
    out_req = canonical_request(n, blocks, equations, rhs)
    return {"status": "EXACT", "value": [value.numerator, value.denominator],
            "rank": rank, "inconsistent": False,
            "rref": [[mask, bit] for mask, bit in rref],
            "characters": records,
            "stats": {"work": budget.work, "local_evaluations": budget.local_evaluations,
                      "characters": characters, "rank": rank},
            "source_hash": request_hash(out_req)}


def verify(n, blocks, equations, rhs, result, caps=None):
    """Independent certificate checker; producer counters are ignored."""
    try:
        req = _canonical_request(n, blocks, equations, rhs)
        budget = Budget(caps)
        out_req = canonical_request(n, blocks, equations, rhs)
        if (req["n"] > budget.caps["max_variables"]
                or len(req["blocks"]) > budget.caps["max_blocks"]
                or req["factor_count"] > budget.caps["max_factors"]
                or any(len(b["scope"]) > budget.caps["max_block_variables"]
                       for b in req["blocks"])):
            return {"valid": False, "status": "UNKNOWN", "errors": ["input cap"]}
        if type(result) is not dict or result.get("status") != "EXACT":
            return {"valid": False, "status": "INVALID", "errors": ["not an exact result"]}
        if result.get("source_hash") != request_hash(out_req):
            return {"valid": False, "status": "INVALID", "errors": ["source hash mismatch"]}
        expected_rows, inconsistent = _rref(list(zip(req["equations"], req["rhs"])), req["n"])
        if inconsistent:
            ok = result.get("inconsistent") is True and result.get("value") == [0, 1]
            return {"valid": ok, "status": "VERIFIED" if ok else "INVALID", "errors": [] if ok else ["bad inconsistent certificate"]}
        rank = len(expected_rows)
        if rank > budget.caps["max_rank"] or (1 << rank) > budget.caps["max_characters"]:
            return {"valid": False, "status": "UNKNOWN", "errors": ["character cap"]}
        if result.get("rank") != rank or result.get("rref") != [[m, b] for m, b in expected_rows]:
            return {"valid": False, "status": "INVALID", "errors": ["RREF mismatch"]}
        records = result.get("characters")
        if type(records) is not list or len(records) != 1 << rank:
            return {"valid": False, "status": "INVALID", "errors": ["character record count"]}
        rhs_mask = sum(bit << j for j, (_, bit) in enumerate(expected_rows))
        total = 0
        row_masks = [mask for mask, _ in expected_rows]
        for character, record in enumerate(records):
            if (type(record) is not dict or record.get("character") != character):
                return {"valid": False, "status": "INVALID", "errors": ["character ordering"]}
            expected_sign = -1 if ((character & rhs_mask).bit_count() & 1) else 1
            if record.get("sign") != expected_sign:
                return {"valid": False, "status": "INVALID", "errors": ["character sign"]}
            locals_ = record.get("local")
            if type(locals_) is not list or len(locals_) != len(req["blocks"]):
                return {"valid": False, "status": "INVALID", "errors": ["local record count"]}
            product = 1
            for block, local in zip(req["blocks"], locals_):
                if local.get("block_id") != block["id"]:
                    return {"valid": False, "status": "INVALID", "errors": ["block ownership/order"]}
                expected, expected_mask = _block_transform(block, character, row_masks, budget)
                if local.get("mask") != expected_mask or local.get("value") != expected:
                    return {"valid": False, "status": "INVALID", "errors": ["local transform mismatch"]}
                product *= expected
            if record.get("product") != product or record.get("term") != expected_sign * product:
                return {"valid": False, "status": "INVALID", "errors": ["product mismatch"]}
            total += expected_sign * product
        value = Fraction(total, 1 << rank)
        if value.denominator != 1 or result.get("value") != [value.numerator, value.denominator]:
            return {"valid": False, "status": "INVALID", "errors": ["final value mismatch"]}
        return {"valid": True, "status": "VERIFIED", "errors": [],
                "stats": {"work": budget.work, "local_evaluations": budget.local_evaluations,
                          "characters": 1 << rank, "rank": rank}}
    except Exhausted as exc:
        return {"valid": False, "status": "UNKNOWN", "errors": [str(exc)]}
    except (ValueError, KeyError, TypeError, AssertionError) as exc:
        return {"valid": False, "status": "INVALID", "errors": [str(exc)]}


def direct_count(n, blocks, equations, rhs):
    """Independent finite oracle for small n; never used by solve/verify."""
    req = _canonical_request(n, blocks, equations, rhs)
    if n > 22:
        raise ValueError("direct oracle capped at 22 variables")
    count = 0
    for assignment in range(1 << n):
        if any((assignment & mask).bit_count() % 2 != bit
               for mask, bit in zip(req["equations"], req["rhs"])):
            continue
        value = 1
        for block in req["blocks"]:
            value *= _assignment_table(block, sum(((assignment >> v) & 1) << j
                                                  for j, v in enumerate(block["scope"])))
        count += value
    return count


def paired_or_blocks(m, rank_mode="global"):
    """Return disjoint OR pairs with either one global or m local parity rows."""
    blocks = []
    rows = []
    rhs = []
    for i in range(m):
        x, y = 2 * i, 2 * i + 1
        blocks.append({"id": f"block-{i}", "scope": [x, y],
                       "factors": [{"id": f"or-{i}", "scope": [x, y],
                                    "table": [0, 1, 1, 1]}]})
    if rank_mode == "global" and m:
        rows = [(1 << (2 * m)) - 1]
        rhs = [0]
    elif rank_mode == "local":
        rows = [3 << (2 * i) for i in range(m)]
        rhs = [0] * m
    elif rank_mode == "connected":
        # Independent cumulative parity rows form one connected component.
        # Their rank is m, so component factorization cannot split them.
        rows = [3]
        rows.extend((3 << (2 * i)) | (3 << (2 * (i - 1))) for i in range(1, m))
        rhs = [0] * m
    elif rank_mode != "none":
        raise ValueError("unknown rank mode")
    return 2 * m, blocks, rows, rhs


def _component_partition(req):
    """Partition blocks and nonzero equations by their incidence graph."""
    blocks = req["blocks"]
    rows = req["equations"]
    parent = list(range(len(blocks) + len(rows)))

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    def union(a, b):
        a, b = find(a), find(b)
        if a != b:
            parent[b] = a

    scalar_rows = []
    for ri, mask in enumerate(rows):
        touched = [bi for bi, block in enumerate(blocks)
                   if any((mask >> v) & 1 for v in block["scope"])]
        if not touched:
            scalar_rows.append(ri)
            continue
        row_node = len(blocks) + ri
        for bi in touched:
            union(row_node, bi)
    grouped = {}
    for bi in range(len(blocks)):
        grouped.setdefault(find(bi), {"block_indices": [], "row_indices": []})["block_indices"].append(bi)
    for ri, mask in enumerate(rows):
        if ri in scalar_rows:
            continue
        # A nonzero row touches at least one block and therefore has a root.
        touched = next(bi for bi, block in enumerate(blocks)
                       if any((mask >> v) & 1 for v in block["scope"]))
        grouped[find(touched)]["row_indices"].append(ri)
    components = list(grouped.values())
    components.sort(key=lambda c: min(c["block_indices"]))
    for component in components:
        component["block_indices"].sort()
        component["row_indices"].sort()
    return components, scalar_rows


def _local_component_request(req, component):
    """Relabel one incidence component to a dense local variable universe."""
    variables = sorted({v for bi in component["block_indices"] for v in req["blocks"][bi]["scope"]})
    mapping = {old: new for new, old in enumerate(variables)}
    blocks = []
    for bi in component["block_indices"]:
        block = req["blocks"][bi]
        blocks.append({"id": block["id"],
                       "scope": [mapping[v] for v in block["scope"]],
                       "factors": [{"id": factor["id"],
                                    "scope": [mapping[v] for v in factor["scope"]],
                                    "table": list(factor["table"])}
                                   for factor in block["factors"]]})
    rows = []
    rhs = []
    for ri in component["row_indices"]:
        mask = req["equations"][ri]
        local_mask = sum(1 << mapping[v] for v in variables if (mask >> v) & 1)
        rows.append(local_mask)
        rhs.append(req["rhs"][ri])
    return len(variables), blocks, rows, rhs, variables


def solve_components(n, blocks, equations, rhs, caps=None):
    """Split disconnected affine/factor incidence before character expansion."""
    req = _canonical_request(n, blocks, equations, rhs)
    budget = Budget(caps)
    if (req["n"] > budget.caps["max_variables"]
            or len(req["blocks"]) > budget.caps["max_blocks"]
            or req["factor_count"] > budget.caps["max_factors"]
            or any(len(b["scope"]) > budget.caps["max_block_variables"] for b in req["blocks"])):
        return {"status": "UNKNOWN", "reason": "input cap"}
    components, scalar_rows = _component_partition(req)
    if any(req["rhs"][ri] for ri in scalar_rows):
        return {"status": "EXACT", "value": [0, 1], "component_count": len(components),
                "scalar_rows": [[ri, req["rhs"][ri]] for ri in scalar_rows],
                "components": [], "source_hash": request_hash(canonical_request(n, blocks, equations, rhs))}
    remaining = budget.caps["max_work"]
    component_records = []
    total = 1
    for ci, component in enumerate(components):
        local_n, local_blocks, local_rows, local_rhs, variables = _local_component_request(req, component)
        child_caps = dict(budget.caps)
        child_caps["max_work"] = remaining
        child = solve(local_n, local_blocks, local_rows, local_rhs, child_caps)
        child_work = child.get("stats", {}).get("work", 0)
        remaining -= child_work
        if child["status"] != "EXACT":
            return {"status": "UNKNOWN", "reason": child.get("reason", "component unknown"),
                    "component_index": ci, "component_count": len(components),
                    "scalar_rows": [[ri, req["rhs"][ri]] for ri in scalar_rows],
                    "stats": {"components_completed": ci, "work": budget.caps["max_work"] - remaining}}
        total *= child["value"][0]
        component_records.append({"block_indices": list(component["block_indices"]),
                                  "row_indices": list(component["row_indices"]),
                                  "variables": variables, "result": child})
    return {"status": "EXACT", "value": [total, 1],
            "component_count": len(components),
            "scalar_rows": [[ri, req["rhs"][ri]] for ri in scalar_rows],
            "components": component_records,
            "stats": {"components": len(components),
                      "component_characters": [r["result"].get("stats", {}).get("characters", 0)
                                                for r in component_records],
                      "work": budget.caps["max_work"] - remaining},
            "source_hash": request_hash(canonical_request(n, blocks, equations, rhs))}


def verify_components(n, blocks, equations, rhs, result, caps=None):
    """Verify the component certificate using fresh incidence and local replay."""
    try:
        req = _canonical_request(n, blocks, equations, rhs)
        budget = Budget(caps)
        if result.get("status") != "EXACT":
            return {"valid": False, "status": "INVALID", "errors": ["not exact"]}
        if result.get("source_hash") != request_hash(canonical_request(n, blocks, equations, rhs)):
            return {"valid": False, "status": "INVALID", "errors": ["source hash"]}
        components, scalar_rows = _component_partition(req)
        expected_scalars = [[ri, req["rhs"][ri]] for ri in scalar_rows]
        if result.get("scalar_rows") != expected_scalars:
            return {"valid": False, "status": "INVALID", "errors": ["scalar rows"]}
        if any(req["rhs"][ri] for ri in scalar_rows):
            return {"valid": result.get("value") == [0, 1],
                    "status": "VERIFIED" if result.get("value") == [0, 1] else "INVALID", "errors": []}
        records = result.get("components")
        if (type(records) is not list or len(records) != len(components)
                or result.get("component_count") != len(components)):
            return {"valid": False, "status": "INVALID", "errors": ["component count"]}
        remaining = budget.caps["max_work"]
        total = 1
        for component, record in zip(components, records):
            if (record.get("block_indices") != component["block_indices"]
                    or record.get("row_indices") != component["row_indices"]):
                return {"valid": False, "status": "INVALID", "errors": ["component ownership"]}
            local_n, local_blocks, local_rows, local_rhs, variables = _local_component_request(req, component)
            if record.get("variables") != variables:
                return {"valid": False, "status": "INVALID", "errors": ["component variables"]}
            child_caps = dict(budget.caps)
            child_caps["max_work"] = remaining
            child_check = verify(local_n, local_blocks, local_rows, local_rhs,
                                 record.get("result"), child_caps)
            if not child_check.get("valid"):
                return {"valid": False, "status": child_check.get("status", "INVALID"),
                        "errors": ["child: " + "; ".join(child_check.get("errors", []))]}
            child_value = record["result"]["value"]
            total *= child_value[0]
            remaining -= child_check.get("stats", {}).get("work", 0)
        if result.get("value") != [total, 1]:
            return {"valid": False, "status": "INVALID", "errors": ["component product"]}
        return {"valid": True, "status": "VERIFIED", "errors": [],
                "stats": {"components": len(components), "work": budget.caps["max_work"] - remaining,
                           "component_characters": [r["result"].get("stats", {}).get("characters", 0)
                                                     for r in records]}}
    except (ValueError, KeyError, TypeError, AssertionError) as exc:
        return {"valid": False, "status": "INVALID", "errors": [str(exc)]}
