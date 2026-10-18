"""Independent replay for the symbolic Hall-plus-implication rule."""
from __future__ import annotations
import copy
import json
from pathlib import Path
ROOT = Path(__file__).resolve().parent

def norm(clause):
    values = tuple(sorted(set(int(x) for x in clause), key=lambda z: (abs(z), z < 0)))
    assert not any(-value in values for value in values)
    return values

def formula(clauses): return tuple(sorted({norm(c) for c in clauses}))

def resolve(left, right, pivot):
    pivot=int(pivot); a,b=set(left),set(right)
    if pivot in a and -pivot in b: return norm((a-{pivot})|(b-{-pivot}))
    if -pivot in a and pivot in b: return norm((a-{-pivot})|(b-{pivot}))
    raise AssertionError("bad pivot")

def replay(proof, premises):
    allowed={norm(c) for c in premises}; nodes=[]
    for row in proof["nodes"]:
        clause=norm(row["clause"])
        if row["kind"] == "leaf": assert clause in allowed
        else:
            assert row["kind"] == "res"
            assert clause == resolve(nodes[int(row["left"])],nodes[int(row["right"])],row["pivot"])
        nodes.append(clause)
    assert nodes[int(proof["root"])] == ()
    return nodes

def expected_pattern(width):
    local=tuple(range(2,width+1)); return formula([(1,)+local]+[(1,-v) for v in local]),local

def verify_result(result,width):
    clauses,local=expected_pattern(width)
    assert result["status"] == "FOUND" and formula(result["clauses"]) == clauses
    assert int(result["representative"]) == 1 and tuple(result["local"]) == local
    assert result["relation_bits"] == [0,1]
    witness={int(v):bool(x) for v,x in result["witness"].items()}
    assert witness[1] is True and all(witness[v] is False for v in local)
    premises=formula(result["certificate"]["premises"])
    assert premises == formula(list(clauses)+[(-1,)])
    nodes=replay(result["certificate"],premises)
    assert len(nodes) == result["symbolic_certificate_nodes"]
    assert result["symbolic_discovery_work"] == len(clauses)+len(local)
    for clause in clauses: assert any((witness[abs(l)] if l>0 else not witness[abs(l)]) for l in clause)

def main():
    artifact=json.loads((ROOT/"SYMBOLIC_UNIT_TEMPLATE.json").read_text(encoding="utf-8"))
    assert artifact["all_checks_passed"]; widths=[]
    for row in artifact["rows"]:
        width=int(row["width"]); widths.append(width)
        verify_result({**row["symbolic_result"],"symbolic_certificate_nodes":row["symbolic_certificate_nodes"],"symbolic_discovery_work":row["symbolic_discovery_work"]},width)
        assert row["bounded_status"] == ("FOUND" if width-1 <= 6 else "UNKNOWN")
        assert row["exact_projection_assignments"] == 1 << width
        assert row["symbolic_certificate_nodes"] == 2*(width-1)+3
    assert widths == [2,3,4,7,8,16,32,64,128,256]
    forged=copy.deepcopy(artifact["rows"][-1]["symbolic_result"]); forged["certificate"]["nodes"][-1]["clause"]=[1]
    rejected=False
    try: verify_result({**forged,"symbolic_certificate_nodes":artifact["rows"][-1]["symbolic_certificate_nodes"],"symbolic_discovery_work":artifact["rows"][-1]["symbolic_discovery_work"]},256)
    except AssertionError: rejected=True
    assert rejected and artifact["near_miss_status"] == "UNKNOWN"
    assert artifact["adversarial"] == {"forged_certificate_rejected":True,"near_miss_rejected":True}
    print(json.dumps({"independent_checks_passed":True,"widths":widths,"bounded_unknown_from_width":8,"largest_certificate_nodes":artifact["rows"][-1]["symbolic_certificate_nodes"]}))

if __name__ == "__main__": main()
