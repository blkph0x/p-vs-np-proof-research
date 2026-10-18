"""Independent replay for the existential projection barrier fixture."""
from __future__ import annotations
from itertools import product
import copy
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parent


def norm(clause):
    vals=tuple(sorted(set(int(x) for x in clause),key=lambda z:(abs(z),z<0)))
    if any(-value in vals for value in vals):
        raise ValueError("tautology")
    return vals


def formula(clauses):
    out=[]; seen=set()
    for clause in clauses:
        value=norm(clause)
        if value not in seen:
            seen.add(value); out.append(value)
    return tuple(sorted(out))


def sat(clauses,assignment):
    return all(any((assignment[abs(lit)-1] if lit>0 else not assignment[abs(lit)-1]) for lit in clause) for clause in clauses)


def lift(clauses):
    return tuple(tuple(lit+1 if lit>0 else lit-1 for lit in clause) for clause in clauses)+((-1,),)


def projection(clauses,nvars):
    clauses=formula(clauses); lifted=lift(clauses); bits=[]
    for z in (False,True):
        bits.append(int(any(sat(lifted,(z,)+y) for y in product((False,True),repeat=nvars))))
    return tuple(bits)


def classify(bits):
    bits=tuple(int(x) for x in bits)
    return "UNIT_Z_FALSE" if bits==(1,0) else "EMPTY" if bits==(0,0) else "OTHER"


def verify(record):
    try:
        n=int(record["nvars"]); clauses=tuple(tuple(c) for c in record["g_clauses"]); normalized=formula(clauses)
        if [list(c) for c in normalized]!=record["g_clauses"]:
            return False
        models=[y for y in product((False,True),repeat=n) if sat(normalized,y)]
        bits=projection(normalized,n)
        return (record["boundary_width"]==1 and bool(record["g_satisfiable"])==bool(models)
                and record["g_model_count"]==len(models) and record["projection_bits"]==list(bits)
                and record["relation_class"]==classify(bits) and record["lifted_clauses"]==[list(c) for c in lift(normalized)])
    except (KeyError,TypeError,ValueError,IndexError):
        return False


def main():
    artifact=json.loads((ROOT/"PROJECTION_DISCOVERY_BARRIER.json").read_text(encoding="utf-8"))
    assert artifact["all_checks_passed"] and artifact["small_formula_count"]==256
    assert artifact["satisfiable_count"]==95 and artifact["unsatisfiable_count"]==161
    assert artifact["relation_class_counts"]=={"EMPTY":161,"UNIT_Z_FALSE":95,"OTHER":0}
    assert all(verify(row) for row in artifact["records"]+artifact["controls"])
    forged=copy.deepcopy(artifact["records"][0]); forged["relation_class"]="EMPTY" if forged["relation_class"]=="UNIT_Z_FALSE" else "UNIT_Z_FALSE"
    assert not verify(forged)
    assert artifact["adversarial"]=={"forged_record_rejected":True}
    print(json.dumps({"independent_checks_passed":True,"formula_count":artifact["small_formula_count"],"satisfiable":artifact["satisfiable_count"],"unsatisfiable":artifact["unsatisfiable_count"],"boundary_width":1}))


if __name__=="__main__":
    main()
