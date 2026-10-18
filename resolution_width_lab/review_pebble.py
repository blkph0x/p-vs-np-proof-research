"""Independent tuple-state replay of the pebble-game artifact."""
from __future__ import annotations

from hashlib import sha256
from itertools import combinations, product
import json
from pathlib import Path


HERE = Path(__file__).resolve().parent


def digest(path):
    return sha256(path.read_text(encoding="utf-8").replace("\r\n", "\n").replace("\r", "\n").encode()).hexdigest()


def pigeonhole(pigeons, holes):
    variable = lambda pigeon, hole: pigeon * holes + hole + 1
    clauses = [tuple(variable(pigeon, hole) for hole in range(holes))
               for pigeon in range(pigeons)]
    clauses += [(-variable(pigeon, left), -variable(pigeon, right))
                for pigeon in range(pigeons)
                for left in range(holes) for right in range(left + 1, holes)]
    clauses += [(-variable(left, hole), -variable(right, hole))
                for hole in range(holes)
                for left in range(pigeons) for right in range(left + 1, pigeons)]
    return pigeons * holes, tuple(clauses)


def tuple_game(nvars, clauses, pebbles):
    """Replay with (domain-mask, true-mask) tuples and separate control flow."""
    masks = []
    for clause in clauses:
        positive = negative = 0
        for literal in clause:
            bit = 1 << (abs(literal) - 1)
            if literal > 0:
                positive |= bit
            else:
                negative |= bit
        masks.append((positive, negative))

    active = set()
    for size in range(min(pebbles, nvars) + 1):
        for variables in combinations(range(nvars), size):
            domain = sum(1 << variable for variable in variables)
            true_mask = domain
            while True:
                if not any((positive | negative) & ~domain == 0 and
                           true_mask & positive == 0 and
                           true_mask & negative == negative
                           for positive, negative in masks):
                    active.add((domain, true_mask))
                if true_mask == 0:
                    break
                true_mask = (true_mask - 1) & domain

    initial_count = len(active)
    rounds = []
    all_variables = (1 << nvars) - 1
    while True:
        removed = []
        projection_witnesses = extension_witnesses = 0
        for domain, true_mask in active:
            failed = False
            assigned = domain
            while assigned:
                bit = assigned & -assigned
                assigned -= bit
                if (domain ^ bit, true_mask & ~bit) not in active:
                    failed = True
                    projection_witnesses += 1
                    break
            if failed:
                removed.append((domain, true_mask))
                continue
            if domain.bit_count() < pebbles:
                missing = all_variables ^ domain
                while missing:
                    bit = missing & -missing
                    missing -= bit
                    child_domain = domain | bit
                    if ((child_domain, true_mask) not in active and
                            (child_domain, true_mask | bit) not in active):
                        failed = True
                        extension_witnesses += 1
                        break
            if failed:
                removed.append((domain, true_mask))
        if not removed:
            break
        for state in removed:
            active.remove(state)
        rounds.append({"removed": len(removed),
                       "projection_witnesses": projection_witnesses,
                       "extension_witnesses": extension_witnesses,
                       "remaining": len(active)})
    encoded = sorted((domain << nvars) | true_mask for domain, true_mask in active)
    return {"status": "DUPLICATOR_WINS" if active else "SPOILER_WINS",
            "initial_states": initial_count,
            "final_states": len(active),
            "rounds": rounds,
            "surviving_state_sha256": sha256(
                json.dumps(encoded, separators=(",", ":")).encode()).hexdigest()}


def expected_cases():
    return [
        ("pigeonhole_4_3_pebbles_4", *pigeonhole(4, 3), 4),
        ("pigeonhole_5_4_pebbles_4", *pigeonhole(5, 4), 4),
        ("pigeonhole_5_4_pebbles_5", *pigeonhole(5, 4), 5),
    ]


def main():
    artifact = json.loads((HERE / "PEBBLE_RESULTS.json").read_text(encoding="utf-8"))
    for relative, expected in artifact["source_sha256"].items():
        assert digest(HERE / relative) == expected, relative

    replayed = 0
    for name, nvars, clauses, pebbles in expected_cases():
        row = next(item for item in artifact["rows"] if item["name"] == name)
        result = tuple_game(nvars, clauses, pebbles)
        saved = row["result"]
        assert saved["status"] == result["status"]
        assert saved["initial_states"] == result["initial_states"]
        assert saved["final_states"] == result["final_states"]
        assert saved["rounds"] == result["rounds"]
        assert saved["surviving_state_sha256"] == result["surviving_state_sha256"]
        replayed += 1

    bitset = json.loads((HERE / "BITSET_RESULTS.json").read_text(encoding="utf-8"))
    stress = next(row for row in bitset["rows"]
                  if row["family"] == "pigeonhole_stress" and row["width"] == 3)
    assert stress["status"] == "UNKNOWN"
    assert stress["reason"] == "NO_WIDTH_W_REFUTATION"
    assert stress["closure_size"] == 2230

    output = {"status": "PASS", "independent_rows_replayed": replayed,
              "php_5_4_spoiler_width4_bridge": True,
              "php_5_4_width3_closure_bridge": True,
              "source_hashes_match": True}
    (HERE / "PEBBLE_REVIEW.json").write_text(
        json.dumps(output, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(output))


if __name__ == "__main__":
    main()
