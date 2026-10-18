"""Independent bridge from invented truth tables to the typed planner.

The bounded-language inventor stores a canonical Boolean truth table as its
authoritative relation certificate.  This module converts that certificate to
tuples, recomputes the six Schaefer closure tests independently, and exposes
the corresponding planner routes.  It deliberately does not trust a compact
representation chosen by the inventor.
"""
from __future__ import annotations

from itertools import product
import json
from hashlib import sha256
from pathlib import Path

import engine as planner


ROOT = Path(__file__).resolve().parent
RESULTS_PATH = ROOT.parent / "bounded_language_invention_lab" / "RESULTS.json"


def truth_table_rows(table: int, arity: int) -> tuple[tuple[int, ...], ...]:
    """Decode the inventor's lexicographic truth-table bit convention."""
    if type(table) is not int or table < 0:
        raise ValueError("table must be a nonnegative integer")
    if type(arity) is not int or arity < 0:
        raise ValueError("arity must be a nonnegative integer")
    limit = 1 << (1 << arity)
    if table >= limit:
        raise ValueError("table has bits outside the declared arity")
    rows = []
    for bits in product((0, 1), repeat=arity):
        index = 0
        for bit in bits:
            index = (index << 1) | bit
        if (table >> index) & 1:
            rows.append(tuple(bits))
    return tuple(rows)


def _and(a, b):
    return tuple(x & y for x, y in zip(a, b))


def _or(a, b):
    return tuple(x | y for x, y in zip(a, b))


def _majority(a, b, c):
    return tuple(int(x + y + z >= 2) for x, y, z in zip(a, b, c))


def _minority(a, b, c):
    return tuple(x ^ y ^ z for x, y, z in zip(a, b, c))


def direct_signature(rows, arity: int) -> frozenset[str]:
    """Recompute the six Schaefer tags without calling the planner helper."""
    relation = set(tuple(row) for row in rows)
    if any(len(row) != arity or any(bit not in (0, 1) for bit in row)
           for row in relation):
        raise ValueError("rows do not match the declared arity")
    tags = set()
    zero, one = (0,) * arity, (1,) * arity
    if zero in relation:
        tags.add("ZERO")
    if one in relation:
        tags.add("ONE")

    for name, operation in (("AND", _and), ("OR", _or)):
        if all(operation(a, b) in relation for a in relation for b in relation):
            tags.add(name)
    for name, operation in (("MAJ", _majority), ("MIN", _minority)):
        if all(operation(a, b, c) in relation
               for a in relation for b in relation for c in relation):
            tags.add(name)
    return frozenset(tags)


def planner_types(signature: frozenset[str]) -> tuple[str, ...]:
    """Return native planner theories supported by an invented relation."""
    mapping = (("AND", "HORN"), ("OR", "DUALHORN"),
               ("MAJ", "BIJUNCTIVE"), ("MIN", "AFFINE"))
    return tuple(native for tag, native in mapping if tag in signature)


def classify_table(table: int, arity: int) -> dict:
    rows = truth_table_rows(table, arity)
    direct = direct_signature(rows, arity)
    planner_signature = planner.relation_signature(rows, arity)
    if direct != planner_signature:
        raise AssertionError("independent and planner signatures disagree")
    unpinned = planner.schaefer_pair_status(direct, direct)
    pinned = planner.schaefer_pair_status(direct, direct, allow_pins=True)
    # Keep the artifact JSON-stable: the planner returns tuples internally,
    # while serialized certificates must use lists.
    unpinned = {"status": unpinned["status"],
                "common": list(unpinned["common"])}
    pinned = {"status": pinned["status"],
              "common": list(pinned["common"])}
    return {
        "arity": arity,
        "canonical_tt": table,
        "signature": sorted(direct),
        "planner_types": list(planner_types(direct)),
        "unpinned_status": unpinned,
        "pinned_status": pinned,
    }


def build_catalog_artifact(path: Path = RESULTS_PATH) -> dict:
    """Create a deterministic signature record for every saved inventor entry."""
    raw = path.read_bytes()
    source = json.loads(raw)
    records = []
    for entry in source.get("catalog", []):
        record = classify_table(entry["canonical_tt"], entry["arity"])
        record.update({"relation_id": entry["id"],
                       "best_kind": entry["best_rep"]["kind"],
                       "occurrences": entry["count"]})
        records.append(record)
    records.sort(key=lambda row: row["relation_id"])
    return {"schema": "invented_relation_signatures_v1",
            "source_sha256": sha256(raw).hexdigest(),
            "relation_count": len(records), "relations": records}


def verify_catalog_artifact(path: Path, artifact: dict) -> dict:
    expected = build_catalog_artifact(path)
    if artifact != expected:
        return {"valid": False, "reason": "artifact differs from independent replay"}
    return {"valid": True, "relation_count": len(expected["relations"]),
            "source_sha256": expected["source_sha256"]}
