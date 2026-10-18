"""A proof-producing symbolic Hall-plus-implication unit rule."""
from __future__ import annotations
import copy
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent

def normalize_clause(clause):
    values = tuple(sorted(set(int(x) for x in clause), key=lambda z: (abs(z), z < 0)))
    if any(-value in values for value in values):
        return None
    return values

def normalize_formula(clauses):
    result, seen = [], set()
    for clause in clauses:
        normalized = normalize_clause(clause)
        if normalized is None:
            return None
        if normalized not in seen:
            seen.add(normalized); result.append(normalized)
    return tuple(sorted(result))

def resolve(left, right, pivot):
    pivot = int(pivot); a, b = set(left), set(right)
    if pivot in a and -pivot in b:
        out = (a - {pivot}) | (b - {-pivot})
    elif -pivot in a and pivot in b:
        out = (a - {-pivot}) | (b - {pivot})
    else:
        raise ValueError("non-resolvable clauses")
    return normalize_clause(out)

def replay_resolution(proof, premises):
    allowed = {normalize_clause(clause) for clause in premises}; nodes = []
    for row in proof["nodes"]:
        clause = normalize_clause(row["clause"])
        if row["kind"] == "leaf":
            if clause not in allowed: return False
        elif row["kind"] == "res":
            try: expected = resolve(nodes[int(row["left"])], nodes[int(row["right"])], row["pivot"])
            except (IndexError, TypeError, ValueError): return False
            if clause != expected: return False
        else: return False
        nodes.append(clause)
    root = int(proof["root"])
    return 0 <= root < len(nodes) and nodes[root] == ()

def pattern_for_width(width, representative=1):
    if type(width) is not int or width < 2: raise ValueError("width must be an integer >= 2")
    if type(representative) is not int or representative < 1: raise ValueError("representative must be positive")
    local = tuple(representative + offset for offset in range(1, width))
    return ((representative,) + local,) + tuple((representative, -v) for v in local), local

def _pattern_match(clauses, representative):
    normalized = normalize_formula(clauses)
    if normalized is None or representative not in {abs(l) for c in normalized for l in c}: return None
    local = tuple(sorted({abs(l) for c in normalized for l in c} - {representative}))
    if not local: return None
    hall = normalize_clause((representative,) + local)
    implications = {normalize_clause((representative, -v)) for v in local}
    expected = {hall} | implications
    if set(normalized) != expected or len(normalized) != len(expected): return None
    return normalized, local

def build_unit_certificate(clauses, representative, local):
    normalized = normalize_formula(clauses); hall = normalize_clause((representative,) + tuple(local))
    premises = list(normalized) + [(-representative,)]; nodes, indices = [], {}
    for clause in premises:
        if clause not in indices:
            indices[clause] = len(nodes); nodes.append({"kind":"leaf", "clause":list(clause)})
    current = indices[hall]; current_clause = hall
    for variable in local:
        implication = normalize_clause((representative, -variable))
        current_clause = resolve(current_clause, implication, variable)
        nodes.append({"kind":"res", "clause":list(current_clause), "left":current, "right":indices[implication], "pivot":variable})
        current = len(nodes) - 1
    assert current_clause == (representative,)
    assert resolve(current_clause, (-representative,), representative) == ()
    nodes.append({"kind":"res", "clause":[], "left":current, "right":indices[(-representative,)], "pivot":representative})
    return {"premises":[list(c) for c in premises], "nodes":nodes, "root":len(nodes)-1}

def verify_unit_certificate(result):
    try:
        clauses = normalize_formula(result["clauses"]); representative = int(result["representative"])
        local = tuple(int(v) for v in result["local"]); matched = _pattern_match(clauses, representative)
        if matched is None or matched[1] != local: return False
        certificate = result["certificate"]; expected = normalize_formula(list(clauses) + [(-representative,)])
        if normalize_formula(certificate["premises"]) != expected or not replay_resolution(certificate, expected): return False
        witness = {int(v):bool(x) for v,x in result["witness"].items()}
        if set(witness) != {representative}|set(local) or witness[representative] is not True: return False
        return all(any((witness[abs(l)] if l > 0 else not witness[abs(l)]) for l in c) for c in clauses)
    except (KeyError, TypeError, ValueError, IndexError): return False

def recognize_unit_template(clauses, representative=None):
    normalized = normalize_formula(clauses)
    if normalized is None: return {"status":"UNKNOWN", "reason":"tautological clause"}
    variables = sorted({abs(l) for c in normalized for l in c}); candidates = [int(representative)] if representative is not None else variables
    for candidate in candidates:
        matched = _pattern_match(normalized, candidate)
        if matched is None: continue
        _, local = matched; certificate = build_unit_certificate(normalized, candidate, local)
        result = {"status":"FOUND", "kind":"UNIT", "clauses":[list(c) for c in normalized], "representative":candidate, "local":list(local), "relation_bits":[0,1], "witness":{str(candidate):True, **{str(v):False for v in local}}, "certificate":certificate, "discovery_work":len(normalized)+len(local)}
        if not verify_unit_certificate(result): raise AssertionError("invalid generated certificate")
        return result
    return {"status":"UNKNOWN", "reason":"Hall-plus-implication pattern not found"}

def bounded_projection_status(width, max_local=6):
    return "FOUND" if width - 1 <= max_local else "UNKNOWN"

def build_artifact():
    rows=[]
    for width in (2,3,4,7,8,16,32,64,128,256):
        clauses, local = pattern_for_width(width); symbolic = recognize_unit_template(clauses, representative=1); assert symbolic["status"] == "FOUND"
        rows.append({"width":width,"local_count":len(local),"bounded_max_local":6,"bounded_status":bounded_projection_status(width),"symbolic_status":symbolic["status"],"symbolic_certificate_nodes":len(symbolic["certificate"]["nodes"]),"symbolic_discovery_work":symbolic["discovery_work"],"exact_projection_assignments":1<<width,"symbolic_result":symbolic})
    near_miss,_=pattern_for_width(8); near_miss=list(near_miss[:-1])+[(1,7)]; forged=copy.deepcopy(rows[-1]["symbolic_result"]); forged["certificate"]["nodes"][-1]["clause"]=[1]; near_status=recognize_unit_template(near_miss, representative=1)["status"]
    artifact={"all_checks_passed":True,"bounded_rule":"local_count <= 6","rows":rows,"near_miss_status":near_status,"adversarial":{"forged_certificate_rejected":not verify_unit_certificate(forged),"near_miss_rejected":near_status=="UNKNOWN"}}
    assert artifact["adversarial"] == {"forged_certificate_rejected":True,"near_miss_rejected":True}; return artifact

def write_artifact():
    artifact=build_artifact(); (ROOT/"SYMBOLIC_UNIT_TEMPLATE.json").write_text(json.dumps(artifact,indent=2)+"\n",encoding="utf-8"); return artifact

if __name__ == "__main__": print(json.dumps(write_artifact(), indent=2))
