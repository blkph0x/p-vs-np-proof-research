"""Independent bounded replay. Imports neither chain.py nor a SAT solver."""
from __future__ import annotations

from collections import Counter
import gzip
import hashlib
from itertools import product
import json
from pathlib import Path
import re

HERE = Path(__file__).resolve().parent
SOURCE_NAMES = ("chain.py", "verify.py", "test_hierarchy.py",
                "run_experiments.py", "THEOREM.md")


def require(condition, message):
    if not condition:
        raise ValueError(message)


def text_hash(data):
    text = data.decode("utf-8").replace("\r\n", "\n").replace("\r", "\n")
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def original(k, sources):
    require(type(k) is int and 0 <= k <= 4, "unsupported finite visible width")
    require(type(sources) is list and len(sources) == max(1, 2*k - 1),
            "wrong source list")
    for spec in sources:
        require(type(spec) is dict and set(spec) == {"nvars", "clauses"}, "source fields")
        n = spec["nvars"]
        require(type(n) is int and 0 <= n <= 18, "source width")
        require(type(spec["clauses"]) is list, "source clauses")
        for row in spec["clauses"]:
            require(type(row) is list, "source clause")
            require(all(type(v) is int and v != 0 and abs(v) <= n for v in row),
                    "source literal")


def affine_by_closure(relation, k):
    """Translate by a member and check binary XOR closure directly."""
    points = {p for p in range(2**k) if relation & 2**p}
    if not points:
        return False
    anchor = min(points)
    translated = {p ^ anchor for p in points}
    return all(a ^ b in translated for a in translated for b in translated)


def expected_chain(k):
    if k < 2:
        return [sum(2**p for p in range(2**k))]
    answer = [1]
    for d in range(2, k + 1):
        # For d=2 this is the three-point nonaffine set, not a three-point subspace.
        preceding = {0, 1} if d == 2 else set(range(2**(d-1)))
        answer.append(sum(2**p for p in preceding | {2**(d-1)}))
        answer.append(sum(2**p for p in range(2**d)))
    return answer


def check_chain(record, k):
    require(type(record) is dict and set(record) ==
            {"visible_width", "affinity_bits", "depths", "canonical_chain"}, "chain fields")
    require(type(record["visible_width"]) is int and record["visible_width"] == k,
            "chain width")
    total = 2**(2**k)
    bits = record["affinity_bits"]
    depths = record["depths"]
    require(type(bits) is str and len(bits) == total and set(bits) <= {"0", "1"},
            "affinity array")
    require(type(depths) is list and len(depths) == total
            and all(type(d) is int and 0 <= d <= max(1, 2*k-1) for d in depths),
            "depth array")
    actual_affinity = [affine_by_closure(mask, k) for mask in range(total)]
    require(bits == "".join("1" if a else "0" for a in actual_affinity),
            "affinity criterion mismatch")
    # Forward propagation, independent of the producer's deletion recurrence.
    actual_depth = [0]*total
    for mask in range(total):
        for p in range(2**k):
            added = mask | 2**p
            if added != mask:
                cost = actual_depth[mask] + int(actual_affinity[added] != actual_affinity[mask])
                actual_depth[added] = max(actual_depth[added], cost)
    require(depths == actual_depth, "chain depth recurrence mismatch")
    require(all(bool(d % 2) == a for d, a in zip(depths, actual_affinity)),
            "depth parity mismatch")
    require(max(depths) == max(1, 2*k-1), "wrong attained chain bound")
    chain = record["canonical_chain"]
    require(type(chain) is list and all(type(v) is int for v in chain)
            and chain == expected_chain(k), "canonical chain")
    previous = 0
    for i, stage in enumerate(chain, 1):
        require(previous != stage and previous & stage == previous, "chain inclusion")
        require(affine_by_closure(stage, k) == bool(i % 2), "canonical chain parity")
        previous = stage
    return {"visible_width": k, "relations": total, "maximum_depth": max(depths),
            "depth_histogram": dict(sorted(Counter(depths).items()))}


def evaluate(clauses, values):
    # Tuple-of-bools evaluation, rather than the producer's assignment bit operations.
    for row in clauses:
        if not any(values[abs(lit)-1] if lit > 0 else not values[abs(lit)-1]
                   for lit in row):
            return False
    return True


def rebuild(k, sources):
    original(k, sources)
    stages = expected_chain(k)
    point_selectors = list(range(k, k + 2**k))
    cursor = k + 2**k
    source_blocks = []
    for spec in sources:
        source_blocks.append(list(range(cursor, cursor + spec["nvars"])))
        cursor += spec["nvars"]
    entered = []
    rows = [[v+1 for v in point_selectors]]
    for p in range(2**k):
        stage = 1
        while not stages[stage-1] & 2**p:
            stage += 1
        entered.append(stage)
        s = point_selectors[p]+1
        rows.extend([[-s, (j+1)*(1 if p & 2**j else -1)] for j in range(k)])
        for index in range(stage):
            for clause in sources[index]["clauses"]:
                mapped = [(source_blocks[index][abs(lit)-1]+1)*(1 if lit > 0 else -1)
                          for lit in clause]
                rows.append([-s] + mapped)
    payload = json.dumps({"visible_width": k, "sources": sources},
                         sort_keys=True, separators=(",", ":")).encode("utf-8")
    return {"schema": "fixed-width-affine-prefix-v1", "visible_width": k,
            "sources": sources, "input_sha256": hashlib.sha256(payload).hexdigest(),
            "nvars": cursor, "clauses": rows, "selectors": point_selectors,
            "source_variables": source_blocks, "entry_stage": entered,
            "canonical_chain": stages}


def check_reduction(k, sources, record):
    original(k, sources)
    fields = {"gadget", "source_sat", "longest_sat_prefix", "projection",
              "projection_affine", "source_formula_evaluations", "gadget_formula_evaluations"}
    require(type(record) is dict and set(record) == fields, "reduction fields")
    expected = rebuild(k, sources)
    # Strict JSON comparison distinguishes true from 1 in every nested field.
    canonical = lambda obj: json.dumps(obj, sort_keys=True, separators=(",", ":"))
    require(canonical(record["gadget"]) == canonical(expected), "original gadget mismatch")
    require(expected["nvars"] <= 18, "independent enumeration resource limit")
    truths = []
    source_work = 0
    for spec in sources:
        answers = [evaluate(spec["clauses"], values)
                   for values in product((False, True), repeat=spec["nvars"])]
        source_work += len(answers)
        truths.append(any(answers))
    prefix = next((i for i, sat in enumerate(truths) if not sat), len(truths))
    # Evaluate the nested difference separately, from its innermost predicate.
    nested_answer = False
    for sat in reversed(truths):
        nested_answer = sat and not nested_answer
    relation = 0
    formula_work = 0
    for values in product((False, True), repeat=expected["nvars"]):
        formula_work += 1
        if evaluate(expected["clauses"], values):
            word = sum(2**i for i in range(k) if values[i])
            relation |= 2**word
    affine = affine_by_closure(relation, k)
    require(affine == nested_answer, "nested SAT difference not preserved")
    expected_relation = expected["canonical_chain"][prefix-1] if prefix else 0
    require(relation == expected_relation, "unexpected projected relation")
    claims = {"source_sat": truths, "longest_sat_prefix": prefix, "projection": relation,
              "projection_affine": affine, "source_formula_evaluations": source_work,
              "gadget_formula_evaluations": formula_work}
    require(all(canonical(record[name]) == canonical(value) for name, value in claims.items()),
            "false reduction claim")
    return {"accepted": int(affine), "source_evaluations": source_work,
            "gadget_evaluations": formula_work, "width": k}


def verify_reduction(k, sources, record):
    try:
        return {"valid": True, "stats": check_reduction(k, sources, record), "errors": []}
    except (ValueError, TypeError, KeyError, IndexError, OverflowError) as exc:
        return {"valid": False, "errors": [str(exc)]}


def originals():
    for n, clauses in ((0, []), (0, [[]]), (1, [[1]]), (1, [[1], [-1]])):
        yield 0, [{"nvars": n, "clauses": clauses}]
    # Independent ternary-digit reconstruction of the nine clause choices.
    pool = []
    for number in range(9):
        left, right = divmod(number, 3)
        pool.append([i+1 if digit == 2 else -i-1
                     for i, digit in enumerate((left, right)) if digit != 1])
    for chosen in range(512):
        yield 1, [{"nvars": 2, "clauses": [pool[i] for i in range(9)
                                          if chosen & 2**i]}]
    for first in range(8):
        for second in range(8):
            for third in range(8):
                specs = []
                for code in (first, second, third):
                    clauses = []
                    if code & 1: clauses.append([])
                    if code & 2: clauses.append([1])
                    if code & 4: clauses.append([-1])
                    specs.append({"nvars": 1, "clauses": clauses})
                yield 2, specs
    for pattern in range(32):
        yield 3, [{"nvars": 0, "clauses": [] if pattern & 2**i else [[]]}
                  for i in range(5)]


def verify_artifact(artifact):
    try:
        require(type(artifact) is dict and set(artifact) ==
                {"schema", "convention", "chains", "reductions"}, "artifact fields")
        require(artifact["schema"] == "fixed-width-affine-hierarchy-v1"
                and artifact["convention"] == "nonempty_affine", "claim convention")
        require(type(artifact["chains"]) is list and len(artifact["chains"]) == 5,
                "missing or extra widths")
        chain_stats = [check_chain(record, k) for k, record in enumerate(artifact["chains"])]
        expected = list(originals())
        records = artifact["reductions"]
        require(type(records) is list and len(records) == len(expected), "campaign coverage")
        totals = Counter()
        by_width = Counter()
        for (k, specs), record in zip(expected, records):
            checked = check_reduction(k, specs, record)
            totals.update({key: checked[key] for key in
                           ("accepted", "source_evaluations", "gadget_evaluations")})
            by_width[k] += 1
        return {"valid": True, "status": "PASS", "errors": [], "chains": chain_stats,
                "relations": sum(item["relations"] for item in chain_stats),
                "reduction_cases": len(records), "cases_by_width": dict(by_width),
                **dict(totals)}
    except (ValueError, TypeError, KeyError, IndexError, OverflowError) as exc:
        return {"valid": False, "status": "INVALID", "errors": [str(exc)]}


def verify_saved():
    artifact_bytes = (HERE / "CERTIFICATE.json.gz").read_bytes()
    checked = verify_artifact(json.loads(gzip.decompress(artifact_bytes)))
    require(checked["valid"], str(checked["errors"]))
    results = json.loads((HERE / "RESULTS.json").read_text(encoding="utf-8"))
    require(results["schema"] == "fixed-width-affine-hierarchy-results-v1"
            and results["status"] == "PASS", "result schema or status")
    current = {name: text_hash((HERE/name).read_bytes()) for name in SOURCE_NAMES}
    require(results["source_sha256_lf"] == current
            and results["source_after_sha256_lf"] == current
            and results["sources_unchanged"] is True, "recorded source binding")
    require(results["certificate_sha256"] == hashlib.sha256(artifact_bytes).hexdigest(),
            "certificate digest")
    # JSON canonicalization removes only the integer/string distinction in dictionary keys.
    require(json.dumps(checked, sort_keys=True) ==
            json.dumps(results["independent_replay"], sort_keys=True), "recorded replay totals")
    require(type(results["tests"]) is list and len(results["tests"]) == 2,
            "normal/optimized test coverage")
    for run, optimized in zip(results["tests"], (False, True)):
        require(run["optimized"] is optimized and type(run["exit_code"]) is int
                and run["exit_code"] == 0, "test status")
        expected_name = "TESTS_OPTIMIZED.txt" if optimized else "TESTS_NORMAL.txt"
        require(run["transcript"] == expected_name, "test transcript path")
        transcript = (HERE/expected_name).read_bytes()
        require(text_hash(transcript) == run["sha256_lf"],
                "test transcript digest")
        counts = re.findall(r"Ran (\d+) tests? in", transcript.decode("utf-8"))
        require(counts == ["10"] and type(run["tests"]) is int and run["tests"] == 10
                and transcript.rstrip().endswith(b"OK"), "test transcript outcome")
    return checked


if __name__ == "__main__":
    answer = verify_saved()
    print(json.dumps(answer, indent=2, sort_keys=True))
