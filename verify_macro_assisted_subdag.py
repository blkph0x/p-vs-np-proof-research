"""Independent replay of the macro-assisted proof-DAG scan."""
from collections import Counter, OrderedDict
import copy
import json
from pathlib import Path
import verify_repeated_subdag_templates as base
import verify_symbolic_suffix_template as suffix_verify
ROOT=Path(__file__).resolve().parent

def verify_symbolic_result(result):
    try:
        clauses={base.norm_clause(c) for c in result["clauses"]}; rep=int(result["representative"]); local=tuple(int(v) for v in result["local"])
        if not local or clauses != {base.norm_clause((rep,)+local)} | {base.norm_clause((rep,-v)) for v in local}: return False
        expected=clauses | {(-rep,)}
        if {base.norm_clause(c) for c in result["certificate"]["premises"]} != expected: return False
        if not replay_symbolic(result["certificate"], expected): return False
        witness={int(v):bool(x) for v,x in result["witness"].items()}
        if set(witness)!={rep}|set(local) or witness[rep] is not True: return False
        return all(any((witness[abs(l)] if l>0 else not witness[abs(l)]) for l in c) for c in clauses)
    except (KeyError,TypeError,ValueError,IndexError,AssertionError): return False

def replay_symbolic(proof,premises):
    allowed={base.norm_clause(c) for c in premises}; nodes=[]
    for row in proof["nodes"]:
        clause=base.norm_clause(row["clause"])
        if row["kind"]=="leaf":
            if clause not in allowed: return False
        elif row["kind"]=="res":
            try:
                left=set(nodes[int(row["left"])]); right=set(nodes[int(row["right"])]); pivot=int(row["pivot"])
                if pivot in left and -pivot in right: expected=base.norm_clause((left-{pivot})|(right-{-pivot}))
                elif -pivot in left and pivot in right: expected=base.norm_clause((left-{-pivot})|(right-{pivot}))
                else: return False
            except (IndexError,TypeError): return False
            if clause != expected: return False
        else: return False
        nodes.append(clause)
    return 0 <= int(proof["root"]) < len(nodes) and nodes[int(proof["root"])] == ()

def verify_block(artifact):
    assert artifact["all_checks_passed"]
    params=artifact["parameters"]; nodes=base.replay_proof(artifact["proof_certificate"])
    assert len(nodes)==artifact["proof_nodes"]==4097 and nodes[int(artifact["proof_root"])]==()
    serialized=artifact["proof_certificate"]["nodes"]
    for row in artifact["records"]:
        if row["status"] == "FOUND_SUFFIX_SYMBOLIC":
            assert row["source_unknown_stage"] == "subdag_cap"
            suffix_result=row["suffix_result"]
            assert suffix_verify.verify_suffix_result(artifact["proof_certificate"],suffix_result)
            assert suffix_result["boundary"] == row["boundary"]
            assert row["candidate"] == suffix_result["candidate"]
            assert row["relation_bits"] == suffix_result["relation_bits"]
            assert row["visited_nodes"] == suffix_result["discovery_work"]
            assert row["leaf_clauses"] == [] and row["local"] == []
            continue
        if row["status"] != "FOUND_SYMBOLIC":
            base.verify_record(row,serialized,params["max_nodes"],params["max_local"]); continue
        assert row["source_unknown_stage"]=="projection_cap" and len(row["boundary"])==1
        extracted=base.extract_leaves(serialized,row["node_index"],params["max_nodes"]); assert extracted is not None
        leaves,visited=extracted; assert visited==row["visited_nodes"] and [list(c) for c in leaves]==row["leaf_clauses"]
        rep=int(row["boundary"][0])+1; symbolic=row["symbolic_result"]
        assert int(symbolic["representative"])==rep and tuple(symbolic["local"])==tuple(v+1 for v in row["local"])
        assert {base.norm_clause(c) for c in symbolic["clauses"]} == {base.norm_clause(c) for c in row["leaf_clauses"]}
        assert verify_symbolic_result(symbolic)
        assert row["candidate"]=={"kind":"UNIT","var":row["boundary"][0],"value":True}
        assert row["relation_bits"]==[0,1]
    statuses=Counter(r["status"] for r in artifact["records"]); kinds=Counter(r["candidate"]["kind"] for r in artifact["records"] if r["candidate"] is not None)
    assert dict(sorted(statuses.items()))==artifact["status_counts"]; assert dict(sorted(kinds.items()))==artifact["candidate_kind_counts"]
    grouped=OrderedDict()
    for row in artifact["records"]:
        if row["template_key"] is not None: grouped.setdefault(row["template_key"],[]).append(row)
    assert len(grouped)==len(artifact["template_groups"])
    for expected,(key,rows) in zip(artifact["template_groups"],grouped.items()):
        assert expected["template_key"]==key and expected["occurrences"]==len(rows) and expected["proof_nodes"]==[r["node_index"] for r in rows]
        naive=sum(r["naive_work"] for r in rows)
        reused=naive if rows[0]["status"] in ("FOUND_SYMBOLIC","FOUND_SUFFIX_SYMBOLIC") else rows[0]["naive_work"]+sum(r["projection_work"]+r["template_check_work"] for r in rows[1:])
        assert expected["naive_work"]==naive and expected["reused_work"]==reused and expected["saved_work"]==naive-reused
    first=next(r for r in artifact["records"] if r["status"]=="FOUND_SYMBOLIC"); forged=copy.deepcopy(first["symbolic_result"]); forged["certificate"]["nodes"][-1]["clause"]=[1]
    assert not verify_symbolic_result(forged)
    suffix_row=next(r for r in artifact["records"] if r["status"]=="FOUND_SUFFIX_SYMBOLIC")
    assert suffix_verify.mutate_and_reject(artifact["proof_certificate"],suffix_row["suffix_result"])
    assert artifact["adversarial"]["forged_symbolic_certificate_rejected"] and artifact["adversarial"]["forged_suffix_certificate_rejected"]
    assert artifact["source_unknown_projection_count"]==256 and artifact["source_unknown_subdag_count"]==2

def main():
    artifact=json.loads((ROOT/"MACRO_ASSISTED_SUBDAG.json").read_text(encoding="utf-8")); verify_block(artifact)
    print(json.dumps({"independent_checks_passed":True,"status_counts":artifact["status_counts"],"macro_unit_occurrences":sum(r["status"]=="FOUND_SYMBOLIC" for r in artifact["records"]),"source_unknown_projection_count":artifact["source_unknown_projection_count"]}))

if __name__=="__main__": main()
