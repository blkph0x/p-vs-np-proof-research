"""Macro-assisted proof-DAG scan using a certified structural unit rule."""
from __future__ import annotations
from collections import Counter, OrderedDict
import copy
import json
from pathlib import Path
import repeated_subdag_templates as base
import symbolic_unit_template as symbolic
import symbolic_suffix_template as suffix

ROOT=Path(__file__).resolve().parent

def canonical_candidate(candidate,boundary):
    positions={int(v):i for i,v in enumerate(boundary)}; kind=candidate["kind"]
    if kind=="UNIT": return {"kind":kind,"var":positions[int(candidate["var"])],"value":bool(candidate["value"])}
    if kind=="PB":
        weights={str(positions[int(v)]):int(w) for v,w in candidate["weights"].items()}
        return {"kind":kind,"weights":dict(sorted(weights.items(),key=lambda x:int(x[0]))),"sense":candidate["sense"],"bound":int(candidate["bound"])}
    if kind=="TRUTH_TABLE": return {"kind":kind,"support":[positions[int(v)] for v in candidate["support"]],"accepted_mask":int(candidate["accepted_mask"])}
    return candidate

def key_for(row):
    return json.dumps({"status":row["status"],"candidate":row["canonical_candidate"],"relation_bits":row["relation_bits"]},sort_keys=True)

def build_groups(records):
    grouped=OrderedDict()
    for row in records:
        if row["template_key"] is not None: grouped.setdefault(row["template_key"],[]).append(row)
    groups=[]
    for i,(key,rows) in enumerate(grouped.items()):
        for row in rows: row["template_id"]=f"T{i}"
        first=rows[0]; naive=sum(r["naive_work"] for r in rows)
        if first["status"] in ("FOUND_SYMBOLIC","FOUND_SUFFIX_SYMBOLIC"):
            reused=naive
        else:
            reused=first["naive_work"]+sum(r["projection_work"]+r["template_check_work"] for r in rows[1:])
        groups.append({"template_id":f"T{i}","template_key":key,"status":first["status"],"canonical_candidate":first["canonical_candidate"],"relation_bits":first["relation_bits"],"occurrences":len(rows),"proof_nodes":[r["node_index"] for r in rows],"naive_work":naive,"reused_work":reused,"saved_work":naive-reused})
    return groups

def build_artifact():
    source=base.scan_repeated_templates(groups=256,width=8,max_boundary=2,max_local=6,max_nodes=32)
    records=[]
    for original in source["records"]:
        if original["status"]=="UNKNOWN" and original.get("unknown_stage")=="projection_cap" and len(original["boundary"])==1:
            representative=int(original["boundary"][0])+1
            result=symbolic.recognize_unit_template(original["leaf_clauses"],representative=representative)
            assert result["status"]=="FOUND" and symbolic.verify_unit_certificate(result)
            candidate={"kind":"UNIT","var":int(original["boundary"][0]),"value":True}
            row={"node_index":original["node_index"],"clause":original["clause"],"boundary":original["boundary"],"status":"FOUND_SYMBOLIC","candidate":candidate,"candidates":[candidate],"relation_bits":[0,1],"local":original["local"],"leaf_clauses":original["leaf_clauses"],"visited_nodes":original["visited_nodes"],"reason":None,"source_unknown_stage":original["unknown_stage"],"source_unknown_reason":original["reason"],"projection_work":0,"candidate_search_work":result["discovery_work"],"template_check_work":0,"naive_work":result["discovery_work"],"symbolic_discovery_work":result["discovery_work"],"symbolic_certificate_nodes":len(result["certificate"]["nodes"]),"symbolic_result":result}
            row["canonical_candidate"]=canonical_candidate(candidate,row["boundary"]); row["template_key"]=key_for(row); records.append(row)
        elif original["status"]=="UNKNOWN" and original.get("unknown_stage")=="subdag_cap":
            result=suffix.recognize_suffix_macro(source["proof_certificate"],original["node_index"],max_boundary=2)
            assert result["status"]=="FOUND" and suffix.verify_suffix_result(source["proof_certificate"],result)
            candidate=result["candidate"]
            row={"node_index":original["node_index"],"clause":original["clause"],"boundary":original["boundary"],"status":"FOUND_SUFFIX_SYMBOLIC","candidate":candidate,"candidates":[candidate],"relation_bits":result["relation_bits"],"local":[],"leaf_clauses":[],"visited_nodes":result["discovery_work"],"reason":None,"source_unknown_stage":original["unknown_stage"],"source_unknown_reason":original["reason"],"projection_work":0,"candidate_search_work":0,"template_check_work":0,"naive_work":result["discovery_work"],"symbolic_discovery_work":result["discovery_work"],"symbolic_certificate_nodes":result["discovery_work"],"suffix_result":result}
            row["canonical_candidate"]=canonical_candidate(candidate,row["boundary"]); row["template_key"]=key_for(row); records.append(row)
        else:
            row=copy.deepcopy(original); row["template_id"]=None; records.append(row)
    for row in records:
        if row["status"]!="FOUND_SYMBOLIC" and row["candidate"] is not None:
            row["canonical_candidate"]=canonical_candidate(row["candidate"],row["boundary"]); row["template_key"]=key_for(row)
    groups=build_groups(records)
    status_counts=Counter(r["status"] for r in records); kind_counts=Counter(r["candidate"]["kind"] for r in records if r["candidate"] is not None)
    forged=copy.deepcopy(next(r for r in records if r["status"]=="FOUND_SYMBOLIC")["symbolic_result"])
    forged["certificate"]["nodes"][-1]["clause"]=[1]
    suffix_row=next(r for r in records if r["status"]=="FOUND_SUFFIX_SYMBOLIC")
    forged_suffix=copy.deepcopy(suffix_row["suffix_result"])
    forged_suffix["candidate"]["bound"]=0
    artifact={"all_checks_passed":True,"parameters":{"groups":256,"width":8,"max_boundary":2,"max_local":6,"max_nodes":32},"proof_nodes":source["proof_nodes"],"proof_root":source["proof_root"],"proof_certificate":source["proof_certificate"],"source_scan_status_counts":source["status_counts"],"considered_nodes":len(records),"status_counts":dict(sorted(status_counts.items())),"candidate_kind_counts":dict(sorted(kind_counts.items())),"records":records,"template_groups":groups,"adversarial":{"forged_symbolic_certificate_rejected":not symbolic.verify_unit_certificate(forged),"forged_suffix_certificate_rejected":not suffix.verify_suffix_result(source["proof_certificate"],forged_suffix)},"source_unknown_projection_count":sum(r["status"]=="UNKNOWN" and r.get("unknown_stage")=="projection_cap" for r in source["records"]),"source_unknown_subdag_count":sum(r["status"]=="UNKNOWN" and r.get("unknown_stage")=="subdag_cap" for r in source["records"])}
    assert artifact["status_counts"]=={"FOUND":256,"FOUND_SUFFIX_SYMBOLIC":2,"FOUND_SYMBOLIC":256,"NO_COMPACT":1792}
    assert artifact["candidate_kind_counts"]=={"PB":257,"TRUTH_TABLE":1792,"UNIT":257}
    assert artifact["source_unknown_projection_count"]==256 and artifact["source_unknown_subdag_count"]==2
    assert all(artifact["adversarial"].values())
    return artifact

def write_artifact():
    artifact=build_artifact(); (ROOT/"MACRO_ASSISTED_SUBDAG.json").write_text(json.dumps(artifact,indent=2)+"\n",encoding="utf-8"); return artifact

if __name__=="__main__": print(json.dumps(write_artifact(),indent=2))
